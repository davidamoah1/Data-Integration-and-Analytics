# API Authorization Matrix

> **Version**: 1.0.0  
> **Last Updated**: 2026-07-30  
> **Status**: Active

---

## Overview

This document maps every API endpoint to its authorization requirements. All endpoints except public ones require a valid JWT bearer token.

---

## Authentication Endpoints (`/api/auth`)

| Method | Path | Permission | Org Scope | Notes |
|--------|------|------------|-----------|-------|
| POST | `/api/auth/login` | Public | No | Returns access + refresh tokens |
| POST | `/api/auth/signup` | Public | No | Creates user, optionally org + workspace |
| POST | `/api/auth/signup-v2` | Public | No | Enhanced 3-mode registration |
| POST | `/api/auth/refresh` | Valid refresh token | No | Issues new access token |
| POST | `/api/auth/logout` | Authenticated | No | Revokes session |
| POST | `/api/auth/forgot-password` | Public | No | Sends reset email |
| POST | `/api/auth/reset-password` | Public | No | Resets password with token |
| POST | `/api/auth/verify-email` | Public | No | Verifies email with token |
| POST | `/api/auth/onboarding` | Authenticated | No | Saves onboarding data |
| GET | `/api/auth/me` | Authenticated | No | Returns current user profile |
| PUT | `/api/auth/profile` | `profile.update` | No | Updates own profile |
| POST | `/api/auth/change-password` | Authenticated | No | Changes password |

## User Management (`/api/users`)

| Method | Path | Permission | Org Scope | Notes |
|--------|------|------------|-----------|-------|
| GET | `/api/users` | `users.read` | Yes | Super admin sees all; others see own org only |
| POST | `/api/users` | `users.create` | Yes | Cannot create users outside own org (non-super-admin) |
| GET | `/api/users/{id}` | `users.read` | Yes | 403 if user belongs to different org |
| PUT | `/api/users/{id}` | `users.edit` | Yes | 403 if user belongs to different org |
| DELETE | `/api/users/{id}` | `users.delete` | Yes | 403 if user belongs to different org |
| POST | `/api/users/{id}/roles` | `users.manage` | Yes | 403 if user belongs to different org; blocks super_admin/org_owner for non-super-admins |

## Role Management (`/api/roles`)

| Method | Path | Permission | Org Scope | Notes |
|--------|------|------------|-----------|-------|
| GET | `/api/roles` | `roles.read` | No | Lists all roles |
| POST | `/api/roles` | `roles.manage` | No | Creates custom role |
| PUT | `/api/roles/{id}` | `roles.manage` | No | Updates role permissions |
| DELETE | `/api/roles/{id}` | `roles.manage` | No | Soft-deletes non-system roles |
| GET | `/api/roles/permissions` | `roles.read` | No | Lists all permissions |

## Organization Management (`/api/organizations`)

| Method | Path | Permission | Org Scope | Notes |
|--------|------|------------|-----------|-------|
| GET | `/api/organizations` | Authenticated | Yes | Super admin sees all; others see own org only |
| POST | `/api/organizations` | `organizations.manage` | No | Creates new org |
| GET | `/api/organizations/{id}` | Authenticated | Yes | `require_organization_access` enforced |
| PUT | `/api/organizations/{id}` | `organizations.manage` | Yes | `require_organization_access` enforced |
| DELETE | `/api/organizations/{id}` | `organizations.manage` | Yes | `require_organization_access` enforced |

## Department Management (`/api/departments`)

| Method | Path | Permission | Org Scope | Notes |
|--------|------|------------|-----------|-------|
| GET | `/api/departments` | Authenticated | Yes | Super admin can specify org_id; others use own |
| POST | `/api/departments` | `departments.manage` | Yes | Non-super-admin must create within own org |
| PUT | `/api/departments/{id}` | `departments.manage` | Yes | |
| DELETE | `/api/departments/{id}` | `departments.manage` | Yes | |

## Invitation Management (`/api/invitations`)

