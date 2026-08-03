# Compliance Mapping

> **Version**: 1.0.0  
> **Last Updated**: 2026-08-01  
> **Status**: Active  
> **Owner**: Compliance Officer

---

## Purpose

Map platform security controls to common compliance frameworks.

## Scope

SOC 2, ISO 27001, GDPR, and HIPAA compliance readiness.

## Audience

Compliance officers, security architects, auditors, and legal counsel.

---

## 1. SOC 2 Type II

### Security (Common Criteria)

| Control | Implementation | Status |
|---------|---------------|--------|
| CC6.1 — Logical access | RBAC, JWT auth, permission middleware | ✅ Implemented |
| CC6.2 — User auth | bcrypt, MFA (TOTP), account lockout | ✅ Implemented |
| CC6.3 — Access restrictions | Org-scoped queries, tenant isolation | ✅ Implemented |
| CC7.1 — System monitoring | Audit logs, security logs, health checks | ✅ Implemented |
| CC7.2 — Anomaly detection | Rate limiting, account lockout, cross-tenant logging | ✅ Implemented |
| CC7.3 — Incident response | Vulnerability management process | ✅ Documented |
| CC8.1 — Change management | CI/CD pipeline, branch protection, PR reviews | ✅ Implemented |

### Availability

| Control | Implementation | Status |
|---------|---------------|--------|
| A1.1 — Capacity planning | Docker resource limits, connection pooling | ✅ Implemented |
| A1.2 — Environmental protections | Docker container isolation, non-root user | ✅ Implemented |
| A1.3 — Backup and recovery | Backup manager, recovery plan, retention | ✅ Implemented |

### Confidentiality

| Control | Implementation | Status |
|---------|---------------|--------|
| C1.1 — Data classification | PII handling policy, encrypted fields | ✅ Implemented |
| C1.2 — Data disposal | Soft deletes, retention policies, backup cleanup | ✅ Implemented |

### Processing Integrity

| Control | Implementation | Status |
|---------|---------------|--------|
| PI1.1 — Input validation | Pydantic schema validation on all endpoints | ✅ Implemented |
| PI1.2 — Processing monitoring | ETL pipeline run tracking, error logging | ✅ Implemented |

### Privacy

| Control | Implementation | Status |
|---------|---------------|--------|
| P2.1 — Consent | Email verification, terms acceptance | ✅ Implemented |
| P3.1 — Data retention | Configurable retention policies | ✅ Implemented |
| P4.1 — Data access | User can view, export, delete their data | ✅ Implemented |
| P5.1 — Incident notification | Vulnerability management process | ⚠️ Partial |

## 2. ISO 27001

### Annex A Controls

| Control | Implementation | Status |
|---------|---------------|--------|
| A.5.1 — Information security policy | This documentation suite | ✅ Documented |
| A.6.1 — Organization of security | Security Architect role | ✅ Defined |
| A.8.2 — Privileged access | Super admin role, audit-logged | ✅ Implemented |
| A.8.3 — Access restriction | RBAC, tenant isolation | ✅ Implemented |
| A.9.1 — Secure areas | Docker isolation, non-root container | ✅ Implemented |
| A.10.1 — Cryptography | AES-256 at rest, TLS in transit | ✅ Implemented |
| A.12.1 — Operational procedures | Operations manual, runbooks | ✅ Documented |
| A.12.4 — Logging | Audit logs, security logs, application logs | ✅ Implemented |
| A.12.6 — Vulnerability management | pip-audit, npm audit, Bandit, Trivy, Dependabot | ✅ Implemented |
| A.12.7 — Secure development | CI/CD pipeline, SAST, code reviews | ✅ Implemented |
| A.14.2 — Secure engineering | Input validation, ORM, security headers | ✅ Implemented |
| A.16.1 — Incident management | Incident response process | ✅ Documented |
| A.17.1 — Business continuity | Backup and recovery plan | ✅ Documented |

## 3. GDPR

| Article | Requirement | Implementation | Status |
|---------|------------|---------------|--------|
| Art. 6 | Lawful basis | Consent on registration | ✅ Implemented |
| Art. 7 | Consent withdrawal | Account deactivation | ✅ Implemented |
| Art. 12 | Transparent info | Privacy policy (planned) | ⚠️ Partial |
| Art. 15 | Right of access | `/auth/me` endpoint, data export | ✅ Implemented |
| Art. 16 | Right to rectification | Profile update endpoints | ✅ Implemented |
| Art. 17 | Right to erasure | Soft delete + manual purge | ✅ Implemented |
| Art. 20 | Right to portability | Data export (planned) | ⚠️ Partial |
| Art. 25 | Privacy by design | Encryption at rest, PII handling | ✅ Implemented |
| Art. 30 | Records of processing | Audit logs | ✅ Implemented |
| Art. 32 | Security of processing | Encryption, RBAC, rate limiting | ✅ Implemented |
| Art. 33 | Breach notification | Incident response process | ⚠️ Partial |
| Art. 35 | DPIA | Not yet performed | ❌ Not started |

## 4. HIPAA

| Requirement | Implementation | Status |
|-------------|---------------|--------|
| Access control (§164.312(a)(1)) | RBAC, JWT, unique user IDs | ✅ Implemented |
| Audit controls (§164.312(b)) | Audit logs, security logs | ✅ Implemented |
| Integrity (§164.312(c)(1)) | Soft deletes, audit trail | ✅ Implemented |
| Person/entity auth (§164.312(d)) | JWT authentication, MFA | ✅ Implemented |
| Transmission security (§164.312(e)(1)) | TLS, HTTPS enforcement (HSTS) | ✅ Implemented |
| Encryption at rest (§164.312(a)(2)(iv)) | AES-256 field-level encryption | ✅ Implemented |
| Business associate agreements | Not yet established | ❌ Not started |

### HIPAA Limitations

The platform is not currently HIPAA-certified. Organizations using the platform for Protected Health Information (PHI) must:
1. Sign a Business Associate Agreement (BAA)
2. Configure production environment with MySQL + TLS
3. Enable encryption at rest with a managed key
4. Configure audit log retention for 6 years minimum
5. Implement data retention policies per organizational requirements

## 5. Compliance Gaps

| Gap | Framework | Priority | Plan |
|-----|-----------|----------|------|
| Privacy policy not written | GDPR | High | Draft privacy policy |
| DPIA not performed | GDPR | Medium | Conduct DPIA for data processing |
| Data export endpoint | GDPR | Medium | Implement `/auth/export-data` |
| BAA template | HIPAA | Low | Legal counsel required |
| Breach notification process | GDPR/HIPAA | Medium | Document notification timeline |
| Penetration testing | SOC 2 | Medium | Schedule annual pentest |

## Related Documents

- [overview.md](overview.md) — Security architecture overview
- [data-protection.md](data-protection.md) — Data protection details
- [vulnerability-management.md](vulnerability-management.md) — Vulnerability management
- [../governance/compliance-notes.md](../governance/compliance-notes.md) — Compliance notes
