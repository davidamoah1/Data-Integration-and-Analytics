# System Design

> **Version**: 1.0.0  
> **Last Updated**: 2026-07-30  
> **Status**: Active  
> **Owner**: Enterprise Architect

---

## Purpose

Detailed system design with component breakdown and interaction patterns.

## Scope

All major subsystems, their responsibilities, and how they interact.

## Audience

Developers, architects, and technical leads.

---

## 1. Backend Architecture (FastAPI)

### Layered Architecture

```
┌─────────────────────────────────────────┐
│           API Routes (FastAPI)          │
│  authentication/routes.py               │
│  organizations/services.py              │
│  organizations/invitation_routes.py     │
│  analytics/routes.py, etl/routes.py     │
│  ai/routes.py, ml/routes.py             │
│  capture/routes.py, audit/services.py  │
├─────────────────────────────────────────┤
│          Service Layer                  │
│  authentication/services.py             │
│  organizations/invitation_service.py    │
│  workflows/service.py                   │
│  services/etl_service.py                │
├─────────────────────────────────────────┤
│         Repository Layer                │
│  authentication/repositories.py        │
│  database/repositories.py              │
├─────────────────────────────────────────┤
│          ORM Models (SQLAlchemy)        │
│  authentication/models.py              │
│  organizations/models.py               │
│  audit/models.py, analytics/models.py  │
├─────────────────────────────────────────┤
│          PostgreSQL Database            │
└─────────────────────────────────────────┘
```

### Key Design Patterns

- **Dependency Injection**: FastAPI `Depends()` for auth, permissions, database sessions
- **Repository Pattern**: Data access abstracted in repository classes
- **Service Layer**: Business logic in service classes, not in route handlers
- **Middleware Chain**: Request logging, security headers, rate limiting, tenant isolation, CORS, GZip, request size limit

### Middleware Stack (in order)

```python
RequestSizeLimitMiddleware  # Reject oversized requests
GZipMiddleware              # Compress responses
RequestContextMiddleware   # Attach request/correlation IDs
SecurityHeadersMiddleware  # Add security headers (CSP, HSTS, etc.)
RequestLoggingMiddleware   # Log all requests
TenantIsolationMiddleware  # Log cross-tenant access attempts
RateLimitMiddleware        # Rate limit per IP (120 RPM default)
CORSMiddleware             # Cross-origin support
```

### Router Registration

All routers are registered in `api/main.py`:

```python
app.include_router(auth_router)          # /api/auth/*
app.include_router(users_router)         # /api/users/*
app.include_router(roles_router)          # /api/roles/*
app.include_router(org_router)           # /api/organizations/*
app.include_router(dept_router)           # /api/departments/*
app.include_router(invitation_router)    # /api/invitations/*
app.include_router(registration_router)  # /api/auth/signup-v2
app.include_router(audit_router)          # /api/audit/*
app.include_router(etl_router)            # /api/etl/*
app.include_router(ai_router)             # /api/ai/*
app.include_router(analytics_router)       # /api/analytics/*
app.include_router(workflow_router)       # /api/workflows/*
app.include_router(ml_router)             # /api/ml/*
app.include_router(capture_router)        # /api/capture/*
app.include_router(studios_router)        # /api/studios/*
app.include_router(connectors_router)     # /api/connectors/*
app.include_router(saas_router)           # /api/saas/*
# ... and more
```

## 2. Frontend Architecture (Next.js)

### App Router Structure

```
frontend/app/
├── (app)/              # Authenticated app layout
│   ├── dashboard/      # Main dashboard
│   ├── datasets/       # Dataset management
│   ├── analytics/      # Dashboard builder
│   ├── reports/        # Reports
│   ├── ai/             # AI assistant
│   ├── capture/        # Smart Data Capture
│   ├── admin/          # User management
│   ├── admin-portal/   # Super admin portal
│   ├── audit/          # Audit logs
│   ├── settings/       # Settings (tabbed)
│   ├── studios/        # Industry studios
│   ├── templates/      # Template library
│   ├── notifications/  # Notifications
│   ├── billing/        # Billing (placeholder)
│   ├── connectors/     # Connectors (placeholder)
│   ├── api-keys/       # API keys (future)
│   ├── webhooks/       # Webhooks (placeholder)
│   ├── marketplace/    # Marketplace (placeholder)
│   ├── scheduler/      # Scheduler (placeholder)
│   └── workflows/      # Workflows
├── login/              # Public: login
├── signup/             # Public: registration
├── invite/             # Public: invitation acceptance
├── onboarding/         # Authenticated: onboarding wizard
├── about/              # Public: about
├── features/           # Public: features
├── pricing/            # Public: pricing
├── solutions/         # Public: solutions
├── industries/        # Public: industries
├── contact/           # Public: contact
├── help/              # Public: help center
├── forgot-password/   # Public: password reset
├── reset-password/    # Public: password reset
├── privacy/           # Public: privacy policy
├── terms/             # Public: terms of service
├── forbidden/         # Error: 403
└── offline/           # Error: offline
```

### State Management

- **Zustand** for global state (`frontend/stores/authStore.ts`)
- Auth state: user, roles, permissions, tokens
- `hasPermission()` and `hasRole()` helper functions
- No Redux or Context API — Zustand is the single state management solution

### Key Components

| Component | Path | Purpose |
|-----------|------|---------|
| RouteGuard | `components/auth/RouteGuard.tsx` | Route-level permission guard |
| Can | `components/auth/Can.tsx` | Conditional rendering by permission |
| Sidebar | `components/layout/Sidebar.tsx` | Navigation with permission filtering |
| EmptyState | `components/ui/EmptyState.tsx` | Empty state with CTA |
| ErrorState | `components/ui/ErrorState.tsx` | Error state with retry |
| ThemeProvider | `providers/ThemeProvider.tsx` | Light/dark/system theme |

## 3. Database Architecture

### ORM

- **SQLAlchemy 2.0** with declarative models
- All models inherit from `Base` (defined in `shared/database.py`)
- Tables auto-created via `Base.metadata.create_all(engine)` on startup
- No Alembic migrations — schema is code-first

### Key Models

| Model | File | Tables |
|-------|------|--------|
| User | `authentication/models.py` | `users` |
| Role | `authentication/models.py` | `roles` |
| Permission | `authentication/models.py` | `permissions` |
| UserRole | `authentication/models.py` | `user_roles` |
| RolePermission | `authentication/models.py` | `role_permissions` |
| Session | `authentication/models.py` | `sessions` |
| Organization | `organizations/models.py` | `organizations` |
| Department | `organizations/models.py` | `departments` |
| Workspace | `organizations/workspace_models.py` | `workspaces` |
| Invitation | `organizations/workspace_models.py` | `invitations` |
| AuditLog | `audit/models.py` | `audit_logs` |
| SecurityLog | `audit/models.py` | `security_logs` |
| SystemLog | `audit/models.py` | `system_logs` |
| UserActivity | `audit/models.py` | `user_activities` |

## 4. Background Jobs

- **APScheduler** for scheduled tasks
- Report scheduler runs in application process
- Daily database backup at 02:00 UTC
- Disabled in serverless mode (Vercel)

## Related Documents

- [overview.md](overview.md) — High-level architecture
- [component-diagram.md](component-diagram.md) — Component diagram
- [data-flow.md](data-flow.md) — Data flow through the platform
- [technology-stack.md](technology-stack.md) — Complete tech stack