| Method | Path | Permission | Org Scope | Notes |
|--------|------|------------|-----------|-------|
| GET | `/api/invitations` | `users.read` | Yes | Lists invitations for own org |
| POST | `/api/invitations` | `users.manage` | Yes | Creates invitation; blocks super_admin/org_owner roles |
| DELETE | `/api/invitations/{id}` | `users.manage` | Yes | Revokes pending invitation |
| GET | `/api/invitations/info/{token}` | Public | No | Returns invitation details for landing page |
| POST | `/api/invitations/accept` | Public | No | Creates user from invitation; validates email match |

## Dataset Management (`/api/datasets`)

| Method | Path | Permission | Org Scope | Notes |
|--------|------|------------|-----------|-------|
| GET | `/api/datasets` | `datasets.view` | Yes | Org-scoped query |
| POST | `/api/datasets` | `datasets.upload` | Yes | Upload to own org |
| GET | `/api/datasets/{id}` | `datasets.view` | Yes | 403 if dataset belongs to different org |
| DELETE | `/api/datasets/{id}` | `datasets.delete` | Yes | 403 if dataset belongs to different org |

## Workflow Management (`/api/workflows`)

| Method | Path | Permission | Org Scope | Notes |
|--------|------|------------|-----------|-------|
| GET | `/api/workflows` | Authenticated | Yes | Org-scoped; super admin sees all |
| POST | `/api/workflows` | `pipelines.create` | Yes | |
| GET | `/api/workflows/{id}` | `pipelines.view` | Yes | `_ensure_org_access` enforced |
| PUT | `/api/workflows/{id}` | `pipelines.create` | Yes | |
| DELETE | `/api/workflows/{id}` | `pipelines.create` | Yes | |
| POST | `/api/workflows/{id}/execute` | `pipelines.execute` | Yes | |

## Analytics & Dashboards

| Method | Path | Permission | Org Scope | Notes |
|--------|------|------------|-----------|-------|
| GET | `/api/dashboards` | `dashboard.view` | Yes | Org-scoped |
| POST | `/api/dashboards` | `dashboard.manage` | Yes | |
| GET | `/api/dashboards/{id}` | `dashboard.view` | Yes | |
| PUT | `/api/dashboards/{id}` | `dashboard.manage` | Yes | |
| DELETE | `/api/dashboards/{id}` | `dashboard.manage` | Yes | |

## Reports

| Method | Path | Permission | Org Scope | Notes |
|--------|------|------------|-----------|-------|
| GET | `/api/reports` | `reports.view` | Yes | Org-scoped |
| POST | `/api/reports` | `reports.generate` | Yes | |
| GET | `/api/reports/{id}` | `reports.view` | Yes | |
| GET | `/api/reports/{id}/export` | `reports.export` | Yes | |

## Audit Logs

| Method | Path | Permission | Org Scope | Notes |
|--------|------|------------|-----------|-------|
| GET | `/api/audit/logs` | `audit.view` | Yes | Org-scoped; super admin sees all |

## Notification Endpoints

| Method | Path | Permission | Org Scope | Notes |
|--------|------|------------|-----------|-------|
| GET | `/api/notifications` | Authenticated | No | User-scoped (own notifications) |
| PUT | `/api/notifications/settings` | `notifications.manage` | No | |

## Session Management

| Method | Path | Permission | Org Scope | Notes |
|--------|------|------------|-----------|-------|
| GET | `/api/sessions` | `sessions.manage` | Yes | Lists active sessions for org |
| DELETE | `/api/sessions/{id}` | `sessions.manage` | Yes | Revokes session |

---

## Authorization Flow

```
Request → HTTPBearer → decode_token → get_current_user
                                    → check user.is_active
                                    → load roles from DB
                                    → load permissions from DB
                                    → require_permissions(*perms)
                                    → check super_admin bypass
                                    → check permission intersection
                                    → require_organization_access (if applicable)
                                    → check user.organization_id == resource.organization_id
                                    → Route handler
```

## Key Files

- **JWT verification & user loading**: `shared/dependencies.py`
- **Permission checking**: `shared/dependencies.py:require_permissions()`
- **Org access enforcement**: `shared/tenant.py:require_organization_access()`
- **Tenant context**: `platform_features/tenant.py:TenantContext`
- **Tenant isolation middleware**: `saas/tenant_middleware.py:TenantIsolationMiddleware`
