# Governance Documentation Index

> **Version**: 1.0.0  
> **Last Updated**: 2026-07-30  
> **Status**: Active  
> **Repository**: `davidamoah1/Data-Integration-and-Analytics`

---

## Overview

This is the authoritative index for all enterprise governance documentation. All documents are maintained alongside the source code in the `docs/governance/` directory.

---

## Document Catalog

### 1. Permission & Authorization

| Document | Path | Description |
|----------|------|-------------|
| Enterprise Permission Matrix | `permission-matrix.md` | Human-readable permission matrix: roles, modules, actions, restrictions |
| Permission Matrix (JSON) | `permission-matrix.json` | Machine-readable permission definitions, role-permission mappings, module definitions |
| API Authorization Matrix | `api-authorization-matrix.md` | Every API endpoint mapped to required permissions and org scope |
| Frontend Navigation Matrix | `frontend-navigation-matrix.md` | Sidebar visibility rules, page-level access control, role-to-navigation mapping |

### 2. User Journeys

| Document | Path | Description |
|----------|------|-------------|
| User Journey Maps | `user-journeys.md` | Complete lifecycle for every role: entry, goals, tasks, decisions, errors, success, exit |

### 3. Architecture Decision Records (ADR)

| ADR | Path | Title | Status |
|-----|------|-------|--------|
| ADR-0001 | `adr/ADR-0001-enterprise-multi-tenant-architecture.md` | Enterprise Multi-Tenant Architecture | Accepted |
| ADR-0002 | `adr/ADR-0002-blank-workspace-by-default.md` | Blank Workspace by Default | Accepted |
| ADR-0003 | `adr/ADR-0003-optional-sample-workspace.md` | Optional Sample Workspace | Accepted |
| ADR-0004 | `adr/ADR-0004-invitation-based-user-onboarding.md` | Invitation-Based User Onboarding | Accepted |
| ADR-0005 | `adr/ADR-0005-role-based-access-control.md` | Role-Based Access Control | Accepted |
| ADR-0006 | `adr/ADR-0006-platform-owner-vs-organization-administrator.md` | Platform Owner vs Organization Administrator | Accepted |
| ADR-0007 | `adr/ADR-0007-department-based-data-governance.md` | Department-Based Data Governance | Accepted |
| ADR-0008 | `adr/ADR-0008-permission-middleware.md` | Permission Middleware | Accepted |
| ADR-0009 | `adr/ADR-0009-workspace-model.md` | Workspace Model | Accepted |
| ADR-0010 | `adr/ADR-0010-audit-logging.md` | Audit Logging | Accepted |
| ADR-0011 | `adr/ADR-0011-template-architecture.md` | Template Architecture | Accepted |
| ADR-0012 | `adr/ADR-0012-future-enterprise-readiness.md` | Future Enterprise Readiness | Proposed |

### 4. Governance

| Document | Path | Description |
|----------|------|-------------|
| Governance Summary | `governance-summary.md` | Executive summary of governance posture |
| Maintenance Guidelines | `maintenance-guidelines.md` | How to keep documentation synchronized with code |

---

## Source Code References

### Backend (Python / FastAPI)

| File | Purpose |
|------|---------|
| `authentication/routes.py` | Auth, user management, role management API routes |
| `authentication/services.py` | Auth, user, role services + `seed_default_data()` |
| `authentication/models.py` | User, Role, Permission, RolePermission, UserRole models |
| `authentication/repositories.py` | Repository classes for auth models |
| `authentication/schemas.py` | Pydantic schemas for auth requests/responses |
| `organizations/services.py` | Organization and department API routes |
| `organizations/invitation_service.py` | Invitation and registration services |
| `organizations/invitation_routes.py` | Invitation and registration v2 API routes |
| `organizations/invitation_schemas.py` | Pydantic schemas for invitations |
| `organizations/models.py` | Organization, Department models |
| `organizations/workspace_models.py` | Workspace, Invitation models |
| `shared/dependencies.py` | `get_current_user`, `require_permissions`, `require_any_role` |
| `shared/tenant.py` | `get_current_organization_id`, `is_super_admin`, `require_organization_access` |
| `platform_features/tenant.py` | `TenantContext`, `TenantFilter` |
| `platform_features/rbac.py` | `RoleHierarchy`, `PermissionMatrix`, `ROLE_HIERARCHY` |
| `saas/tenant_middleware.py` | `TenantIsolationMiddleware` |
| `audit/models.py` | `AuditLog`, `SecurityLog`, `SystemLog`, `UserActivity` models |
| `enterprise/demo_data.py` | `seed_demo_data()` function |
| `api/main.py` | Application entry point, demo data seeding check |

### Frontend (React / Next.js)

| File | Purpose |
|------|---------|
| `frontend/lib/permissions.ts` | Permission constants, role definitions, permission groups |
| `frontend/stores/authStore.ts` | `useAuthStore` hook with `hasPermission()`, `hasRole()` |
| `frontend/components/auth/RouteGuard.tsx` | Route-level permission/role guard |
| `frontend/components/auth/Can.tsx` | Conditional rendering based on permissions |
| `frontend/components/layout/Sidebar.tsx` | Navigation with permission-based visibility |
| `frontend/app/(app)/dashboard/page.tsx` | Dashboard with empty states and quick start |
| `frontend/app/(app)/settings/page.tsx` | Settings with permission-filtered tabs |
| `frontend/app/(app)/admin/page.tsx` | User management page |
| `frontend/app/(app)/admin-portal/page.tsx` | Super admin portal |
| `frontend/app/(app)/audit/page.tsx` | Audit log viewer |
| `frontend/app/signup/page.tsx` | Multi-mode registration page |
| `frontend/app/invite/page.tsx` | Invitation acceptance page |
| `frontend/app/onboarding/page.tsx` | Onboarding wizard |

---

## Validation Checklist

- [x] Every role has documented permissions — See `permission-matrix.md` Section 4
- [x] Every permission maps to a module — See `permission-matrix.md` Section 5
- [x] Every module defines allowed actions — See `permission-matrix.md` Section 5
- [x] Every user type has a complete journey — See `user-journeys.md`
- [x] Every major architectural decision has an ADR — See ADR-0001 through ADR-0012
- [x] Documentation reflects the current implementation — Verified against source code
- [x] Future features are clearly marked as planned — See ADR-0012 (status: Proposed)
- [x] Machine-readable permission definitions exist — See `permission-matrix.json`
- [x] API authorization mapping is complete — See `api-authorization-matrix.md`
- [x] Frontend navigation rules are documented — See `frontend-navigation-matrix.md`
