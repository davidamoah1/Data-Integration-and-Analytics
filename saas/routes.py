"""FastAPI routes for SaaS Platform â€” subscriptions, billing, feature flags, onboarding."""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session as DbSession

from saas.models import (
    NotificationPreference,
    SupportTicket,
    SystemAnnouncement,
)
from saas.services import (
    CustomerSuccessService,
    FeatureFlagService,
    OnboardingService,
    SubscriptionService,
)
from shared.database import get_db
from shared.dependencies import get_current_user
from shared.response import success_response
from shared.tenant import get_current_organization_id, require_super_admin

router = APIRouter(prefix="/api/saas", tags=["SaaS Platform"])


# â”€â”€â”€ Schemas â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€


class SubscribeRequest(BaseModel):
    plan_code: str
    billing_cycle: str = "monthly"
    is_trial: bool = False


class UpgradeRequest(BaseModel):
    plan_code: str


class FeatureOverrideRequest(BaseModel):
    flag_key: str
    is_enabled: bool
    reason: str | None = None


class OnboardingStepRequest(BaseModel):
    step_key: str
    industry: str | None = None


class SupportTicketCreate(BaseModel):
    subject: str = Field(..., min_length=1)
    description: str | None = None
    priority: str = "normal"
    category: str | None = None


class AnnouncementCreate(BaseModel):
    title: str
    message: str
    severity: str = "info"
    target_audience: str = "all"
    ends_at: str | None = None


class NotificationPrefUpdate(BaseModel):
    channel_in_app: bool | None = None
    channel_email: bool | None = None
    channel_sms: bool | None = None
    channel_webhook: bool | None = None
    event_workflow_completed: bool | None = None
    event_dataset_processed: bool | None = None
    event_subscription_changes: bool | None = None
    event_security_alerts: bool | None = None
    event_billing_reminders: bool | None = None
    event_system_maintenance: bool | None = None


# â”€â”€â”€ Subscription Plans â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€


@saas_router.get("/plans")
async def list_plans(
    current_user: dict = Depends(get_current_user),
    db: DbSession = Depends(get_db),
):
    """List all available subscription plans."""
    service = SubscriptionService(db)
    plans = service.list_plans(public_only=True)
    return success_response(
        [
            {
                "id": p.id,
                "plan_code": p.plan_code,
                "name": p.name,
                "description": p.description,
                "price_monthly": p.price_monthly,
                "price_yearly": p.price_yearly,
                "currency": p.currency,
                "max_users": p.max_users,
                "max_storage_mb": p.max_storage_mb,
                "features": p.features,
                "is_trial_available": p.is_trial_available,
                "trial_days": p.trial_days,
            }
            for p in plans
        ]
    )


@saas_router.get("/subscription")
async def get_subscription(
    current_user: dict = Depends(get_current_user),
    db: DbSession = Depends(get_db),
):
    """Get the current organization's subscription status."""
    org_id = get_current_organization_id(current_user, db)
    service = SubscriptionService(db)
    status = service.check_subscription_status(org_id)
    usage = service.get_usage(org_id)
    return success_response({**status, "usage": usage})


@saas_router.post("/subscribe")
async def subscribe(
    body: SubscribeRequest,
    current_user: dict = Depends(get_current_user),
    db: DbSession = Depends(get_db),
):
    """Create a new subscription for the current organization."""
    org_id = get_current_organization_id(current_user, db)
    service = SubscriptionService(db)
    sub = service.create_subscription(org_id, body.plan_code, body.billing_cycle, body.is_trial)
    return success_response(
        {"id": sub.id, "status": sub.status, "plan": body.plan_code}, "Subscription created"
    )


@saas_router.post("/upgrade")
async def upgrade(
    body: UpgradeRequest,
    current_user: dict = Depends(get_current_user),
    db: DbSession = Depends(get_db),
):
    """Upgrade or downgrade the current subscription."""
    org_id = get_current_organization_id(current_user, db)
    service = SubscriptionService(db)
    sub = service.upgrade_subscription(org_id, body.plan_code)
    return success_response({"id": sub.id, "status": sub.status}, "Subscription updated")


@saas_router.post("/cancel")
async def cancel_subscription(
    current_user: dict = Depends(get_current_user),
    db: DbSession = Depends(get_db),
):
    """Cancel the current subscription."""
    org_id = get_current_organization_id(current_user, db)
    service = SubscriptionService(db)
    sub = service.cancel_subscription(org_id)
    return success_response({"id": sub.id, "status": sub.status}, "Subscription cancelled")


# â”€â”€â”€ Usage & Invoices â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€


@saas_router.get("/usage")
async def get_usage(
    current_user: dict = Depends(get_current_user),
    db: DbSession = Depends(get_db),
):
    """Get current usage metrics for the organization."""
    org_id = get_current_organization_id(current_user, db)
    service = SubscriptionService(db)
    return success_response(service.get_usage(org_id))


