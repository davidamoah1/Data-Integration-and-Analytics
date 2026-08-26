"""FastAPI routes for the Webhook Event System."""

from __future__ import annotations

import secrets

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session as DbSession

from ecosystem.webhooks import (
    SUPPORTED_EVENTS,
    WebhookDelivery,
    WebhookDispatcher,
    WebhookSubscription,
)
from shared.database import get_db
from shared.dependencies import get_current_user
from shared.response import success_response
from shared.tenant import get_current_organization_id

webhook_router = APIRouter(prefix="/api/webhooks", tags=["Platform / Webhooks"])


class WebhookCreate(BaseModel):
    url: str = Field(..., min_length=1)
    events: list[str]
    description: str | None = None


class WebhookUpdate(BaseModel):
    url: str | None = None
    events: list[str] | None = None
    is_active: bool | None = None
    description: str | None = None


@webhook_router.get("/events")
async def list_supported_events(
    current_user: dict = Depends(get_current_user),
):
    """List all supported webhook event types."""
    return success_response(SUPPORTED_EVENTS)


@webhook_router.post("")
async def create_webhook(
    body: WebhookCreate,
    current_user: dict = Depends(get_current_user),
    db: DbSession = Depends(get_db),
):
    """Create a webhook subscription."""
    org_id = get_current_organization_id(current_user, db)
    invalid = [e for e in body.events if e not in SUPPORTED_EVENTS]
    if invalid:
        raise HTTPException(status_code=400, detail=f"Unsupported events: {invalid}")

    secret = secrets.token_urlsafe(32)
    sub = WebhookSubscription(
        organization_id=org_id,
        url=body.url,
        secret=secret,
        events=body.events,
        description=body.description,
    )
    db.add(sub)
    db.flush()
    db.commit()
    return success_response(
        {
            "id": sub.id,
            "url": sub.url,
            "events": sub.events,
            "secret": secret,  # only shown once
            "is_active": sub.is_active,
        },
        "Webhook created â€” save the secret for signature verification",
    )


@webhook_router.get("")
async def list_webhooks(
    current_user: dict = Depends(get_current_user),
    db: DbSession = Depends(get_db),
):
    """List webhook subscriptions for the current organization."""
    org_id = get_current_organization_id(current_user, db)
    subs = (
        db.execute(
            select(WebhookSubscription)
            .where(WebhookSubscription.organization_id == org_id)
            .order_by(WebhookSubscription.created_at.desc())
        )
        .scalars()
        .all()
    )
    return success_response(
        [
            {
                "id": s.id,
                "url": s.url,
                "events": s.events,
                "is_active": s.is_active,
                "description": s.description,
                "created_at": str(s.created_at) if s.created_at else None,
            }
            for s in subs
        ]
    )


@webhook_router.delete("/{webhook_id}")
async def delete_webhook(
    webhook_id: int,
    current_user: dict = Depends(get_current_user),
    db: DbSession = Depends(get_db),
):
    """Delete a webhook subscription."""
    org_id = get_current_organization_id(current_user, db)
    sub = db.execute(
        select(WebhookSubscription).where(
            WebhookSubscription.id == webhook_id,
            WebhookSubscription.organization_id == org_id,
        )
    ).scalar_one_or_none()
    if not sub:
        raise HTTPException(status_code=404, detail="Webhook not found")
    db.delete(sub)
    db.commit()
    return success_response(None, "Webhook deleted")


@webhook_router.get("/{webhook_id}/deliveries")
async def list_deliveries(
    webhook_id: int,
    limit: int = Query(20, ge=1, le=100),
    current_user: dict = Depends(get_current_user),
    db: DbSession = Depends(get_db),
):
    """List delivery history for a webhook."""
    org_id = get_current_organization_id(current_user, db)
    deliveries = (
        db.execute(
            select(WebhookDelivery)
            .where(
                WebhookDelivery.subscription_id == webhook_id,
                WebhookDelivery.organization_id == org_id,
            )
            .order_by(WebhookDelivery.created_at.desc())
            .limit(limit)
        )
        .scalars()
        .all()
    )
    return success_response(
        [
            {
                "id": d.id,
                "event_type": d.event_type,
                "status": d.status,
                "status_code": d.status_code,
                "attempt": d.attempt,
                "error_message": d.error_message,
                "delivered_at": str(d.delivered_at) if d.delivered_at else None,
                "created_at": str(d.created_at) if d.created_at else None,
            }
            for d in deliveries
        ]
    )


@webhook_router.post("/{webhook_id}/redeliver/{delivery_id}")
async def redeliver(
    webhook_id: int,
    delivery_id: int,
    current_user: dict = Depends(get_current_user),
    db: DbSession = Depends(get_db),
):
    """Redeliver a failed webhook delivery."""
    org_id = get_current_organization_id(current_user, db)
    sub = db.execute(
        select(WebhookSubscription).where(
            WebhookSubscription.id == webhook_id,
            WebhookSubscription.organization_id == org_id,
        )
    ).scalar_one_or_none()
    if not sub:
        raise HTTPException(status_code=404, detail="Webhook not found")

    delivery = db.execute(
        select(WebhookDelivery).where(WebhookDelivery.id == delivery_id)
    ).scalar_one_or_none()
    if not delivery:
        raise HTTPException(status_code=404, detail="Delivery not found")

    WebhookDispatcher._deliver(sub, delivery, delivery.payload or {})
    db.commit()
    return success_response({"status": delivery.status}, "Webhook redelivered")
