"""MFA (Multi-Factor Authentication) service layer.

Provides TOTP-based MFA setup, verification, and management.
Uses pyotp for TOTP generation and verification.

Future-ready: supports additional methods (SMS, email) via method field.
"""

from datetime import datetime, timedelta, timezone

import pyotp
from sqlalchemy import select
from sqlalchemy.orm import Session as DbSession

from authentication.mfa_models import MFASession, UserMFA
from shared.exceptions import AuthenticationError, NotFoundError, ValidationError
from shared.security import (
    ACCOUNT_LOCKOUT_THRESHOLD,
    decrypt_secret,
    encrypt_secret,
    generate_token,
)


class MFAService:
    """Service for MFA operations."""

    def __init__(self, db: DbSession):
        self.db = db

    def _get_mfa_config(self, user_id: int) -> UserMFA | None:
        return self.db.execute(
            select(UserMFA).where(UserMFA.user_id == user_id)
        ).scalar_one_or_none()

    def setup(self, user_id: int) -> dict:
        """Generate a new TOTP secret for the user.

        Returns the secret, QR URI, and backup codes.
        The MFA is not enabled until the user verifies with a code.
        """
        existing = self._get_mfa_config(user_id)
        if existing and existing.is_enabled:
            raise ValidationError("MFA is already enabled for this user")

        # Generate new TOTP secret
        secret = pyotp.random_base32()

        # Generate backup codes (10 codes)
        backup_codes = [generate_token(8) for _ in range(10)]

        # Hash backup codes for storage
        from shared.security import hash_password

        backup_codes_hashed = [hash_password(code) for code in backup_codes]

        if existing:
            # Update existing pending setup
            existing.secret_encrypted = encrypt_secret(secret)
            existing.backup_codes_hashed = backup_codes_hashed
            existing.is_enabled = False
            existing.failed_attempts = 0
        else:
            config = UserMFA(
                user_id=user_id,
                method="totp",
                secret_encrypted=encrypt_secret(secret),
                backup_codes_hashed=backup_codes_hashed,
                is_enabled=False,
            )
            self.db.add(config)

        self.db.commit()

        # Build QR URI for authenticator apps
        from authentication.repositories import UserRepository
        from config import MFA_TOTP_ISSUER

        user = UserRepository(self.db).get_by_id(user_id)
        issuer = MFA_TOTP_ISSUER
        account = user.email if user else str(user_id)
        qr_uri = pyotp.totp.TOTP(secret).provisioning_uri(name=account, issuer_name=issuer)

        return {
            "secret": secret,
            "qr_uri": qr_uri,
            "backup_codes": backup_codes,
        }

    def verify_and_enable(self, user_id: int, code: str) -> bool:
        """Verify a TOTP code and enable MFA for the user."""
        config = self._get_mfa_config(user_id)
        if not config:
            raise NotFoundError("MFA setup not found. Call setup first.")
        if config.is_enabled:
            raise ValidationError("MFA is already enabled")

        secret = decrypt_secret(config.secret_encrypted)
        totp = pyotp.TOTP(secret)

        if not totp.verify(code):
            config.failed_attempts += 1
            self.db.commit()
            raise AuthenticationError("Invalid verification code")

        config.is_enabled = True
        config.enabled_at = datetime.now(timezone.utc)
        config.failed_attempts = 0
        self.db.commit()
        return True

    def disable(self, user_id: int, code: str) -> bool:
        """Disable MFA for a user. Requires a valid TOTP code."""
        config = self._get_mfa_config(user_id)
        if not config or not config.is_enabled:
            raise NotFoundError("MFA is not enabled for this user")

        secret = decrypt_secret(config.secret_encrypted)
        totp = pyotp.TOTP(secret)

        if not totp.verify(code):
            raise AuthenticationError("Invalid verification code")

        self.db.delete(config)
        self.db.commit()
        return True

    def is_mfa_enabled(self, user_id: int) -> bool:
        """Check if MFA is enabled for a user."""
        config = self._get_mfa_config(user_id)
        return config is not None and config.is_enabled

    def create_challenge(self, user_id: int) -> str:
        """Create an MFA challenge during login flow.

        Returns a challenge token that the client uses to submit the MFA code.
        """
        config = self._get_mfa_config(user_id)
        if not config or not config.is_enabled:
            raise ValidationError("MFA is not enabled for this user")

        challenge_token = generate_token(32)
        challenge = MFASession(
            user_id=user_id,
            challenge_token=challenge_token,
            method="totp",
            is_verified=False,
            expires_at=datetime.now(timezone.utc) + timedelta(minutes=5),
        )
        self.db.add(challenge)
        self.db.commit()
        return challenge_token

    def verify_challenge(self, challenge_token: str, code: str) -> dict:
        """Verify an MFA challenge during login flow.

        Returns user_id if verified. Raises AuthenticationError if invalid.
        """
        challenge = self.db.execute(
            select(MFASession).where(MFASession.challenge_token == challenge_token)
        ).scalar_one_or_none()

        if not challenge:
            raise AuthenticationError("Invalid MFA challenge")

        if challenge.is_verified:
            raise AuthenticationError("MFA challenge already used")

        if challenge.expires_at < datetime.now(timezone.utc):
            raise AuthenticationError("MFA challenge has expired")

        config = self._get_mfa_config(challenge.user_id)
        if not config:
            raise AuthenticationError("MFA configuration not found")

        secret = decrypt_secret(config.secret_encrypted)
        totp = pyotp.TOTP(secret)

        # Check TOTP code
        if totp.verify(code):
            challenge.is_verified = True
            challenge.verified_at = datetime.now(timezone.utc)
            config.last_used_at = datetime.now(timezone.utc)
            config.failed_attempts = 0
            self.db.commit()
            return {"user_id": challenge.user_id, "verified": True}

        # Check backup codes
        if config.backup_codes_hashed:
            from shared.security import verify_password

            for i, hashed_code in enumerate(config.backup_codes_hashed):
                if verify_password(code, hashed_code):
                    # Remove used backup code
                    config.backup_codes_hashed.pop(i)
                    challenge.is_verified = True
                    challenge.verified_at = datetime.now(timezone.utc)
                    self.db.commit()
                    return {"user_id": challenge.user_id, "verified": True}

        config.failed_attempts += 1
        if config.failed_attempts >= ACCOUNT_LOCKOUT_THRESHOLD:
            config.is_enabled = False
            self.db.commit()
            raise AuthenticationError("Too many failed MFA attempts. MFA has been disabled, please re-setup.")
        self.db.commit()
        raise AuthenticationError("Invalid MFA code")

    def get_status(self, user_id: int) -> dict:
        """Get MFA status for a user."""
        config = self._get_mfa_config(user_id)
        if not config:
            return {"enabled": False, "method": None, "setup_pending": False}

        return {
            "enabled": config.is_enabled,
            "method": config.method,
            "setup_pending": not config.is_enabled,
            "enabled_at": config.enabled_at,
            "last_used_at": config.last_used_at,
            "backup_codes_remaining": (
                len(config.backup_codes_hashed) if config.backup_codes_hashed else 0
            ),
        }
