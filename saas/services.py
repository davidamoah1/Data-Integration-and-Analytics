"""Subscription and billing service — plan management, lifecycle, usage tracking."""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy import select, update, func as sa_func
from sqlalchemy.orm import Session as DbSession

from saas.models import (
    FeatureFlag,
    Invoice,
    OnboardingRecord,
    OrganizationFeatureOverride,
    Subscription,
    SubscriptionPlan,
    UsageRecord,
)

logger = logging.getLogger("etl_project.saas")


# ═══════════════════════════════════════════════════════════════
# Plan Definitions (seeded on startup)
# ═══════════════════════════════════════════════════════════════

PLAN_DEFINITIONS = [
    {
        "plan_code": "free",
        "name": "Free",
        "description": "Get started with basic data analytics",
        "price_monthly": 0.0,
        "price_yearly": 0.0,
        "max_users": 5,
        "max_storage_mb": 500,
        "max_ai_requests_monthly": 50,
        "max_api_calls_monthly": 1000,
        "max_workflow_executions": 100,
        "max_scheduled_jobs": 5,
        "max_model_trainings": 2,
        "max_connectors": 3,
        "features": ["dashboards", "etl", "reports", "basic_analytics"],
        "is_trial_available": False,
        "trial_days": 0,
        "sort_order": 1,
    },
    {
        "plan_code": "starter",
        "name": "Starter",
        "description": "For small teams getting started with data intelligence",
        "price_monthly": 29.0,
        "price_yearly": 290.0,
        "max_users": 15,
        "max_storage_mb": 5000,
        "max_ai_requests_monthly": 500,
        "max_api_calls_monthly": 10000,
        "max_workflow_executions": 1000,
        "max_scheduled_jobs": 20,
        "max_model_trainings": 10,
        "max_connectors": 10,
        "features": ["dashboards", "etl", "reports", "basic_analytics", "ai_copilot", "workflows", "connectors"],
        "is_trial_available": True,
        "trial_days": 14,
        "sort_order": 2,
    },
    {
        "plan_code": "professional",
        "name": "Professional",
        "description": "Advanced analytics and AI for growing organizations",
        "price_monthly": 99.0,
        "price_yearly": 990.0,
        "max_users": 50,
        "max_storage_mb": 25000,
        "max_ai_requests_monthly": 5000,
        "max_api_calls_monthly": 50000,
        "max_workflow_executions": 10000,
        "max_scheduled_jobs": 100,
        "max_model_trainings": 50,
        "max_connectors": 25,
        "features": ["dashboards", "etl", "reports", "basic_analytics", "ai_copilot", "workflows", "connectors", "marketplace", "forecasting", "api_access", "webhooks"],
        "is_trial_available": True,
        "trial_days": 14,
        "sort_order": 3,
    },
    {
        "plan_code": "business",
        "name": "Business",
        "description": "Full platform access for data-driven enterprises",
        "price_monthly": 299.0,
        "price_yearly": 2990.0,
        "max_users": 200,
        "max_storage_mb": 100000,
        "max_ai_requests_monthly": 25000,
        "max_api_calls_monthly": 250000,
        "max_workflow_executions": 50000,
        "max_scheduled_jobs": 500,
        "max_model_trainings": 200,
        "max_connectors": 100,
        "features": ["dashboards", "etl", "reports", "basic_analytics", "ai_copilot", "workflows", "connectors", "marketplace", "forecasting", "api_access", "webhooks", "automl", "decision_intelligence", "white_label"],
        "is_trial_available": True,
        "trial_days": 30,
        "sort_order": 4,
    },
    {
        "plan_code": "enterprise",
        "name": "Enterprise",
        "description": "Unlimited scale with dedicated support and custom integrations",
        "price_monthly": 999.0,
        "price_yearly": 9990.0,
        "max_users": None,
        "max_storage_mb": None,
        "max_ai_requests_monthly": None,
        "max_api_calls_monthly": None,
        "max_workflow_executions": None,
        "max_scheduled_jobs": None,
        "max_model_trainings": None,
        "max_connectors": None,
        "features": ["dashboards", "etl", "reports", "basic_analytics", "ai_copilot", "workflows", "connectors", "marketplace", "forecasting", "api_access", "webhooks", "automl", "decision_intelligence", "white_label", "sso", "audit_export", "priority_support", "custom_connectors"],
        "is_trial_available": True,
        "trial_days": 30,
        "sort_order": 5,
    },
]


