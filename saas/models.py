"""SaaS Platform â€” Subscription, Billing, Licensing, Onboarding, and Customer Success."""

from __future__ import annotations

from sqlalchemy import (
    JSON,
    TIMESTAMP,
    Boolean,
    Column,
    Float,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    func,
)

from shared.database import Base, BigInt

# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# Subscription Plans
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•


class SubscriptionPlan(Base):
    """Defines a subscription tier (Free, Starter, Professional, Business, Enterprise)."""

    __tablename__ = "saas_subscription_plans"

    id = Column(BigInt, primary_key=True, autoincrement=True)
    plan_code = Column(
        String(50), unique=True, nullable=False
    )  # free, starter, professional, business, enterprise
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    price_monthly = Column(Numeric(18, 2), nullable=False, default=0.0)
    price_yearly = Column(Numeric(18, 2), nullable=False, default=0.0)
    currency = Column(String(10), nullable=False, default="USD")
    is_active = Column(Boolean, default=True, nullable=False)
    is_public = Column(Boolean, default=True, nullable=False)
    sort_order = Column(Integer, default=0, nullable=False)

    # Limits
    max_users = Column(Integer, nullable=True)  # None = unlimited
    max_storage_mb = Column(Integer, nullable=True)
    max_ai_requests_monthly = Column(Integer, nullable=True)
    max_api_calls_monthly = Column(Integer, nullable=True)
    max_workflow_executions = Column(Integer, nullable=True)
    max_scheduled_jobs = Column(Integer, nullable=True)
    max_model_trainings = Column(Integer, nullable=True)
    max_connectors = Column(Integer, nullable=True)

    # Features
    features = Column(JSON, nullable=True)  # list of feature keys enabled
    is_trial_available = Column(Boolean, default=False, nullable=False)
    trial_days = Column(Integer, default=14, nullable=False)

    created_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now(), nullable=False)


class Subscription(Base):
    """An organization's active subscription."""

    __tablename__ = "saas_subscriptions"

    id = Column(BigInt, primary_key=True, autoincrement=True)
    organization_id = Column(BigInt, nullable=False, index=True)
    plan_id = Column(BigInt, ForeignKey("saas_subscription_plans.id"), nullable=False)
    status = Column(
        String(20), nullable=False, default="active"
    )  # active, trial, past_due, cancelled, expired
    billing_cycle = Column(String(10), nullable=False, default="monthly")  # monthly, yearly
    started_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)
    current_period_start = Column(TIMESTAMP, nullable=False)
    current_period_end = Column(TIMESTAMP, nullable=False)
    trial_end = Column(TIMESTAMP, nullable=True)
    grace_period_end = Column(TIMESTAMP, nullable=True)
    cancelled_at = Column(TIMESTAMP, nullable=True)
    payment_method = Column(String(50), nullable=True)  # stripe, paystack, flutterwave, manual
    payment_customer_id = Column(String(255), nullable=True)
    payment_subscription_id = Column(String(255), nullable=True)
    created_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now(), nullable=False)


class Invoice(Base):
    """Billing invoice for a subscription period."""

    __tablename__ = "saas_invoices"

    id = Column(BigInt, primary_key=True, autoincrement=True)
    organization_id = Column(BigInt, nullable=False, index=True)
    subscription_id = Column(BigInt, nullable=False, index=True)
    invoice_number = Column(String(100), unique=True, nullable=False)
    amount = Column(Float, nullable=False)
    currency = Column(String(10), nullable=False, default="USD")
    status = Column(
        String(20), nullable=False, default="pending"
    )  # pending, paid, failed, refunded
    billing_period_start = Column(TIMESTAMP, nullable=False)
    billing_period_end = Column(TIMESTAMP, nullable=False)
    due_date = Column(TIMESTAMP, nullable=True)
    paid_at = Column(TIMESTAMP, nullable=True)
    line_items = Column(JSON, nullable=True)  # list of {description, quantity, unit_price, total}
    payment_provider = Column(String(50), nullable=True)
    payment_reference = Column(String(255), nullable=True)
    created_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)


class UsageRecord(Base):
    """Monthly usage tracking per organization."""

    __tablename__ = "saas_usage_records"

    id = Column(BigInt, primary_key=True, autoincrement=True)
    organization_id = Column(BigInt, nullable=False, index=True)
    period_year = Column(Integer, nullable=False)
    period_month = Column(Integer, nullable=False)
    active_users = Column(Integer, default=0, nullable=False)
    storage_used_mb = Column(Float, default=0.0, nullable=False)
    ai_requests = Column(Integer, default=0, nullable=False)
    api_calls = Column(Integer, default=0, nullable=False)
    workflow_executions = Column(Integer, default=0, nullable=False)
    scheduled_jobs = Column(Integer, default=0, nullable=False)
    model_trainings = Column(Integer, default=0, nullable=False)
    connector_usage = Column(Integer, default=0, nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now(), nullable=False)


# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# Feature Flags & Licensing
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•


