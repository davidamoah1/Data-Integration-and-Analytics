"""Notification domain models."""

from datetime import datetime, timezone

from sqlalchemy import JSON, TIMESTAMP, BigInteger, Boolean, Column, String, Text

from shared.database import Base, BigInt


class Notification(Base):
    """In-app notification record for a user or organization."""

    __tablename__ = "notifications"

    id = Column(BigInt, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, nullable=True, index=True)
    organization_id = Column(BigInteger, nullable=True, index=True)
    channel = Column(String(20), nullable=False)  # email, sms, whatsapp, push, in_app
    subject = Column(String(255), nullable=False)
    body = Column(Text, nullable=False)
    status = Column(String(20), nullable=False, default="pending")  # pending, sent, failed, skipped
    read = Column(Boolean, nullable=False, default=False)
    metadata_ = Column("metadata", JSON, nullable=True, default=dict)
    created_at = Column(TIMESTAMP, default=datetime.now(timezone.utc), nullable=False)
    sent_at = Column(TIMESTAMP, nullable=True)
