# Security Tests

> **Version**: 1.0.0  
> **Last Updated**: 2026-07-30  
> **Status**: Active  
> **Owner**: Security Architect

---

## Purpose

Security testing checklist and approach.

## Scope

All security tests: authentication, authorization, tenant isolation, input validation.

## Audience

Security architects and QA engineers.

---

## 1. Security Test Areas

### Authentication

- [ ] Login with valid credentials succeeds
- [ ] Login with invalid password fails (401)
- [ ] Account lockout after max failed attempts
- [ ] JWT token expires correctly
- [ ] Refresh token works
- [ ] Revoked sessions rejected
- [ ] Password reset flow works
- [ ] Password history enforced

### Authorization (RBAC)

- [ ] Each role has correct permissions
- [ ] Permission denied returns 403
- [ ] Super admin bypass works
- [ ] Non-super-admin cannot assign super_admin role
- [ ] Platform roles cannot be invited
- [ ] Role hierarchy prevents privilege escalation

### Tenant Isolation

- [ ] Non-super-admin cannot access other org's users
- [ ] Non-super-admin cannot access other org's data
- [ ] Non-super-admin cannot update other org's settings
- [ ] Non-super-admin cannot delete other org's resources
- [ ] Super admin can access all orgs
- [ ] Cross-tenant access logged by middleware

### Input Validation

- [ ] SQL injection prevention (SQLAlchemy parameterized queries)
- [ ] XSS prevention (React auto-escaping)
- [ ] File upload validation (type, size)
- [ ] Request body size limit enforced
- [ ] Rate limiting active

### Session Management

- [ ] Session revocation works
- [ ] Expired sessions rejected
- [ ] Logout clears tokens
- [ ] Concurrent session limit (if configured)

## 2. Security Audit History

| Audit | Date | Findings | Status |
|-------|------|----------|--------|
| Phase 24 Security Audit | 2026-07-30 | Critical and high issues found | ✅ Fixed |
| Ongoing | — | Periodic review needed | ⚠️ Scheduled |

## 3. Security Headers Verification

- [ ] Content-Security-Policy header present
- [ ] X-Content-Type-Options: nosniff
- [ ] X-Frame-Options: DENY
- [ ] Strict-Transport-Security (HSTS)
- [ ] X-XSS-Protection

## 4. Planned Automated Security Tests

> **⚠️ Planned**: The following are not yet automated.

- OWASP ZAP scan
- Dependency vulnerability scan (pip-audit, npm audit)
- SAST (Static Application Security Testing)
- DAST (Dynamic Application Security Testing)

## Related Documents

- [../governance/security-model.md](../governance/security-model.md) — Security model
- [../governance/authorization.md](../governance/authorization.md) — Authorization
- [../governance/compliance-notes.md](../governance/compliance-notes.md) — Compliance
- [strategy.md](strategy.md) — Testing strategy
