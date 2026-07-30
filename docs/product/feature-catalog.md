# Feature Catalog

> **Version**: 1.0.0  
> **Last Updated**: 2026-07-30  
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
| MFA | ⚠️ Planned | TOTP-based |
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
| Compliance reporting | ⚠️ Planned | SOC 2, ISO 27001 |

## 9. Platform & Ecosystem

| Feature | Status | Description |
|---------|--------|-------------|
| Plugin system | ✅ | Extensible architecture |
| Webhooks | ✅ | Outbound events |
| Marketplace | ✅ Placeholder | Extension marketplace |
| Connectors | ✅ | Data source connectors |
| SaaS subscriptions | ✅ | Trial management |
| Feature flags | ✅ | Plan-based gating |

## Related Documents

- [roadmap.md](roadmap.md) — Product roadmap
- [pricing-notes.md](pricing-notes.md) — Pricing model
- [industry-solutions.md](industry-solutions.md) — Industry solutions