FEATURE_FLAG_DEFINITIONS = [
    {"flag_key": "dashboards", "name": "Dashboards", "description": "View and create dashboards", "category": "core", "default_enabled": True, "min_plan": "free"},
    {"flag_key": "etl", "name": "ETL Engine", "description": "Data extraction, transformation, loading", "category": "core", "default_enabled": True, "min_plan": "free"},
    {"flag_key": "reports", "name": "Reports", "description": "Generate and export reports", "category": "core", "default_enabled": True, "min_plan": "free"},
    {"flag_key": "basic_analytics", "name": "Basic Analytics", "description": "KPIs and basic analytics", "category": "core", "default_enabled": True, "min_plan": "free"},
    {"flag_key": "ai_copilot", "name": "AI Copilot", "description": "AI-powered data assistant", "category": "premium", "default_enabled": False, "min_plan": "starter"},
    {"flag_key": "workflows", "name": "Workflow Engine", "description": "Automated workflow execution", "category": "premium", "default_enabled": False, "min_plan": "starter"},
    {"flag_key": "connectors", "name": "Connectors", "description": "External data source connectors", "category": "premium", "default_enabled": False, "min_plan": "starter"},
    {"flag_key": "marketplace", "name": "Marketplace", "description": "Plugin marketplace access", "category": "premium", "default_enabled": False, "min_plan": "professional"},
    {"flag_key": "forecasting", "name": "Forecasting", "description": "ML-powered forecasting", "category": "premium", "default_enabled": False, "min_plan": "professional"},
    {"flag_key": "api_access", "name": "Public API Access", "description": "External API key access", "category": "premium", "default_enabled": False, "min_plan": "professional"},
    {"flag_key": "webhooks", "name": "Webhooks", "description": "Webhook event subscriptions", "category": "premium", "default_enabled": False, "min_plan": "professional"},
    {"flag_key": "automl", "name": "AutoML", "description": "Automated model selection and tuning", "category": "enterprise", "default_enabled": False, "min_plan": "business"},
    {"flag_key": "decision_intelligence", "name": "Decision Intelligence", "description": "AI-powered decision recommendations", "category": "enterprise", "default_enabled": False, "min_plan": "business"},
    {"flag_key": "white_label", "name": "White Labeling", "description": "Custom branding", "category": "enterprise", "default_enabled": False, "min_plan": "business"},
    {"flag_key": "sso", "name": "Single Sign-On", "description": "SAML/OIDC SSO integration", "category": "enterprise", "default_enabled": False, "min_plan": "enterprise"},
    {"flag_key": "audit_export", "name": "Audit Export", "description": "Export audit logs", "category": "enterprise", "default_enabled": False, "min_plan": "enterprise"},
    {"flag_key": "priority_support", "name": "Priority Support", "description": "Dedicated support channel", "category": "enterprise", "default_enabled": False, "min_plan": "enterprise"},
    {"flag_key": "custom_connectors", "name": "Custom Connectors", "description": "Build custom connectors", "category": "enterprise", "default_enabled": False, "min_plan": "enterprise"},
]


