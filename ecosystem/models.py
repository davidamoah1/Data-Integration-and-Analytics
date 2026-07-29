"""Public API Platform — API key management, usage tracking, and developer access."""

from __future__ import annotations

import hashlib
import secrets
from datetime import datetime, timedelta, timezone

from sqlalchemy import JSON, TIMESTAMP, Boolean, Column, Integer, String, Text, func
from shared.database import Base, BigInt


class APIKey(Base):
    """Developer API key for external access."""

    __tablename__ = "ecosystem_api_keys"

    id = Column(BigInt, primary_key=True, autoincrement=True)
    organization_id = Column(BigInt, nullable=False, index=True)
    user_id = Column(BigInt, nullable=False, index=True)
    name = Column(String(200), nullable=False)
    key_prefix = Column(String(20), nullable=False)  # first 8 chars for identification
    key_hash = Column(String(255), unique=True, nullable=False)  # SHA-256 hash of full key
    scopes = Column(JSON, nullable=True)  # list of allowed scopes: datasets, analytics, ai, workflows
    rate_limit_per_hour = Column(Integer, nullable=False, default=1000)
    is_active = Column(Boolean, default=True, nullable=False)
    expires_at = Column(TIMESTAMP, nullable=True)
    last_used_at = Column(TIMESTAMP, nullable=True)
    created_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)
    revoked_at = Column(TIMESTAMP, nullable=True)


class APIUsageLog(Base):
    """Per-request usage log for API keys."""

    __tablename__ = "ecosystem_api_usage_logs"

    id = Column(BigInt, primary_key=True, autoincrement=True)
    api_key_id = Column(BigInt, nullable=True, index=True)
    organization_id = Column(BigInt, nullable=True, index=True)
    endpoint = Column(String(500), nullable=False)
    method = Column(String(10), nullable=False)
    status_code = Column(Integer, nullable=False)
    response_time_ms = Column(Integer, nullable=True)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(500), nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(TIMESTAMP, server_default=func.now(), nullable=False, index=True)


class APIKeyService:
    """Service for API key lifecycle management."""

    @staticmethod
    def generate_key() -> tuple[str, str, str]:
        """Generate a new API key. Returns (raw_key, key_prefix, key_hash)."""
        raw_key = f"dfk_{secrets.token_urlsafe(32)}"
        key_prefix = raw_key[:12]
        key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
        return raw_key, key_prefix, key_hash

    @staticmethod
    def hash_key(raw_key: str) -> str:
        return hashlib.sha256(raw_key.encode()).hexdigest()

    @staticmethod
    def verify_key(raw_key: str, key_hash: str) -> bool:
        return APIKeyService.hash_key(raw_key) == key_hash
