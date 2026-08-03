# Feature Catalog

> **Version**: 2.0.0  
> **Last Updated**: 2026-08-01  
> **Status**: Active  
> **Owner**: Product Manager

---

## Purpose

Complete catalog of all platform features.

## Scope

Every feature available in DataFlow.

## Audience

Product managers, sales, and customers.

---

## 1. Authentication & User Management

| Feature | Status | Description |
|---------|--------|-------------|
| JWT authentication | ✅ | Access + refresh tokens |
| Multi-mode registration | ✅ | Create org, join org, personal |
| Invitation-based onboarding | ✅ | Email + token + role |
| Password reset | ✅ | Token-based reset |
| Email verification | ✅ | Token-based verification |
| Account lockout | ✅ | After failed attempts |
| Password history | ✅ | Prevent reuse |
| Session management | ✅ | Database-backed sessions |
| User CRUD | ✅ | Create, read, update, delete |
| Role management | ✅ | 13 system roles + custom |
| Permission management | ✅ | 30+ permissions |
| MFA | ✅ | TOTP-based (pyotp) |
| SSO | ⚠️ Planned | SAML/OIDC |
| API Keys | ⚠️ Planned | Scoped tokens |

## 2. Organization Management

| Feature | Status | Description |
|---------|--------|-------------|
| Multi-tenant architecture | ✅ | Org-scoped data isolation |
| Organization CRUD | ✅ | Create, update, delete |
| Department management | ✅ | Subdivide org by department |
| Workspace model | ✅ | Org + personal workspaces |
| Tenant isolation | ✅ | Three-layer enforcement |
| Tenant suspend/activate | ✅ | Super admin control |

## 3. Data & Analytics

| Feature | Status | Description |
|---------|--------|-------------|
| Dataset upload (CSV/Excel) | ✅ | File import and parsing |
| Dataset management | ✅ | View, delete datasets |
| Dashboard builder | ✅ | Create visual dashboards |
| KPI tracking | ✅ | Key performance indicators |
| Analytics views | ✅ | Charts and visualizations |
| Report generation | ✅ | Create reports |
| Report export | ✅ | PDF, CSV, Excel |
| Scheduled reports | ✅ | APScheduler integration |
| Presentation builder | ⚠️ Planned | Slide deck creation |

## 4. ETL & Automation

| Feature | Status | Description |
|---------|--------|-------------|
| ETL pipelines | ✅ | Extract, transform, load |
| Workflow management | ✅ | Create and execute workflows |
| Pipeline run history | ✅ | Track execution status |
| Data import/export | ✅ | Via ETL pipelines |
| Scheduler | ✅ | Background job execution |

## 5. AI & Machine Learning

| Feature | Status | Description |
|---------|--------|-------------|
| AI analytics assistant | ✅ | Conversational analytics |
| AI report generation | ✅ | AI-assisted summaries |
| ML model management | ✅ | Train and deploy models |
| ML predictions | ✅ | Predictive analytics |
| AI plugins | ✅ | System AI plugins |

## 6. Smart Data Capture

| Feature | Status | Description |
|---------|--------|-------------|
| Document upload (PDF/image) | ✅ | File upload |
| OCR text extraction | ✅ | Automatic text recognition |
| Field extraction | ✅ | Intelligent field detection |
| Confidence scoring | ✅ | Per-field confidence |
| Data correction | ✅ | Manual correction UI |

## 7. Studios

| Feature | Status | Description |
|---------|--------|-------------|
| Analytics Studio | ✅ | General analytics |
| Healthcare Studio | ✅ | Healthcare analytics |
| Education Studio | ✅ | Education analytics |
| Business Studio | ✅ | Business analytics |
| Research Studio | ✅ | Research analytics |
| Automation Studio | ✅ | ETL and automation |
| Template library | ✅ | Pre-built templates |

## 8. Security & Compliance

| Feature | Status | Description |
|---------|--------|-------------|
| RBAC | ✅ | 13 roles, 30+ permissions |
| Audit logging | ✅ | All critical actions |
| Security logging | ✅ | Security events |
| Tenant isolation | ✅ | Org-scoped access |
| Security headers | ✅ | CSP, HSTS, etc. |
| Rate limiting | ✅ | 120 RPM default |
| Request size limit | ✅ | 50MB max |
| Encryption at rest | ✅ | AES-256 field-level encryption |
| MFA (TOTP) | ✅ | Per-user multi-factor auth |
| Account lockout | ✅ | 5 attempts / 15 min lockout |
| Vulnerability scanning | ✅ | pip-audit, npm audit, Bandit, Trivy |
| Dependabot | ✅ | Automated dependency updates |
| Compliance mapping | ✅ | SOC 2, ISO 27001, GDPR, HIPAA |
| Security checklist | ✅ | Production hardening checklist |

