# Current Architecture Report

## System Overview

**Repository**: `davidamoah1/Data-Integration-and-Analytics`
**Platform Name**: DataFlow / AEDIP (Enterprise Data Intelligence Platform)
**Version**: 1.0.0

### High-Level Architecture

```
┌─────────────────────────────────────────────────────┐
│                    Frontend (Next.js 14)              │
│  React 18 · TailwindCSS · Zustand · Lucide Icons     │
│  Port 3000                                           │
├─────────────────────────────────────────────────────┤
│                    API Gateway / Nginx                │
│  TLS termination · Static assets · Reverse proxy     │
├─────────────────────────────────────────────────────┤
│                    Backend (FastAPI)                  │
│  Python 3.12 · SQLAlchemy ORM · JWT Auth             │
│  Port 8000                                           │
├──────────────┬──────────────┬────────────────────────┤
│  MySQL 8.0   │  Redis 7     │  File Storage          │
│  (Primary DB)│  (Cache/Queue)│  (Uploads/Backups)     │
└──────────────┴──────────────┴────────────────────────┘
```

### Frontend Architecture

**Framework**: Next.js 14 with App Router
**State Management**: Zustand with persist middleware (auth state)
**Styling**: TailwindCSS with CSS variables for theming
**Icons**: Lucide React
**PWA**: @ducanh2912/next-pwa (disabled in dev)

**Structure**:
```
frontend/
├── app/
│   ├── (app)/          # Authenticated app routes (with AppShell layout)
│   │   ├── dashboard/  # Adaptive dashboard
│   │   ├── datasets/   # Dataset management
│   │   ├── analytics/  # Dashboard builder & viewer
│   │   ├── ai/         # AI assistant
│   │   ├── capture/    # Smart data capture
│   │   ├── studios/    # Industry-specific studios
│   │   ├── admin/      # User management
│   │   ├── admin-portal/ # Platform admin
│   │   ├── audit/      # Audit logs
│   │   └── ...
│   ├── login/          # Public auth pages
│   ├── signup/
│   ├── onboarding/
│   ├── demo/           # Demo booking page
│   ├── pricing/
│   └── ...
├── components/
│   ├── adaptive/       # Role-aware UI components
│   ├── auth/           # Can, RouteGuard
│   ├── layout/         # AppShell, Sidebar, TopNav
│   ├── ui/             # Reusable UI primitives
│   ├── landing-v2/     # Marketing landing page
│   └── settings/       # Settings panels
├── lib/
│   ├── navigation.ts   # Dynamic navigation engine
│   ├── dashboards.ts   # Role-specific dashboard configs
│   ├── onboarding.ts   # Role-specific onboarding flows
│   ├── help.ts         # Context-aware help configs
│   ├── search.ts       # Adaptive search scopes
│   ├── notifications.ts # Role-based notification types
│   ├── permissions.ts  # Permission & role constants
│   └── workflows.ts   # Guided tasks & templates
├── services/          # API service layer
├── stores/            # Zustand stores
└── types/             # TypeScript types
```

**Key Patterns**:
- Route groups: `(app)/` for authenticated routes with shared layout
- Error boundaries wrap the app shell
- AppShell provides Sidebar + TopNav + content area
- Adaptive components render based on role/permission
- API client with JWT token management and auto-refresh

### Backend Architecture

**Framework**: FastAPI (Python 3.12)
**ORM**: SQLAlchemy with declarative Base
**Auth**: JWT (HS256) with access + refresh tokens
**Password Hashing**: Argon2 (preferred) with bcrypt fallback

