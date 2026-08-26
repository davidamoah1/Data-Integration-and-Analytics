"""Subscription & Licensing module for AEDIP SaaS.

Models:
  - Subscription: Organization subscription state (plan, status, trial, limits)
  - FeatureFlag: Per-organization feature toggles

Plans: free_trial, starter, professional, enterprise, government
"""

from datetime import datetime, timedelta, timezone

from sqlalchemy import JSON, TIMESTAMP, BigInteger, Boolean, Column, Integer, String, func
from sqlalchemy.orm import Session as DbSession

from shared.database import Base, BigInt

# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# Plan definitions
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

PLAN_DEFINITIONS = {
    "free_trial": {
        "name": "Free Trial",
        "description": "14-day full-access trial. No credit card required.",
        "trial_days": 14,
        "max_users": 5,
        "max_dashboards": 10,
        "max_pipelines": 5,
        "max_ai_queries_per_month": 100,
        "max_upload_mb": 50,
        "features": [
            "dashboards",
            "etl_pipelines",
            "ai_copilot",
            "data_upload",
            "industry_packs",
            "reports",
        ],
    },
    "starter": {
        "name": "Starter",
        "description": "For small teams getting started with data analytics.",
        "trial_days": 0,
        "max_users": 10,
        "max_dashboards": 25,
        "max_pipelines": 10,
        "max_ai_queries_per_month": 500,
        "max_upload_mb": 200,
        "features": [
            "dashboards",
            "etl_pipelines",
            "ai_copilot",
            "data_upload",
            "industry_packs",
            "reports",
            "scheduled_pipelines",
        ],
    },
    "professional": {
        "name": "Professional",
        "description": "For growing organizations that need advanced analytics.",
        "trial_days": 0,
        "max_users": 50,
        "max_dashboards": 100,
        "max_pipelines": 50,
        "max_ai_queries_per_month": 5000,
        "max_upload_mb": 1000,
        "features": [
            "dashboards",
            "etl_pipelines",
            "ai_copilot",
            "data_upload",
            "industry_packs",
            "reports",
            "scheduled_pipelines",
            "ai_forecasts",
            "anomaly_detection",
            "audit_logs",
            "api_access",
        ],
    },
    "enterprise": {
        "name": "Enterprise",
        "description": "For large organizations with advanced security and scale needs.",
        "trial_days": 0,
        "max_users": 500,
        "max_dashboards": 1000,
        "max_pipelines": 500,
        "max_ai_queries_per_month": 50000,
        "max_upload_mb": 10000,
        "features": [
            "dashboards",
            "etl_pipelines",
            "ai_copilot",
            "data_upload",
            "industry_packs",
            "reports",
            "scheduled_pipelines",
            "ai_forecasts",
            "anomaly_detection",
            "audit_logs",
            "api_access",
            "sso",
            "custom_branding",
            "priority_support",
            "white_label",
            "data_governance",
            "advanced_rbac",
        ],
    },
    "government": {
        "name": "Government",
        "description": "For government agencies with compliance and security requirements.",
        "trial_days": 0,
        "max_users": 1000,
        "max_dashboards": 2000,
        "max_pipelines": 1000,
        "max_ai_queries_per_month": 100000,
        "max_upload_mb": 50000,
        "features": [
            "dashboards",
            "etl_pipelines",
            "ai_copilot",
            "data_upload",
            "industry_packs",
            "reports",
            "scheduled_pipelines",
            "ai_forecasts",
            "anomaly_detection",
            "audit_logs",
            "api_access",
            "sso",
            "custom_branding",
            "priority_support",
            "white_label",
            "data_governance",
            "advanced_rbac",
            "compliance_reports",
            "on_premise_option",
            "data_residency",
        ],
    },
}

ALL_FEATURES = sorted({f for plan in PLAN_DEFINITIONS.values() for f in plan["features"]})


# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# Models
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€


class Subscription(Base):
    """Organization subscription state."""

    __tablename__ = "subscriptions"

    id = Column(BigInt, primary_key=True, autoincrement=True)
    organization_id = Column(BigInteger, nullable=False, unique=True, index=True)
    plan = Column(String(50), nullable=False, default="free_trial")
    status = Column(
        String(20), nullable=False, default="trialing"
    )  # trialing, active, past_due, canceled, expired
    trial_started_at = Column(TIMESTAMP, nullable=True)
    trial_ends_at = Column(TIMESTAMP, nullable=True)
    subscription_started_at = Column(TIMESTAMP, nullable=True)
    subscription_ends_at = Column(TIMESTAMP, nullable=True)
    canceled_at = Column(TIMESTAMP, nullable=True)
    max_users = Column(Integer, nullable=False, default=5)
    max_dashboards = Column(Integer, nullable=False, default=10)
    max_pipelines = Column(Integer, nullable=False, default=5)
    max_ai_queries_per_month = Column(Integer, nullable=False, default=100)
    max_upload_mb = Column(Integer, nullable=False, default=50)
    features = Column(JSON, nullable=True, default=list)
    metadata_ = Column("metadata", JSON, nullable=True, default=dict)
    created_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now(), nullable=False)


class FeatureFlag(Base):
    """Per-organization feature flag overrides."""

    __tablename__ = "feature_flags"

    id = Column(BigInt, primary_key=True, autoincrement=True)
    organization_id = Column(BigInteger, nullable=False, index=True)
    feature_key = Column(String(100), nullable=False, index=True)
    is_enabled = Column(Boolean, nullable=False, default=True)
    created_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now(), nullable=False)


# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# Service
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€


class SubscriptionService:
    """Manage organization subscriptions, trials, and feature access."""

    def __init__(self, db: DbSession):
        self.db = db

    def get_subscription(self, org_id: int) -> Subscription | None:
        return self.db.query(Subscription).filter(Subscription.organization_id == org_id).first()

    def create_trial(self, org_id: int, plan: str = "free_trial") -> Subscription:
        """Create a free trial subscription for a new organization."""
        existing = self.get_subscription(org_id)
        if existing:
            return existing

        plan_def = PLAN_DEFINITIONS.get(plan, PLAN_DEFINITIONS["free_trial"])
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        trial_end = now + timedelta(days=plan_def["trial_days"]) if plan_def["trial_days"] else None

        sub = Subscription(
            organization_id=org_id,
            plan=plan,
            status="trialing" if plan_def["trial_days"] else "active",
            trial_started_at=now if plan_def["trial_days"] else None,
            trial_ends_at=trial_end,
            max_users=plan_def["max_users"],
            max_dashboards=plan_def["max_dashboards"],
            max_pipelines=plan_def["max_pipelines"],
            max_ai_queries_per_month=plan_def["max_ai_queries_per_month"],
            max_upload_mb=plan_def["max_upload_mb"],
            features=plan_def["features"],
        )
        self.db.add(sub)
        self.db.commit()
        self.db.refresh(sub)
        return sub

    def upgrade_plan(self, org_id: int, new_plan: str) -> Subscription:
        """Upgrade an organization to a new plan."""
        sub = self.get_subscription(org_id)
        if not sub:
            sub = self.create_trial(org_id, new_plan)
            return sub

        plan_def = PLAN_DEFINITIONS.get(new_plan)
        if not plan_def:
            raise ValueError(f"Unknown plan: {new_plan}")

        now = datetime.now(timezone.utc).replace(tzinfo=None)
        sub.plan = new_plan
        sub.status = "active"
        sub.subscription_started_at = now
        sub.max_users = plan_def["max_users"]
        sub.max_dashboards = plan_def["max_dashboards"]
        sub.max_pipelines = plan_def["max_pipelines"]
        sub.max_ai_queries_per_month = plan_def["max_ai_queries_per_month"]
        sub.max_upload_mb = plan_def["max_upload_mb"]
        sub.features = plan_def["features"]
        self.db.commit()
        self.db.refresh(sub)
        return sub

    def cancel_subscription(self, org_id: int) -> Subscription | None:
        sub = self.get_subscription(org_id)
        if sub:
            now = datetime.now(timezone.utc).replace(tzinfo=None)
            sub.status = "canceled"
            sub.canceled_at = now
            self.db.commit()
            self.db.refresh(sub)
        return sub

    def check_trial_expired(self, org_id: int) -> bool:
        """Check if the trial has expired and update status if so."""
        sub = self.get_subscription(org_id)
        if not sub or sub.status != "trialing":
            return False
        if sub.trial_ends_at:
            now = datetime.now(timezone.utc).replace(tzinfo=None)
            if now > sub.trial_ends_at:
                sub.status = "expired"
                self.db.commit()
                return True
        return False

    def has_feature(self, org_id: int, feature_key: str) -> bool:
        """Check if an organization has access to a feature."""
        # Check feature flag override first
        flag = (
            self.db.query(FeatureFlag)
            .filter(
                FeatureFlag.organization_id == org_id,
                FeatureFlag.feature_key == feature_key,
            )
            .first()
        )
        if flag:
            return flag.is_enabled

        # Fall back to plan features
        sub = self.get_subscription(org_id)
        if not sub:
            return False
        if self.check_trial_expired(org_id):
            return False
        return feature_key in (sub.features or [])

    def get_limits(self, org_id: int) -> dict:
        """Get the current limits for an organization."""
        sub = self.get_subscription(org_id)
        if not sub:
            return PLAN_DEFINITIONS["free_trial"].copy()
        if self.check_trial_expired(org_id):
            return {
                "max_users": 1,
                "max_dashboards": 1,
                "max_pipelines": 0,
                "max_ai_queries_per_month": 0,
                "max_upload_mb": 1,
                "features": [],
                "status": "expired",
            }
        return {
            "plan": sub.plan,
            "status": sub.status,
            "max_users": sub.max_users,
            "max_dashboards": sub.max_dashboards,
            "max_pipelines": sub.max_pipelines,
            "max_ai_queries_per_month": sub.max_ai_queries_per_month,
            "max_upload_mb": sub.max_upload_mb,
            "features": sub.features or [],
            "trial_ends_at": sub.trial_ends_at.isoformat() if sub.trial_ends_at else None,
        }

    def set_feature_flag(self, org_id: int, feature_key: str, enabled: bool):
        """Set a feature flag override for an organization."""
        flag = (
            self.db.query(FeatureFlag)
            .filter(
                FeatureFlag.organization_id == org_id,
                FeatureFlag.feature_key == feature_key,
            )
            .first()
        )
        if not flag:
            flag = FeatureFlag(
                organization_id=org_id,
                feature_key=feature_key,
                is_enabled=enabled,
            )
            self.db.add(flag)
        else:
            flag.is_enabled = enabled
        self.db.commit()
        return flag
