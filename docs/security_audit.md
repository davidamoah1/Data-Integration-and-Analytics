# Security Audit Report — DataFlow Enterprise Platform

**Repository:** `davidamoah1/Data-Integration-and-Analytics`  
**Audit Date:** 2026-07-27  
**Auditor:** Principal Enterprise Architect / Cybersecurity Engineer  
**Scope:** FastAPI backend, Next.js frontend, database layer, deployment configuration, secrets management.

---

## Executive Summary

The platform already contains a substantial identity-and-access foundation: JWT-based authentication, Argon2 password hashing, role/permission models, session tracking, login-history, audit-log tables, and `organization_id` columns on most resources. However, several routes bypass authentication and organization isolation entirely, and a number of defense-in-depth controls are missing or ineffective in the current serverless deployment. The items marked **CRITICAL** and **HIGH** must be remediated before the platform can safely host multi-tenant data for healthcare, finance, government, or other regulated industries.

| Severity | Count | Categories |
| :--- | :--- | :--- |
| **Critical** | 3 | Unauthenticated data-processing endpoints, missing org isolation on uploads, SSRF/data-exfiltration via connectors |
| **High** | 6 | In-memory rate limiting, missing request size limits, no malware scanning, weak AI prompt injection controls, missing CSP/HSTS, global API key |
| **Medium** | 7 | Email verification, default dev API key, password history not enforced, audit gaps, missing row-level security, CORS defaults, verbose errors |
| **Low** | 4 | Information disclosure in health endpoint, hardcoded defaults, signup role assignment, missing account lockout notifications |

---

## 1. Authentication

### 1.1 JWT implementation

**Status:** Generally sound, with gaps.

- Tokens are signed with HS256 and a configurable `JWT_SECRET_KEY`.
- `iat`, `exp`, `type` (access/refresh), and `jti` claims are present.
- Refresh tokens are persisted in `UserSession` with revocation support.
- Access tokens embed `roles`, `permissions`, and `org_id`.

**Findings:**

- **HIGH** The same secret is used for both access and refresh tokens. Compromising one key compromises both token types.
- **MEDIUM** No explicit token binding to IP, device fingerprint, or `aud` claim. Stolen tokens are fully portable.
- **MEDIUM** Token refresh does not rotate the refresh token or update its `jti`. A leaked refresh token remains valid until expiry.
- **MEDIUM** `get_current_user` performs a database lookup on every authenticated request, which is correct, but the function only checks `is_active`; it does not verify `email_verified_at`.

**Affected files:**

- `shared/security.py` — token creation and decoding
- `shared/dependencies.py` — `get_current_user`
- `authentication/services.py` — `refresh_tokens`

### 1.2 Password handling

**Status:** Good baseline.

- Argon2id is the primary hashing scheme with bcrypt fallback (`shared/security.py`).
- Password policy is configurable via environment variables and enforced on signup/change.

**Findings:**

- **MEDIUM** `PASSWORD_HISTORY_COUNT` is configured but no code path actually rejects reused passwords during password changes.
- **LOW** Default minimum length is 8 characters; for regulated industries 12+ is recommended.
- **LOW** No breached-password checking (e.g., Have I Been Pwned).

**Affected files:**

- `shared/security.py`
- `authentication/services.py`

### 1.3 Session management

**Status:** Adequate but improvable.

- Login history records IP and user-agent.
- Failed-login counter and lockout exist.
- Sessions can be revoked.

**Findings:**

- **MEDIUM** Lockout state (`locked_until`) is set by `increment_failed_login`, but the increment/lock logic is not atomic and is vulnerable to race conditions under concurrent requests.
- **LOW** No notification to the user or admin when an account is locked.
- **LOW** No maximum session lifetime or absolute timeout for refresh tokens.

**Affected files:**

- `authentication/services.py` — `login`
- `authentication/repositories.py` — `UserRepository`

---

## 2. Authorization

### 2.1 RBAC foundation

**Status:** Present and functional.

- Models: `User`, `Role`, `Permission`, `RolePermission`, `UserRole`.
- Dependencies: `require_permissions(...)`, `require_any_role(...)`.
- Super admin bypass is implemented.
- Routes under `authentication/routes.py` use permission checks (e.g., `users.manage`, `roles.manage`).

**Findings:**

- **CRITICAL** Several high-risk routes do **not** use `get_current_user` or `require_permissions`. Any anonymous user can upload files, run ETL/validation/semantic workflows, and trigger data pipelines:
  - `validation/routes.py::run_validation` — no auth, no org isolation
  - `semantic/routes.py::analyze_upload`, `analyze_with_overrides`, `detect_industry` — no auth, no org isolation
  - `services/dataset_workflow_routes.py::run_workflow` — no auth, no org isolation
  - `etl/routes.py::upload_file` requires auth but does not enforce organization ownership of the resulting data.
