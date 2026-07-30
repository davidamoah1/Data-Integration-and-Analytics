# API Overview

> **Version**: 1.0.0  
> **Last Updated**: 2026-07-30  
> **Status**: Active  
> **Owner**: Backend Lead

---

## Purpose

API architecture, versioning, and response format.

## Scope

All REST API endpoints and conventions.

## Audience

Backend developers and API consumers.

---

## 1. API Architecture

- **Framework**: FastAPI (Python)
- **Base URL**: `/api` (on Vercel) or `/` (local)
- **Authentication**: JWT Bearer tokens
- **Content Type**: `application/json`
- **Response Format**: Consistent JSON envelope

## 2. Response Format

All API responses follow this structure:

```json
{
  "success": true,
  "message": "Operation successful",
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

## 3. API Routers

| Router | Prefix | Description |
|--------|--------|-------------|
| auth_router | `/api/auth` | Authentication (login, signup, refresh) |
| users_router | `/api/users` | User management |
| roles_router | `/api/roles` | Role and permission management |
| org_router | `/api/organizations` | Organization management |
| dept_router | `/api/departments` | Department management |
| invitation_router | `/api/invitations` | Invitation management |
| registration_router | `/api/auth/signup-v2` | Enhanced registration |
| audit_router | `/api/audit` | Audit log viewing |
| etl_router | `/api/etl` | ETL operations |
| ai_router | `/api/ai` | AI features |
| analytics_router | `/api/analytics` | Analytics and dashboards |
| workflow_router | `/api/workflows` | ETL workflow management |
| ml_router | `/api/ml` | Machine learning |
| capture_router | `/api/capture` | Smart Data Capture |
| studios_router | `/api/studios` | Industry studios |
| connectors_router | `/api/connectors` | Data connectors |
| saas_router | `/api/saas` | SaaS management |
| scheduler_router | `/api/scheduler` | Job scheduling |
| notifications_router | `/api/notifications` | Notifications |

## 4. Versioning

- Current version: 1.0.0
- No URL-based versioning yet (e.g., `/api/v2/`)
- Future: Add version prefix when breaking changes are needed

## 5. OpenAPI Documentation

- FastAPI auto-generates OpenAPI schema at `/docs` (Swagger UI) and `/redoc`
- Available in development mode

## Related Documents

- [endpoints.md](endpoints.md) — Complete endpoint catalog
- [authentication.md](authentication.md) — Authentication details
- [authorization.md](authorization.md) — Authorization details
- [error-handling.md](error-handling.md) — Error handling
- [../governance/api-authorization-matrix.md](../governance/api-authorization-matrix.md) — API auth matrix
