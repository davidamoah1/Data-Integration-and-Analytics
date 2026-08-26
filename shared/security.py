"""Security utilities â€” JWT tokens, password hashing, password policies.

Uses Argon2 for password hashing (preferred) with bcrypt fallback.
JWT tokens signed with HS256.
"""

import os
import re
import secrets
from datetime import datetime, timedelta, timezone
from uuid import uuid4

import jwt
from passlib.context import CryptContext

from config import (
    ENCRYPTION_KEY as _ENCRYPTION_KEY,
)
from config import (
    JWT_ACCESS_EXPIRE_MINUTES as _JWT_ACCESS_EXPIRE_MINUTES,
)
from config import (
    JWT_REFRESH_EXPIRE_DAYS as _JWT_REFRESH_EXPIRE_DAYS,
)
from config import (
    JWT_SECRET_KEY,
)

# --- Password hashing -------------------------------------------------------

pwd_context = CryptContext(
    schemes=["argon2", "bcrypt"],
    deprecated="auto",
    argon2__memory_cost=65536,
    argon2__time_cost=3,
    argon2__parallelism=4,
)


def hash_password(plain: str) -> str:
    """Hash a plaintext password using Argon2."""
    return pwd_context.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    """Verify a plaintext password against a hash."""
    try:
        return pwd_context.verify(plain, hashed)
    except Exception:
        return False


# --- JWT tokens -------------------------------------------------------------

JWT_ALGORITHM = "HS256"
JWT_ACCESS_EXPIRE_MINUTES = _JWT_ACCESS_EXPIRE_MINUTES
JWT_REFRESH_EXPIRE_DAYS = _JWT_REFRESH_EXPIRE_DAYS


def create_access_token(
    subject: str,
    extra_claims: dict | None = None,
    expires_minutes: int | None = None,
) -> str:
    """Create a short-lived JWT access token.

    Args:
        subject: User ID (string).
        extra_claims: Additional claims to embed (e.g. roles, org_id).
        expires_minutes: Override default expiry.

    Returns:
        Encoded JWT string.
    """
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=expires_minutes or JWT_ACCESS_EXPIRE_MINUTES
    )
    payload = {
        "sub": subject,
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "type": "access",
        "jti": uuid4().hex,
    }
    if extra_claims:
        payload.update(extra_claims)
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


def create_refresh_token(
    subject: str,
    extra_claims: dict | None = None,
    expires_days: int | None = None,
) -> str:
    """Create a long-lived JWT refresh token.

    Args:
        subject: User ID (string).
        extra_claims: Additional claims.
        expires_days: Override default expiry.

    Returns:
        Encoded JWT string.
    """
    expire = datetime.now(timezone.utc) + timedelta(days=expires_days or JWT_REFRESH_EXPIRE_DAYS)
    payload = {
        "sub": subject,
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "type": "refresh",
        "jti": uuid4().hex,
    }
    if extra_claims:
        payload.update(extra_claims)
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


def decode_token(token: str) -> dict:
    """Decode and verify a JWT token.

    Returns:
        Decoded payload dict.

    Raises:
        jwt.ExpiredSignatureError: If token has expired.
        jwt.InvalidTokenError: If token is invalid.
    """
    return jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])


# --- Password policy --------------------------------------------------------

PASSWORD_MIN_LENGTH = int(os.getenv("PASSWORD_MIN_LENGTH") or "8")
PASSWORD_REQUIRE_UPPERCASE = os.getenv("PASSWORD_REQUIRE_UPPERCASE", "true").lower() == "true"
PASSWORD_REQUIRE_LOWERCASE = os.getenv("PASSWORD_REQUIRE_LOWERCASE", "true").lower() == "true"
PASSWORD_REQUIRE_DIGIT = os.getenv("PASSWORD_REQUIRE_DIGIT", "true").lower() == "true"
PASSWORD_REQUIRE_SPECIAL = os.getenv("PASSWORD_REQUIRE_SPECIAL", "true").lower() == "true"
PASSWORD_HISTORY_COUNT = int(os.getenv("PASSWORD_HISTORY_COUNT") or "5")


def validate_password(password: str) -> list[str]:
    """Validate a password against the configured policy.

    Returns:
        List of error messages (empty if valid).
    """
    errors = []
    if len(password) < PASSWORD_MIN_LENGTH:
        errors.append(f"Password must be at least {PASSWORD_MIN_LENGTH} characters long")
    if PASSWORD_REQUIRE_UPPERCASE and not any(c.isupper() for c in password):
        errors.append("Password must contain at least one uppercase letter")
    if PASSWORD_REQUIRE_LOWERCASE and not any(c.islower() for c in password):
        errors.append("Password must contain at least one lowercase letter")
    if PASSWORD_REQUIRE_DIGIT and not any(c.isdigit() for c in password):
        errors.append("Password must contain at least one digit")
    if PASSWORD_REQUIRE_SPECIAL and not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password):
        errors.append("Password must contain at least one special character")
    return errors


def generate_token(length: int = 32) -> str:
    """Generate a cryptographically secure random token."""
    return secrets.token_urlsafe(length)


# --- Account lockout --------------------------------------------------------

ACCOUNT_LOCKOUT_THRESHOLD = int(os.getenv("ACCOUNT_LOCKOUT_THRESHOLD") or "5")
ACCOUNT_LOCKOUT_DURATION_MINUTES = int(os.getenv("ACCOUNT_LOCKOUT_DURATION_MINUTES") or "30")


# --- SQL identifier validation ------------------------------------------------

_SQL_IDENTIFIER_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def validate_sql_identifier(name: str) -> str:
    """Validate a string is a safe SQL identifier.

    Returns the identifier unchanged. Raises ValueError if it contains
    characters that could be used for SQL injection.
    """
    if not name or not _SQL_IDENTIFIER_RE.match(name):
        raise ValueError(f"Invalid SQL identifier: {name!r}")
    return name


# --- API key encryption ------------------------------------------------------

import base64 as _base64  # noqa: E402
import hashlib as _hashlib  # noqa: E402

from cryptography.fernet import Fernet, InvalidToken  # noqa: E402


def _get_fernet_key() -> bytes:
    """Derive a Fernet key for symmetric encryption.

    Uses ENCRYPTION_KEY if set, otherwise falls back to deriving from
    JWT_SECRET_KEY for development convenience. Production should set
    ENCRYPTION_KEY explicitly to avoid coupling with JWT secrets.
    """
    source = _ENCRYPTION_KEY if _ENCRYPTION_KEY else JWT_SECRET_KEY
    secret = source.encode()
    derived = _hashlib.sha256(secret).digest()
    return _base64.urlsafe_b64encode(derived)


def encrypt_secret(plaintext: str) -> str:
    """Encrypt a secret string using Fernet symmetric encryption.

    Args:
        plaintext: The secret to encrypt (e.g. an API key).

    Returns:
        Encrypted string safe for database storage.
    """
    if not plaintext:
        return ""
    f = Fernet(_get_fernet_key())
    return f.encrypt(plaintext.encode()).decode()


def decrypt_secret(ciphertext: str) -> str:
    """Decrypt a Fernet-encrypted secret.

    Args:
        ciphertext: The encrypted string from the database.

    Returns:
        Decrypted plaintext string, or empty string if decryption fails.
    """
    if not ciphertext:
        return ""
    try:
        f = Fernet(_get_fernet_key())
        return f.decrypt(ciphertext.encode()).decode()
    except InvalidToken:
        return ""