- **CRITICAL** Even after auth is added, no repository-level organization filtering guarantees that a user cannot access another organization's resources.
- **HIGH** `organizations/services.py` organization endpoints allow any authenticated user to `list_organizations`, `get_organization`, and `list_departments` without verifying membership in the requested organization.

**Affected files:**

- `validation/routes.py`
- `semantic/routes.py`
- `services/dataset_workflow_routes.py`
- `etl/routes.py`
- `organizations/services.py`
- `shared/dependencies.py`

### 2.2 API key authentication

**Status:** Functional but not tenant-aware.

- `api/auth.py` validates a single global `API_KEY` against `X-API-Key` header or `?api_key` query parameter.

**Findings:**

- **HIGH** One global key for all tenants. Compromise exposes every organization.
- **MEDIUM** Accepting the key in the query string risks leakage in access logs and browser history.
- **LOW** Default dev key `dev-api-key-change-in-production` is rejected when `DB_TYPE=mysql`, but local/dev configs may still use it.

**Affected files:**

- `api/auth.py`
- `config.py`

---

## 3. API Security

### 3.1 Rate limiting

**Status:** Implemented but unsuitable for serverless.

- `RateLimitMiddleware` uses an in-memory `defaultdict(list)` keyed by client IP.

**Findings:**

- **HIGH** In-memory counters do not persist across Vercel function invocations. An attacker can distribute requests across many cold starts and effectively bypass rate limiting.
- **HIGH** Rate limiting is disabled in test mode (`PYTEST_RUNNING`) but there is no Redis/external backend for production.
- **MEDIUM** Health/readiness endpoints are exempt, which is correct, but there is no separate stricter limit for authentication endpoints.

**Affected files:**

- `shared/middleware.py`
- `api/main.py`

### 3.2 CORS

**Status:** Configurable but permissive defaults.

- `CORS_ORIGINS` is read from environment; default is `http://localhost:8501,http://localhost:3000`.
- Credentials are allowed.

**Findings:**

- **MEDIUM** If `CORS_ORIGINS` is accidentally set to `*`, `validate_config()` rejects it, but a missing value silently falls back to localhost. Production deployments must explicitly set allowed origins.
- **LOW** `allow_methods` includes `DELETE`; ensure destructive operations are also protected by auth/CSRF-safe patterns.

**Affected files:**

- `api/main.py`
- `config.py`

### 3.3 Security headers

**Status:** Partial.

- `SecurityHeadersMiddleware` sets `X-Content-Type-Options`, `X-Frame-Options`, `X-XSS-Protection`, `Referrer-Policy`, and `Permissions-Policy`.

**Findings:**

- **HIGH** Missing `Content-Security-Policy`. The frontend loads Next.js scripts; without CSP, XSS payloads can execute even when injection occurs.
- **HIGH** Missing `Strict-Transport-Security` (HSTS). Without it, clients may fall back to HTTP and expose tokens/cookies.
- **MEDIUM** Missing `Cross-Origin-Resource-Policy`, `Cross-Origin-Embedder-Policy`, and `Cross-Origin-Opener-Policy` headers.

**Affected files:**

- `shared/middleware.py`

### 3.4 Input validation & request limits

**Status:** Inconsistent.

- Pydantic schemas are used for JSON bodies.
- Individual endpoints validate file extensions and size (50 MB max in `FileValidator`).

**Findings:**

- **CRITICAL** `etl/routes.py::test_connector` and `discover_connector` accept arbitrary `source_config` and pass it to connectors. If a connector supports JDBC/HTTP URLs, this is a clear Server-Side Request Forgery (SSRF) and data-exfiltration vector. No allow-list or sandboxing is visible.
- **HIGH** There is no global `max_request_body_size` or reverse-proxy limit. An attacker can upload an arbitrarily large body before `FileValidator` rejects it, causing memory exhaustion (DoS) on serverless functions.
- **MEDIUM** File content is parsed with `pandas` and `openpyxl`. Malicious files (e.g., XML external entities in XLSX, formula injection in CSV) are not sanitized before being returned to users or stored.
- **MEDIUM** AI endpoints accept user input up to `AI_MAX_INPUT_LENGTH` but do not appear to have output validation or prompt-output filtering.

**Affected files:**

- `etl/routes.py`
- `etl/file_security.py`
- `validation/routes.py`
- `semantic/routes.py`
- `ai/routes.py`

### 3.5 Error handling

**Status:** Reasonable for production.