class FeatureFlag(Base):
    """Feature flag definition."""

    __tablename__ = "saas_feature_flags"

    id = Column(BigInt, primary_key=True, autoincrement=True)
    flag_key = Column(
        String(100), unique=True, nullable=False
    )  # e.g. "ai_copilot", "marketplace", "automl"
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    category = Column(String(50), nullable=False)  # core, premium, enterprise, beta
    default_enabled = Column(Boolean, default=False, nullable=False)
    min_plan = Column(String(50), nullable=True)  # minimum plan code required
    is_beta = Column(Boolean, default=False, nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)


class OrganizationFeatureOverride(Base):
    """Per-organization feature flag override."""

    __tablename__ = "saas_feature_overrides"

    id = Column(BigInt, primary_key=True, autoincrement=True)
    organization_id = Column(BigInt, nullable=False, index=True)
    flag_key = Column(String(100), nullable=False)
    is_enabled = Column(Boolean, nullable=False)
    reason = Column(String(200), nullable=True)  # beta_access, manual_override, region_restriction
    expires_at = Column(TIMESTAMP, nullable=True)
    created_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)


# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# Customer Onboarding
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•


class OnboardingRecord(Base):
    """Tracks organization onboarding progress."""

    __tablename__ = "saas_onboarding_records"

    id = Column(BigInt, primary_key=True, autoincrement=True)
    organization_id = Column(BigInt, nullable=False, index=True)
    industry = Column(String(100), nullable=True)
    steps_completed = Column(JSON, nullable=True)  # list of completed step keys
    current_step = Column(String(50), default="org_creation", nullable=False)
    completion_percentage = Column(Integer, default=0, nullable=False)
    is_complete = Column(Boolean, default=False, nullable=False)
    completed_at = Column(TIMESTAMP, nullable=True)
    sample_data_loaded = Column(Boolean, default=False, nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now(), nullable=False)


# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# Customer Success
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•


class CustomerHealthScore(Base):
    """Computed health score for an organization."""

    __tablename__ = "saas_customer_health_scores"

    id = Column(BigInt, primary_key=True, autoincrement=True)
    organization_id = Column(BigInt, nullable=False, index=True)
    score = Column(Integer, nullable=False)  # 0-100
    status = Column(String(20), nullable=False)  # healthy, at_risk, critical
    factors = Column(JSON, nullable=True)  # {factor_name: {score, weight, detail}}
    active_users = Column(Integer, default=0, nullable=False)
    feature_adoption = Column(Float, default=0.0, nullable=False)  # % of features used
    last_activity = Column(TIMESTAMP, nullable=True)
    computed_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)


class SupportTicket(Base):
    """Support ticket for customer success tracking."""

    __tablename__ = "saas_support_tickets"

    id = Column(BigInt, primary_key=True, autoincrement=True)
    organization_id = Column(BigInt, nullable=False, index=True)
    user_id = Column(BigInt, nullable=False)
    subject = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    priority = Column(String(20), default="normal", nullable=False)  # low, normal, high, urgent
    status = Column(
        String(20), default="open", nullable=False
    )  # open, in_progress, resolved, closed
    category = Column(String(100), nullable=True)
    assigned_to = Column(BigInt, nullable=True)
    resolved_at = Column(TIMESTAMP, nullable=True)
    created_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now(), nullable=False)


# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# System Announcements
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•


class SystemAnnouncement(Base):
    """Platform-wide announcement from super admins."""

    __tablename__ = "saas_system_announcements"

    id = Column(BigInt, primary_key=True, autoincrement=True)
    title = Column(String(300), nullable=False)
    message = Column(Text, nullable=False)
    severity = Column(String(20), default="info", nullable=False)  # info, warning, critical
    target_audience = Column(
        String(50), default="all", nullable=False
    )  # all, free, paid, enterprise
    is_active = Column(Boolean, default=True, nullable=False)
    starts_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)
    ends_at = Column(TIMESTAMP, nullable=True)
    created_by = Column(BigInt, nullable=True)
    created_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)


# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# Notification Preferences
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•


class NotificationPreference(Base):
    """Per-user notification channel preferences."""

    __tablename__ = "saas_notification_preferences"

    id = Column(BigInt, primary_key=True, autoincrement=True)
    user_id = Column(BigInt, nullable=False, index=True)
    organization_id = Column(BigInt, nullable=False, index=True)
    channel_in_app = Column(Boolean, default=True, nullable=False)
    channel_email = Column(Boolean, default=True, nullable=False)
    channel_sms = Column(Boolean, default=False, nullable=False)
    channel_webhook = Column(Boolean, default=False, nullable=False)
    event_workflow_completed = Column(Boolean, default=True, nullable=False)
    event_dataset_processed = Column(Boolean, default=True, nullable=False)
    event_subscription_changes = Column(Boolean, default=True, nullable=False)
    event_security_alerts = Column(Boolean, default=True, nullable=False)
    event_billing_reminders = Column(Boolean, default=True, nullable=False)
    event_system_maintenance = Column(Boolean, default=True, nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now(), nullable=False)