class SubscriptionService:
    """Service for subscription lifecycle management."""

    def __init__(self, db: DbSession):
        self.db = db

    def get_plan(self, plan_code: str) -> SubscriptionPlan | None:
        return self.db.execute(
            select(SubscriptionPlan).where(SubscriptionPlan.plan_code == plan_code)
        ).scalar_one_or_none()

    def list_plans(self, public_only: bool = True) -> list[SubscriptionPlan]:
        query = select(SubscriptionPlan).where(SubscriptionPlan.is_active == True)  # noqa: E712
        if public_only:
            query = query.where(SubscriptionPlan.is_public == True)  # noqa: E712
        return self.db.execute(query.order_by(SubscriptionPlan.sort_order)).scalars().all()

    def get_org_subscription(self, org_id: int) -> Subscription | None:
        return self.db.execute(
            select(Subscription)
            .where(Subscription.organization_id == org_id, Subscription.status.in_(["active", "trial", "past_due"]))
            .order_by(Subscription.created_at.desc())
        ).scalars().first()

    def create_subscription(
        self,
        org_id: int,
        plan_code: str,
        billing_cycle: str = "monthly",
        is_trial: bool = False,
    ) -> Subscription:
        plan = self.get_plan(plan_code)
        if not plan:
            raise ValueError(f"Unknown plan: {plan_code}")

        now = datetime.now(timezone.utc)
        if billing_cycle == "yearly":
            period_end = now + timedelta(days=365)
        else:
            period_end = now + timedelta(days=30)

        trial_end = None
        if is_trial and plan.is_trial_available:
            trial_end = now + timedelta(days=plan.trial_days)
            status = "trial"
        else:
            status = "active"

        sub = Subscription(
            organization_id=org_id,
            plan_id=plan.id,
            status=status,
            billing_cycle=billing_cycle,
            current_period_start=now,
            current_period_end=period_end,
            trial_end=trial_end,
        )
        self.db.add(sub)
        self.db.flush()
        self.db.commit()
        return sub

    def upgrade_subscription(self, org_id: int, new_plan_code: str) -> Subscription:
        sub = self.get_org_subscription(org_id)
        if not sub:
            return self.create_subscription(org_id, new_plan_code)

        plan = self.get_plan(new_plan_code)
        if not plan:
            raise ValueError(f"Unknown plan: {new_plan_code}")

        sub.plan_id = plan.id
        self.db.commit()
        return sub

    def cancel_subscription(self, org_id: int) -> Subscription:
        sub = self.get_org_subscription(org_id)
        if not sub:
            raise ValueError("No active subscription found")
        sub.status = "cancelled"
        sub.cancelled_at = datetime.now(timezone.utc)
        self.db.commit()
        return sub

    def check_subscription_status(self, org_id: int) -> dict:
        sub = self.get_org_subscription(org_id)
        if not sub:
            return {"status": "none", "plan": "free", "is_active": False}

        plan = self.db.execute(
            select(SubscriptionPlan).where(SubscriptionPlan.id == sub.plan_id)
        ).scalar_one_or_none()

        now = datetime.now(timezone.utc)

        def _aware(dt):
            """Normalize a possibly-naive DB timestamp to UTC-aware for comparison."""
            if dt is None:
                return None
            return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)

        trial_end = _aware(sub.trial_end)
        grace_period_end = _aware(sub.grace_period_end)

        if sub.status == "trial" and trial_end and trial_end < now:
            sub.status = "past_due"
            sub.grace_period_end = now + timedelta(days=7)
            self.db.commit()

        if sub.status == "past_due" and grace_period_end and grace_period_end < now:
            sub.status = "expired"
            self.db.commit()

        return {
            "status": sub.status,
            "plan": plan.plan_code if plan else "free",
            "plan_name": plan.name if plan else "Free",
            "is_active": sub.status in ("active", "trial"),
            "current_period_end": str(sub.current_period_end) if sub.current_period_end else None,
            "trial_end": str(sub.trial_end) if sub.trial_end else None,
        }

    def get_usage(self, org_id: int) -> dict:
        now = datetime.now(timezone.utc)
        record = self.db.execute(
            select(UsageRecord).where(
                UsageRecord.organization_id == org_id,
                UsageRecord.period_year == now.year,
                UsageRecord.period_month == now.month,
            )
        ).scalar_one_or_none()

        sub = self.get_org_subscription(org_id)
        plan = None
        if sub:
            plan = self.db.execute(
                select(SubscriptionPlan).where(SubscriptionPlan.id == sub.plan_id)
            ).scalar_one_or_none()

        if not record:
            record = UsageRecord(
                organization_id=org_id,
                period_year=now.year,
                period_month=now.month,
            )
            self.db.add(record)
            self.db.flush()
            self.db.commit()

        return {
            "active_users": record.active_users,
            "storage_used_mb": record.storage_used_mb,
            "ai_requests": record.ai_requests,
            "api_calls": record.api_calls,
            "workflow_executions": record.workflow_executions,
            "scheduled_jobs": record.scheduled_jobs,
            "model_trainings": record.model_trainings,
            "connector_usage": record.connector_usage,
            "limits": {
                "max_users": plan.max_users if plan else 5,
                "max_storage_mb": plan.max_storage_mb if plan else 500,
                "max_ai_requests_monthly": plan.max_ai_requests_monthly if plan else 50,
                "max_api_calls_monthly": plan.max_api_calls_monthly if plan else 1000,
                "max_workflow_executions": plan.max_workflow_executions if plan else 100,
                "max_scheduled_jobs": plan.max_scheduled_jobs if plan else 5,
                "max_model_trainings": plan.max_model_trainings if plan else 2,
                "max_connectors": plan.max_connectors if plan else 3,
            } if plan else {},
        }

    def increment_usage(self, org_id: int, field: str, amount: int = 1) -> None:
        now = datetime.now(timezone.utc)
        record = self.db.execute(
            select(UsageRecord).where(
                UsageRecord.organization_id == org_id,
                UsageRecord.period_year == now.year,
                UsageRecord.period_month == now.month,
            )
        ).scalar_one_or_none()

        if not record:
            record = UsageRecord(
                organization_id=org_id,
                period_year=now.year,
                period_month=now.month,
            )
            self.db.add(record)
            self.db.flush()

        current = getattr(record, field, 0) or 0
        setattr(record, field, current + amount)
        self.db.commit()

    def list_invoices(self, org_id: int, limit: int = 20) -> list[Invoice]:
        return self.db.execute(
            select(Invoice)
            .where(Invoice.organization_id == org_id)
            .order_by(Invoice.created_at.desc())
            .limit(limit)
        ).scalars().all()