- `api/main.py` has a global exception handler that returns a safe JSON response and logs stack traces server-side.

**Findings:**

- **MEDIUM** Some routes still return raw exception messages (e.g., `semantic/routes.py::analyze_upload` returns `{"error": str(e)}`), which can leak file paths or internal configuration.
- **LOW** The health endpoint exposes record counts and database connectivity status publicly. This is low-sensitivity but should be considered for defense-in-depth.

**Affected files:**

- `api/main.py`
- `semantic/routes.py`
- `services/dataset_workflow_routes.py`

---

## 4. File Upload Security

### 4.1 Existing controls

- `FileValidator` checks extension, size (50 MB), MIME type when `python-magic` is available, and basic structure via `pandas`.
- `etl/routes.py::upload_file` saves to a temporary file and deletes it after validation.

### 4.2 Findings

- **HIGH** No antivirus/malware scanning or sandbox execution.
- **HIGH** Magic/MIME detection is optional (`python-magic` may be unavailable on Vercel). Extension-only validation is trivially bypassed.
- **MEDIUM** Files are read entirely into memory (`await file.read()`), increasing DoS risk.
- **MEDIUM** The same temporary file is written, deleted, then rewritten for processing; a race condition or symlink attack could occur if the temp directory is shared.
- **MEDIUM** No quarantine or scanning delay before data is processed.
- **LOW** No per-user or per-organization upload quota.

**Affected files:**

- `etl/file_security.py`
- `etl/routes.py`
- `validation/routes.py`
- `semantic/routes.py`
- `services/dataset_workflow_routes.py`

---

## 5. Database Security

### 5.1 Connection & secrets

**Status:** Standard SQLAlchemy with environment-driven connection string.

**Findings:**

- **MEDIUM** Database credentials are passed through environment variables; no evidence of secret rotation or IAM authentication.
- **LOW** SQLite is permitted in development but correctly blocked by `validate_config()` in production (`DB_TYPE=mysql`).
- **LOW** No statement timeout or connection-pool size limits configured for Vercel's serverless environment.

**Affected files:**

- `shared/database.py`
- `config.py`

### 5.2 Row-level security / multi-tenancy

**Status:** Schema supports multi-tenancy; enforcement is incomplete.

- `users`, `branches`, `departments`, `teams`, and audit tables include `organization_id`.
- Many analytics/ETL tables do not appear to have `organization_id` columns or repositories do not filter by it.

**Findings:**

- **CRITICAL** No centralized mechanism ensures that repository queries always include `organization_id = :current_org_id`. Missing a single query path allows cross-tenant data leakage.
- **HIGH** Dataset/workflow results are stored in memory or temp files without ownership tags in the current code paths.
- **MEDIUM** Soft-delete fields (`is_deleted`, `deleted_at`) exist on most tables but not all repository queries filter them out.

**Affected files:**

- `database/repositories.py`
- `services/dataset_workflow_routes.py`
- `etl/routes.py`
- `analytics/routes.py`

---

## 6. Secrets Management

### 6.1 Environment variables

**Status:** Variables are loaded from `.env`/environment.

**Findings:**

- **HIGH** `JWT_SECRET_KEY` has a fallback default. `validate_config()` rejects the default in production, but a missing env var during development still produces valid tokens with a known secret.
- **HIGH** `API_KEY` has a known default (`dev-api-key-change-in-production`) that is only rejected when `DB_TYPE=mysql`. Other production-like environments could silently use it.
- **MEDIUM** AI provider API keys (`OPENAI_API_KEY`, etc.) are read but not validated for presence; missing keys will cause runtime failures rather than startup failures.
- **MEDIUM** Database password is passed via plain env var; no support for secret managers (AWS Secrets Manager, Azure Key Vault, HashiCorp Vault).
- **LOW** No masking in logs; ensure `JWT_SECRET_KEY` and `API_KEY` are never printed.

**Affected files:**

- `config.py`
- `api/auth.py`
- `shared/security.py`

---

## 7. AI & Copilot Security

### 7.1 Findings

- **HIGH** AI endpoints likely accept arbitrary user content and forward it to third-party LLMs. Without output validation, the system may return harmful, biased, or confidential information.
- **MEDIUM** No per-user or per-organization token/cost budget enforcement at the API layer.
- **MEDIUM** AI memory/cache may retain sensitive data across sessions/organizations if not scoped.
- **LOW** `AI_ENFORCE_PERMISSIONS` exists but its enforcement path is not audited here.

**Affected files:**

- `ai/routes.py`
- `ai/context_engine.py`

---

## 8. Audit & Logging

### 8.1 Existing controls

