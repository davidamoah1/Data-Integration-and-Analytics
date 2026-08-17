# CHAPTER THREE

# METHODOLOGY / SYSTEM ANALYSIS AND DESIGN

## 3.1 Introduction

This chapter describes the methodology adopted for the design and
implementation of the DataFlow (AEDIP) platform. It presents the software
development methodology used, the analysis of functional and non-functional
requirements, the overall system architecture, the database design, the
security design, and the tools and technologies employed in building the
platform.

## 3.2 Software Development Methodology

The **Agile (iterative and incremental) methodology** was adopted for the
development of this project, rather than a traditional linear (Waterfall)
approach. This decision was informed by the scale and evolving nature of the
platform's requirements, which grew from a simple ETL pipeline into a
multi-module enterprise system spanning authentication, analytics, AI, and
performance infrastructure.

The project was developed in successive phases, each delivering a working,
independently testable increment of functionality:

| Phase | Deliverable |
|-------|-------------|
| Phase 1–3 | Core ETL pipeline, dashboard, and REST API |
| Phase 4 | Enterprise Identity & Access Management (JWT, RBAC, Organizations) |
| Phase 5 | AI Intelligence Platform (multi-provider AI gateway, Copilot) |
| Phase 6 | Analytics & Alerting (dashboards, widgets, KPIs) |
| Phase 7 | Executive Decision Center |
| Phase 8 | Platform Features (connectors, workflows, report builder, search) |
| Phase 9 | Enterprise Hardening (security, observability, backup, performance) |
| Phase 10 | Performance & Global Scale (workers, task queue, Redis, DB optimization) |
| Phase 11 | Final Product Polish (UI, documentation, demo data) |

This iterative approach allowed each phase to be independently designed,
implemented, tested (via an automated regression test suite), and validated
before the next phase began, reducing integration risk and allowing course
correction based on findings from earlier phases.

## 3.3 Requirements Analysis

### 3.3.1 Functional Requirements

The system shall:

1. Allow a registered user to upload a CSV or Excel file containing tabular
   business data.
2. Automatically extract, clean, validate, and load the uploaded data into a
   relational database, detecting and skipping duplicate records.
3. Automatically map raw column names to standardized business fields using
   pattern-based semantic recognition, including support for common
   abbreviations and industry-specific terminology.
4. Automatically classify the dataset's industry domain (e.g., Retail,
   Healthcare, Banking, Agriculture) using weighted entity voting, and route
   the user to an appropriate pre-built dashboard.
5. Compute and display Key Performance Indicators (KPIs) and interactive
   charts based on the uploaded/queried data, with filtering by date, region,
   and category.
6. Allow users to register, log in, and log out securely, with session and
   refresh-token management.
7. Enforce role-based access control (RBAC), restricting access to specific
   features and data based on a user's assigned role and permissions.
8. Support multiple organizations (tenants) operating independently within a
   single deployment, with data isolation enforced between tenants.
9. Allow authorized users to query their data using natural language via an
   AI Copilot, and receive AI-generated anomaly alerts and forecasts.
10. Log all significant user actions (logins, data changes, permission
    changes) to an audit trail for accountability and traceability.
11. Allow scheduling of recurring ETL pipeline runs and generation of
    scheduled reports.
12. Expose all core functionality via a documented, versioned REST API in
    addition to the web dashboard.

### 3.3.2 Non-Functional Requirements

1. **Performance**: The system shall respond to typical API requests within
   an acceptable latency threshold and shall support datasets containing
   hundreds of thousands to millions of rows through chunked query
   processing and caching.
2. **Security**: The system shall protect user credentials using industry
   standard hashing (Argon2), transmit authentication tokens using signed
   JWTs, and enforce HTTPS in production. Sensitive actions must be
   authenticated and authorized before execution.
3. **Scalability**: The system shall support horizontal scaling of
   background workers and shall use a connection pool to efficiently manage
   database connections under concurrent load.
4. **Reliability**: The system shall implement retry logic with exponential
   backoff for transient failures and a circuit breaker pattern for external
   AI provider calls.
