# Architecture Decision Records (ADR) Index

> **Version**: 1.0.0  
> **Last Updated**: 2026-07-30  
> **Status**: Active  
> **Owner**: Enterprise Architecture Board

---

## Purpose

Index of all Architecture Decision Records. ADRs capture important architectural decisions, their context, and consequences.

## Scope

All architectural decisions made during the platform's development.

## Audience

All developers, architects, and technical stakeholders.

---

## ADR Catalog

| ADR | Title | Status | Date |
|-----|-------|--------|------|
| [ADR-0001](../../governance/adr/ADR-0001-enterprise-multi-tenant-architecture.md) | Enterprise Multi-Tenant Architecture | Accepted | 2026-07-30 |
| [ADR-0002](../../governance/adr/ADR-0002-blank-workspace-by-default.md) | Blank Workspace by Default | Accepted | 2026-07-30 |
| [ADR-0003](../../governance/adr/ADR-0003-optional-sample-workspace.md) | Optional Sample Workspace | Accepted | 2026-07-30 |
| [ADR-0004](../../governance/adr/ADR-0004-invitation-based-user-onboarding.md) | Invitation-Based User Onboarding | Accepted | 2026-07-30 |
| [ADR-0005](../../governance/adr/ADR-0005-role-based-access-control.md) | Role-Based Access Control | Accepted | 2026-07-30 |
| [ADR-0006](../../governance/adr/ADR-0006-platform-owner-vs-organization-administrator.md) | Platform Owner vs Organization Administrator | Accepted | 2026-07-30 |
| [ADR-0007](../../governance/adr/ADR-0007-department-based-data-governance.md) | Department-Based Data Governance | Accepted | 2026-07-30 |
| [ADR-0008](../../governance/adr/ADR-0008-permission-middleware.md) | Permission Middleware | Accepted | 2026-07-30 |
| [ADR-0009](../../governance/adr/ADR-0009-workspace-model.md) | Workspace Model | Accepted | 2026-07-30 |
| [ADR-0010](../../governance/adr/ADR-0010-audit-logging.md) | Audit Logging | Accepted | 2026-07-30 |
| [ADR-0011](../../governance/adr/ADR-0011-template-architecture.md) | Template Architecture | Accepted | 2026-07-30 |
| [ADR-0012](../../governance/adr/ADR-0012-future-enterprise-readiness.md) | Future Enterprise Readiness | Proposed | 2026-07-30 |
| [ADR-0013](../../governance/adr/ADR-0013-multi-environment-database-configuration.md) | Multi-Environment Database Configuration | Accepted | 2026-08-01 |
| [ADR-0014](../../governance/adr/ADR-0014-production-database-hardening.md) | Production Database Hardening | Accepted | 2026-08-01 |
| [ADR-0015](../../governance/adr/ADR-0015-slow-query-logging.md) | Slow Query Logging and Query Optimization | Accepted | 2026-08-01 |
| [ADR-0016](../../governance/adr/ADR-0016-cicd-pipeline-architecture.md) | CI/CD Pipeline Architecture | Accepted | 2026-08-01 |
| [ADR-0017](../../governance/adr/ADR-0017-backup-and-recovery-strategy.md) | Backup and Recovery Strategy | Accepted | 2026-08-01 |
| [ADR-0018](../../governance/adr/ADR-0018-production-monitoring-architecture.md) | Production Monitoring Architecture | Accepted | 2026-08-01 |

---

## ADR Template

New ADRs should follow this structure:

```markdown
# ADR-XXXX: Title

| Field | Value |
|-------|-------|
| **Status** | Proposed | Accepted | Deprecated | Superseded |
| **Date** | YYYY-MM-DD |
| **Decision Maker** | Enterprise Architecture Board |
| **Related ADRs** | ADR-XXXX |

## Context
Why is this decision needed?

## Decision
What was decided?

## Alternatives Considered
What other options were evaluated?

## Consequences
What are the positive and negative impacts?

## Implementation Notes
How was it implemented?

## Future Considerations
What may change in the future?
```

## ADR Rules

1. ADRs are numbered sequentially (ADR-0001, ADR-0002, ...)
2. Accepted ADRs are immutable — if a decision changes, create a new ADR that supersedes the old one
3. Update the old ADR's status to "Superseded by ADR-XXXX"
4. ADRs are stored in `docs/governance/adr/` (canonical location)
5. This index in `docs/architecture/adr/` links to the canonical location

## Related Documents

- [overview.md](../overview.md) — Architecture overview
- [../../governance/README.md](../../governance/README.md) — Governance documentation index
