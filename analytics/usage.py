"""Usage analytics aggregation service.

Aggregates counts of platform resources for billing, monitoring, and
admin dashboards. All queries are scoped by organization unless the caller
is a super admin.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session as DbSession

from analytics.models import KPI, Dashboard
from audit.models import AuditLog
from authentication.models import User
from organizations.models import Organization
from shared.tenant import is_super_admin


class UsageAnalyticsService:
    """Service for collecting usage metrics."""

    def __init__(self, db: DbSession, current_user: dict):
        self.db = db
        self.current_user = current_user

    def get_organization_metrics(self, org_id: int | None = None) -> dict:
        """Return usage metrics for one or all organizations."""
        if org_id is None:
            if is_super_admin(self.current_user):
                return self._get_all_organizations_metrics()
            org_id = self.current_user.get("organization_id")
            if org_id is None:
                return {"organizations": []}
            return {"organizations": [self._get_single_org_metrics(org_id)]}

        if not is_super_admin(self.current_user):
            if self.current_user.get("organization_id") != org_id:
                return {"organizations": []}
        return {"organizations": [self._get_single_org_metrics(org_id)]}

    def get_system_metrics(self) -> dict:
        """Return overall platform metrics."""
        total_orgs = (
            self.db.execute(
                select(func.count(Organization.id)).where(Organization.is_deleted == 0)
            ).scalar()
            or 0
        )
        total_users = (
            self.db.execute(select(func.count(User.id)).where(User.is_deleted == 0)).scalar() or 0
        )
        total_dashboards = self.db.execute(select(func.count(Dashboard.id))).scalar() or 0
        total_kpis = self.db.execute(select(func.count(KPI.id))).scalar() or 0

        # Audit counts in the last 30 days.
        since = datetime.now(timezone.utc) - timedelta(days=30)
        recent_actions = (
            self.db.execute(
                select(func.count(AuditLog.id)).where(AuditLog.created_at >= since)
            ).scalar()
            or 0
        )

        return {
            "total_organizations": total_orgs,
            "total_users": total_users,
            "total_dashboards": total_dashboards,
            "total_kpis": total_kpis,
            "actions_last_30_days": recent_actions,
        }

    def _get_all_organizations_metrics(self) -> dict:
        orgs = (
            self.db.execute(
                select(Organization).where(Organization.is_deleted == 0).order_by(Organization.name)
            )
            .scalars()
            .all()
        )
        return {"organizations": [self._org_metrics(o) for o in orgs]}

    def _get_single_org_metrics(self, org_id: int) -> dict:
        org = self.db.execute(
            select(Organization).where(Organization.id == org_id, Organization.is_deleted == 0)
        ).scalar_one_or_none()
        if not org:
            return {}
        return self._org_metrics(org)

    def _org_metrics(self, org: Organization) -> dict:
        user_count = (
            self.db.execute(
                select(func.count(User.id)).where(
                    User.organization_id == org.id, User.is_deleted == 0
                )
            ).scalar()
            or 0
        )
        active_user_count = (
            self.db.execute(
                select(func.count(User.id)).where(
                    User.organization_id == org.id,
                    User.is_active == 1,
                    User.is_deleted == 0,
                )
            ).scalar()
            or 0
        )
        dashboard_count = (
            self.db.execute(
                select(func.count(Dashboard.id)).where(Dashboard.organization_id == org.id)
            ).scalar()
            or 0
        )
        kpi_count = (
            self.db.execute(
                select(func.count(KPI.id)).where(KPI.organization_id == org.id)
            ).scalar()
            or 0
        )
        return {
            "organization_id": org.id,
            "name": org.name,
            "slug": org.slug,
            "is_active": bool(org.is_active),
            "total_users": user_count,
            "active_users": active_user_count,
            "dashboards": dashboard_count,
            "kpis": kpi_count,
        }
