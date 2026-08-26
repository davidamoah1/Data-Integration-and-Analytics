"""MFA (Multi-Factor Authentication) domain models.

Future-ready architecture for TOTP-based MFA.
Supports enable/disable, backup codes, and recovery.
"""

from datetime import datetime, timezone

from sqlalchemy import JSON, TIMESTAMP, BigInteger, Boolean, Column, Integer, String, Text

from shared.database import Base, BigInt


class UserMFA(Base):
    """MFA configuration for a user (TOTP-based)."""

    __tablename__ = "user_mfa"

    id = Column(BigInt, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, nullable=False, index=True)
    method = Column(String(20), nullable=False, default="totp")  # totp, sms, email
    secret_encrypted = Column(Text, nullable=False)  # Fernet-encrypted TOTP secret
    backup_codes_hashed = Column(JSON, nullable=True)  # List of hashed backup codes
    is_enabled = Column(Boolean, nullable=False, default=False)
    enabled_at = Column(TIMESTAMP, nullable=True)
    failed_attempts = Column(Integer, nullable=False, default=0)
    last_used_at = Column(TIMESTAMP, nullable=True)
    created_at = Column(TIMESTAMP, default=datetime.now(timezone.utc), nullable=False)
    updated_at = Column(
        TIMESTAMP,
        default=datetime.now(timezone.utc),
        onupdate=datetime.now(timezone.utc),
        nullable=False,
    )


class MFASession(Base):
    """Tracks MFA verification state during login (pending â†’ verified)."""

    __tablename__ = "mfa_sessions"

    id = Column(BigInt, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, nullable=False, index=True)
    challenge_token = Column(String(255), nullable=False, unique=True, index=True)
    method = Column(String(20), nullable=False, default="totp")
    is_verified = Column(Boolean, nullable=False, default=False)
    expires_at = Column(TIMESTAMP, nullable=False)
    verified_at = Column(TIMESTAMP, nullable=True)
    created_at = Column(TIMESTAMP, default=datetime.now(timezone.utc), nullable=False)
