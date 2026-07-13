# Enterprise Data Intelligence Platform — Architecture Refactoring Plan

**Status:** Planning Phase  
**Date:** 2026-07-11  
**Author:** Lead Software Architect  

---

## Table of Contents

1. [Current State Assessment](#1-current-state-assessment)
2. [Target Architecture](#2-target-architecture)
3. [Updated Folder Structure](#3-updated-folder-structure)
4. [Module Responsibilities](#4-module-responsibilities)
5. [Dependency Diagram](#5-dependency-diagram)
6. [Refactoring Implementation Plan](#6-refactoring-implementation-plan)
7. [File-by-File Modification Plan](#7-file-by-file-modification-plan)
8. [Standard API Response Format](#8-standard-api-response-format)
9. [Database Improvement Plan](#9-database-improvement-plan)
10. [Security Improvement Plan](#10-security-improvement-plan)
11. [Frontend Architecture](#11-frontend-architecture)

---

## 1. Current State Assessment

### What Exists (Python Backend)

| Area | Current | Status |
|------|---------|--------|
| ETL Pipeline | `etl/extract.py`, `etl/transform.py`, `etl/load.py` | Working — keep logic, restructure location |
| Database | SQLAlchemy ORM, SQLite + MySQL support, `SalesRecord` + `PipelineRun` models | Working — improve schema, add Alembic migrations |
| Repository | `database/repositories.py` — `SalesRepository`, `PipelineRunRepository` | Working — move into feature modules |
| Services | `services/etl_service.py`, `services/dashboard_data_service.py` | Working — move into feature modules |
| API | `api/main.py` — FastAPI with 7 endpoints, API key auth | Working — restructure into feature-based routes, add JWT |
| Dashboard | `dashboard/app.py` — Streamlit monolith | **Replace** with Next.js frontend |
| Scheduler | `scheduler/scheduler.py` — APScheduler | Working — move into `etl/` module |
| Monitoring | `monitoring/health_check.py` | Working — move into `monitoring/` module |
| Logging | `etl/logging_config.py` — RotatingFileHandler | Working — enhance with structured logging |
| Config | `config.py` — python-dotenv | Working — split into `shared/config/` |
| Tests | 6 test files in `tests/` | Working — restructure per module |

### What Must Change

| Change | Reason |
|--------|--------|
| Streamlit → Next.js | Target stack specifies Next.js + TypeScript + Tailwind |
| Plotly → Apache ECharts | Target stack specifies ECharts |
| Session auth → JWT + RBAC | Target stack specifies JWT, RBAC |
| API key auth → JWT | Standardize on JWT for all auth |
| Flat structure → Feature-based modules | Maintainability, scalability |
| pandas-only → pandas + Polars | Performance for large datasets |
| No Alembic → Alembic migrations | Database migration management |
| No audit logging → Audit log table + middleware | Security requirement |

### What Must NOT Change

- ETL business logic (extract, transform, load rules)
- Database table semantics (sales data schema)
- Pipeline scheduling behavior
- Existing API endpoint contracts (keep backwards-compatible URLs)

---

## 2. Target Architecture

### Clean Architecture Layers

```
┌─────────────────────────────────────────────────────────┐
│                    Presentation Layer                      │
│   FastAPI Routes ← Request/Response Schemas ← Validators   │
│   Next.js Pages ← Components ← Hooks ← API Client          │
├─────────────────────────────────────────────────────────┤
│                     Business Layer                         │
│   Services ← Domain Models ← Business Logic                │
│   ETLService, AnalyticsService, AuthService, etc.          │
├─────────────────────────────────────────────────────────┤
│                    Repository Layer                        │
│   Repositories ← SQLAlchemy ORM ← Data Access              │
│   SalesRepository, UserRepository, AuditRepository, etc.   │
├─────────────────────────────────────────────────────────┤
│                     Database Layer                         │
│   MySQL (Hostinger) ← Alembic Migrations ← Models          │
├─────────────────────────────────────────────────────────┤
│                     Utility Layer                          │
│   Config, Logging, Security, Validators, Exceptions        │
└─────────────────────────────────────────────────────────┘
```

### Key Principles

- **No business logic in routes** — routes only call services and return standardized responses
- **No direct DB access in services** — services use repositories
- **No ORM imports in routes** — routes use Pydantic schemas
- **Shared utilities only in `shared/`** — no cross-module imports outside shared
- **Each module is self-contained** — can be developed, tested, and deployed independently

---

## 3. Updated Folder Structure

### Backend (Python / FastAPI)

```
backend/
├── main.py                          # FastAPI app entry point
├── alembic.ini                      # Alembic configuration
├── requirements.txt                 # Pinned dependencies
├── pyproject.toml                   # Ruff + black config
├── .env.example
│
├── alembic/                         # Database migrations
│   ├── env.py
│   ├── script.py.mako
│   └── versions/
│       ├── 001_initial_schema.py
│       ├── 002_add_audit_log.py
│       └── 003_add_user_tables.py
│
├── shared/                          # Cross-cutting concerns
│   ├── __init__.py
│   ├── config/
│   │   ├── __init__.py
│   │   ├── settings.py              # Pydantic Settings (env vars)
│   │   └── database.py              # Engine factory, session factory
│   ├── logging/
│   │   ├── __init__.py
│   │   └── logger.py                # Structured logging (JSON format)
│   ├── security/
│   │   ├── __init__.py
│   │   ├── jwt_handler.py           # JWT encode/decode
│   │   ├── password.py              # bcrypt hashing
│   │   └── permissions.py           # RBAC permission checker
│   ├── exceptions/
│   │   ├── __init__.py
│   │   ├── base.py                  # BaseAppException
│   │   └── handlers.py              # FastAPI exception handlers
│   ├── response/
│   │   ├── __init__.py
│   │   └── standard.py              # StandardResponse wrapper
│   ├── middleware/
│   │   ├── __init__.py
│   │   ├── request_id.py            # X-Request-ID middleware
│   │   ├── audit_log.py             # Audit logging middleware
│   │   └── rate_limit.py            # Rate limiting middleware
│   └── utils/
│       ├── __init__.py
│       ├── dates.py                 # Date formatting helpers
│       ├── formatting.py            # Currency/number formatting
│       └── sanitization.py          # HTML escaping, input cleaning
│
├── authentication/                  # Auth module
│   ├── __init__.py
│   ├── routes.py                    # /api/v1/auth/*
│   ├── services.py                  # AuthService
│   ├── repositories.py              # UserRepository
│   ├── schemas.py                   # LoginRequest, TokenResponse, etc.
│   ├── models.py                    # User, Role, UserSession ORM
│   ├── validators.py                # Login validator, registration validator
│   └── tests/
│       ├── test_services.py
│       ├── test_routes.py
│       └── test_validators.py
│
├── users/                           # User management module
│   ├── __init__.py
│   ├── routes.py                    # /api/v1/users/*
│   ├── services.py
│   ├── repositories.py
│   ├── schemas.py
│   ├── models.py                    # Re-exports User from auth or own models
│   ├── validators.py
│   └── tests/
│
├── organizations/                   # Multi-tenant (future-ready)
│   ├── __init__.py
│   ├── routes.py
│   ├── services.py
│   ├── repositories.py
│   ├── schemas.py
│   ├── models.py
│   └── tests/
│
├── departments/                     # Department management
│   ├── __init__.py
│   ├── routes.py
│   ├── services.py
│   ├── repositories.py
│   ├── schemas.py
│   ├── models.py
│   └── tests/
│
├── etl/                             # ETL module (core business)
│   ├── __init__.py
│   ├── routes.py                    # /api/v1/etl/*
│   ├── services.py                  # ETLService (from services/etl_service.py)
│   ├── repositories.py              # PipelineRunRepository
│   ├── schemas.py                   # PipelineTriggerResponse, PipelineRunResponse
│   ├── models.py                    # PipelineRun ORM (from db_setup.py)
│   ├── validators.py                # Pipeline config validation
│   ├── extract.py                   # ← from etl/extract.py (logic unchanged)
│   ├── transform.py                 # ← from etl/transform.py (logic unchanged)
│   ├── load.py                      # ← from etl/load.py (logic unchanged)
│   ├── scheduler.py                 # ← from scheduler/scheduler.py
│   ├── pipeline.py                  # ← from pipeline/run_pipeline.py
│   └── tests/
│       ├── test_extract.py          # ← from tests/test_extract.py
│       ├── test_transform.py        # ← from tests/test_transform.py
│       ├── test_load.py             # ← from tests/test_load.py
│       └── test_pipeline.py
│
├── analytics/                       # Analytics & KPI module
│   ├── __init__.py
│   ├── routes.py                    # /api/v1/analytics/*
│   ├── services.py                  # AnalyticsService (KPI computation)
│   ├── repositories.py              # SalesRepository (from database/repositories.py)
│   ├── schemas.py                   # KPIResponse, SalesListResponse, etc.
│   ├── models.py                    # SalesRecord ORM (from db_setup.py)
│   ├── validators.py                # Filter validation
│   └── tests/
│       ├── test_repository.py       # ← from tests/test_repository.py
│       └── test_services.py
│
├── reports/                         # Report generation module
│   ├── __init__.py
│   ├── routes.py                    # /api/v1/reports/*
│   ├── services.py                  # ReportService (PDF/Excel export)
│   ├── schemas.py
│   ├── generators/
│   │   ├── pdf_generator.py
│   │   └── excel_generator.py
│   └── tests/
│
├── dashboard/                       # Dashboard data module (backend)
│   ├── __init__.py
│   ├── routes.py                    # /api/v1/dashboard/*
│   ├── services.py                  # DashboardDataService (from services/)
│   ├── schemas.py                   # DashboardDataResponse, WidgetConfig
│   └── tests/
│       └── test_dashboard_service.py
│
├── notifications/                   # Notification module
│   ├── __init__.py
│   ├── routes.py
│   ├── services.py
│   ├── repositories.py
│   ├── schemas.py
│   ├── models.py                    # Notification ORM
│   └── tests/
│
├── settings/                        # System settings module
│   ├── __init__.py
│   ├── routes.py
│   ├── services.py
│   ├── repositories.py
│   ├── schemas.py
│   └── tests/
│
├── ai/                              # AI/ML module (future-ready)
│   ├── __init__.py
│   ├── routes.py
│   ├── services.py                  # Forecasting, anomaly detection
│   ├── schemas.py
│   └── tests/
│
├── audit/                           # Audit log module
│   ├── __init__.py
│   ├── routes.py                    # /api/v1/audit/*
│   ├── services.py
│   ├── repositories.py
│   ├── schemas.py
│   ├── models.py                    # AuditLog ORM
│   └── tests/
│
├── monitoring/                      # System monitoring module
│   ├── __init__.py
│   ├── routes.py                    # /api/v1/monitoring/*
│   ├── services.py                  # ← from monitoring/health_check.py
│   ├── schemas.py
│   └── tests/
│
└── api/                             # API assembly (not business logic)
    ├── __init__.py
    ├── router.py                    # Aggregates all module routers
    └── dependencies.py              # Shared FastAPI dependencies
```

### Frontend (Next.js / TypeScript)

```
frontend/
├── package.json
├── tsconfig.json
├── tailwind.config.ts
├── next.config.js
├── .env.example
│
├── public/
│   ├── icons/
│   └── images/
│
├── src/
│   ├── app/                         # Next.js App Router
│   │   ├── layout.tsx               # Root layout
│   │   ├── page.tsx                 # Dashboard home
│   │   ├── login/
│   │   │   └── page.tsx
│   │   ├── analytics/
│   │   │   └── page.tsx
│   │   ├── reports/
│   │   │   └── page.tsx
│   │   ├── etl/
│   │   │   └── page.tsx             # Pipeline status & trigger
│   │   ├── settings/
│   │   │   └── page.tsx
│   │   └── api/                     # Next.js API routes (if needed)
│   │
│   ├── components/                  # Reusable UI components
│   │   ├── layout/
│   │   │   ├── Sidebar.tsx
│   │   │   ├── Header.tsx
│   │   │   ├── PageContainer.tsx
│   │   │   └── Breadcrumb.tsx
│   │   ├── cards/
│   │   │   ├── KPICard.tsx
│   │   │   ├── StatCard.tsx
│   │   │   └── InfoCard.tsx
│   │   ├── tables/
│   │   │   ├── DataTable.tsx
│   │   │   ├── DataTableColumn.tsx
│   │   │   └── Pagination.tsx
│   │   ├── charts/
│   │   │   ├── AreaChart.tsx        # ECharts wrapper
│   │   │   ├── BarChart.tsx
│   │   │   ├── PieChart.tsx
│   │   │   ├── ScatterChart.tsx
│   │   │   ├── HeatmapChart.tsx
│   │   │   └── ChartContainer.tsx
│   │   ├── maps/
│   │   │   ├── RegionMap.tsx        # Leaflet wrapper
│   │   │   └── MapMarker.tsx
│   │   ├── filters/
│   │   │   ├── RegionFilter.tsx
│   │   │   ├── CategoryFilter.tsx
│   │   │   ├── DateRangeFilter.tsx
│   │   │   └── FilterBar.tsx
│   │   ├── forms/
│   │   │   ├── LoginForm.tsx
│   │   │   ├── SettingsForm.tsx
│   │   │   └── UploadForm.tsx
│   │   ├── dialogs/
│   │   │   ├── ConfirmDialog.tsx
│   │   │   └── DetailDialog.tsx
│   │   ├── feedback/
│   │   │   ├── LoadingState.tsx
│   │   │   ├── ErrorState.tsx
│   │   │   ├── EmptyState.tsx
│   │   │   ├── Toast.tsx
│   │   │   └── ProgressBar.tsx
│   │   └── common/
│   │       ├── Button.tsx
│   │       ├── Input.tsx
│   │       ├── Select.tsx
│   │       ├── Badge.tsx
│   │       └── Spinner.tsx
│   │
│   ├── hooks/                       # Custom React hooks
│   │   ├── useAuth.ts
│   │   ├── useFetch.ts
│   │   ├── useKPIs.ts
│   │   ├── useSalesData.ts
│   │   ├── useFilters.ts
│   │   ├── usePipeline.ts
│   │   └── useDebounce.ts
│   │
│   ├── stores/                      # State management (Zustand)
│   │   ├── authStore.ts
│   │   ├── filterStore.ts
│   │   ├── dashboardStore.ts
│   │   └── notificationStore.ts
│   │
│   ├── services/                    # API client layer
│   │   ├── apiClient.ts             # Axios/fetch wrapper with interceptors
│   │   ├── authService.ts
│   │   ├── analyticsService.ts
│   │   ├── etlService.ts
│   │   ├── reportService.ts
│   │   └── monitoringService.ts
│   │
│   ├── types/                       # TypeScript types
│   │   ├── api.ts                   # Response types matching backend schemas
│   │   ├── models.ts                # Domain models
│   │   ├── charts.ts                # Chart config types
│   │   └── common.ts
│   │
│   ├── utils/                       # Frontend utilities
│   │   ├── formatting.ts            # Currency, number, date formatting
│   │   ├── validation.ts            # Form validation helpers
│   │   ├── constants.ts             # App constants
│   │   └── errorMessages.ts
│   │
│   └── styles/
│       └── globals.css              # Tailwind + custom CSS
│
└── tests/
    ├── components/
    ├── hooks/
    └── e2e/                         # Playwright E2E tests
```

---

## 4. Module Responsibilities

### Backend Modules

| Module | Responsibility | Key Files |
|--------|---------------|-----------|
| `shared/` | Cross-cutting: config, logging, security, exceptions, response format, middleware | `settings.py`, `logger.py`, `jwt_handler.py`, `standard.py` |
| `authentication/` | Login, token refresh, logout, password reset | `routes.py`, `services.py`, `repositories.py` |
| `users/` | CRUD users, assign roles, profile management | `routes.py`, `services.py` |
| `organizations/` | Multi-tenant org management (future-ready) | `routes.py`, `services.py` |
| `departments/` | Department CRUD, user-department assignment | `routes.py`, `services.py` |
| `etl/` | Extract, transform, load, pipeline orchestration, scheduling | `extract.py`, `transform.py`, `load.py`, `services.py`, `scheduler.py` |
| `analytics/` | KPI computation, sales queries, filtering, aggregation | `services.py`, `repositories.py` |
| `reports/` | PDF/Excel report generation, scheduled reports | `services.py`, `generators/` |
| `dashboard/` | Dashboard data assembly, widget configs, cached queries | `services.py` |
| `notifications/` | In-app, email, webhook notifications | `services.py`, `models.py` |
| `settings/` | System configuration, feature flags | `services.py` |
| `ai/` | Forecasting, anomaly detection, insights (future) | `services.py` |
| `audit/` | Audit log queries, compliance reports | `routes.py`, `services.py` |
| `monitoring/` | Health checks, pipeline status, system metrics | `services.py` |
| `api/` | Router aggregation, shared dependencies | `router.py`, `dependencies.py` |

### Dependency Rules

```
routes → services → repositories → models
routes → schemas (for request/response)
routes → validators (for input validation)
services → shared/ (config, logging, exceptions)
services → other services (via dependency injection)
repositories → shared/config/database.py (for engine)
NO routes → repositories (must go through services)
NO services → routes (no upward dependency)
NO modules → other modules' internals (only via shared/ or api/dependencies)
```

---

## 5. Dependency Diagram

```
                    ┌──────────┐
                    │  Next.js  │
                    │ Frontend  │
                    └─────┬─────┘
                          │ HTTP (REST)
                          ▼
┌─────────────────────────────────────────────┐
│                  api/router.py                │
│   (aggregates all module routers into app)    │
└──┬───────┬───────┬───────┬───────┬───────┬───┘
   │       │       │       │       │       │
   ▼       ▼       ▼       ▼       ▼       ▼
┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐
│auth │ │ etl │ │analy│ │dash │ │moni │ │audit│
│     │ │     │ │tics │ │board│ │tor  │ │     │
└──┬──┘ └──┬──┘ └──┬──┘ └──┬──┘ └──┬──┘ └──┬──┘
   │       │       │       │       │       │
   ▼       ▼       │       │       │       │
┌─────┐ ┌─────┐   │       │       │       │
│user │ │pipe │   │       │       │       │
│repo │ │line │   │       │       │       │
└──┬──┘ └─────┘   │       │       │       │
   │              │       │       │       │
   │     ┌────────┘       │       │       │
   │     │                │       │       │
   ▼     ▼                ▼       │       │
┌─────────────┐    ┌───────────┐  │       │
│SalesRepo    │    │SalesRepo  │  │       │
│(analytics)  │    │(dashboard)│  │       │
└──────┬──────┘    └─────┬─────┘  │       │
       │                 │        │       │
       ▼                 ▼        ▼       ▼
┌─────────────────────────────────────────┐
│            shared/config/database.py      │
│         (SQLAlchemy engine + session)     │
└──────────────────┬──────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────┐
│              MySQL (Hostinger)            │
│    sales, pipeline_runs, users, roles,    │
│    audit_logs, notifications, etc.        │
└─────────────────────────────────────────┘

Vertical dependency on shared/ (all modules):
┌─────────────────────────────────────────┐
│              shared/                      │
│  config/  logging/  security/  exceptions │
│  response/  middleware/  utils/            │
└─────────────────────────────────────────┘
     ▲        ▲        ▲        ▲
     │        │        │        │
  (all modules depend on shared/, never on each other directly)
```

---

## 6. Refactoring Implementation Plan

### Phase Overview

| Phase | Module | Priority | Effort | Risk |
|-------|--------|----------|--------|------|
| 1 | `shared/` foundation | Critical | Medium | Low |
| 2 | `authentication/` + `users/` | Critical | High | Medium |
| 3 | `etl/` migration | Critical | Medium | Low |
| 4 | `analytics/` + `dashboard/` | Critical | Medium | Low |
| 5 | `monitoring/` + `audit/` | High | Low | Low |
| 6 | `reports/` | Medium | Medium | Low |
| 7 | `notifications/` | Medium | Medium | Low |
| 8 | `organizations/` + `departments/` | Low | Medium | Low |
| 9 | `settings/` | Low | Low | Low |
| 10 | `ai/` | Future | High | Medium |
| 11 | Frontend (Next.js) | Critical | High | Medium |
| 12 | CI/CD + Docker | High | Low | Low |

### Phase 1: Shared Foundation (Week 1)

**Goal:** Create the `shared/` module that all other modules depend on.

**Tasks:**
1. Create `shared/config/settings.py` — Pydantic Settings class replacing `config.py`
2. Create `shared/config/database.py` — engine factory, session factory, `get_db()` dependency
3. Create `shared/logging/logger.py` — structured JSON logging with rotation
4. Create `shared/security/jwt_handler.py` — JWT encode/decode with refresh tokens
5. Create `shared/security/password.py` — bcrypt password hashing
6. Create `shared/security/permissions.py` — RBAC decorator/dependency
7. Create `shared/exceptions/base.py` — `BaseAppException` hierarchy
8. Create `shared/exceptions/handlers.py` — FastAPI exception handlers
9. Create `shared/response/standard.py` — `StandardResponse` wrapper
10. Create `shared/middleware/request_id.py` — request ID generation
11. Create `shared/middleware/audit_log.py` — audit logging middleware
12. Create `shared/middleware/rate_limit.py` — rate limiting
13. Create `shared/utils/` — date, formatting, sanitization helpers
14. Set up Alembic with initial migration

**Files created:** ~20 new files in `shared/`
**Files modified:** `config.py` → deprecated (replaced by `shared/config/settings.py`)
**Risk:** Low — new files only, nothing breaks

### Phase 2: Authentication + Users (Week 2)

**Goal:** JWT-based auth with RBAC, user management.

**Tasks:**
1. Create `authentication/models.py` — `User`, `Role`, `UserSession` ORM models
2. Create `authentication/repositories.py` — `UserRepository`
3. Create `authentication/schemas.py` — `LoginRequest`, `TokenResponse`, `RefreshTokenRequest`
4. Create `authentication/validators.py` — login, registration validators
5. Create `authentication/services.py` — `AuthService` (login, refresh, logout)
6. Create `authentication/routes.py` — `/api/v1/auth/login`, `/refresh`, `/logout`
7. Create `users/` module — CRUD routes, services, schemas
8. Create Alembic migration for `users`, `roles`, `user_sessions` tables
9. Seed default admin user and roles
10. Write tests for auth and users

**Files created:** ~20 new files
**Files modified:** `api/auth.py` → deprecated (replaced by `authentication/`)
**Risk:** Medium — new auth system, but old API key auth kept as fallback during transition

### Phase 3: ETL Module Migration (Week 3)

**Goal:** Move ETL code into `etl/` feature module without changing logic.

**Tasks:**
1. Move `etl/extract.py` → `etl/extract.py` (stays, update imports)
2. Move `etl/transform.py` → `etl/transform.py` (stays, update imports)
3. Move `etl/load.py` → `etl/load.py` (stays, update imports)
4. Move `services/etl_service.py` → `etl/services.py`
5. Move `pipeline/run_pipeline.py` → `etl/pipeline.py`
6. Move `scheduler/scheduler.py` → `etl/scheduler.py`
7. Move `database/repositories.py` `PipelineRunRepository` → `etl/repositories.py`
8. Move `database/db_setup.py` `PipelineRun` → `etl/models.py`
9. Create `etl/schemas.py` — pipeline response schemas
10. Create `etl/routes.py` — `/api/v1/etl/trigger`, `/api/v1/etl/runs`
11. Create `etl/validators.py` — pipeline config validation
12. Update all imports across codebase
13. Move and update tests

**Files moved:** ~10 files
**Files modified:** All files that import from old locations
**Risk:** Low — logic unchanged, only file locations and imports change

### Phase 4: Analytics + Dashboard (Week 3-4)

**Goal:** Move analytics and dashboard data into feature modules.

**Tasks:**
1. Move `SalesRepository` → `analytics/repositories.py`
2. Move `SalesRecord` ORM → `analytics/models.py`
3. Move `services/dashboard_data_service.py` → `dashboard/services.py`
4. Create `analytics/services.py` — `AnalyticsService` (KPI computation)
5. Create `analytics/schemas.py` — KPI, sales list, filter options schemas
6. Create `analytics/routes.py` — `/api/v1/analytics/sales`, `/kpis`, `/filters`
7. Create `analytics/validators.py` — filter parameter validation
8. Create `dashboard/routes.py` — `/api/v1/dashboard/data`, `/widgets`
9. Create `dashboard/schemas.py` — dashboard-specific response schemas
10. Move and update tests
11. Add Polars for large dataset query optimization in repository

**Files moved:** ~5 files
**Files created:** ~10 new files
**Risk:** Low — logic preserved, restructured

### Phase 5: Monitoring + Audit (Week 4)

**Goal:** Health checks and audit logging as proper modules.

**Tasks:**
1. Move `monitoring/health_check.py` → `monitoring/services.py`
2. Create `monitoring/routes.py` — `/api/v1/monitoring/health`
3. Create `monitoring/schemas.py`
4. Create `audit/models.py` — `AuditLog` ORM
5. Create `audit/repositories.py` — `AuditRepository`
6. Create `audit/services.py` — `AuditService`
7. Create `audit/routes.py` — `/api/v1/audit/logs`
8. Create `audit/schemas.py`
9. Wire `shared/middleware/audit_log.py` to write to `AuditLog` table
10. Create Alembic migration for `audit_logs` table
11. Write tests

**Files created:** ~12 new files
**Risk:** Low

### Phase 6: Reports (Week 5)

**Goal:** Report generation module.

**Tasks:**
1. Create `reports/services.py` — `ReportService`
2. Create `reports/generators/pdf_generator.py` — PDF report generation
3. Create `reports/generators/excel_generator.py` — Excel export
4. Create `reports/routes.py` — `/api/v1/reports/generate`, `/download`
5. Create `reports/schemas.py`
6. Write tests

**Files created:** ~8 new files
**Risk:** Low

### Phase 7: Notifications (Week 5)

**Goal:** Notification system for pipeline events, alerts.

**Tasks:**
1. Create `notifications/models.py` — `Notification` ORM
2. Create `notifications/repositories.py`
3. Create `notifications/services.py` — in-app, email (SMTP), webhook
4. Create `notifications/routes.py` — `/api/v1/notifications/*`
5. Create `notifications/schemas.py`
6. Wire ETL service to send notifications on pipeline completion/failure
7. Create Alembic migration
8. Write tests

**Files created:** ~8 new files
**Risk:** Low

### Phase 8: Organizations + Departments (Week 6 — Future-ready)

**Goal:** Multi-tenancy scaffolding.

**Tasks:**
1. Create `organizations/` module with CRUD
2. Create `departments/` module with CRUD
3. Create ORM models with foreign keys to users
4. Create Alembic migration
5. Write tests

**Files created:** ~12 new files
**Risk:** Low — new tables, no impact on existing

### Phase 9: Settings (Week 6)

**Goal:** System settings and feature flags.

**Tasks:**
1. Create `settings/models.py` — `SystemSetting` ORM
2. Create `settings/services.py`
3. Create `settings/routes.py` — `/api/v1/settings/*`
4. Create Alembic migration
5. Write tests

**Files created:** ~6 new files
**Risk:** Low

### Phase 10: AI Module (Future)

**Goal:** Forecasting and anomaly detection.

**Tasks:**
1. Create `ai/services.py` — time-series forecasting, anomaly detection
2. Create `ai/routes.py` — `/api/v1/ai/forecast`, `/anomalies`
3. Create `ai/schemas.py`
4. Write tests

**Files created:** ~5 new files
**Risk:** Medium — new ML dependencies

### Phase 11: Frontend — Next.js (Weeks 4-7, parallel)

**Goal:** Replace Streamlit with Next.js frontend.

**Tasks:**
1. Scaffold Next.js project with TypeScript + Tailwind
2. Set up Zustand stores (auth, filters, dashboard)
3. Create API client with JWT interceptor
4. Build auth pages (login, forgot password)
5. Build dashboard page with ECharts components
6. Build analytics page with filters + data table
7. Build ETL pipeline status page
8. Build settings page
9. Build reusable component library (cards, tables, charts, maps, forms, dialogs, feedback states)
10. Add Leaflet map for regional visualization
11. Deploy to Vercel

**Files created:** ~60+ new files
**Risk:** Medium — new frontend, but backend API remains stable

### Phase 12: CI/CD + Docker (Week 7)

**Goal:** Update CI/CD for monorepo (backend + frontend).

**Tasks:**
1. Update GitHub Actions for backend (ruff, black, pytest)
2. Add GitHub Actions for frontend (eslint, tsc, jest, playwright)
3. Update Dockerfile for backend
4. Create Dockerfile for frontend
5. Create docker-compose.yml for local dev
6. Update Vercel deployment config

**Files created:** ~5 new files
**Risk:** Low

---

## 7. File-by-File Modification Plan

### Files to MOVE (logic unchanged, location changes)

| Current Path | New Path | Notes |
|-------------|----------|-------|
| `config.py` | `shared/config/settings.py` | Refactor to Pydantic Settings |
| `etl/logging_config.py` | `shared/logging/logger.py` | Enhance with JSON structured logging |
| `etl/extract.py` | `etl/extract.py` | Stays — update imports only |
| `etl/transform.py` | `etl/transform.py` | Stays — update imports only |
| `etl/load.py` | `etl/load.py` | Stays — update imports only |
| `services/etl_service.py` | `etl/services.py` | Move, update imports |
| `services/dashboard_data_service.py` | `dashboard/services.py` | Move, update imports |
| `pipeline/run_pipeline.py` | `etl/pipeline.py` | Move, update imports |
| `scheduler/scheduler.py` | `etl/scheduler.py` | Move, update imports |
| `database/db_setup.py` | Split: `analytics/models.py` + `etl/models.py` | Split by domain |
| `database/repositories.py` | Split: `analytics/repositories.py` + `etl/repositories.py` | Split by domain |
| `database/migrate_to_mysql.py` | `alembic/` migrations | Replace with Alembic |
| `api/main.py` | `main.py` + `api/router.py` | Split app entry from router aggregation |
| `api/schemas.py` | Split into module-level `schemas.py` | Per module |
| `api/auth.py` | `authentication/` module | Replace with JWT-based auth |
| `monitoring/health_check.py` | `monitoring/services.py` | Move, update imports |
| `dashboard/app.py` | **DELETE** (replaced by Next.js) | Streamlit → Next.js |
| `dashboard/styles.py` | **DELETE** (replaced by Tailwind) | CSS → Tailwind |
| `dashboard/charts.py` | **DELETE** (replaced by ECharts) | Plotly → ECharts in frontend |
| `dashboard/utils.py` | `shared/utils/` (backend) + `frontend/src/utils/` (frontend) | Split |
| `dashboard/auth.py` | **DELETE** (replaced by JWT auth) | Session auth → JWT |

### Files to CREATE (new)

| Path | Purpose |
|------|---------|
| `main.py` | FastAPI app entry point (replaces `api/main.py`) |
| `api/router.py` | Aggregates all module routers |
| `api/dependencies.py` | Shared FastAPI dependencies (`get_db`, `get_current_user`) |
| `shared/config/settings.py` | Pydantic Settings (env vars) |
| `shared/config/database.py` | Engine factory, session factory |
| `shared/logging/logger.py` | Structured JSON logging |
| `shared/security/jwt_handler.py` | JWT encode/decode |
| `shared/security/password.py` | bcrypt hashing |
| `shared/security/permissions.py` | RBAC permission checker |
| `shared/exceptions/base.py` | Exception hierarchy |
| `shared/exceptions/handlers.py` | FastAPI exception handlers |
| `shared/response/standard.py` | StandardResponse wrapper |
| `shared/middleware/request_id.py` | Request ID middleware |
| `shared/middleware/audit_log.py` | Audit logging middleware |
| `shared/middleware/rate_limit.py` | Rate limiting middleware |
| `shared/utils/dates.py` | Date helpers |
| `shared/utils/formatting.py` | Currency/number formatting |
| `shared/utils/sanitization.py` | Input sanitization |
| `authentication/routes.py` | Auth endpoints |
| `authentication/services.py` | Auth business logic |
| `authentication/repositories.py` | User data access |
| `authentication/schemas.py` | Auth request/response schemas |
| `authentication/models.py` | User, Role, UserSession ORM |
| `authentication/validators.py` | Auth input validation |
| `users/routes.py` | User CRUD endpoints |
| `users/services.py` | User business logic |
| `users/schemas.py` | User schemas |
| `analytics/routes.py` | Analytics endpoints |
| `analytics/services.py` | KPI computation |
| `analytics/repositories.py` | Sales data access |
| `analytics/schemas.py` | Analytics response schemas |
| `analytics/models.py` | SalesRecord ORM |
| `analytics/validators.py` | Filter validation |
| `etl/routes.py` | ETL endpoints |
| `etl/services.py` | ETL orchestration |
| `etl/repositories.py` | PipelineRun data access |
| `etl/schemas.py` | ETL response schemas |
| `etl/models.py` | PipelineRun ORM |
| `etl/validators.py` | Pipeline config validation |
| `etl/pipeline.py` | Pipeline orchestrator |
| `etl/scheduler.py` | APScheduler |
| `dashboard/routes.py` | Dashboard data endpoints |
| `dashboard/services.py` | Dashboard data assembly |
| `dashboard/schemas.py` | Dashboard schemas |
| `monitoring/routes.py` | Health check endpoints |
| `monitoring/services.py` | Health check logic |
| `monitoring/schemas.py` | Health response schemas |
| `audit/routes.py` | Audit log endpoints |
| `audit/services.py` | Audit service |
| `audit/repositories.py` | Audit data access |
| `audit/schemas.py` | Audit schemas |
| `audit/models.py` | AuditLog ORM |
| `reports/routes.py` | Report endpoints |
| `reports/services.py` | Report generation |
| `reports/generators/pdf_generator.py` | PDF generation |
| `reports/generators/excel_generator.py` | Excel generation |
| `reports/schemas.py` | Report schemas |
| `notifications/routes.py` | Notification endpoints |
| `notifications/services.py` | Notification logic |
| `notifications/repositories.py` | Notification data access |
| `notifications/schemas.py` | Notification schemas |
| `notifications/models.py` | Notification ORM |
| `organizations/` | Full module (future-ready) |
| `departments/` | Full module (future-ready) |
| `settings/` | Full module |
| `ai/` | Full module (future) |
| `alembic/env.py` | Alembic environment |
| `alembic/versions/*.py` | Migration scripts |
| `frontend/` | Entire Next.js project (~60+ files) |

### Files to DELETE (after migration complete)

| Path | Reason |
|------|--------|
| `dashboard/app.py` | Replaced by Next.js frontend |
| `dashboard/styles.py` | Replaced by Tailwind CSS |
| `dashboard/charts.py` | Replaced by ECharts in frontend |
| `dashboard/auth.py` | Replaced by JWT auth |
| `config.py` | Replaced by `shared/config/settings.py` |
| `api/main.py` | Replaced by `main.py` + `api/router.py` |
| `api/schemas.py` | Split into module schemas |
| `api/auth.py` | Replaced by `authentication/` module |
| `database/migrate_to_mysql.py` | Replaced by Alembic |
| `services/etl_service.py` | Moved to `etl/services.py` |
| `services/dashboard_data_service.py` | Moved to `dashboard/services.py` |
| `pipeline/run_pipeline.py` | Moved to `etl/pipeline.py` |
| `scheduler/scheduler.py` | Moved to `etl/scheduler.py` |

### Files to KEEP (unchanged or minimal changes)

| Path | Notes |
|------|-------|
| `etl/extract.py` | Logic unchanged — update imports only |
| `etl/transform.py` | Logic unchanged — update imports only |
| `etl/load.py` | Logic unchanged — update imports only |
| `requirements.txt` | Add new deps (PyJWT, bcrypt, polars, alembic, reportlab) |
| `pyproject.toml` | Update ruff/black config for new structure |
| `.gitignore` | Add frontend entries |
| `.env.example` | Add new env vars |
| `dataset/` | Unchanged |
| `data/` | Unchanged |
| `logs/` | Unchanged |
| `Dockerfile` | Update for new structure |

---

## 8. Standard API Response Format

All API endpoints will return this standardized format:

```json
{
  "success": true,
  "message": "Operation completed successfully",
  "data": { ... },
  "errors": null,
  "timestamp": "2026-07-11T14:00:00.000Z",
  "requestId": "req_abc123def456"
}
```

### Error Response

```json
{
  "success": false,
  "message": "Validation failed",
  "data": null,
  "errors": [
    {
      "field": "email",
      "message": "Invalid email format"
    }
  ],
  "timestamp": "2026-07-11T14:00:00.000Z",
  "requestId": "req_abc123def456"
}
```

### Implementation

```python
# shared/response/standard.py
from typing import Any, Optional
from datetime import datetime
from pydantic import BaseModel


class ErrorDetail(BaseModel):
    field: str
    message: str


class StandardResponse(BaseModel):
    success: bool
    message: str
    data: Optional[Any] = None
    errors: Optional[list[ErrorDetail]] = None
    timestamp: datetime
    requestId: str


def success_response(data: Any, message: str = "OK", request_id: str = "") -> StandardResponse:
    return StandardResponse(
        success=True,
        message=message,
        data=data,
        timestamp=datetime.utcnow(),
        requestId=request_id,
    )


def error_response(message: str, errors: list[ErrorDetail] = None, request_id: str = "") -> StandardResponse:
    return StandardResponse(
        success=False,
        message=message,
        errors=errors,
        timestamp=datetime.utcnow(),
        requestId=request_id,
    )
```

---

## 9. Database Improvement Plan

### New Tables

| Table | Purpose | Module |
|-------|---------|--------|
| `users` | User accounts (email, password_hash, role_id, is_active) | `authentication/` |
| `roles` | Role definitions (admin, analyst, viewer) | `authentication/` |
| `user_sessions` | JWT refresh tokens, session tracking | `authentication/` |
| `audit_logs` | Audit trail (user_id, action, resource, timestamp, ip) | `audit/` |
| `notifications` | In-app notifications (user_id, type, message, read_at) | `notifications/` |
| `organizations` | Multi-tenant orgs (future) | `organizations/` |
| `departments` | Departments (org_id, name, head_id) | `departments/` |
| `system_settings` | Key-value system config | `settings/` |

### Existing Tables (Improvements)

| Table | Change |
|-------|--------|
| `sales` | Add foreign key to `organizations` (nullable, for future multi-tenancy) |
| `pipeline_runs` | Add `triggered_by` column (FK to `users`) |

### Indexes to Add

```sql
-- Users
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_role_id ON users(role_id);

-- Audit logs
CREATE INDEX idx_audit_user_id ON audit_logs(user_id);
CREATE INDEX idx_audit_created_at ON audit_logs(created_at);
CREATE INDEX idx_audit_action ON audit_logs(action);

-- Notifications
CREATE INDEX idx_notifications_user_id ON notifications(user_id);
CREATE INDEX idx_notifications_read_at ON notifications(read_at);
```

### Alembic Migration Plan

| Migration | Description |
|-----------|-------------|
| `001_initial_schema` | Create `sales` and `pipeline_runs` (matching current schema) |
| `002_add_users_roles` | Create `users`, `roles`, `user_sessions` |
| `003_add_audit_logs` | Create `audit_logs` |
| `004_add_notifications` | Create `notifications` |
| `005_add_organizations_departments` | Create `organizations`, `departments` |
| `006_add_system_settings` | Create `system_settings` |
| `007_add_triggered_by` | Add `triggered_by` FK to `pipeline_runs` |

---

## 10. Security Improvement Plan

| Area | Current | Target |
|------|---------|--------|
| Authentication | API key (header/query) | JWT access + refresh tokens |
| Authorization | None | RBAC (admin, analyst, viewer roles) |
| Password storage | N/A | bcrypt with salt rounds=12 |
| Input validation | Pydantic schemas | Pydantic + custom validators per module |
| SQL injection | SQLAlchemy parameterized queries | Keep — already protected |
| Rate limiting | None | SlowAPI middleware (configurable per endpoint) |
| Audit logging | None | Middleware logs all write operations to `audit_logs` |
| File uploads | 50MB limit, XSS sanitization | Keep + add file type validation, virus scan hook |
| CORS | `*` (all origins) | Configure specific origins via env var |
| HTTPS | Not enforced | Add HSTS middleware, redirect HTTP→HTTPS |
| Secrets | `.env` files | Keep `.env` + add secret rotation documentation |

### JWT Configuration

```python
# shared/security/jwt_handler.py
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7
ALGORITHM = "HS256"
# JWT_SECRET_KEY from env var
```

### RBAC Roles

| Role | Permissions |
|------|------------|
| `admin` | Full access — all modules, user management, settings |
| `analyst` | Read analytics, trigger pipeline, view dashboard, generate reports |
| `viewer` | Read dashboard, view analytics (no write access) |

---

## 11. Frontend Architecture

### State Management (Zustand)

```
authStore.ts      → user, token, isAuthenticated, login(), logout()
filterStore.ts    → region, category, dateRange, setFilters(), clearFilters()
dashboardStore.ts → kpis, salesData, loading, error, fetchData()
notificationStore → notifications, unreadCount, markRead(), add()
```

### API Client

```typescript
// services/apiClient.ts
const apiClient = {
  baseURL: process.env.NEXT_PUBLIC_API_URL,
  interceptors: {
    request: (config) => {
      // Attach JWT token from authStore
      // Attach request ID
    },
    response: (response) => {
      // Unwrap StandardResponse format
      // Handle 401 → refresh token → retry
      // Handle errors → show toast
    }
  }
}
```

### Reusable Components

| Component | Props | Used In |
|-----------|-------|---------|
| `KPICard` | title, value, icon, trend, color | Dashboard, Analytics |
| `DataTable` | columns, data, pagination, sorting | All data views |
| `ChartContainer` | title, children, loading, error | All chart pages |
| `AreaChart` | data, xKey, yKey, colors | Revenue trends |
| `BarChart` | data, xKey, yKey, orientation | Category breakdown |
| `PieChart` | data, nameKey, valueKey, colors | Regional distribution |
| `HeatmapChart` | data, xLabels, yLabels, values | Region × Category |
| `RegionMap` | data, regionKey, valueKey | Geographic view |
| `FilterBar` | filters, onChange | Analytics, Dashboard |
| `DateRangeFilter` | value, onChange, min, max | All filtered views |
| `LoadingState` | message | All async views |
| `ErrorState` | message, onRetry | All async views |
| `EmptyState` | icon, title, description | All data views |
| `Button` | variant, size, loading, onClick | Everywhere |
| `Input` | label, error, value, onChange | All forms |
| `Select` | label, options, value, onChange | All filters |
| `Dialog` | open, onClose, title, children | Confirmations, details |
| `Toast` | type, message, duration | Global notifications |

### Page Structure

| Page | Route | Components Used |
|------|-------|-----------------|
| Dashboard | `/` | KPICard × 4, AreaChart, BarChart, PieChart, HeatmapChart, FilterBar |
| Analytics | `/analytics` | KPICard, DataTable, BarChart, ScatterChart, FilterBar, DateRangeFilter |
| ETL Pipeline | `/etl` | DataTable (runs), Button (trigger), ProgressBar, StatusBadge |
| Reports | `/reports` | ReportCard, Button (generate), DownloadLink |
| Settings | `/settings` | SettingsForm, ToggleSwitch |
| Login | `/login` | LoginForm, Button |

---

## Summary

This plan transforms the current flat-structure ETL project into a modular, enterprise-grade platform with:

- **14 feature-based backend modules** following Clean Architecture
- **Next.js frontend** with 20+ reusable components and Zustand state management
- **JWT + RBAC** authentication replacing API key and session auth
- **Alembic migrations** for database schema management
- **Standardized API responses** with request IDs and error details
- **Audit logging** middleware for compliance
- **Rate limiting** for API protection
- **Polars** added for high-performance data processing
- **Apache ECharts + Leaflet** replacing Plotly for frontend visualization
- **Vercel deployment** for frontend, Docker for backend

### Implementation Order

1. **Phase 1** — `shared/` foundation (no breaking changes)
2. **Phase 2** — Authentication + Users (new, parallel to existing)
3. **Phase 3** — ETL module migration (move files, update imports)
4. **Phase 4** — Analytics + Dashboard migration
5. **Phase 5** — Monitoring + Audit
6. **Phase 11** — Frontend (starts in parallel with Phase 4)
7. **Phases 6-10** — Reports, Notifications, Orgs, Settings, AI
8. **Phase 12** — CI/CD update

Each phase is independently deployable. Existing functionality remains operational throughout.