# ═══════════════════════════════════════════════════════════════
# Feature Flag Service
# ═══════════════════════════════════════════════════════════════


class FeatureFlagService:
    """Service for feature flag and licensing management."""

    PLAN_HIERARCHY = {"free": 1, "starter": 2, "professional": 3, "business": 4, "enterprise": 5}

    def __init__(self, db: DbSession):
        self.db = db

    def is_feature_enabled(self, org_id: int, flag_key: str) -> bool:
        # Check override first
        override = self.db.execute(
            select(OrganizationFeatureOverride).where(
                OrganizationFeatureOverride.organization_id == org_id,
                OrganizationFeatureOverride.flag_key == flag_key,
            )
        ).scalar_one_or_none()

        if override:
            if override.expires_at and override.expires_at < datetime.now(timezone.utc):
                return False
            return override.is_enabled

        # Check plan-based access
        flag = self.db.execute(
            select(FeatureFlag).where(FeatureFlag.flag_key == flag_key)
        ).scalar_one_or_none()

        if not flag:
            return False

        if flag.default_enabled:
            return True

        if not flag.min_plan:
            return False

        # Get org's current plan
        sub_service = SubscriptionService(self.db)
        status = sub_service.check_subscription_status(org_id)
        org_plan = status.get("plan", "free")

        org_level = self.PLAN_HIERARCHY.get(org_plan, 0)
        required_level = self.PLAN_HIERARCHY.get(flag.min_plan, 99)

        return org_level >= required_level

    def get_enabled_features(self, org_id: int) -> list[str]:
        flags = self.db.execute(select(FeatureFlag)).scalars().all()
        return [f.flag_key for f in flags if self.is_feature_enabled(org_id, f.flag_key)]

    def set_override(self, org_id: int, flag_key: str, is_enabled: bool, reason: str | None = None) -> OrganizationFeatureOverride:
        existing = self.db.execute(
            select(OrganizationFeatureOverride).where(
                OrganizationFeatureOverride.organization_id == org_id,
                OrganizationFeatureOverride.flag_key == flag_key,
            )
        ).scalar_one_or_none()

        if existing:
            existing.is_enabled = is_enabled
            existing.reason = reason
        else:
            existing = OrganizationFeatureOverride(
                organization_id=org_id,
                flag_key=flag_key,
                is_enabled=is_enabled,
                reason=reason,
            )
            self.db.add(existing)
        self.db.flush()
        self.db.commit()
        return existing

    def list_flags(self) -> list[FeatureFlag]:
        return self.db.execute(select(FeatureFlag).order_by(FeatureFlag.category, FeatureFlag.name)).scalars().all()


