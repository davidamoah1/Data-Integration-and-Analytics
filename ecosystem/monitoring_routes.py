"""Ecosystem monitoring routes — track connectors, plugins, API usage, and webhook health."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func as sa_func, select
from sqlalchemy.orm import Session as DbSession

from connectors.models import Connector, ConnectorExecution
from ecosystem.models import APIKey, APIUsageLog
from ecosystem.plugin_models import Plugin, PluginInstallation
from ecosystem.webhooks import WebhookDelivery, WebhookSubscription
from shared.database import get_db
from shared.dependencies import get_current_user
from shared.response import success_response
from shared.tenant import get_current_organization_id

monitoring_router = APIRouter(prefix="/ecosystem/monitoring", tags=["Ecosystem Monitoring"])


@monitoring_router.get("/overview")
async def ecosystem_overview(
    current_user: dict = Depends(get_current_user),
    db: DbSession = Depends(get_db),
):
    """Get ecosystem overview for the current organization."""
    org_id = get_current_organization_id(current_user, db)

    connectors = db.execute(
        select(sa_func.count(Connector.id)).where(Connector.organization_id == org_id)
    ).scalar() or 0
    active_connectors = db.execute(
        select(sa_func.count(Connector.id)).where(
            Connector.organization_id == org_id, Connector.status == "active"
        )
    ).scalar() or 0

    api_keys = db.execute(
        select(sa_func.count(APIKey.id)).where(
            APIKey.organization_id == org_id, APIKey.is_active == True  # noqa: E712
        )
    ).scalar() or 0

    installed_plugins = db.execute(
        select(sa_func.count(PluginInstallation.id)).where(
            PluginInstallation.organization_id == org_id
        )
    ).scalar() or 0

    webhooks = db.execute(
        select(sa_func.count(WebhookSubscription.id)).where(
            WebhookSubscription.organization_id == org_id, WebhookSubscription.is_active == True  # noqa: E712
        )
    ).scalar() or 0

    since = datetime.now(timezone.utc) - timedelta(days=1)
    api_calls_24h = db.execute(
        select(sa_func.count(APIUsageLog.id)).where(
            APIUsageLog.organization_id == org_id, APIUsageLog.created_at >= since
        )
    ).scalar() or 0

    failed_webhooks = db.execute(
        select(sa_func.count(WebhookDelivery.id)).where(
            WebhookDelivery.organization_id == org_id,
            WebhookDelivery.status == "failed",
            WebhookDelivery.created_at >= since,
        )
    ).scalar() or 0

    return success_response({
        "connectors": {"total": connectors, "active": active_connectors},
        "api_keys": api_keys,
        "installed_plugins": installed_plugins,
        "webhooks": {"total": webhooks, "failed_24h": failed_webhooks},
        "api_calls_24h": api_calls_24h,
    })


@monitoring_router.get("/connectors")
async def connector_health(
    current_user: dict = Depends(get_current_user),
    db: DbSession = Depends(get_db),
):
    """Get health status of all connectors."""
    org_id = get_current_organization_id(current_user, db)
    connectors = db.execute(
        select(Connector).where(Connector.organization_id == org_id).order_by(Connector.name)
    ).scalars().all()

    result = []
    for c in connectors:
        last_exec = db.execute(
            select(ConnectorExecution)
            .where(ConnectorExecution.connector_id == c.id)
            .order_by(ConnectorExecution.started_at.desc())
            .limit(1)
        ).scalar_one_or_none()

        result.append({
            "id": c.id,
            "name": c.name,
            "type": c.connector_type,
            "status": c.status,
            "last_tested": str(c.last_tested_at) if c.last_tested_at else None,
            "last_execution": {
                "status": last_exec.status if last_exec else None,
                "rows": last_exec.rows_extracted if last_exec else None,
                "completed_at": str(last_exec.completed_at) if last_exec and last_exec.completed_at else None,
            } if last_exec else None,
        })
    return success_response(result)


@monitoring_router.get("/webhooks")
async def webhook_health(
    days: int = Query(7, ge=1, le=30),
    current_user: dict = Depends(get_current_user),
    db: DbSession = Depends(get_db),
):
    """Get webhook delivery health."""
    org_id = get_current_organization_id(current_user, db)
    since = datetime.now(timezone.utc) - timedelta(days=days)

    subs = db.execute(
        select(WebhookSubscription).where(WebhookSubscription.organization_id == org_id)
    ).scalars().all()

    result = []
    for sub in subs:
        total = db.execute(
            select(sa_func.count(WebhookDelivery.id)).where(
                WebhookDelivery.subscription_id == sub.id,
                WebhookDelivery.created_at >= since,
            )
        ).scalar() or 0
        delivered = db.execute(
            select(sa_func.count(WebhookDelivery.id)).where(
                WebhookDelivery.subscription_id == sub.id,
                WebhookDelivery.status == "delivered",
                WebhookDelivery.created_at >= since,
            )
        ).scalar() or 0
        failed = db.execute(
            select(sa_func.count(WebhookDelivery.id)).where(
                WebhookDelivery.subscription_id == sub.id,
                WebhookDelivery.status == "failed",
                WebhookDelivery.created_at >= since,
            )
        ).scalar() or 0

        result.append({
            "id": sub.id,
            "url": sub.url,
            "is_active": sub.is_active,
            "total_deliveries": total,
            "delivered": delivered,
            "failed": failed,
            "success_rate": round(delivered / total * 100, 1) if total else 0,
        })
    return success_response(result)