@saas_router.get("/invoices")
async def list_invoices(
    current_user: dict = Depends(get_current_user),
    db: DbSession = Depends(get_db),
):
    """List billing invoices for the organization."""
    org_id = get_current_organization_id(current_user, db)
    service = SubscriptionService(db)
    invoices = service.list_invoices(org_id)
    return success_response(
        [
            {
                "id": inv.id,
                "invoice_number": inv.invoice_number,
                "amount": inv.amount,
                "currency": inv.currency,
                "status": inv.status,
                "billing_period_start": (
                    str(inv.billing_period_start) if inv.billing_period_start else None
                ),
                "billing_period_end": (
                    str(inv.billing_period_end) if inv.billing_period_end else None
                ),
                "paid_at": str(inv.paid_at) if inv.paid_at else None,
            }
            for inv in invoices
        ]
    )


# â”€â”€â”€ Feature Flags â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€


@saas_router.get("/features")
async def get_features(
    current_user: dict = Depends(get_current_user),
    db: DbSession = Depends(get_db),
):
    """Get enabled features for the current organization."""
    org_id = get_current_organization_id(current_user, db)
    service = FeatureFlagService(db)
    return success_response({"enabled": service.get_enabled_features(org_id)})


@saas_router.get("/features/all")
async def list_all_feature_flags(
    current_user: dict = Depends(get_current_user),
    db: DbSession = Depends(get_db),
):
    """List all feature flags (admin only)."""
    require_super_admin(current_user)
    service = FeatureFlagService(db)
    flags = service.list_flags()
    return success_response(
        [
            {
                "id": f.id,
                "flag_key": f.flag_key,
                "name": f.name,
                "description": f.description,
                "category": f.category,
                "default_enabled": f.default_enabled,
                "min_plan": f.min_plan,
                "is_beta": f.is_beta,
            }
            for f in flags
        ]
    )


@saas_router.post("/features/override")
async def set_feature_override(
    body: FeatureOverrideRequest,
    current_user: dict = Depends(get_current_user),
    db: DbSession = Depends(get_db),
):
    """Set a feature flag override for an organization (super admin only)."""
    require_super_admin(current_user)
    org_id = body.organization_id if hasattr(body, "organization_id") else None
    if not org_id:
        org_id = get_current_organization_id(current_user, db)
    service = FeatureFlagService(db)
    override = service.set_override(org_id, body.flag_key, body.is_enabled, body.reason)
    return success_response({"id": override.id}, "Feature override set")


# â”€â”€â”€ Onboarding â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€


@saas_router.get("/onboarding")
async def get_onboarding(
    current_user: dict = Depends(get_current_user),
    db: DbSession = Depends(get_db),
):
    """Get onboarding progress for the current organization."""
    org_id = get_current_organization_id(current_user, db)
    service = OnboardingService(db)
    return success_response(service.get_progress(org_id))


@saas_router.post("/onboarding/complete-step")
async def complete_onboarding_step(
    body: OnboardingStepRequest,
    current_user: dict = Depends(get_current_user),
    db: DbSession = Depends(get_db),
):
    """Mark an onboarding step as complete."""
    org_id = get_current_organization_id(current_user, db)
    service = OnboardingService(db)
    record = service.complete_step(org_id, body.step_key)
    if body.industry:
        record.industry = body.industry
        db.commit()
    return success_response(
        {
            "completion_percentage": record.completion_percentage,
            "is_complete": record.is_complete,
            "current_step": record.current_step,
        }
    )


# â”€â”€â”€ Customer Success â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€


@saas_router.get("/health-score")
async def get_health_score(
    current_user: dict = Depends(get_current_user),
    db: DbSession = Depends(get_db),
):
    """Compute and return the customer health score."""
    org_id = get_current_organization_id(current_user, db)
    service = CustomerSuccessService(db)
    return success_response(service.compute_health_score(org_id))


@saas_router.post("/support/tickets")
async def create_support_ticket(
    body: SupportTicketCreate,
    current_user: dict = Depends(get_current_user),
    db: DbSession = Depends(get_db),
):
    """Create a support ticket."""
    org_id = get_current_organization_id(current_user, db)
    ticket = SupportTicket(
        organization_id=org_id,
        user_id=current_user["id"],
        subject=body.subject,
        description=body.description,
        priority=body.priority,
        category=body.category,
    )
    db.add(ticket)
    db.flush()
    db.commit()
    return success_response({"id": ticket.id, "status": ticket.status}, "Support ticket created")


