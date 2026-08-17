# World-Class Data Platform Architecture

> Document created as part of Phase 0 audit before implementing the Data-to-Decision workflow.
> Last updated: 2026-08-17

## Executive Summary

DataFlow is an enterprise-grade data integration and analytics platform built with:
- **Backend**: FastAPI 0.115.6 (Python 3.12)
- **Frontend**: Next.js 14 (React 18, TypeScript 5.5)
- **Secondary Dashboard**: Streamlit (for legacy analytics)
- **Database**: SQLAlchemy 2.0 with MySQL 8.0 (production) / SQLite (development)
- **Migrations**: Alembic 1.14 (18 migration files)
- **Queue**: Custom task queue with Redis backend (in-memory fallback for dev)
- **Storage**: Multi-backend (Local, S3, R2, Supabase)
- **Auth**: JWT with Argon2 hashing, RBAC
- **CI/CD**: GitHub Actions (6 workflows)

## Current Architecture

### Technology Stack

| Layer | Technology | Version |
|-------|-----------|---------|
| API Framework | FastAPI | 0.115.6 |
| ASGI Server | Uvicorn | 0.34.0 |
| Frontend | Next.js (App Router) | 14.2.5 |
| Language (FE) | TypeScript | 5.5.4 |
| Styling | Tailwind CSS | 3.4.7 |
| State Management | Zustand | 4.5.4 |
| ORM | SQLAlchemy | 2.0.36 |
| Migrations | Alembic | 1.14.0 |
| Production DB | MySQL | 8.0 |
| Dev DB | SQLite | 3.x |
| Queue/Cache | Redis | 7.x |
| Storage | S3/R2/Supabase/Local | - |
| Auth | JWT (HS256) | - |
| Password Hash | Argon2 | - |
| AI Providers | OpenAI, Claude, Gemini, DeepSeek | - |

### Backend Directory Structure

```
D:\Dataflow\
├── api/              # FastAPI entry point, routes, middleware
├── authentication/   # Auth models, services, routes
├── organizations/    # Multi-tenant organization management
├── analytics/        # Dashboard, KPI, alert models & routes
├── ai/              # AI platform (15+ engines, multi-provider)
├── ai_copilot/      # Local NL query engine (no LLM required)
├── audit/           # Audit trail (4 log types)
├── capture/         # Smart data capture (OCR, forms)
├── connectors/      # 15+ data connectors (DB, file, cloud, API)
├── data_quality/    # Quality checks, drift detection, scoring
├── database/        # Core DB setup, legacy models
├── dataset/         # Test dataset generation
├── dataset_library/ # Dataset catalog
├── etl/             # Full ETL pipeline (extract, transform, load)
├── governance/      # Data classification, privacy
├── jobs/            # Background job system
├── ml/              # MLOps platform (AutoML, forecasting, anomaly)
├── monitoring/      # Health checks, Prometheus, Sentry
├── notifications/   # Multi-channel notifications
├── organizations/   # Organization, department, team models
├── performance/     # Task queue, caching
├── pipeline/        # Simple pipeline orchestrator
├── predictive_analytics/ # Industry-specific predictions
├── saas/            # Subscription, billing, feature flags
├── scheduler/       # Scheduled reports/tasks
├── semantic/        # Semantic mapping, KPI generation
├── services/        # Service layer (dashboard, report, workflow)
├── shared/          # Shared utilities (database, security, deps)
├── storage/         # File storage abstraction
├── studios/         # Data Intelligence Studios
├── validation/      # Data validation engine
├── workflows/       # Workflow definitions & execution
├── alembic/         # Database migrations
├── docs/            # Documentation (60+ files)
├── tests/           # Test suite (53 backend + 4 frontend files)
└── frontend/        # Next.js 14 application
```

### Frontend Directory Structure

```
frontend/
├── app/
│   ├── (app)/       # Protected routes (authenticated)
│   │   ├── dashboard/
│   │   ├── datasets/
│   │   ├── analytics/
│   │   ├── reports/
│   │   ├── studios/
│   │   ├── capture/
│   │   ├── jobs/
│   │   ├── settings/
│   │   └── ...
│   ├── login/
│   ├── signup/
│   └── layout.tsx
├── components/
│   ├── ui/          # Reusable UI components
│   ├── layout/      # AppShell, Sidebar, TopNav
│   ├── auth/        # RouteGuard, Can (permission)
│   ├── reports/     # Report builder, presentation viewer
│   └── ...
├── features/        # Feature-specific components
│   └── datasets/    # DatasetUpload component
├── services/        # API service layer
│   ├── api/         # Centralized API client
│   ├── datasets/    # Dataset service
│   ├── reports/     # Report service
│   └── ...
├── stores/          # Zustand stores
├── lib/             # Utilities
└── types/           # TypeScript types
```

### Database Architecture

