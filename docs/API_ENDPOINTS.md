# Phase 4 — API Endpoint Reference

All Phase 4 endpoints use JWT Bearer token authentication unless noted otherwise.
Legacy endpoints (sales, KPIs, pipeline) still support API key auth for backward compatibility.

## Authentication Endpoints (`/auth`)

| Method | Path | Description | Auth | Permissions |
|--------|------|-------------|------|-------------|
| POST | `/auth/login` | Authenticate and receive JWT tokens | None | Public |
| POST | `/auth/logout` | Revoke current session | Bearer | Any authenticated user |
| POST | `/auth/refresh` | Refresh access token | None (refresh token in body) | Public |
| POST | `/auth/change-password` | Change current user's password | Bearer | Any authenticated user |
| POST | `/auth/forgot-password` | Request password reset email | None | Public |
| POST | `/auth/reset-password` | Reset password with token | None | Public |
| GET | `/auth/profile` | Get current user's profile | Bearer | Any authenticated user |
| PUT | `/auth/profile` | Update current user's profile | Bearer | Any authenticated user |
| GET | `/auth/sessions` | List active sessions | Bearer | Any authenticated user |
| DELETE | `/auth/sessions/{session_id}` | Revoke a session | Bearer | Any authenticated user |
| GET | `/auth/login-history` | Get login history | Bearer | Any authenticated user |
| GET | `/auth/activity` | Get activity log | Bearer | Any authenticated user |

## User Management Endpoints (`/users`)

| Method | Path | Description | Auth | Permissions |
|--------|------|-------------|------|-------------|
| GET | `/users` | List all users (paginated) | Bearer | users.read |
| POST | `/users` | Create a new user | Bearer | users.create |
| GET | `/users/{user_id}` | Get a specific user | Bearer | users.read |
| PUT | `/users/{user_id}` | Update a user | Bearer | users.update |
| DELETE | `/users/{user_id}` | Soft-delete a user | Bearer | users.delete |
| POST | `/users/{user_id}/roles` | Assign roles to a user | Bearer | users.assign_roles |

## Role Management Endpoints (`/roles`)

| Method | Path | Description | Auth | Permissions |
|--------|------|-------------|------|-------------|
| GET | `/roles` | List all roles | Bearer | roles.read |
| POST | `/roles` | Create a custom role | Bearer | roles.create |
| GET | `/roles/permissions` | List all permissions | Bearer | roles.read |
| GET | `/roles/{role_id}` | Get a specific role | Bearer | roles.read |
| PUT | `/roles/{role_id}` | Update a role | Bearer | roles.update |
| DELETE | `/roles/{role_id}` | Delete a non-system role | Bearer | roles.delete |

## Organization Endpoints (`/organizations`)

| Method | Path | Description | Auth | Permissions |
|--------|------|-------------|------|-------------|
| GET | `/organizations` | List organizations | Bearer | organizations.read |
| POST | `/organizations` | Create an organization | Bearer | organizations.create |
| GET | `/organizations/{org_id}` | Get an organization | Bearer | organizations.read |
| PUT | `/organizations/{org_id}` | Update an organization | Bearer | organizations.update |
| DELETE | `/organizations/{org_id}` | Delete an organization | Bearer | organizations.delete |

## Department Endpoints (`/departments`)

| Method | Path | Description | Auth | Permissions |
|--------|------|-------------|------|-------------|
| GET | `/departments` | List departments (filter by org) | Bearer | departments.read |
| POST | `/departments` | Create a department | Bearer | departments.create |
| GET | `/departments/{dept_id}` | Get a department | Bearer | departments.read |
| PUT | `/departments/{dept_id}` | Update a department | Bearer | departments.update |
| DELETE | `/departments/{dept_id}` | Delete a department | Bearer | departments.delete |

## Audit Endpoints (`/audit`)

| Method | Path | Description | Auth | Permissions |
|--------|------|-------------|------|-------------|
| GET | `/audit/logs` | List audit logs (paginated) | Bearer | audit.view |
| GET | `/audit/security` | List security logs | Bearer | audit.view |
| GET | `/audit/system` | List system logs | Bearer | audit.view |

## Standard Response Format

All Phase 4 endpoints return a consistent response format:

```json
{
  "success": true,
  "message": "Operation completed successfully",
  "data": { ... }
}
```

Error responses:
```json
{
  "success": false,
  "message": "Error description",
  "data": null
}
```

Or for validation/HTTP errors (FastAPI default):
```json
{
  "detail": "Error description"
}
```

## Authentication Header

```
Authorization: Bearer <access_token>
```

## Default Credentials

- **Email**: `admin@dataflow.io`
- **Password**: `Admin@12345`
