"""Enterprise Platform Features.

Multi-tenancy, RBAC enhancements, and comprehensive audit tracking.

Modules:
  tenant — TenantContext for org-scoped data isolation
  rbac — Role hierarchy, permission matrix, role checks
  audit_tracker — Automatic audit logging for all actions
  seed — Seed organizations (Hospital A, School B, Company C) and roles
"""

from __future__ import annotations

from platform_features.tenant import TenantContext, TenantFilter, tenant_scope
from platform_features.rbac import (
    RoleHierarchy,
    PermissionMatrix,
    ROLE_HIERARCHY,
    PERMISSION_MATRIX,
    has_role_or_higher,
    get_role_level,
    RoleLevel,
)
from platform_features.audit_tracker import (
    AuditTracker,
    AuditCategory,
    track_action,
    AuditSummary,
)
from platform_features.seed import seed_enterprise_data

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