**18 Alembic migrations** covering:
1. IAM (User, Role, Permission, Session, Resource)
2. ETL (Pipeline, Job, Profile, Quality Report, Lineage)
3. AI (Conversation, Message, Provider, Usage, Workflow)
4. Organizations (Organization, Branch, Department, Team)
5. Analytics (Dashboard, Widget, KPI, Alert)
6. Audit (AuditLog, SecurityLog, SystemLog, UserActivity)
7. Jobs (Background job tracking)
8. Storage (FileRecord)
9. ML (Model, TrainingRun, Prediction, Feature)
10. SaaS (Subscription, Invoice, Usage, FeatureFlag)
11. Workflows (Definition, Version, Execution)
12. Enterprise (Template, Comment, Branding)
13. Studios (Intelligence modules)
14. Capture (Document, Task, Queue)
15. Connectors (Configuration, Execution)

### Authentication & RBAC

- **JWT tokens**: Access (30min) + Refresh (7 days)
- **Role hierarchy**: Platform → Organization → Department → Personal
- **Default roles**: super_admin, org_admin, editor, viewer
- **Permission model**: Module-based permissions (datasets.view, reports.create, etc.)
- **Middleware**: TenantIsolationMiddleware enforces org scoping

### Job Architecture

- **Custom TaskQueue**: Redis (prod) / in-memory (dev)
- **Priority levels**: HIGH, ETL, NORMAL, REPORTS, NOTIFICATIONS, LOW
- **Job model**: Persisted in DB with progress, retry, timeout
- **Worker**: Separate process with auto-scaling (2-20 workers)
- **Job types**: etl_run, ocr_batch, report_gen, data_import, export, custom

### Storage Architecture

- **Backends**: Local, S3, R2, Supabase
- **Metadata**: Database (FileRecord table)
- **Content**: Object storage
- **Features**: SHA-256 checksums, presigned URLs, CDN support
- **Isolation**: Organization-scoped

## Existing Workflow (Dataset Intelligence)

The platform already has a dataset workflow at `/datasets/workflow`:

```
Upload → Validate → Profile → Quality Check → Semantic Analysis
→ Industry Detection → Metadata Generation → Knowledge Extraction
→ Smart Insights → Dashboard Ready → Analysis Complete
```

This workflow uses `services/dataset_workflow.py` which orchestrates the stages.

## Key Gaps Identified (vs. Master Prompt Requirements)

### 1. Unified Primary Workflow UX
- The workflow exists but is not the primary landing experience
- No visible stepper/progress bar showing all 7 stages
- Missing: Clean → Analyze → Visualize → Report → Present progression in UI

### 2. Data Quality / Smart Cleaning
- Backend quality engine exists (`data_quality/`) but frontend cleaning UX is minimal
- No before/after comparison UI
- No transformation history viewer with undo
- Quality score exists but not prominently displayed

### 3. Analysis Engine (Easy/Pro Modes)
- Backend has comprehensive statistical tools
- Frontend lacks a dedicated "Easy Mode" for non-technical users
- Frontend lacks a dedicated "Pro Mode" with full statistical controls

### 4. Visualization Recommendation
- Backend `services/dashboard_recommender.py` exists
- Frontend dashboard builder exists but chart type recommendation is not prominent

### 5. Report Builder
- Backend `services/report_engine.py` exists
- Frontend `components/reports/ReportBuilder.tsx` exists
- Needs verification that end-to-end flow works

### 6. One-Click Presentation
- Backend `studios/presentation_service.py` exists
- Frontend has PresentationViewer component
- Needs verification of PPTX generation

### 7. Blank Workspace
- ADR-0002 documents "Blank Workspace by Default"
- Needs verification that new orgs get clean workspaces

## Security Posture

- JWT with random ephemeral secret in dev (good)
- Production requires explicit JWT_SECRET_KEY (good)
- Argon2 password hashing (excellent)
- Rate limiting middleware (good)
- Tenant isolation middleware (good)
- RBAC with permission checks (good)
- No secrets exposed to frontend (verified)
- Security headers configured (good)

## Performance Architecture

- Connection pooling for MySQL (10 pool, 20 overflow)
- Redis caching with configurable TTL
- Background workers for heavy processing
- Chunked queries (default 5000)
- Paginated API responses
- Streaming upload support

## Deployment Architecture

- Docker Compose with MySQL, Redis, Worker, API, Dashboard
- Production: Nginx reverse proxy with SSL
- CI/CD: GitHub Actions (lint, security, test, build, deploy)
- Vercel deployment for serverless frontend
- Health check endpoints (/health, /ready, /metrics)

---

## Implementation Priority

Based on audit findings, the following are the priorities for the Data-to-Decision transformation:

1. **HIGH**: Create unified workflow stepper UI (the primary user journey)
2. **HIGH**: Strengthen data quality display and cleaning UX
3. **HIGH**: Build Easy/Pro analysis modes
4. **HIGH**: Verify and enhance report → presentation pipeline
5. **MEDIUM**: Dashboard auto-generation improvements
6. **MEDIUM**: Sector intelligence UI enhancements
7. **MEDIUM**: Transformation history with undo
8. **LOW**: Additional file format support
9. **LOW**: Additional connector types