# ═══════════════════════════════════════════════════════════════
# Onboarding Service
# ═══════════════════════════════════════════════════════════════


ONBOARDING_STEPS = [
    {"key": "org_creation", "name": "Organization Created", "weight": 10},
    {"key": "admin_account", "name": "Admin Account Setup", "weight": 10},
    {"key": "industry_selection", "name": "Industry Selection", "weight": 10},
    {"key": "dataset_upload", "name": "First Dataset Upload", "weight": 15},
    {"key": "connector_setup", "name": "Connector Setup", "weight": 10},
    {"key": "dashboard_creation", "name": "Dashboard Creation", "weight": 15},
    {"key": "ai_introduction", "name": "AI Copilot Introduction", "weight": 10},
    {"key": "sample_data", "name": "Sample Data Loaded", "weight": 10},
    {"key": "product_tour", "name": "Product Tour Completed", "weight": 10},
]


class OnboardingService:
    """Service for guided customer onboarding."""

    def __init__(self, db: DbSession):
        self.db = db

    def get_or_create(self, org_id: int) -> OnboardingRecord:
        record = self.db.execute(
            select(OnboardingRecord).where(OnboardingRecord.organization_id == org_id)
        ).scalar_one_or_none()

        if not record:
            record = OnboardingRecord(
                organization_id=org_id,
                steps_completed=["org_creation"],
                current_step="admin_account",
                completion_percentage=10,
            )
            self.db.add(record)
            self.db.flush()
            self.db.commit()
        return record

    def complete_step(self, org_id: int, step_key: str) -> OnboardingRecord:
        record = self.get_or_create(org_id)
        completed = set(record.steps_completed or [])
        completed.add(step_key)

        total_weight = sum(s["weight"] for s in ONBOARDING_STEPS)
        completed_weight = sum(s["weight"] for s in ONBOARDING_STEPS if s["key"] in completed)
        percentage = int((completed_weight / total_weight) * 100)

        record.steps_completed = list(completed)
        record.completion_percentage = percentage
        record.is_complete = percentage >= 100
        if record.is_complete:
            record.completed_at = datetime.now(timezone.utc)

        # Find next step
        for step in ONBOARDING_STEPS:
            if step["key"] not in completed:
                record.current_step = step["key"]
                break

        self.db.commit()
        return record

    def get_progress(self, org_id: int) -> dict:
        record = self.get_or_create(org_id)
        return {
            "steps_completed": record.steps_completed,
            "current_step": record.current_step,
            "completion_percentage": record.completion_percentage,
            "is_complete": record.is_complete,
            "all_steps": ONBOARDING_STEPS,
        }


# ═══════════════════════════════════════════════════════════════
# Customer Health Score Service
# ═══════════════════════════════════════════════════════════════