5. **Availability**: The system shall expose health (`/health`) and
   readiness (`/ready`) endpoints to support automated monitoring and
   container orchestration.
6. **Maintainability**: The codebase shall follow a modular, layered
   architecture with clear separation of concerns (routes, services,
   repositories, models) and shall be covered by an automated test suite to
   support safe refactoring.
7. **Portability**: The system shall run identically across local
   development (SQLite), containerized deployment (Docker Compose with
   MySQL and Redis), and serverless cloud deployment (Vercel).
8. **Usability**: The dashboard shall be accessible to non-technical users,
   requiring no coding or query-writing to view standard KPIs and reports.

## 3.4 System Architecture

The DataFlow platform follows a **layered, modular monolith architecture**,
in which distinct business domains (authentication, ETL, analytics, AI, etc.)
are organized into independent Python packages that communicate through
well-defined service interfaces, while sharing a common database and
infrastructure layer. This design was chosen over a full microservices
architecture to reduce operational complexity while still preserving strong
internal modularity that would allow future extraction into independent
services if required.

### 3.4.1 High-Level Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│         Presentation Layer                                       │
│  Next.js/React Web Frontend (:3000)  |  Streamlit Dashboard (:8501) │
└───────────────────────┬───────────────────────────────────────────┘
                        │ HTTPS (JWT Bearer Token)
┌───────────────────────▼─────────────────────────────────────────┐
│                    FastAPI Backend (:8000)                       │
│  ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐ │
│  │ Auth │ │Sales │ │ ETL  │ │ AI   │ │Audit │ │ Org  │ │ ...  │ │
│  └──────┘ └──────┘ └──────┘ └──────┘ └──────┘ └──────┘ └──────┘ │
│  Middleware: CORS | GZip | Security Headers | Rate Limiting |    │
│              Request Context | Request Logging                  │
└───────────────────────┬───────────────────────────────────────────┘
                        │ SQLAlchemy ORM (Repository Pattern)
┌───────────────────────▼─────────────────────────────────────────┐
│              Database (MySQL 8.0 in production / SQLite in dev)  │
└─────────────────────────────────────────────────────────────────┘

         Cross-cutting infrastructure used by the backend:
   Redis (cache + task queue) | Background Workers | APScheduler
```

### 3.4.2 Architectural (Clean Architecture) Layering

Within each business domain module (e.g., `authentication/`), the codebase
follows a clean-architecture-inspired layering:

```
Routes (FastAPI)      →  HTTP request/response handling, input validation
        │
Services              →  Business logic, orchestration, transaction boundaries
        │
Repositories           →  Data access abstraction over the ORM
        │
Models (SQLAlchemy ORM) →  Persistent entity definitions
        │
Shared Infrastructure   →  Database session/engine, security utilities (JWT,
                            Argon2), custom exception hierarchy, standardized
                            API response envelope, dependency-injected guards
                            (get_current_user, require_permissions)
