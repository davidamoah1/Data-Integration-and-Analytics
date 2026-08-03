"""Repository for audit log data access with rich filtering."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session as DbSession

from audit.models import AuditLog, SecurityLog, UserActivity


class AuditRepository:
    """Repository for querying audit logs with organization-scoped filtering."""

    def __init__(self, db: DbSession):
        self.db = db

    # ── Audit Logs ──────────────────────────────────────────────────────

    def list_logs(
        self,
        *,
        organization_id: int | None = None,
        user_id: int | None = None,
        action: str | None = None,
        resource_type: str | None = None,
        resource_id: int | None = None,
        ip_address: str | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[AuditLog]:
        """Query audit logs with optional filters."""
        q = select(AuditLog).order_by(AuditLog.created_at.desc())
        q = self._apply_filters(
            q, organization_id, user_id, action, resource_type,
            resource_id, ip_address, start_date, end_date,
        )
        return list(self.db.execute(q.offset(offset).limit(limit)).scalars().all())

    def count_logs(
        self,
        *,
        organization_id: int | None = None,
        user_id: int | None = None,
        action: str | None = None,
        resource_type: str | None = None,
        resource_id: int | None = None,
        ip_address: str | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ) -> int:
        """Count audit logs matching filters."""
        q = select(func.count()).select_from(AuditLog)
        q = self._apply_filters(
            q, organization_id, user_id, action, resource_type,
            resource_id, ip_address, start_date, end_date,
        )
        return int(self.db.execute(q).scalar() or 0)

    def get_log(self, log_id: int) -> AuditLog | None:
        return self.db.execute(
            select(AuditLog).where(AuditLog.id == log_id)
        ).scalar_one_or_none()

    def list_actions(self, organization_id: int | None = None) -> list[str]:
        """Get distinct action types for filter dropdowns."""
        q = select(AuditLog.action).distinct().order_by(AuditLog.action)
        if organization_id is not None:
            q = q.where(AuditLog.organization_id == organization_id)
        return [r[0] for r in self.db.execute(q).all()]

    def list_resource_types(self, organization_id: int | None = None) -> list[str]:
        """Get distinct resource types for filter dropdowns."""
        q = (
            select(AuditLog.resource_type)
            .distinct()
            .where(AuditLog.resource_type.isnot(None))
            .order_by(AuditLog.resource_type)
        )
        if organization_id is not None:
            q = q.where(AuditLog.organization_id == organization_id)
        return [r[0] for r in self.db.execute(q).all()]

    # ── Stats / Aggregations ────────────────────────────────────────────

    def action_counts(
        self,
        organization_id: int | None = None,
        *,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ) -> dict[str, int]:
        """Count logs grouped by action."""
        q = (
            select(AuditLog.action, func.count())
            .group_by(AuditLog.action)
            .order_by(func.count().desc())
        )
        if organization_id is not None:
            q = q.where(AuditLog.organization_id == organization_id)
        if start_date is not None:
            q = q.where(AuditLog.created_at >= start_date)
        if end_date is not None:
            q = q.where(AuditLog.created_at <= end_date)
        return {row[0]: row[1] for row in self.db.execute(q).all()}

    def daily_counts(
        self,
        organization_id: int | None = None,
        *,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ) -> list[dict[str, Any]]:
        """Count logs grouped by day."""
        day = func.date(AuditLog.created_at).label("day")
        q = select(day, func.count()).group_by(day).order_by(day.desc())
        if organization_id is not None:
            q = q.where(AuditLog.organization_id == organization_id)
        if start_date is not None:
            q = q.where(AuditLog.created_at >= start_date)
        if end_date is not None:
            q = q.where(AuditLog.created_at <= end_date)
        return [{"date": str(row[0]), "count": row[1]} for row in self.db.execute(q).all()]

    def top_users(
        self,
        organization_id: int | None = None,
        *,
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        """Get most active users by audit event count."""
        q = (
            select(AuditLog.user_id, func.count().label("cnt"))
            .where(AuditLog.user_id.isnot(None))
            .group_by(AuditLog.user_id)
            .order_by(func.count().desc())
            .limit(limit)
        )
        if organization_id is not None:
            q = q.where(AuditLog.organization_id == organization_id)
        return [{"user_id": row[0], "count": row[1]} for row in self.db.execute(q).all()]

    # ── Security Logs ───────────────────────────────────────────────────

    def list_security_logs(
        self,
        *,
        organization_id: int | None = None,
        severity: str | None = None,
        event_type: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[SecurityLog]:
        q = select(SecurityLog).order_by(SecurityLog.created_at.desc())
        if organization_id is not None:
            q = q.where(SecurityLog.organization_id == organization_id)
        if severity:
            q = q.where(SecurityLog.severity == severity)
        if event_type:
            q = q.where(SecurityLog.event_type == event_type)
        return list(self.db.execute(q.offset(offset).limit(limit)).scalars().all())

    def count_security_logs(
        self,
        *,
        organization_id: int | None = None,
        severity: str | None = None,
        event_type: str | None = None,
    ) -> int:
        q = select(func.count()).select_from(SecurityLog)
        if organization_id is not None:
            q = q.where(SecurityLog.organization_id == organization_id)
        if severity:
            q = q.where(SecurityLog.severity == severity)
        if event_type:
            q = q.where(SecurityLog.event_type == event_type)
        return int(self.db.execute(q).scalar() or 0)

    # ── User Activity ───────────────────────────────────────────────────

    def list_user_activity(
        self,
        user_id: int,
        *,
        limit: int = 50,
        offset: int = 0,
    ) -> list[UserActivity]:
        q = (
            select(UserActivity)
            .where(UserActivity.user_id == user_id)
            .order_by(UserActivity.created_at.desc())
        )
        return list(self.db.execute(q.offset(offset).limit(limit)).scalars().all())

    # ── Helpers ─────────────────────────────────────────────────────────

    @staticmethod
    def _apply_filters(
        q,
        organization_id: int | None,
        user_id: int | None,
        action: str | None,
        resource_type: str | None,
        resource_id: int | None,
        ip_address: str | None,
        start_date: datetime | None,
        end_date: datetime | None,
    ):
        if organization_id is not None:
            q = q.where(AuditLog.organization_id == organization_id)
        if user_id is not None:
            q = q.where(AuditLog.user_id == user_id)
        if action:
            q = q.where(AuditLog.action == action)
        if resource_type:
            q = q.where(AuditLog.resource_type == resource_type)
        if resource_id is not None:
            q = q.where(AuditLog.resource_id == resource_id)
        if ip_address:
            q = q.where(AuditLog.ip_address == ip_address)
        if start_date is not None:
            q = q.where(AuditLog.created_at >= start_date)
        if end_date is not None:
            q = q.where(AuditLog.created_at <= end_date)
        return q
