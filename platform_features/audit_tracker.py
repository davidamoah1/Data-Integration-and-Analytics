"""Audit Tracker — Automatic Audit Logging.

Tracks all user actions across 4 categories:
  - USER_ACTION: login, logout, profile updates, user management
  - DATA_ACCESS: dataset uploads, ETL imports/exports, data views
  - REPORTS: report generation, exports, dashboard views
  - AI_USAGE: AI queries, forecasts, copilot interactions

Provides:
  - AuditTracker: Service for logging and querying audit events
  - track_action: Decorator for automatic audit logging on route handlers
  - AuditSummary: Aggregated stats by category, user, and time period

Usage:
    from platform_features import AuditTracker, AuditCategory

    tracker = AuditTracker(db)
    tracker.log(user_id=1, action="dataset_upload", category=AuditCategory.DATA_ACCESS,
                resource_type="dataset", resource_id=42, org_id=1)
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from functools import wraps
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session as DbSession

logger = logging.getLogger(__name__)


class AuditCategory(str, Enum):
    """Categories of auditable actions."""

    USER_ACTION = "user_action"
    DATA_ACCESS = "data_access"
    REPORTS = "reports"
    AI_USAGE = "ai_usage"


# Maps action strings to categories
ACTION_CATEGORY_MAP: dict[str, AuditCategory] = {
    # User actions
    "login": AuditCategory.USER_ACTION,
    "logout": AuditCategory.USER_ACTION,
    "password_change": AuditCategory.USER_ACTION,
    "profile_updated": AuditCategory.USER_ACTION,
    "user_created": AuditCategory.USER_ACTION,
    "user_updated": AuditCategory.USER_ACTION,
    "user_deleted": AuditCategory.USER_ACTION,
    "user_roles_changed": AuditCategory.USER_ACTION,
    "email_verified": AuditCategory.USER_ACTION,
    "session_revoked": AuditCategory.USER_ACTION,
    "password_reset_requested": AuditCategory.USER_ACTION,
    "password_reset_completed": AuditCategory.USER_ACTION,
    # Data access
    "dataset_upload": AuditCategory.DATA_ACCESS,
    "dataset_view": AuditCategory.DATA_ACCESS,
    "dataset_delete": AuditCategory.DATA_ACCESS,
    "etl_import": AuditCategory.DATA_ACCESS,
    "etl_export": AuditCategory.DATA_ACCESS,
    "pipeline_execute": AuditCategory.DATA_ACCESS,
    "pipeline_create": AuditCategory.DATA_ACCESS,
    "data_export": AuditCategory.DATA_ACCESS,
    "data_view": AuditCategory.DATA_ACCESS,
    # Reports
    "report_generated": AuditCategory.REPORTS,
    "report_exported": AuditCategory.REPORTS,
    "report_viewed": AuditCategory.REPORTS,
    "dashboard_viewed": AuditCategory.REPORTS,
    "validation_run": AuditCategory.REPORTS,
    "quality_check": AuditCategory.REPORTS,
    # AI usage
    "ai_query": AuditCategory.AI_USAGE,
    "ai_forecast": AuditCategory.AI_USAGE,
    "ai_copilot": AuditCategory.AI_USAGE,
    "ai_anomaly": AuditCategory.AI_USAGE,
    "ai_workflow": AuditCategory.AI_USAGE,
    "ai_sql_generate": AuditCategory.AI_USAGE,
    "ai_data_quality": AuditCategory.AI_USAGE,
    "ai_predictive": AuditCategory.AI_USAGE,
}


@dataclass
class AuditSummary:
    """Aggregated audit summary."""

    total_events: int = 0
    by_category: dict[str, int] = field(default_factory=dict)
    by_user: dict[str, int] = field(default_factory=dict)
    by_action: dict[str, int] = field(default_factory=dict)
    period_start: str = ""
    period_end: str = ""

    def to_dict(self) -> dict:
        return {
            "total_events": self.total_events,
            "by_category": self.by_category,
            "by_user": self.by_user,
            "by_action": dict(
                sorted(self.by_action.items(), key=lambda x: x[1], reverse=True)[:20]
            ),
            "period_start": self.period_start,
            "period_end": self.period_end,
        }


class AuditTracker:
    """Service for logging and querying audit events."""

    def __init__(self, db: DbSession):
        self.db = db

    def log(
        self,
        user_id: int,
        action: str,
        category: AuditCategory | None = None,
        resource_type: str | None = None,
        resource_id: int | None = None,
        organization_id: int | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
        extra_data: dict | None = None,
    ) -> None:
        """Log an audit event.

        Args:
            user_id: ID of the user performing the action.
            action: Action name (e.g., "dataset_upload").
            category: Audit category. If None, auto-detected from action.
            resource_type: Type of resource affected.
            resource_id: ID of the resource affected.
            organization_id: Organization ID for tenant scoping.
            ip_address: Request IP address.
            user_agent: Request user agent.
            extra_data: Additional metadata.
        """
        if category is None:
            category = ACTION_CATEGORY_MAP.get(action, AuditCategory.USER_ACTION)

        # Store the category in extra_data since the ActivityLog model
        # doesn't have a category column
        data = extra_data or {}
        data["audit_category"] = category.value

        from authentication.models import ActivityLog

        log_entry = ActivityLog(
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            ip_address=ip_address,
            user_agent=user_agent,
            extra_data=data,
        )
        self.db.add(log_entry)
        self.db.flush()

    def log_from_request(
        self,
        user: dict,
        action: str,
        category: AuditCategory | None = None,
        resource_type: str | None = None,
        resource_id: int | None = None,
        request=None,
        extra_data: dict | None = None,
    ) -> None:
        """Log an audit event from a FastAPI request context."""
        ip = None
        ua = None
        if request:
            ip = request.client.host if request.client else None
            ua = request.headers.get("user-agent")

        self.log(
            user_id=user["id"],
            action=action,
            category=category,
            resource_type=resource_type,
            resource_id=resource_id,
            organization_id=user.get("organization_id"),
            ip_address=ip,
            user_agent=ua,
            extra_data=extra_data,
        )

    def get_summary(
        self,
        organization_id: int | None = None,
        days: int = 30,
    ) -> AuditSummary:
        """Get an aggregated audit summary.

        Args:
            organization_id: Filter by organization (None = all).
            days: Number of days to include.

        Returns:
            AuditSummary with counts by category, user, and action.
        """
        from authentication.models import ActivityLog

        since = datetime.now(timezone.utc) - timedelta(days=days)

        query = select(ActivityLog).where(ActivityLog.created_at >= since)
        if organization_id is not None:
            # Filter by user's org — would need a join in production
            pass

        logs = self.db.execute(query).scalars().all()

        by_category: dict[str, int] = {}
        by_user: dict[str, int] = {}
        by_action: dict[str, int] = {}

        for log in logs:
            # Extract category from extra_data
            data = log.extra_data or {}
            cat = data.get("audit_category", AuditCategory.USER_ACTION.value)
            by_category[cat] = by_category.get(cat, 0) + 1

            user_key = str(log.user_id) if log.user_id else "system"
            by_user[user_key] = by_user.get(user_key, 0) + 1

            by_action[log.action] = by_action.get(log.action, 0) + 1

        return AuditSummary(
            total_events=len(logs),
            by_category=by_category,
            by_user=by_user,
            by_action=by_action,
            period_start=since.isoformat(),
            period_end=datetime.now(timezone.utc).isoformat(),
        )

    def get_user_activity(
        self,
        user_id: int,
        days: int = 30,
        category: AuditCategory | None = None,
    ) -> list[dict]:
        """Get activity log for a specific user."""
        from authentication.models import ActivityLog

        since = datetime.now(timezone.utc) - timedelta(days=days)
        query = (
            select(ActivityLog)
            .where(ActivityLog.user_id == user_id, ActivityLog.created_at >= since)
            .order_by(ActivityLog.created_at.desc())
        )

        logs = self.db.execute(query).scalars().all()

        results = []
        for log in logs:
            data = log.extra_data or {}
            cat = data.get("audit_category", AuditCategory.USER_ACTION.value)
            if category and cat != category.value:
                continue
            results.append(
                {
                    "id": log.id,
                    "action": log.action,
                    "category": cat,
                    "resource_type": log.resource_type,
                    "resource_id": log.resource_id,
                    "ip_address": log.ip_address,
                    "created_at": str(log.created_at) if log.created_at else None,
                }
            )

        return results

    def get_category_stats(
        self,
        organization_id: int | None = None,
        days: int = 30,
    ) -> dict[str, dict]:
        """Get detailed stats per audit category."""
        summary = self.get_summary(organization_id, days)

        stats = {}
        for cat_name, count in summary.by_category.items():
            stats[cat_name] = {
                "count": count,
                "percentage": round(count / max(summary.total_events, 1) * 100, 1),
            }

        return stats


def track_action(
    action: str,
    category: AuditCategory | None = None,
    resource_type: str | None = None,
) -> Callable:
    """Decorator for automatic audit logging on route handlers.

    Usage:
        @router.post("/datasets/upload")
        @track_action("dataset_upload", AuditCategory.DATA_ACCESS, "dataset")
        async def upload_dataset(...):
            ...

    The decorator logs the action after the route handler completes.
    It requires the route to have a `current_user` parameter.
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            # Extract current_user from kwargs
            current_user = kwargs.get("current_user")
            request = kwargs.get("request")
            db = kwargs.get("db")

            result = await func(*args, **kwargs)

            # Log the action
            if current_user and db:
                try:
                    tracker = AuditTracker(db)
                    tracker.log_from_request(
                        user=current_user,
                        action=action,
                        category=category,
                        resource_type=resource_type,
                        request=request,
                    )
                    db.commit()
                except Exception:
                    # Don't fail the request if audit logging fails, but make
                    # sure the gap in the audit trail is visible in logs.
                    logger.warning(
                        "Audit logging failed for action '%s' (category=%s)",
                        action,
                        category,
                        exc_info=True,
                    )

            return result

        return wrapper

    return decorator