@saas_router.get("/support/tickets")
async def list_support_tickets(
    current_user: dict = Depends(get_current_user),
    db: DbSession = Depends(get_db),
):
    """List support tickets for the organization."""
    org_id = get_current_organization_id(current_user, db)
    tickets = (
        db.execute(
            select(SupportTicket)
            .where(SupportTicket.organization_id == org_id)
            .order_by(SupportTicket.created_at.desc())
        )
        .scalars()
        .all()
    )
    return success_response(
        [
            {
                "id": t.id,
                "subject": t.subject,
                "priority": t.priority,
                "status": t.status,
                "category": t.category,
                "created_at": str(t.created_at) if t.created_at else None,
            }
            for t in tickets
        ]
    )


# â”€â”€â”€ Notification Preferences â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€


@saas_router.get("/notification-preferences")
async def get_notification_preferences(
    current_user: dict = Depends(get_current_user),
    db: DbSession = Depends(get_db),
):
    """Get notification preferences for the current user."""
    org_id = get_current_organization_id(current_user, db)
    pref = db.execute(
        select(NotificationPreference).where(
            NotificationPreference.user_id == current_user["id"],
            NotificationPreference.organization_id == org_id,
        )
    ).scalar_one_or_none()

    if not pref:
        pref = NotificationPreference(
            user_id=current_user["id"],
            organization_id=org_id,
        )
        db.add(pref)
        db.flush()
        db.commit()

    return success_response(
        {
            "channel_in_app": pref.channel_in_app,
            "channel_email": pref.channel_email,
            "channel_sms": pref.channel_sms,
            "channel_webhook": pref.channel_webhook,
            "event_workflow_completed": pref.event_workflow_completed,
            "event_dataset_processed": pref.event_dataset_processed,
            "event_subscription_changes": pref.event_subscription_changes,
            "event_security_alerts": pref.event_security_alerts,
            "event_billing_reminders": pref.event_billing_reminders,
            "event_system_maintenance": pref.event_system_maintenance,
        }
    )


@saas_router.put("/notification-preferences")
async def update_notification_preferences(
    body: NotificationPrefUpdate,
    current_user: dict = Depends(get_current_user),
    db: DbSession = Depends(get_db),
):
    """Update notification preferences."""
    org_id = get_current_organization_id(current_user, db)
    pref = db.execute(
        select(NotificationPreference).where(
            NotificationPreference.user_id == current_user["id"],
            NotificationPreference.organization_id == org_id,
        )
    ).scalar_one_or_none()

    if not pref:
        pref = NotificationPreference(
            user_id=current_user["id"],
            organization_id=org_id,
        )
        db.add(pref)
        db.flush()

    kwargs = {k: v for k, v in body.model_dump().items() if v is not None}
    for k, v in kwargs.items():
        setattr(pref, k, v)
    db.commit()
    return success_response(None, "Notification preferences updated")


# â”€â”€â”€ Super Admin: System Announcements â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€


@saas_router.get("/announcements")
async def list_announcements(
    current_user: dict = Depends(get_current_user),
    db: DbSession = Depends(get_db),
):
    """List active system announcements."""
    now = datetime.now(timezone.utc)
    announcements = (
        db.execute(
            select(SystemAnnouncement)
            .where(
                SystemAnnouncement.is_active == True,  # noqa: E712
                SystemAnnouncement.starts_at <= now,
            )
            .order_by(SystemAnnouncement.created_at.desc())
        )
        .scalars()
        .all()
    )

    # Filter by audience
    org_id = get_current_organization_id(current_user, db)
    sub_service = SubscriptionService(db)
    sub_status = sub_service.check_subscription_status(org_id)
    plan = sub_status.get("plan", "free")

    result = []
    for ann in announcements:
        if ann.ends_at and ann.ends_at < now:
            continue
        if (
            ann.target_audience == "all"
            or ann.target_audience == "free"
            and plan == "free"
            or ann.target_audience == "paid"
            and plan != "free"
            or ann.target_audience == "enterprise"
            and plan == "enterprise"
        ):
            result.append(ann)

    return success_response(
        [
            {
                "id": a.id,
                "title": a.title,
                "message": a.message,
                "severity": a.severity,
                "ends_at": str(a.ends_at) if a.ends_at else None,
            }
            for a in result
        ]
    )


@saas_router.post("/announcements")
async def create_announcement(
    body: AnnouncementCreate,
    current_user: dict = Depends(get_current_user),
    db: DbSession = Depends(get_db),
):
    """Create a system announcement (super admin only)."""
    require_super_admin(current_user)
    ends_at = None
    if body.ends_at:
        ends_at = datetime.fromisoformat(body.ends_at.replace("Z", "+00:00"))

    ann = SystemAnnouncement(
        title=body.title,
        message=body.message,
        severity=body.severity,
        target_audience=body.target_audience,
        ends_at=ends_at,
        created_by=current_user["id"],
    )
    db.add(ann)
    db.flush()
    db.commit()
    return success_response({"id": ann.id}, "Announcement created")
