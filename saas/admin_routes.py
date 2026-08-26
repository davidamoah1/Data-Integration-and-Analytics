"""Super Admin Portal routes â€” tenant management, platform analytics, oversight."""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func as sa_func
from sqlalchemy import select, update
from sqlalchemy.orm import Session as DbSession

from saas.models import (
    CustomerHealthScore,
    OnboardingRecord,
    Subscription,
    SubscriptionPlan,
    SupportTicket,
    UsageRecord,
)
from saas.services import SubscriptionService
from shared.database import get_db
from shared.dependencies import get_current_user
from shared.response import success_response
from shared.tenant import require_super_admin

admin_router = APIRouter(prefix="/api/admin-portal", tags=["Super Admin Portal"])


@admin_router.get("/overview")
async def platform_overview(
    current_user: dict = Depends(get_current_user),
    db: DbSession = Depends(get_db),
):
    """Platform-wide overview for super admins."""
    require_super_admin(current_user)

    from authentication.models import User
    from ecosystem.plugin_models import Plugin, PluginInstallation
    from organizations.models import Organization

    total_orgs = (
        db.execute(
            select(sa_func.count(Organization.id)).where(Organization.is_deleted == 0)
        ).scalar()
        or 0
    )
    active_orgs = (
        db.execute(
            select(sa_func.count(Organization.id)).where(
                Organization.is_deleted == 0, Organization.is_active == 1
            )
        ).scalar()
        or 0
    )
    total_users = (
        db.execute(select(sa_func.count(User.id)).where(User.is_deleted == 0)).scalar() or 0
    )
    active_users = (
        db.execute(
            select(sa_func.count(User.id)).where(User.is_deleted == 0, User.is_active == 1)
        ).scalar()
        or 0
    )
    total_subscriptions = (
        db.execute(
            select(sa_func.count(Subscription.id)).where(
                Subscription.status.in_(["active", "trial"])
            )
        ).scalar()
        or 0
    )
    total_plugins = db.execute(select(sa_func.count(Plugin.id))).scalar() or 0
    total_installations = db.execute(select(sa_func.count(PluginInstallation.id))).scalar() or 0
    open_tickets = (
        db.execute(
            select(sa_func.count(SupportTicket.id)).where(SupportTicket.status == "open")
        ).scalar()
        or 0
    )

    # Revenue estimate
    subs = db.execute(
        select(Subscription, SubscriptionPlan)
        .join(SubscriptionPlan, Subscription.plan_id == SubscriptionPlan.id)
        .where(Subscription.status.in_(["active", "trial"]))
    ).all()
    monthly_revenue = sum(p.price_monthly for _, p in subs if p.price_monthly)

    return success_response(
        {
            "organizations": {"total": total_orgs, "active": active_orgs},
            "users": {"total": total_users, "active": active_users},
            "subscriptions": total_subscriptions,
            "monthly_revenue_estimate": monthly_revenue,
            "marketplace": {"plugins": total_plugins, "installations": total_installations},
            "support": {"open_tickets": open_tickets},
        }
    )


@admin_router.get("/tenants")
async def list_tenants(
    search: str | None = Query(None),
    limit: int = Query(50, ge=1, le=200),
    current_user: dict = Depends(get_current_user),
    db: DbSession = Depends(get_db),
):
    """List all tenants (organizations) with subscription info."""
    require_super_admin(current_user)

    from authentication.models import User
    from organizations.models import Organization

    query = select(Organization).where(Organization.is_deleted == 0)
    if search:
        query = query.where(Organization.name.ilike(f"%{search}%"))
    orgs = db.execute(query.order_by(Organization.created_at.desc()).limit(limit)).scalars().all()

    result = []
    for org in orgs:
        user_count = (
            db.execute(
                select(sa_func.count(User.id)).where(
                    User.organization_id == org.id, User.is_deleted == 0
                )
            ).scalar()
            or 0
        )

        sub = (
            db.execute(
                select(Subscription)
                .where(
                    Subscription.organization_id == org.id,
                    Subscription.status.in_(["active", "trial", "past_due"]),
                )
                .order_by(Subscription.created_at.desc())
                .limit(1)
            )
            .scalars()
            .first()
        )

        plan_name = "free"
        sub_status = "none"
        if sub:
            plan = db.execute(
                select(SubscriptionPlan).where(SubscriptionPlan.id == sub.plan_id)
            ).scalar_one_or_none()
            plan_name = plan.plan_code if plan else "free"
            sub_status = sub.status

        result.append(
            {
                "id": org.id,
                "name": org.name,
                "slug": org.slug,
                "is_active": bool(org.is_active),
                "user_count": user_count,
                "plan": plan_name,
                "subscription_status": sub_status,
                "created_at": str(org.created_at) if org.created_at else None,
            }
        )

    return success_response(result)


