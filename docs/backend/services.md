# Services

> **Version**: 1.0.0  
> **Last Updated**: 2026-07-30  
> **Status**: Active  
> **Owner**: Backend Lead

---

## Purpose

Service layer architecture and key services.

## Scope

All major service classes and their responsibilities.

## Audience

Backend developers.

---

## 1. Service Layer Pattern

The platform uses a service layer between route handlers and repositories:

```
Route Handler → Service → Repository → ORM → Database
```

Services contain business logic; repositories handle data access.

## 2. Key Services

| Service | File | Purpose |
|---------|------|---------|
| `AuthService` | `authentication/services.py` | Login, signup, password reset, token management |
| `UserService` | `authentication/services.py` | User CRUD, role assignment, org-scoped listing |
| `RoleService` | `authentication/services.py` | Role CRUD, permission management |
| `InvitationService` | `organizations/invitation_service.py` | Invitation create, accept, revoke |
| `RegistrationService` | `organizations/invitation_service.py` | 3-mode registration (create org, join, personal) |
| `ETLService` | `services/etl_service.py` | ETL pipeline execution |
| `BackupService` | `services/backup_service.py` | Database backup creation |
| `ReportScheduler` | `scheduler/report_scheduler.py` | Background job scheduling |
| `SubscriptionService` | `enterprise/subscription.py` | SaaS subscription management |

## 3. Service Conventions

- Services receive a `db` session (SQLAlchemy) in constructor
- Services use repositories for data access
- Services handle audit logging
- Services raise domain-specific exceptions (e.g., `NotFoundError`, `AuthorizationError`)
- Services do not handle HTTP concerns (that's the route handler's job)

## 4. seed_default_data()

Called on application startup (non-serverless) to seed:
- All system permissions (30+)
- All system roles (13)
- Role-permission mappings
- Default super admin user

## Related Documents

- [api-overview.md](api-overview.md) — API overview
- [authentication.md](authentication.md) — Authentication
- [authorization.md](authorization.md) — Authorization
- [../architecture/system-design.md](../architecture/system-design.md) — System design