## 9. Platform & Ecosystem

| Feature | Status | Description |
|---------|--------|-------------|
| Plugin system | ✅ | Extensible architecture |
| Webhooks | ✅ | Outbound events |
| Marketplace | ✅ Placeholder | Extension marketplace |
| Connectors | ✅ | Data source connectors |
| SaaS subscriptions | ✅ | Trial management |
| Feature flags | ✅ | Plan-based gating |

## 10. Database & Infrastructure

| Feature | Status | Description |
|---------|--------|-------------|
| Alembic migrations | ✅ | Version-controlled schema changes |
| Production indexes | ✅ | 56 indexes across all major tables |
| Backup system | ✅ | BackupManager (MySQL + SQLite) |
| Recovery system | ✅ | CLI + API restore, recovery plan |
| Slow query logging | ✅ | Configurable threshold (default 500ms) |
| Query timeout | ✅ | Configurable (default 30s) |
| Connection pooling | ✅ | Production-tuned pool sizing |
| Multi-env config | ✅ | Development, testing, production |
| Database CLI | ✅ | init, migrate, backup, restore, status |
| Database API | ✅ | Super admin DB management routes |
| IndexManager | ✅ | Runtime index verification and creation |

## 11. CI/CD & DevOps

| Feature | Status | Description |
|---------|--------|-------------|
| 6-stage CI pipeline | ✅ | Lint → Security → Unit → Integration → Build → Deploy |
| PR checks workflow | ✅ | Fast feedback on pull requests |
| Build verification | ✅ | Backend, frontend, Docker build checks |
| Dependency check | ✅ | Weekly pip-audit + npm audit with auto-issues |
| Dependabot | ✅ | Weekly PRs for pip, npm, GitHub Actions |
| Docker build caching | ✅ | GHA cache backend |
| Security scanning | ✅ | pip-audit, Bandit, npm audit, Trivy (SARIF) |
| Vercel deployment | ✅ | Automated with health check |

## 13. Production Monitoring

| Feature | Status | Description |
|---------|--------|-------------|
| Sentry error tracking | ✅ | Exception capture, breadcrumbs, release tracking, data scrubbing |
| OpenTelemetry tracing | ✅ | Distributed spans for FastAPI, SQLAlchemy, Redis, logging |
| OTel custom metrics | ✅ | 7 application metrics (HTTP, DB, pipeline, errors, sessions) |
| Prometheus metrics | ✅ | 12 metrics in text exposition format, no external dependency |
| Prometheus /metrics endpoint | ✅ | Counters, histograms, gauges with path normalisation |
| Grafana dashboard | ✅ | 10-panel dashboard, auto-provisioned |
| Monitoring Docker stack | ✅ | Prometheus + Grafana + Node Exporter via docker-compose |
| Unified monitoring middleware | ✅ | Metrics + tracing + error capture + correlation IDs |
| Liveness probe | ✅ | /monitoring/health/live (process-only check) |
| Readiness probe | ✅ | /monitoring/health/ready (DB + Redis + integrations) |
| Detailed health check | ✅ | /monitoring/health/detailed (all subsystems) |
| Monitoring status endpoint | ✅ | /monitoring/status (Sentry/OTel/Prometheus enablement) |
| Structured JSON logging | ✅ | LOG_FORMAT=json with request_id and correlation_id |
| Correlation IDs | ✅ | X-Request-ID and X-Correlation-ID headers |
| Pipeline run metrics | ✅ | Pipeline success/failure recorded in Prometheus and OTel |

## 14. Documentation

| Feature | Status | Description |
|---------|--------|-------------|
| Architecture docs | ✅ | Overview, system design, diagrams, ADRs |
| Security docs | ✅ | Auth, authz, data protection, compliance |
| Database docs | ✅ | Schema, migrations, indexing, backup |
| API reference | ✅ | OpenAPI, authentication, examples |
| User guides | ✅ | Role-specific guides (8 roles) |
| Deployment docs | ✅ | Local, Docker, Vercel, production, CI/CD |
| Testing docs | ✅ | Strategy, unit, integration, e2e, security |
| ADR catalog | ✅ | 18 Architecture Decision Records |
| Product docs | ✅ | Vision, roadmap, personas, features |
| Workflow docs | ✅ | Onboarding, ETL, dashboards, capture |

## Related Documents

- [roadmap.md](roadmap.md) — Product roadmap
- [pricing-notes.md](pricing-notes.md) — Pricing model
- [industry-solutions.md](industry-solutions.md) — Industry solutions