@admin_router.get("/tenants/{org_id}")
async def get_tenant_detail(
    org_id: int,
    current_user: dict = Depends(get_current_user),
    db: DbSession = Depends(get_db),
):
    """Get detailed information about a specific tenant."""
    require_super_admin(current_user)

    from authentication.models import User
    from organizations.models import Organization

    org = db.execute(select(Organization).where(Organization.id == org_id)).scalar_one_or_none()
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")

    users = (
        db.execute(select(User).where(User.organization_id == org_id, User.is_deleted == 0))
        .scalars()
        .all()
    )

    sub_service = SubscriptionService(db)
    sub_status = sub_service.check_subscription_status(org_id)
    usage = sub_service.get_usage(org_id)

    # Onboarding
    onboarding = db.execute(
        select(OnboardingRecord).where(OnboardingRecord.organization_id == org_id)
    ).scalar_one_or_none()

    # Health score
    health = (
        db.execute(
            select(CustomerHealthScore)
            .where(CustomerHealthScore.organization_id == org_id)
            .order_by(CustomerHealthScore.computed_at.desc())
            .limit(1)
        )
        .scalars()
        .first()
    )

    return success_response(
        {
            "organization": {
                "id": org.id,
                "name": org.name,
                "slug": org.slug,
                "is_active": bool(org.is_active),
                "created_at": str(org.created_at) if org.created_at else None,
            },
            "users": [
                {
                    "id": u.id,
                    "email": u.email,
                    "full_name": u.full_name,
                    "is_active": bool(u.is_active),
                }
                for u in users
            ],
            "subscription": sub_status,
            "usage": usage,
            "onboarding": (
                {
                    "completion_percentage": onboarding.completion_percentage if onboarding else 0,
                    "is_complete": onboarding.is_complete if onboarding else False,
                    "current_step": onboarding.current_step if onboarding else None,
                }
                if onboarding
                else None
            ),
            "health_score": (
                {
                    "score": health.score,
                    "status": health.status,
                    "factors": health.factors,
                }
                if health
                else None
            ),
        }
    )


@admin_router.post("/tenants/{org_id}/suspend")
async def suspend_tenant(
    org_id: int,
    current_user: dict = Depends(get_current_user),
    db: DbSession = Depends(get_db),
):
    """Suspend an organization."""
    require_super_admin(current_user)
    from organizations.models import Organization

    db.execute(update(Organization).where(Organization.id == org_id).values(is_active=0))
    db.commit()
    return success_response(None, "Organization suspended")


@admin_router.post("/tenants/{org_id}/activate")
async def activate_tenant(
    org_id: int,
    current_user: dict = Depends(get_current_user),
    db: DbSession = Depends(get_db),
):
    """Activate a suspended organization."""
    require_super_admin(current_user)
    from organizations.models import Organization

    db.execute(update(Organization).where(Organization.id == org_id).values(is_active=1))
    db.commit()
    return success_response(None, "Organization activated")


@admin_router.get("/subscriptions")
async def list_all_subscriptions(
    current_user: dict = Depends(get_current_user),
    db: DbSession = Depends(get_db),
):
    """List all subscriptions across the platform."""
    require_super_admin(current_user)
    subs = db.execute(
        select(Subscription, SubscriptionPlan)
        .join(SubscriptionPlan, Subscription.plan_id == SubscriptionPlan.id)
        .order_by(Subscription.created_at.desc())
    ).all()
    return success_response(
        [
            {
                "id": sub.id,
                "organization_id": sub.organization_id,
                "plan": plan.plan_code,
                "plan_name": plan.name,
                "status": sub.status,
                "billing_cycle": sub.billing_cycle,
                "current_period_end": (
                    str(sub.current_period_end) if sub.current_period_end else None
                ),
                "trial_end": str(sub.trial_end) if sub.trial_end else None,
            }
            for sub, plan in subs
        ]
    )


@admin_router.get("/usage-summary")
async def platform_usage_summary(
    days: int = Query(30, ge=1, le=365),
    current_user: dict = Depends(get_current_user),
    db: DbSession = Depends(get_db),
):
    """Aggregate usage across all organizations."""
    require_super_admin(current_user)
    datetime.now(timezone.utc)

    total_ai = db.execute(select(sa_func.sum(UsageRecord.ai_requests))).scalar() or 0
    total_api = db.execute(select(sa_func.sum(UsageRecord.api_calls))).scalar() or 0
    total_workflows = db.execute(select(sa_func.sum(UsageRecord.workflow_executions))).scalar() or 0
    total_storage = db.execute(select(sa_func.sum(UsageRecord.storage_used_mb))).scalar() or 0

    return success_response(
        {
            "total_ai_requests": total_ai,
            "total_api_calls": total_api,
            "total_workflow_executions": total_workflows,
            "total_storage_mb": total_storage,
        }
    )


@admin_router.get("/support/tickets")
async def list_all_support_tickets(
    status: str | None = Query(None),
    current_user: dict = Depends(get_current_user),
    db: DbSession = Depends(get_db),
):
    """List all support tickets across the platform."""
    require_super_admin(current_user)
    query = select(SupportTicket)
    if status:
        query = query.where(SupportTicket.status == status)
    tickets = db.execute(query.order_by(SupportTicket.created_at.desc())).scalars().all()
    return success_response(
        [
            {
                "id": t.id,
                "organization_id": t.organization_id,
                "subject": t.subject,
                "priority": t.priority,
                "status": t.status,
                "category": t.category,
                "created_at": str(t.created_at) if t.created_at else None,
            }
            for t in tickets
        ]
    )


@admin_router.post("/support/tickets/{ticket_id}/resolve")
async def resolve_ticket(
    ticket_id: int,
    current_user: dict = Depends(get_current_user),
    db: DbSession = Depends(get_db),
):
    """Resolve a support ticket."""
    require_super_admin(current_user)
    ticket = db.execute(
        select(SupportTicket).where(SupportTicket.id == ticket_id)
    ).scalar_one_or_none()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    ticket.status = "resolved"
    ticket.resolved_at = datetime.now(timezone.utc)
    db.commit()
    return success_response(None, "Ticket resolved")
