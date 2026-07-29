"""Webhook event system — models, dispatcher, and delivery."""

from __future__ import annotations

import hashlib
import hmac
import json
import logging
from datetime import datetime, timedelta, timezone

import requests
from sqlalchemy import JSON, TIMESTAMP, Boolean, Column, Integer, String, Text, func
from shared.database import Base, BigInt

logger = logging.getLogger("etl_project.webhooks")


class WebhookSubscription(Base):
    """Webhook endpoint subscription for an organization."""

    __tablename__ = "ecosystem_webhook_subscriptions"

    id = Column(BigInt, primary_key=True, autoincrement=True)
    organization_id = Column(BigInt, nullable=False, index=True)
    url = Column(String(1000), nullable=False)
    secret = Column(String(255), nullable=False)  # for HMAC signing
    events = Column(JSON, nullable=False)  # list of event types to subscribe to
    is_active = Column(Boolean, default=True, nullable=False)
    description = Column(String(500), nullable=True)
    created_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now(), nullable=False)


class WebhookDelivery(Base):
    """Record of a webhook delivery attempt."""

    __tablename__ = "ecosystem_webhook_deliveries"

    id = Column(BigInt, primary_key=True, autoincrement=True)
    subscription_id = Column(BigInt, nullable=False, index=True)
    organization_id = Column(BigInt, nullable=False, index=True)
    event_type = Column(String(100), nullable=False)
    payload = Column(JSON, nullable=True)
    status_code = Column(Integer, nullable=True)
    response_body = Column(Text, nullable=True)
    attempt = Column(Integer, nullable=False, default=1)
    status = Column(String(20), nullable=False, default="pending")  # pending, delivered, failed, retry
    error_message = Column(Text, nullable=True)
    delivered_at = Column(TIMESTAMP, nullable=True)
    next_retry_at = Column(TIMESTAMP, nullable=True)
    created_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)


# Supported event types
SUPPORTED_EVENTS = [
    "dataset.uploaded",
    "pipeline.completed",
    "pipeline.failed",
    "workflow.failed",
    "dashboard.generated",
    "model.trained",
    "report.exported",
    "alert.created",
    "connector.connected",
    "api_key.created",
    "api_key.revoked",
]


class WebhookDispatcher:
    """Dispatches events to subscribed webhook endpoints."""

    MAX_RETRIES = 3
    RETRY_DELAYS = [60, 300, 900]  # 1min, 5min, 15min

    @staticmethod
    def sign_payload(payload: str, secret: str) -> str:
        """Generate HMAC-SHA256 signature."""
        return hmac.new(secret.encode(), payload.encode(), hashlib.sha256).hexdigest()

    @staticmethod
    def get_subscriptions(db, org_id: int, event_type: str) -> list[WebhookSubscription]:
        """Get active subscriptions for an event type."""
        from sqlalchemy import select
        subs = (
            db.execute(
                select(WebhookSubscription).where(
                    WebhookSubscription.organization_id == org_id,
                    WebhookSubscription.is_active == True,  # noqa: E712
                )
            )
            .scalars()
            .all()
        )
        return [s for s in subs if event_type in (s.events or [])]

    @staticmethod
    def dispatch(db, org_id: int, event_type: str, payload: dict) -> None:
        """Dispatch an event to all matching subscriptions."""
        subs = WebhookDispatcher.get_subscriptions(db, org_id, event_type)
        for sub in subs:
            delivery = WebhookDelivery(
                subscription_id=sub.id,
                organization_id=org_id,
                event_type=event_type,
                payload=payload,
                status="pending",
            )
            db.add(delivery)
            db.flush()

            WebhookDispatcher._deliver(sub, delivery, payload)
            db.commit()

    @staticmethod
    def _deliver(sub: WebhookSubscription, delivery: WebhookDelivery, payload: dict) -> None:
        """Attempt to deliver a webhook."""
        body = json.dumps({"event": delivery.event_type, "data": payload, "timestamp": str(datetime.now(timezone.utc))})
        signature = WebhookDispatcher.sign_payload(body, sub.secret)

        try:
            resp = requests.post(
                sub.url,
                data=body,
                headers={
                    "Content-Type": "application/json",
                    "X-Webhook-Event": delivery.event_type,
                    "X-Webhook-Signature": signature,
                },
                timeout=30,
            )
            delivery.status_code = resp.status_code
            delivery.response_body = resp.text[:2000]
            if resp.status_code < 400:
                delivery.status = "delivered"
                delivery.delivered_at = datetime.now(timezone.utc)
            else:
                delivery.status = "failed"
                delivery.error_message = f"HTTP {resp.status_code}"
                if delivery.attempt < WebhookDispatcher.MAX_RETRIES:
                    delivery.status = "retry"
                    delay = WebhookDispatcher.RETRY_DELAYS[min(delivery.attempt - 1, len(WebhookDispatcher.RETRY_DELAYS) - 1)]
                    delivery.next_retry_at = datetime.now(timezone.utc) + timedelta(seconds=delay)
        except Exception as e:
            delivery.status = "failed"
            delivery.error_message = str(e)
            if delivery.attempt < WebhookDispatcher.MAX_RETRIES:
                delivery.status = "retry"
                delay = WebhookDispatcher.RETRY_DELAYS[min(delivery.attempt - 1, len(WebhookDispatcher.RETRY_DELAYS) - 1)]
                delivery.next_retry_at = datetime.now(timezone.utc) + timedelta(seconds=delay)

    @staticmethod
    def retry_pending(db) -> int:
        """Retry pending webhook deliveries. Returns count of retries."""
        from sqlalchemy import select
        now = datetime.now(timezone.utc)
        pending = (
            db.execute(
                select(WebhookDelivery).where(
                    WebhookDelivery.status == "retry",
                    WebhookDelivery.next_retry_at <= now,
                )
            )
            .scalars()
            .all()
        )
        count = 0
        for delivery in pending:
            sub = db.execute(
                select(WebhookSubscription).where(WebhookSubscription.id == delivery.subscription_id)
            ).scalar_one_or_none()
            if not sub or not sub.is_active:
                delivery.status = "failed"
                delivery.error_message = "Subscription inactive"
                continue
            delivery.attempt += 1
            payload = delivery.payload or {}
            WebhookDispatcher._deliver(sub, delivery, payload)
            count += 1
        if count:
            db.commit()
        return count