class CustomerSuccessService:
    """Service for computing customer health scores."""

    def __init__(self, db: DbSession):
        self.db = db

    def compute_health_score(self, org_id: int) -> dict:
        from authentication.models import User
        from audit.models import AuditLog

        now = datetime.now(timezone.utc)
        thirty_days_ago = now - timedelta(days=30)

        # Active users
        active_users = self.db.execute(
            select(sa_func.count(User.id)).where(
                User.organization_id == org_id,
                User.is_active == 1,
                User.is_deleted == 0,
                User.last_login_at >= thirty_days_ago,
            )
        ).scalar() or 0

        total_users = self.db.execute(
            select(sa_func.count(User.id)).where(
                User.organization_id == org_id,
                User.is_deleted == 0,
            )
        ).scalar() or 1

        # Activity
        recent_activity = self.db.execute(
            select(sa_func.count(AuditLog.id)).where(
                AuditLog.organization_id == org_id,
                AuditLog.created_at >= thirty_days_ago,
            )
        ).scalar() or 0

        # Feature adoption
        flag_service = FeatureFlagService(self.db)
        enabled_features = flag_service.get_enabled_features(org_id)
        all_flags = flag_service.list_flags()
        adoption_rate = len(enabled_features) / max(len(all_flags), 1)

        # Compute score
        factors = {}
        score = 0

        # User engagement (30%)
        user_engagement = min(active_users / max(total_users, 1), 1.0) * 100
        factors["user_engagement"] = {"score": int(user_engagement), "weight": 30, "detail": f"{active_users}/{total_users} users active"}
        score += int(user_engagement * 0.3)

        # Activity (25%)
        activity_score = min(recent_activity / 100, 1.0) * 100
        factors["activity"] = {"score": int(activity_score), "weight": 25, "detail": f"{recent_activity} actions in 30 days"}
        score += int(activity_score * 0.25)

        # Feature adoption (25%)
        adoption_score = adoption_rate * 100
        factors["feature_adoption"] = {"score": int(adoption_score), "weight": 25, "detail": f"{len(enabled_features)}/{len(all_flags)} features used"}
        score += int(adoption_score * 0.25)

        # Subscription status (20%)
        sub_service = SubscriptionService(self.db)
        sub_status = sub_service.check_subscription_status(org_id)
        sub_score = 100 if sub_status["is_active"] else 20
        factors["subscription"] = {"score": sub_score, "weight": 20, "detail": sub_status["status"]}
        score += int(sub_score * 0.2)

        status = "healthy" if score >= 70 else "at_risk" if score >= 40 else "critical"

        # Save
        health = CustomerHealthScore(
            organization_id=org_id,
            score=score,
            status=status,
            factors=factors,
            active_users=active_users,
            feature_adoption=adoption_rate,
            last_activity=now,
        )
        self.db.add(health)
        self.db.commit()

        return {"score": score, "status": status, "factors": factors}


from saas.models import CustomerHealthScore  # noqa: E402


# ═══════════════════════════════════════════════════════════════
# Seed Function
# ═══════════════════════════════════════════════════════════════


def seed_saas_data(db: DbSession) -> None:
    """Seed subscription plans and feature flags."""
    # Seed plans
    for plan_data in PLAN_DEFINITIONS:
        existing = db.execute(
            select(SubscriptionPlan).where(SubscriptionPlan.plan_code == plan_data["plan_code"])
        ).scalar_one_or_none()
        if not existing:
            plan = SubscriptionPlan(**plan_data)
            db.add(plan)
            db.flush()

    # Seed feature flags
    for flag_data in FEATURE_FLAG_DEFINITIONS:
        existing = db.execute(
            select(FeatureFlag).where(FeatureFlag.flag_key == flag_data["flag_key"])
        ).scalar_one_or_none()
        if not existing:
            flag = FeatureFlag(**flag_data)
            db.add(flag)
            db.flush()

    db.commit()
    logger.info("SaaS plans and feature flags seeded.")