- `AuditLog`, `SecurityLog`, `UserActivity`, `LoginHistory`, and `ActivityEvent` models exist.
- `AuthService.login/logout/assign_roles` records activity.

### 8.2 Findings

- **CRITICAL** The unauthenticated upload/workflow routes produce no audit trail tying actions to a user or organization.
- **HIGH** Failed authentication attempts are logged to `LoginHistory`, but brute-force and anomalous-login detection is not implemented.
- **MEDIUM** Audit entries do not appear to be tamper-evident (no hash chain or append-only stream).
- **MEDIUM** Request IDs and correlation IDs are generated, but logs may still be plaintext and lack structured JSON formatting.
- **LOW** No retention policy is enforced for audit logs; long-term storage could violate privacy regulations.

**Affected files:**

- `audit/models.py`
- `authentication/services.py`
- `shared/middleware.py`

---

## 9. Deployment & Infrastructure

### 9.1 Serverless-specific risks

- **HIGH** Python bundle is ~410 MB. Large bundles increase cold-start time and the attack surface; unused dependencies (e.g., `scipy`, `apscheduler`, `python-pptx`) should be reviewed.
- **MEDIUM** Vercel functions have a 30-second `maxDuration` configured, which is appropriate for most API calls but may be too short for large ETL jobs.
- **MEDIUM** Background scheduler is disabled on Vercel, which is correct, but scheduled jobs must be handled by external cron/Vercel Cron.
- **LOW** SSO deployment protection was re-enabled after testing. Ensure team members needing access are added to the Vercel project.

**Affected files:**

- `vercel.json`
- `pyproject.toml`
- `requirements.txt`

---

## 10. OWASP Top 10 Mapping

| OWASP Category | Risk Level | Primary Finding |
| :--- | :--- | :--- |
| A01 Broken Access Control | **Critical** | Unauthenticated routes + missing org isolation |
| A02 Cryptographic Failures | **Medium** | Same secret for access/refresh tokens |
| A03 Injection | **High** | SSRF via connector configs; prompt injection via AI |
| A04 Insecure Design | **High** | In-memory rate limiter in serverless environment |
| A05 Security Misconfiguration | **Medium** | Default dev API key, permissive CORS fallback |
| A06 Vulnerable Components | **Medium** | Heavy dependency bundle with old/deprecated packages |
| A07 Identity/Auth Failures | **Medium** | No email verification, no refresh rotation |
| A08 Software/Data Integrity | **Medium** | No malware scanning, no input output validation |
| A09 Security Logging Failures | **High** | Missing audit on anonymous data routes |
| A10 Server-Side Request Forgery | **Critical** | Arbitrary connector source_config can reach internal/external hosts |

---

## 11. Recommended Remediation Roadmap

### Immediate (Phase 1 follow-up)

1. Add `get_current_user` to all upload/workflow routes and reject anonymous requests.
2. Enforce organization isolation on every data access path.
3. Add a global request body size limit and per-route file-size validation before reading content into memory.
4. Replace in-memory rate limiting with Redis/Vercel KV (or at least per-instance strict limits).
5. Add CSP and HSTS headers.
6. Restrict connector `source_config` to an allow-listed set of protocols/hosts.

### Short-term

7. Separate access-token and refresh-token secrets; rotate refresh tokens on use.
8. Implement per-organization API keys stored in the database.
9. Add email verification workflow for self-registration.
10. Enforce password history and increase default minimum length to 12.
11. Add audit logging to all data and permission mutations.
12. Introduce a tenant-aware repository base class that automatically applies `organization_id` filters.

### Long-term

13. Integrate a secrets manager and remove fallback defaults.
14. Add malware scanning (ClamAV or cloud service) and sandboxed file parsing.
15. Implement fine-grained sharing/ACLs beyond roles (resource-level permissions).
16. Add real-time anomaly detection for logins, exports, and bulk downloads.
17. Reduce serverless bundle size by splitting heavy ML/data-science dependencies into dedicated workers.

---

## 12. Files Reviewed

- `api/main.py`
- `api/auth.py`
- `shared/security.py`
- `shared/dependencies.py`
- `shared/middleware.py`
- `config.py`
- `authentication/models.py`
- `authentication/services.py`
- `authentication/repositories.py`
- `authentication/routes.py`
- `organizations/models.py`
- `organizations/services.py`
- `audit/models.py`
- `enterprise/models.py`
- `etl/routes.py`
- `etl/file_security.py`
- `validation/routes.py`
- `semantic/routes.py`
- `services/dataset_workflow_routes.py`
- `ai/routes.py`
- `vercel.json`
- `pyproject.toml`
- `requirements.txt`