**Structure**:
```
├── api/main.py         # FastAPI app entry, router registration, lifespan
├── authentication/     # IAM: users, roles, permissions, sessions
├── organizations/       # Org & department management
├── audit/              # Audit logs & security events
├── etl/                # ETL pipeline (extract, transform, load)
├── ai/                 # AI platform (chat, forecasting, anomaly, insights)
├── analytics/          # Dashboard & KPI analytics
├── dataset/            # Dataset management
├── capture/            # Smart data capture (OCR)
├── studios/            # Industry-specific studios
├── semantic/           # Semantic analysis & industry classification
├── validation/         # Data validation
├── connectors/         # External data connectors
├── ecosystem/          # Plugins, webhooks, marketplace
├── saas/               # SaaS subscription & billing
├── enterprise/         # Enterprise features & subscriptions
├── scheduler/          # Report scheduling
├── notifications/      # In-app notifications
├── ml/                 # ML model management
├── performance/        # Performance monitoring & caching
├── shared/             # Cross-cutting: database, security, middleware, tenant
├── config.py           # Centralized configuration
└── tests/              # 53 test files
```

**Key Patterns**:
- Router-based modular API design (20+ routers)
- Dependency injection for auth, DB sessions, and permissions
- `success_response()` wrapper for consistent API responses
- Tenant isolation via `shared/tenant.py` helpers
- Serverless-aware startup (skips heavy init on Vercel)

### Database Architecture

**Primary**: MySQL 8.0 (production)
**Development**: SQLite
**Migrations**: Alembic (11 migration files)
**Caching**: Redis 7

**Key Tables**:
- `users`, `roles`, `permissions`, `role_permissions`, `user_roles`
- `sessions`, `password_resets`, `api_tokens`, `login_history`, `password_history`
- `organizations`, `departments`
- `etl_pipelines`, `etl_jobs`
- `ai_conversations`, `ai_messages`, `ai_insights`
- `audit_logs`, `security_logs`, `system_logs`
- `notifications`
- `dashboards`, `widgets`, `kpis`
- `datasets`, `dataset_schemas`
- `subscriptions`, `plans`, `feature_flags`

### Authentication & Authorization

**JWT-based IAM**:
- Access tokens: 30 min expiry (configurable)
- Refresh tokens: 7 days expiry (configurable)
- Token type checking (`type: "access"` vs `type: "refresh"`)
- JTI (JWT ID) for token uniqueness
- Session tracking with IP, user agent, device info
- Session revocation support

**RBAC**:
- 13 system roles: super_admin, org_owner, org_admin, dept_manager, data_engineer, data_analyst, business_analyst, executive, researcher, auditor, dept_officer, data_entry_officer, viewer
- 50+ permissions across modules
- `require_permissions()` and `require_any_role()` dependency factories
- Super admin bypasses all permission checks
- Organization-scoped access via tenant isolation

**Security Features**:
- Account lockout after 5 failed attempts (30 min lockout)
- Password history (prevents reuse of last 5 passwords)
- Password policy enforcement (min length, complexity)
- API key encryption (Fernet symmetric encryption)
- SQL identifier validation

### Deployment

**Docker**: Multi-service via docker-compose.prod.yml
- nginx (reverse proxy, TLS, static assets)
- certbot (Let's Encrypt auto-renewal)
- api (FastAPI backend)
- dashboard (Streamlit legacy dashboard)
- db (MySQL 8.0)
- redis (Redis 7)

**Serverless**: Vercel support with cold-start optimizations
- Skips DB migrations, seeding, and scheduler on serverless
- SQLite fallback to /tmp for read-only filesystem
- root_path="/api" for Vercel routing

**Health Checks**:
- `/health` — lightweight health check
- `/ready` — readiness check with DB connectivity
- `/health/detailed` — full subsystem health
- `/metrics` — platform metrics

### Testing

**Backend**: 53 test files covering:
- Auth, RBAC, organizations, audit
- ETL pipeline, connectors, data quality
- AI platform, semantic analysis, predictive analytics
- Dashboard engine, dataset workflow
- Notifications, scheduler, validation
- Performance, platform features, ecosystem

**Frontend**: 4 test files (utils, minimal coverage)
- No E2E tests
- No component tests
- No integration tests

### Observability

- Request logging middleware (method, path, status, duration)
- Request context middleware (request ID, correlation ID)
- Security headers middleware
- Rate limiting middleware (in-memory, per-IP)
- Request size limiting (50MB max)
- Gzip compression
