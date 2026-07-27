# Security Architecture — DataFlow Enterprise Platform

**Version:** 1.0  
**Last updated:** 2026-07-27

---

## 1. Security Model Overview

DataFlow uses a **defense-in-depth** architecture with multiple layers of protection:

```
┌─────────────────────────────────────────────┐
│  Perimeter: TLS, CORS, WAF, Security Headers │
├─────────────────────────────────────────────┤
│  Authentication: JWT access + refresh tokens   │
├─────────────────────────────────────────────┤
│  Authorization: RBAC + organization scope    │
├─────────────────────────────────────────────┤
│  Application: Input validation, audit logs   │
├─────────────────────────────────────────────┤
│  Data: SQLAlchemy ORM, tenant isolation        │
├─────────────────────────────────────────────┤
│  Infrastructure: Secrets, encrypted backups    │
└─────────────────────────────────────────────┘
```

---

## 2. Authentication

### 2.1 JWT tokens

- **Access tokens** are short-lived (default 30 minutes) and contain:
  - `sub`: user id
  - `email`, `roles`, `permissions`, `org_id`
  - `exp`, `iat`, `jti`, `type`
- **Refresh tokens** are long-lived and stored in the `sessions` table with revocation support.
- Tokens are signed with `HS256` and a strong `JWT_SECRET_KEY`.

### 2.2 Password policy

- Argon2id password hashing with bcrypt fallback.
- Configurable minimum length, uppercase, lowercase, digit, and special-character requirements.
- Failed-login lockout after repeated attempts.

### 2.3 API keys

- A single service-level `API_KEY` is supported for machine-to-machine access.
- In production (`DB_TYPE=mysql`), the default development key is rejected.

---

## 3. Authorization

### 3.1 Role-based access control

Roles are stored in the `roles` table and linked to users through `user_roles`. Permissions are grouped by module (e.g., `datasets`, `dashboards`, `users`).

### 3.2 Organization isolation

Every authenticated request resolves to an `organization_id`. Resources must include an `organization_id` column, and queries use the helpers in `shared/tenant.py` to enforce scoping.

### 3.3 Permission dependencies

- `require_permissions("datasets.read", "datasets.write")` — user must hold at least one permission.
- `require_any_role("organization_admin", "analyst")` — user must hold at least one role.
- `super_admin` bypasses all permission checks.

---

## 4. API Security

| Control | Implementation |
| :--- | :--- |
| HTTPS/TLS | Enforced by Vercel; HSTS header added |
| CORS | Origin allow-list via `CORS_ORIGINS` env var |
| Security headers | CSP, HSTS, X-Frame-Options, etc. (`shared/middleware.py`) |
| Rate limiting | Per-IP in-memory sliding window; Redis/Vercel KV recommended for multi-instance |
| Request size | `RequestSizeLimitMiddleware` rejects oversized bodies |
| Error handling | Generic 500 messages; stack traces logged server-side |

---

## 5. Audit & Observability

- `AuditLog` records user actions with IP, user-agent, and request id.
- `SecurityLog` records authentication failures and suspicious events.
- `LoginHistory` tracks every login attempt.
- Request ids and correlation ids are generated for tracing.

---

## 6. Secrets Management

Secrets are loaded from environment variables. In production, use a dedicated secret manager and rotate:

- `JWT_SECRET_KEY`
- `API_KEY`
- Database credentials (`MYSQL_*`)
- AI provider API keys (`OPENAI_API_KEY`, etc.)

---

## 7. Deployment Security

- Serverless functions run on Vercel with read-only filesystems.
- Heavy Python dependencies increase the attack surface; review `pyproject.toml` regularly.
- SSO deployment protection is enabled in production.

---

## 8. OWASP Coverage

| OWASP Risk | Mitigation |
| :--- | :--- |
| Broken Access Control | JWT validation, RBAC, tenant isolation |
| Cryptographic Failures | Argon2, strong JWT secret, TLS |
| Injection | Pydantic validation, ORM, input sanitization |
| Insecure Design | Org-scoped repositories, audit logs |
| Security Misconfiguration | `validate_config()`, strict CORS |
| Vulnerable Components | Pinned dependencies, regular updates |
| Identity/Auth Failures | Lockout, token expiry, session revocation |
| Software/Data Integrity | File validation, malware scanning planned |
| Security Logging Failures | Centralized audit service |
| SSRF | Connector allow-list planned |
