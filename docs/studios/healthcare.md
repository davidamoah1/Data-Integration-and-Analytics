# Healthcare Studio

> **Version**: 1.0.0  
> **Last Updated**: 2026-07-30  
> **Status**: Active  
> **Owner**: Product Manager

---

## Purpose

Document the Healthcare Studio for healthcare analytics.

## Scope

Healthcare-specific features, compliance considerations, and data types.

## Audience

Healthcare analysts, product managers, and compliance officers.

---

## 1. Overview

The Healthcare Studio provides industry-specific analytics for healthcare organizations, including patient analytics, treatment outcomes, and compliance reporting.

## 2. Use Cases

- Patient outcome analysis
- Treatment efficacy tracking
- Readmission rate analysis
- Resource utilization
- Compliance reporting (HIPAA considerations)

## 3. Data Types

- Patient records (de-identified)
- Treatment histories
- Lab results
- Resource utilization data
- Outcome metrics

## 4. Compliance

> **⚠️ Note**: Healthcare data requires HIPAA compliance. See [../governance/compliance-notes.md](../governance/compliance-notes.md).

- Encryption at rest: Required (not yet implemented)
- BAA: Required for covered entities
- PHI handling: Must follow HIPAA safeguards
- Audit logging: All access to healthcare data must be logged

## 5. Access

- Route: `/studios` → Healthcare card
- Permission: `dashboard.view` (minimum)
- Org-scoped: All data isolated by organization

## Related Documents

- [../governance/compliance-notes.md](../governance/compliance-notes.md) — HIPAA compliance
- [../governance/security-model.md](../governance/security-model.md) — Security model
- [../product/industry-solutions.md](../product/industry-solutions.md) — Industry solutions
