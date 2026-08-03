# Security Documentation

> **Version**: 1.0.0  
> **Last Updated**: 2026-08-01  
> **Status**: Active  
> **Owner**: Security Architect

---

## Purpose

Comprehensive security documentation covering authentication, authorization, data protection, compliance, and operational security for the AEDIP platform.

## Scope

All security-related aspects: identity management, access control, encryption, tenant isolation, audit logging, vulnerability management, and compliance readiness.

## Audience

Security architects, compliance officers, DevOps engineers, and auditors.

---

## Document Index

| Document | Description |
|----------|-------------|
| [overview.md](overview.md) | Security architecture overview and defense-in-depth strategy |
| [authentication.md](authentication.md) | Authentication mechanisms: JWT, password hashing, MFA, session management |
| [authorization.md](authorization.md) | RBAC model, permission enforcement, tenant isolation |
| [data-protection.md](data-protection.md) | Encryption at rest, data retention, PII handling, soft deletes |
| [api-security.md](api-security.md) | API security: CORS, rate limiting, security headers, input validation |
| [vulnerability-management.md](vulnerability-management.md) | Dependency scanning, SAST, security patching, incident response |
| [compliance.md](compliance.md) | SOC 2, ISO 27001, GDPR, HIPAA compliance mapping |
| [checklist.md](checklist.md) | Production security hardening checklist |

## Related Documents

- [../governance/security-model.md](../governance/security-model.md) — Security model summary
- [../governance/authorization.md](../governance/authorization.md) — Authorization enforcement
- [../governance/compliance-notes.md](../governance/compliance-notes.md) — Compliance readiness notes
- [../testing/security-tests.md](../testing/security-tests.md) — Security testing guide
- [../architecture/adr/README.md](../architecture/adr/README.md) — Security-related ADRs
