"""Platform Features Routes.

Endpoints for:
  - Audit summary and category stats
  - Role hierarchy and permission matrix
  - Tenant context info
  - Enterprise seed data (demo only â€” blocked in production)
"""

from __future__ import annotations

import os

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session as DbSession

from platform_features.audit_tracker import AuditCategory, AuditTracker
from platform_features.rbac import PermissionMatrix, RoleHierarchy
from platform_features.seed import seed_enterprise_data
from shared.database import get_db
from shared.dependencies import get_current_user, require_any_role, require_permissions
from shared.response import success_response

platform_router = APIRouter(prefix="/platform", tags=["Platform"])


# --- Audit Summary --------------------------------------------------------


@platform_router.get("/audit/summary")
async def audit_summary(
    days: int = 30,
    current_user: dict = Depends(require_permissions("audit.view")),
    db: DbSession = Depends(get_db),
):
    """Get aggregated audit summary by category, user, and action."""
    tracker = AuditTracker(db)
    summary = tracker.get_summary(
        organization_id=current_user.get("organization_id"),
        days=days,
    )
    return success_response(summary.to_dict())


@platform_router.get("/audit/categories")
async def audit_category_stats(
    days: int = 30,
    current_user: dict = Depends(require_permissions("audit.view")),
    db: DbSession = Depends(get_db),
):
    """Get audit event counts per category."""
    tracker = AuditTracker(db)
    stats = tracker.get_category_stats(
        organization_id=current_user.get("organization_id"),
        days=days,
    )
    return success_response(stats)


@platform_router.get("/audit/user/{user_id}")
async def user_audit_trail(
    user_id: int,
    days: int = 30,
    category: str | None = None,
    current_user: dict = Depends(require_permissions("audit.view")),
    db: DbSession = Depends(get_db),
):
    """Get detailed audit trail for a specific user."""
    tracker = AuditTracker(db)
    cat = AuditCategory(category) if category else None
    activities = tracker.get_user_activity(user_id, days=days, category=cat)
    return success_response(activities)


# --- Role Hierarchy -------------------------------------------------------


@platform_router.get("/roles/hierarchy")
async def role_hierarchy(
    current_user: dict = Depends(get_current_user),
):
    """Get the role hierarchy with levels and display names."""
    return success_response(RoleHierarchy.all_roles())


@platform_router.get("/roles/permissions-matrix")
async def permissions_matrix(
    current_user: dict = Depends(require_permissions("role.read")),
):
    """Get the full permission matrix for all roles."""
    return success_response(PermissionMatrix.get_role_permissions_summary())


# --- Tenant Context -------------------------------------------------------


@platform_router.get("/tenant/context")
async def tenant_context(
    current_user: dict = Depends(get_current_user),
):
    """Get the current user's tenant context."""
    from platform_features.tenant import TenantContext

    ctx = TenantContext.from_user(current_user)
    return success_response(
        {
            "organization_id": ctx.organization_id,
            "user_id": ctx.user_id,
            "roles": ctx.roles,
            "is_super_admin": ctx.is_super_admin,
            "is_tenant_scoped": ctx.is_tenant_scoped,
            "highest_role": RoleHierarchy.get_highest_role(ctx.roles),
        }
    )


# --- Seed Data ------------------------------------------------------------


@platform_router.post("/seed")
async def seed_enterprise(
    current_user: dict = Depends(require_any_role("super_admin", "org_admin")),
    db: DbSession = Depends(get_db),
):
    """Seed enterprise demo data (organizations, roles, users).

    Blocked in production. Only available when SEED_DEMO_DATA=true
    or APP_ENV is not 'production'.
    """
    app_env = os.getenv("APP_ENV", "development").lower()
    seed_enabled = os.getenv("SEED_DEMO_DATA", "false").lower() in ("true", "1", "yes")
    if app_env == "production" and not seed_enabled:
        raise HTTPException(
            status_code=403,
            detail="Demo data seeding is disabled in production. "
            "Set SEED_DEMO_DATA=true to enable for pilot deployments.",
        )
    result = seed_enterprise_data(db)
    return success_response(result, result["summary"])
