# Changelog

> **Version**: 1.0.0  
> **Last Updated**: 2026-07-30  
> **Status**: Active  
> **Owner**: DevOps Engineer

---

## Purpose

Chronological changelog of all releases.

## Scope

All versions and their changes.

## Audience

All stakeholders.

---

## [1.0.0] — 2026-07-30

### Added

- **Core Platform**: FastAPI backend with PostgreSQL, SQLAlchemy ORM
- **Authentication**: JWT-based auth with access + refresh tokens, bcrypt password hashing, account lockout, password history
- **Registration**: Three-mode signup (create organization, join via invitation, personal workspace)
- **Multi-Tenant Architecture**: Organization-scoped data isolation with three-layer enforcement
- **RBAC**: 13 system roles, 30+ permissions, custom role creation
- **Invitation System**: Email + token-based invitations with 7-day expiry
- **Organization Management**: Organizations, departments, workspaces
- **Audit Logging**: AuditLog, SecurityLog, SystemLog, UserActivity models
- **Analytics Studio**: Dashboards, KPIs, visualizations
- **ETL Engine**: Pipeline creation, execution, run history
- **AI Assistant**: Conversational analytics, AI report generation
- **ML Models**: Model management, training, predictions
- **Smart Data Capture**: Document upload, OCR, field extraction, confidence scoring
- **Industry Studios**: Healthcare, Education, Business, Research, Automation
- **Ecosystem**: Plugins, webhooks, marketplace (placeholder)
- **SaaS**: Subscription management, tenant suspend/activate, feature flags
- **Connectors**: Database connectors, file imports (CSV, Excel)
- **Scheduler**: APScheduler for background jobs and report scheduling
- **Frontend**: Next.js 14 App Router, React 18, TypeScript, Tailwind CSS, Zustand
- **Design System**: Light/dark/system themes, responsive layout
- **Navigation**: Permission-filtered sidebar, route guards, Can component
- **PWA**: Progressive Web App with offline support via Workbox
- **Security**: Security headers middleware, rate limiting, request size limit, tenant isolation middleware
- **Documentation**: Enterprise documentation system with 15 sections, ADR library, style guide, maintenance policy

### Security

- RBAC enforcement on all API endpoints
- Organization-scoped data access
- Super admin bypass (intentional, audit-logged)
- Platform role protection (cannot be invited)
- bcrypt password hashing
- JWT token expiration
- Session revocation
- Security headers (CSP, HSTS, X-Frame-Options, X-Content-Type-Options)
- Rate limiting (120 RPM default)
- Request body size limit (50MB)
- Cross-tenant access logging

### Known Limitations

- No Alembic migrations (code-first schema only)
- No caching layer (Redis planned)
- No MFA
- No SSO (SAML/OIDC planned)
- No email service for invitations
- No API key authentication
- No encryption at rest
- localStorage token storage (XSS risk)
- Background scheduler disabled on serverless

## Related Documents

- [release-process.md](release-process.md) — Release process
- [version-history.md](version-history.md) — Version history
- [../product/roadmap.md](../product/roadmap.md) — Product roadmap
