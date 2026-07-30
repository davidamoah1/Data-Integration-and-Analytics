# API Endpoints

> **Version**: 1.0.0  
> **Last Updated**: 2026-07-30  
> **Status**: Active  
> **Owner**: Backend Lead

---

## Purpose

Complete endpoint catalog with methods, paths, and permissions.

## Scope

All REST API endpoints.

## Audience

Backend developers and API consumers.

---

## Authentication

| Method | Path | Permission | Description |
|--------|------|------------|-------------|
| POST | `/api/auth/login` | Public | Login with email/password |
| POST | `/api/auth/signup` | Public | Register + optionally create org |
| POST | `/api/auth/signup-v2` | Public | Enhanced 3-mode registration |
| POST | `/api/auth/refresh` | Refresh token | Refresh access token |
| POST | `/api/auth/logout` | Authenticated | Revoke session |
| POST | `/api/auth/forgot-password` | Public | Request password reset |
| POST | `/api/auth/reset-password` | Public | Reset password with token |
| POST | `/api/auth/verify-email` | Public | Verify email with token |
| POST | `/api/auth/onboarding` | Authenticated | Save onboarding data |
| GET | `/api/auth/me` | Authenticated | Get current user |
| PUT | `/api/auth/profile` | `profile.update` | Update own profile |
| POST | `/api/auth/change-password` | Authenticated | Change password |

## User Management

| Method | Path | Permission | Org Scope | Description |
|--------|------|------------|-----------|-------------|
| GET | `/api/users` | `users.read` | Yes | List users (org-scoped) |
| POST | `/api/users` | `users.create` | Yes | Create user |
| GET | `/api/users/{id}` | `users.read` | Yes | Get user by ID |
| PUT | `/api/users/{id}` | `users.edit` | Yes | Update user |
| DELETE | `/api/users/{id}` | `users.delete` | Yes | Soft-delete user |
| POST | `/api/users/{id}/roles` | `users.manage` | Yes | Assign roles |

## Role Management

| Method | Path | Permission | Description |
|--------|------|------------|-------------|
| GET | `/api/roles` | `roles.read` | List all roles |
| POST | `/api/roles` | `roles.manage` | Create custom role |
| PUT | `/api/roles/{id}` | `roles.manage` | Update role |
| DELETE | `/api/roles/{id}` | `roles.manage` | Soft-delete role |
| GET | `/api/roles/permissions` | `roles.read` | List all permissions |

## Organization Management

| Method | Path | Permission | Org Scope | Description |
|--------|------|------------|-----------|-------------|
| GET | `/api/organizations` | Authenticated | Yes | List organizations |
| POST | `/api/organizations` | `organizations.manage` | No | Create organization |
| GET | `/api/organizations/{id}` | Authenticated | Yes | Get organization |
| PUT | `/api/organizations/{id}` | `organizations.manage` | Yes | Update organization |
| DELETE | `/api/organizations/{id}` | `organizations.manage` | Yes | Delete organization |

## Department Management

| Method | Path | Permission | Org Scope | Description |
|--------|------|------------|-----------|-------------|
| GET | `/api/departments` | Authenticated | Yes | List departments |
| POST | `/api/departments` | `departments.manage` | Yes | Create department |
| PUT | `/api/departments/{id}` | `departments.manage` | Yes | Update department |
| DELETE | `/api/departments/{id}` | `departments.manage` | Yes | Delete department |

## Invitations

| Method | Path | Permission | Description |
|--------|------|------------|-------------|
| GET | `/api/invitations` | `users.read` | List invitations |
| POST | `/api/invitations` | `users.manage` | Create invitation |
| DELETE | `/api/invitations/{id}` | `users.manage` | Revoke invitation |
| GET | `/api/invitations/info/{token}` | Public | Get invitation info |
| POST | `/api/invitations/accept` | Public | Accept invitation |

## Datasets

| Method | Path | Permission | Org Scope | Description |
|--------|------|------------|-----------|-------------|
| GET | `/api/datasets` | `datasets.view` | Yes | List datasets |
| POST | `/api/datasets` | `datasets.upload` | Yes | Upload dataset |
| GET | `/api/datasets/{id}` | `datasets.view` | Yes | Get dataset |
| DELETE | `/api/datasets/{id}` | `datasets.delete` | Yes | Delete dataset |

## Workflows

| Method | Path | Permission | Org Scope | Description |
|--------|------|------------|-----------|-------------|
| GET | `/api/workflows` | Authenticated | Yes | List workflows |
| POST | `/api/workflows` | `pipelines.create` | Yes | Create workflow |
| GET | `/api/workflows/{id}` | `pipelines.view` | Yes | Get workflow |
| PUT | `/api/workflows/{id}` | `pipelines.create` | Yes | Update workflow |
| DELETE | `/api/workflows/{id}` | `pipelines.create` | Yes | Delete workflow |
| POST | `/api/workflows/{id}/execute` | `pipelines.execute` | Yes | Execute workflow |

## Analytics & Dashboards

| Method | Path | Permission | Org Scope | Description |
|--------|------|------------|-----------|-------------|
| GET | `/api/dashboards` | `dashboard.view` | Yes | List dashboards |
| POST | `/api/dashboards` | `dashboard.manage` | Yes | Create dashboard |
| GET | `/api/dashboards/{id}` | `dashboard.view` | Yes | Get dashboard |
| PUT | `/api/dashboards/{id}` | `dashboard.manage` | Yes | Update dashboard |
| DELETE | `/api/dashboards/{id}` | `dashboard.manage` | Yes | Delete dashboard |

## Reports

| Method | Path | Permission | Org Scope | Description |
|--------|------|------------|-----------|-------------|
| GET | `/api/reports` | `reports.view` | Yes | List reports |
| POST | `/api/reports` | `reports.generate` | Yes | Generate report |
| GET | `/api/reports/{id}` | `reports.view` | Yes | Get report |
| GET | `/api/reports/{id}/export` | `reports.export` | Yes | Export report |

## Audit Logs

| Method | Path | Permission | Org Scope | Description |
|--------|------|------------|-----------|-------------|
| GET | `/api/audit/logs` | `audit.view` | Yes | List audit logs |

## Notifications

| Method | Path | Permission | Description |
|--------|------|------------|-------------|
| GET | `/api/notifications` | Authenticated | List user notifications |
| PUT | `/api/notifications/settings` | `notifications.manage` | Update notification settings |

## Sessions

| Method | Path | Permission | Org Scope | Description |
|--------|------|------------|-----------|-------------|
| GET | `/api/sessions` | `sessions.manage` | Yes | List active sessions |
| DELETE | `/api/sessions/{id}` | `sessions.manage` | Yes | Revoke session |

## Health

| Method | Path | Permission | Description |
|--------|------|------------|-------------|
| GET | `/api/health` | Public | Health check |
| GET | `/api/ready` | Public | Readiness check |

## Related Documents

- [api-overview.md](api-overview.md) — API overview
- [authentication.md](authentication.md) — Authentication
- [authorization.md](authorization.md) — Authorization
- [../governance/api-authorization-matrix.md](../governance/api-authorization-matrix.md) — Detailed auth matrix
