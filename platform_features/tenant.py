"""Multi-Tenancy — Tenant Context and Data Isolation.

Ensures users only access data within their organization.
Provides:
  - TenantContext: Holds the current user's organization context
  - TenantFilter: Query mixin that automatically filters by organization_id
  - tenant_scope: Decorator/context manager for org-scoped operations

Usage in routes:
    @router.get("/datasets")
    async def list_datasets(
        current_user: dict = Depends(get_current_user),
        db: DbSession = Depends(get_db),
    ):
        ctx = TenantContext.from_user(current_user)
        query = TenantFilter.apply_org_filter(select(Dataset), ctx)
        ...
"""

from __future__ import annotations

from collections.abc import Generator
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Any


@dataclass
class TenantContext:
    """Holds tenant context for the current request."""

    organization_id: int | None
    user_id: int
    roles: list[str]
    is_super_admin: bool

    @classmethod
    def from_user(cls, user: dict) -> TenantContext:
        """Create a TenantContext from the current_user dict."""
        return cls(
            organization_id=user.get("organization_id"),
            user_id=user["id"],
            roles=user.get("roles", []),
            is_super_admin="super_admin" in user.get("roles", []),
        )

    @property
    def is_tenant_scoped(self) -> bool:
        """Whether this context enforces tenant isolation."""
        return not self.is_super_admin and self.organization_id is not None

    def can_access_org(self, org_id: int | None) -> bool:
        """Check if this context can access data for the given org."""
        if self.is_super_admin:
            return True
        return org_id == self.organization_id


class TenantFilter:
    """Applies organization filters to queries for tenant isolation."""

    @staticmethod
    def apply_org_filter(query, ctx: TenantContext, model_class=None, org_column=None):
        """Apply organization filter to a SQLAlchemy query.

        Args:
            query: SQLAlchemy select query.
            ctx: Current tenant context.
            model_class: The model class to extract organization_id from (required if org_column is None).
            org_column: The specific organization_id column to filter on.

        Returns:
            Filtered query (super_admin sees all, others see only their org).
        """
        if ctx.is_super_admin:
            return query
        if ctx.organization_id is None:
            return query
        if org_column is not None:
            return query.where(org_column == ctx.organization_id)
        if model_class is not None and hasattr(model_class, "organization_id"):
            return query.where(model_class.organization_id == ctx.organization_id)
        return query

    @staticmethod
    def apply_org_filter_to_model(query, model_class, ctx: TenantContext):
        """Apply org filter using a model class's organization_id column."""
        if ctx.is_super_admin:
            return query
        if ctx.organization_id is None:
            return query
        if hasattr(model_class, "organization_id"):
            return query.where(model_class.organization_id == ctx.organization_id)
        return query


@contextmanager
def tenant_scope(ctx: TenantContext) -> Generator[TenantContext, Any, None]:
    """Context manager for tenant-scoped operations.

    Usage:
        with tenant_scope(TenantContext.from_user(current_user)) as tctx:
            # All operations here are tenant-scoped
            query = TenantFilter.apply_org_filter(select(Model), tctx)
    """
    yield ctx