```

This layering enforces separation of concerns: routes never access the
database directly, services contain no HTTP-specific logic, and repositories
encapsulate all query construction, allowing the underlying database engine
(SQLite vs. MySQL) to be swapped via configuration without code changes
elsewhere in the system.

### 3.4.3 Module Map

| Module | Responsibility |
|--------|-----------------|
| `api/` | FastAPI application entrypoint, routers, request/response schemas |
| `authentication/` | User accounts, roles, permissions, sessions, JWT issuance |
| `organizations/` | Multi-tenant organization, branch, department, team management |
| `etl/` | Data extraction, transformation, loading, pipeline orchestration |
| `semantic/` | Column recognition, entity library, industry classification |
| `analytics/` | KPI aggregation, dashboards, widgets, alerting |
| `ai/` | Multi-provider AI gateway, AI Copilot, plugins, document chat |
| `africa_intelligence/` | Country profiles, currency conversion, industry mapping |
| `audit/` | Security event logging and audit trail |
| `performance/` | Task queue, background workers, caching, database optimization |
| `platform_features/` | Connector marketplace, workflow automation, notifications, search |
| `shared/` | Database session/engine, security utilities, middleware, exceptions |
| `dashboard/` | Streamlit-based analytics dashboard (alternate UI) |
| `frontend/` | Next.js/React web application (primary UI) |

### 3.4.4 Semantic Mapping and Industry Classification Pipeline

A central design element of the platform is the semantic engine, which
processes an uploaded dataset through the following stages:

```
Upload → Column Profiling → Entity Matching → Weighted Voting → Classification
```

1. **Column Profiling** — inspects each column's name and sampled values.
2. **Entity Matching** — matches column names against an entity library of
   ~60+ business entities using exact synonym matching (confidence 1.0),
   partial synonym matching, and fuzzy string matching (threshold 0.65).
3. **Weighted Voting** — each matched entity contributes a weighted vote
   (1.0–3.0) toward a specific industry classification; universal entities
   (e.g., "date," "revenue") do not vote, as they are common to all
   industries.
4. **Tie-Breaking and Confidence Routing** — if the top two industries are
   within 0.5 votes of each other, or the leading industry's vote share is
   below 40%, the dataset is classified as "unknown" and routed to a
   generic dashboard with a manual confirmation prompt; datasets classified
   with ≥85% confidence are automatically routed to a pre-built,
   industry-specific dashboard (e.g., Retail, Healthcare, Banking).

This design allows the platform to support twelve distinct industry
verticals without requiring the end user to manually configure their
dashboard.

## 3.5 Database Design

### 3.5.1 Database Technology

The platform uses **SQLAlchemy 2.0** as its Object-Relational Mapping (ORM)
layer, supporting two interchangeable database backends selected via
configuration:

- **SQLite** — used for local development and automated testing, requiring
  no external database server.
- **MySQL 8.0** — used in staging and production, providing multi-user
  concurrency, connection pooling, and durability guarantees appropriate for
  a production SaaS deployment.

Schema evolution is managed using **Alembic**, which tracks incremental
migrations and allows the schema to be version-controlled alongside the
application code. A dedicated CI check (`alembic check`) verifies that the
migration history remains synchronized with the ORM models on every build.

### 3.5.2 Key Entity Groups

The database schema is organized around the following major entity groups:

- **Identity & Access Management**: `User`, `Role`, `Permission`,
  `RolePermission`, `UserRole`, `Session`, `PasswordReset`, `APIToken`,
  `LoginHistory`, `ActivityLog`, `PasswordHistory`.
- **Organizations**: `Organization`, `Branch`, `Department`, `Team`.
- **Sales / ETL Data**: `Sale`, `PipelineRun` and related operational tables
  populated by the ETL pipeline.
- **Analytics**: Dashboard, widget, KPI, and alert configuration tables.
- **AI Platform**: AI conversation, assistant, and usage tracking tables.
- **Audit & Security**: `AuditLog`, `SystemLog`, `SecurityLog`,
  `UserActivity`.
- **Platform Features**: Connector, workflow, notification, and report
  builder tables.

### 3.5.3 Multi-Tenancy Design

The system implements **multi-tenancy using a shared database, shared
schema** model, in which most tenant-scoped tables include an
`organization_id` discriminator column. Data isolation between
organizations is enforced at the service/repository layer, ensuring that a
user belonging to one organization cannot access another organization's
data, even though all organizations share the same underlying database and
tables. This approach was selected to minimize infrastructure cost while
still providing adequate isolation for a SaaS platform serving many small to
medium-sized tenant organizations.

## 3.6 Security Design

Security was treated as a first-class design concern throughout the
architecture, rather than an afterthought layered on at the end of
development. Key security design decisions include:

1. **Authentication**: JSON Web Tokens (JWT, HS256) are used for stateless
   authentication, with short-lived access tokens (30 minutes) and
   longer-lived refresh tokens (7 days) tracked against server-side session
   records, allowing sessions to be revoked (e.g., on logout or by an
   administrator).
2. **Password Storage**: Passwords are hashed using **Argon2** (with a
   bcrypt fallback for compatibility), configured with a memory cost of
   65536, time cost of 3, and parallelism of 4 — parameters consistent with
   current password-hashing best practice.
3. **Authorization**: A granular Role-Based Access Control (RBAC) system is
   implemented with 11 default roles (e.g., `super_admin`, `org_admin`,
   `data_analyst`, `viewer`) and 30+ discrete permissions organized by
   module, enforced via a `require_permissions()` dependency injected into
   protected API routes.
4. **Password Policy**: Enforced minimum length and complexity (uppercase,
   lowercase, digit, special character), with a password history check
   preventing reuse of the last five passwords.
5. **Account Lockout**: Accounts are automatically locked for a configurable
   duration after five consecutive failed login attempts, mitigating
   brute-force attacks.
6. **Transport and Header Security**: HTTPS is enforced in production, and
   standard security headers (`X-Content-Type-Options`,
   `X-Frame-Options`, `X-XSS-Protection`, `Referrer-Policy`) are applied to
   all responses via middleware.
7. **Rate Limiting**: A sliding-window rate limiter restricts each client to
   a configurable number of requests per minute, mitigating abuse and
   denial-of-service risk.
8. **Audit Logging**: All security-relevant actions (logins, permission
   changes, data modifications) are recorded in an audit trail capturing the
   acting user, action, affected resource, and originating IP address.
9. **Input Validation**: All API input is validated through Pydantic schemas
   before reaching business logic, and all database queries are
   parameterized through the ORM to prevent SQL injection.

## 3.7 Tools and Technologies

| Layer | Technology | Justification |
|-------|-----------|----------------|
| Backend Language | Python 3.12 | Mature ecosystem for data processing and web APIs |
| Web API Framework | FastAPI | High performance, native async support, automatic OpenAPI documentation, Pydantic integration |
| Data Processing | Pandas | Industry-standard library for tabular data manipulation |
| ORM | SQLAlchemy 2.0 | Type-safe, database-agnostic ORM supporting both SQLite and MySQL |
| Database Migrations | Alembic | Version-controlled, incremental schema migrations |
| Database (Dev) | SQLite | Zero-configuration local development and testing |
| Database (Prod) | MySQL 8.0 | Proven, widely-supported relational database for production workloads |
| Caching / Task Queue | Redis | High-performance in-memory store for caching and background task queuing |
| Scheduling | APScheduler | In-process job scheduling for recurring ETL and report generation |
| Frontend Framework | Next.js / React | Modern, component-based UI framework with server-side rendering |
| Alternate Dashboard | Streamlit + Plotly | Rapid, Python-native dashboard development for internal/analyst use |
| Authentication | JWT + Argon2 | Industry-standard, stateless authentication and secure password hashing |
| AI Integration | OpenAI, Gemini, DeepSeek, Claude, local LLMs | Multi-provider abstraction for resilience and cost flexibility |
| Testing | Pytest | De facto standard Python testing framework, supports fixtures and async tests |
| Linting/Formatting | Ruff, Black | Automated code quality and consistent formatting enforcement |
| Containerization | Docker, Docker Compose | Reproducible development and deployment environments |
| CI/CD | GitHub Actions | Automated linting, testing, building, and deployment on every change |
| Cloud Deployment | Vercel (serverless) | Managed, scalable hosting for both frontend and API |
| Version Control | Git / GitHub | Industry-standard distributed version control |

## 3.8 Development Environment and Version Control

Development was conducted using a Git-based workflow, with the source code
hosted on GitHub. A continuous integration (CI) pipeline, implemented with
GitHub Actions, automatically runs on every push to the main branch,
executing the following stages in sequence: **Lint** (Ruff, Black, ESLint,
TypeScript checks) → **Security Scan** (dependency audit, static analysis) →
**Unit Tests** → **Integration Tests** (against a real MySQL and Redis
service) → **Build** (backend import verification, Alembic migration
verification, frontend build, Docker image build) → **Deploy** (to
production, gated on all prior stages passing). This pipeline enforces code
quality and correctness before any change reaches production.

## 3.9 Summary

This chapter presented the Agile methodology adopted for the project, the
functional and non-functional requirements derived from the problem
identified in Chapter One, the layered system architecture, the database and
multi-tenancy design, the security architecture, and the tools and
technologies used to implement the DataFlow (AEDIP) platform. Chapter Four
builds on this design by presenting the concrete implementation and the
results of system testing and evaluation.
