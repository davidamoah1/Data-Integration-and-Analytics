# Version History

> **Version**: 1.0.0  
> **Last Updated**: 2026-07-30  
> **Status**: Active  
> **Owner**: DevOps Engineer

---

## Purpose

Chronological version history with release dates and highlights.

## Scope

All released versions.

## Audience

All stakeholders.

---

## Version History

| Version | Date | Type | Highlights |
|---------|------|------|-----------|
| 1.0.0 | 2026-07-30 | Major | Initial enterprise release |

## 1.0.0 — 2026-07-30 (Initial Enterprise Release)

### Major Features

- Multi-tenant FastAPI backend with PostgreSQL
- Next.js 14 frontend with App Router, Tailwind CSS, Zustand
- JWT authentication with access + refresh tokens
- 13 system roles, 30+ permissions, custom role creation
- Three-mode registration (create org, join org, personal)
- Invitation-based user onboarding with 7-day expiry
- Organization, department, and workspace management
- Three-layer tenant isolation enforcement
- Audit logging (AuditLog, SecurityLog, SystemLog, UserActivity)
- Analytics Studio with dashboards and KPIs
- ETL engine with pipeline management
- AI analytics assistant and AI report generation
- ML model management and predictions
- Smart Data Capture with OCR and confidence scoring
- Industry studios: Healthcare, Education, Business, Research, Automation
- Ecosystem: plugins, webhooks, marketplace (placeholder)
- SaaS: subscription management, tenant suspend/activate
- Connectors: database connectors, CSV/Excel file imports
- APScheduler for background jobs
- PWA with offline support
- Security: headers, rate limiting, request size limit, tenant middleware
- Enterprise documentation system with ADR library

### Security Highlights

- RBAC on all API endpoints
- bcrypt password hashing
- Account lockout after failed attempts
- Password history (prevent reuse)
- Session revocation
- Security headers (CSP, HSTS, X-Frame-Options)
- Rate limiting (120 RPM)
- Cross-tenant access logging

### Known Limitations

- No Alembic migrations
- No caching layer
- No MFA / SSO
- No email service
- No API key authentication
- No encryption at rest
- localStorage token storage
- Scheduler disabled on serverless

## Related Documents

- [CHANGELOG.md](CHANGELOG.md) — Detailed changelog
- [release-process.md](release-process.md) — Release process
- [../product/roadmap.md](../product/roadmap.md) — Product roadmap
