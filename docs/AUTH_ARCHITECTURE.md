# Phase 4 — Enterprise Authentication & Authorization System

## Overview

This document describes the complete Enterprise Identity & Access Management (IAM) system implemented in Phase 4 of the DataFlow platform. The system provides JWT-based authentication, database-driven RBAC, multi-organization support, session management, audit logging, and password policies.

## Architecture

### Clean Architecture Layers

```
┌─────────────────────────────────────────────────────────────┐
│                     API Routes (FastAPI)                      │
│  authentication/routes.py                                    │
│  organizations/services.py (routes embedded)                 │
│  audit/services.py (routes embedded)                         │
├─────────────────────────────────────────────────────────────┤
│                     Services (Business Logic)                 │
│  AuthService, UserService, RoleService                        │
│  OrganizationService, DepartmentService                       │
│  AuditService                                                 │
├─────────────────────────────────────────────────────────────┤
│                     Repositories (Data Access)                │
│  UserRepository, RoleRepository, PermissionRepository, ...    │
├─────────────────────────────────────────────────────────────┤
│                     Models (ORM)                              │
│  authentication/models.py                                     │
│  organizations/models.py                                      │
│  audit/models.py                                              │
├─────────────────────────────────────────────────────────────┤
│                     Shared Infrastructure                     │
│  database.py (Base, engine, sessions)                         │
│  security.py (JWT, Argon2, password policy)                   │
│  exceptions.py (AppException hierarchy)                       │
│  response.py (StandardResponse format)                        │
│  dependencies.py (get_current_user, require_permissions)      │
└─────────────────────────────────────────────────────────────┘
```

### Module Structure

```
shared/
  __init__.py
  database.py       — SQLAlchemy Base, engine, session factory, get_db dependency
  security.py       — JWT creation/decoding, Argon2 password hashing, password policy
  exceptions.py     — AppException → AuthenticationError, AuthorizationError, etc.
  response.py       — StandardResponse model, success_response/error_response helpers
  dependencies.py   — get_current_user, require_permissions, require_any_role

authentication/
  __init__.py
  models.py          — User, Role, Permission, RolePermission, UserRole, Session,
                       PasswordReset, APIToken, LoginHistory, ActivityLog, PasswordHistory
  schemas.py         — Pydantic schemas for all auth/user/role request/response
  repositories.py    — Repository classes for each model
  services.py        — AuthService, UserService, RoleService, seed_default_data
  routes.py          — FastAPI routers: auth_router, users_router, roles_router

organizations/
  __init__.py
  models.py          — Organization, Branch, Department, Team
  schemas.py         — Pydantic schemas for org/dept/branch CRUD
  services.py        — OrganizationService, DepartmentService + embedded routers

audit/
  __init__.py
  models.py          — AuditLog, SystemLog, SecurityLog, UserActivity
  schemas.py         — Pydantic response schemas for audit/security/system logs
  services.py        — AuditService + embedded router

alembic/
  env.py             — Alembic migration environment (uses shared Base.metadata)
  versions/
    0001_phase4_iam.py — Initial migration creating all Phase 4 tables
```

## Authentication Flow

### Login Flow
```
Client → POST /auth/login {email, password}
  → AuthService.login()
    → UserRepository.get_by_email()
    → verify_password() (Argon2)
    → Check account lockout
    → Create access token (JWT, 30 min)
    → Create refresh token (JWT, 7 days)
    → Store session in DB
    → Record login history
  ← {access_token, refresh_token, user info, roles, permissions}
```

### Token Refresh Flow
```
Client → POST /auth/refresh {refresh_token}
  → AuthService.refresh_tokens()
    → decode_token() (verify JWT)
    → Check session is active & not revoked
    → Issue new access token
  ← {access_token, token_type, expires_in}
```

### Authorization Flow
```
Client → GET /users (Authorization: Bearer <access_token>)
  → get_current_user() dependency
    → decode_token()
    → Verify user exists & is active
    → Load roles & permissions from DB
  → require_permissions("users.read") dependency
    → Check if super_admin (bypass)
    → Check if user has required permission
  → UserService.list_users()
  ← {users: [...], total: N}
```

## Security Features

### Password Hashing
- **Algorithm**: Argon2 (preferred) with bcrypt fallback
- **Parameters**: memory_cost=65536, time_cost=3, parallelism=4
- **Implementation**: `passlib.context.CryptContext`

### JWT Tokens
- **Access Token**: HS256, 30-minute expiry, contains user_id, email, roles, org_id
- **Refresh Token**: HS256, 7-day expiry, stored in DB sessions table
- **Secret**: Configurable via `JWT_SECRET_KEY` env var

### Password Policy
- Minimum 8 characters
- Requires uppercase, lowercase, digit, special character
- Password history (last 5 passwords cannot be reused)
- Configurable via environment variables

### Account Lockout
- 5 failed attempts → 30-minute lockout
- Configurable via `ACCOUNT_LOCKOUT_THRESHOLD` and `ACCOUNT_LOCKOUT_DURATION_MINUTES`

### Session Management
- Sessions tracked in DB with IP, user agent, device info
- Refresh tokens tied to sessions
- Logout revokes session
- Administrators can view/revoke active sessions

## Default Seeded Data

### Super Admin User
- **Email**: `admin@dataflow.io`
- **Password**: `Admin@12345`
- **Role**: super_admin (all permissions)

### 11 Default Roles
| Role | Description | Key Permissions |
|------|-------------|-----------------|
| super_admin | Full system access | All permissions |
| org_owner | Organization owner | Full org access |
| org_admin | Organization admin | Manage org users, roles, settings |
| dept_manager | Department manager | Manage dept users, view reports |
| data_engineer | Data engineer | Execute pipelines, manage datasets |
| data_analyst | Data analyst | View analytics, create reports |
| business_analyst | Business analyst | View dashboards, export reports |
| executive | Executive | View dashboards, reports, audit |
| dept_officer | Department officer | View dept data, limited actions |
| auditor | Auditor | View audit logs, security events |
| viewer | Viewer | Read-only dashboard access |

### 30+ Default Permissions
Organized by module: users, roles, organizations, departments, pipelines, datasets, analytics, reports, dashboard, audit, ai, notifications, settings.
