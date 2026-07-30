# Compliance Notes

> **Version**: 1.0.0  
> **Last Updated**: 2026-07-30  
> **Status**: Active  
> **Owner**: Security Architect

---

## Purpose

Document compliance readiness for common frameworks.

## Scope

SOC 2, ISO 27001, GDPR, HIPAA readiness assessment.

## Audience

Compliance officers, security auditors, and CTO.

---

## 1. Compliance Readiness Summary

| Framework | Readiness | Key Gaps |
|-----------|-----------|----------|
| SOC 2 Type I | 70% | IP capture in audit logs, data retention policy, access reviews |
| ISO 27001 | 65% | MFA, SSO, encryption at rest, incident management |
| GDPR | 60% | Data export, right-to-erasure, data processing agreements |
| HIPAA | 50% | BAA, encryption at rest, PHI handling, audit controls |

## 2. SOC 2 Readiness

### Security (CC1–CC9)

| Control | Status | Notes |
|--------|--------|-------|
| Logical access controls | ✅ | RBAC with 13 roles, 30+ permissions |
| User authentication | ✅ | JWT + bcrypt + session management |
| Access reviews | ⚠️ | No automated access review process |
| Audit logging | ✅ | AuditLog model with user, org, action, resource |
| Change management | ⚠️ | Documentation policy exists, no enforced workflow |
| Data retention | ⚠️ | No formal retention policy |
| Incident response | ⚠️ | Document needed (see [../operations/incident-response.md](../operations/incident-response.md)) |

### Availability (A1)

| Control | Status | Notes |
|--------|--------|-------|
| Backup and recovery | ✅ | Daily backup at 02:00 UTC |
| Disaster recovery | ⚠️ | Plan needed |
| Monitoring | ⚠️ | Basic health checks, no alerting |

### Processing Integrity (PI1)

| Control | Status | Notes |
|--------|--------|-------|
| Data validation | ✅ | Pydantic schemas on all inputs |
| Error handling | ✅ | Centralized exception handlers |

### Confidentiality (C1)

| Control | Status | Notes |
|--------|--------|-------|
| Encryption in transit | ✅ | HTTPS enforced |
| Encryption at rest | ⚠️ | Not yet implemented |
| Tenant isolation | ✅ | Org-scoped queries + access checks |

### Privacy (P1–P8)

| Control | Status | Notes |
|--------|--------|-------|
| Data inventory | ⚠️ | No formal data inventory |
| Consent management | ⚠️ | Not implemented |
| Data subject rights | ⚠️ | No export/erasure workflow |

## 3. ISO 27001 Readiness

| Control Area | Status | Key Gaps |
|-------------|--------|----------|
| Access control | ✅ | RBAC, JWT, session management |
| Cryptography | ⚠️ | No encryption at rest, no MFA |
| Operations security | ✅ | Rate limiting, security headers |
| Communications security | ✅ | HTTPS, CORS |
| System acquisition | ✅ | Dependency management via pip/npm |
| Supplier relationships | ⚠️ | No vendor risk assessment |
| Incident management | ⚠️ | Process needed |
| Business continuity | ⚠️ | DR plan needed |

## 4. GDPR Readiness

| Requirement | Status | Notes |
|-------------|--------|-------|
| Lawful basis | ⚠️ | Terms of service reference needed |
| Data subject access | ⚠️ | No export workflow |
| Right to erasure | ⚠️ | Soft delete exists, no user-initiated erasure |
| Data portability | ⚠️ | No data export API |
| Privacy by design | ✅ | Org isolation, minimal data collection |
| Breach notification | ⚠️ | Process needed |
| Data processing records | ⚠️ | Audit logs exist, no formal DPA |

## 5. HIPAA Readiness

> **⚠️ Note**: HIPAA compliance requires additional infrastructure and legal agreements.

| Requirement | Status | Notes |
|-------------|--------|-------|
| Access control | ✅ | RBAC, unique user IDs |
| Audit controls | ✅ | AuditLog model |
| Integrity controls | ✅ | Data validation |
| Transmission security | ✅ | HTTPS |
| Encryption at rest | ⚠️ | Not implemented |
| BAA | ❌ | Business Associate Agreement needed |
| PHI handling | ⚠️ | No specific PHI safeguards |

## 6. Recommendations

### Short-term (3 months)
1. Implement IP address capture in audit logs
2. Create data retention policy
3. Implement user data export (GDPR)
4. Implement user-initiated account deletion (GDPR)
5. Document incident response procedure

### Medium-term (6 months)
1. Implement MFA for super_admin
2. Add encryption at rest (PostgreSQL TDE)
3. Create disaster recovery plan
4. Implement access review workflow
5. Add breach notification process

### Long-term (12 months)
1. Achieve SOC 2 Type II
2. Implement SSO (SAML/OIDC)
3. HIPAA compliance (if serving healthcare)
4. ISO 27001 certification

## Related Documents

- [security-model.md](security-model.md) — Security architecture
- [audit-logging.md](audit-logging.md) — Audit logging
- [../operations/incident-response.md](../operations/incident-response.md) — Incident response
- [../operations/disaster-recovery.md](../operations/disaster-recovery.md) — Disaster recovery
