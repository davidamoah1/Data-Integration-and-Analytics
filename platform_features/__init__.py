"""Enterprise Platform Features.

Multi-tenancy, RBAC enhancements, and comprehensive audit tracking.

Modules:
  tenant â€” TenantContext for org-scoped data isolation
  rbac â€” Role hierarchy, permission matrix, role checks
  audit_tracker â€” Automatic audit logging for all actions
  seed â€” Seed organizations (Hospital A, School B, Company C) and roles
"""

from __future__ import annotations

from platform_features.audit_tracker import (
    AuditCategory,
    AuditSummary,
    AuditTracker,
    track_action,
)
from platform_features.rbac import (
    PERMISSION_MATRIX,
    ROLE_HIERARCHY,
    PermissionMatrix,
    RoleHierarchy,
    RoleLevel,
    get_role_level,
    has_role_or_higher,
)
from platform_features.seed import seed_enterprise_data
from platform_features.tenant import TenantContext, TenantFilter, tenant_scope

__all__ = [
    "TenantContext",
    "TenantFilter",
    "tenant_scope",
    "RoleHierarchy",
    "PermissionMatrix",
    "ROLE_HIERARCHY",
    "PERMISSION_MATRIX",
    "has_role_or_higher",
    "get_role_level",
    "RoleLevel",
    "AuditTracker",
    "AuditCategory",
    "track_action",
    "AuditSummary",
    "seed_enterprise_data",
]
