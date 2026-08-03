# Security Findings

## Overview

Security audit of the DataFlow platform, covering authentication, authorization, data protection, API security, infrastructure, and OWASP Top 10 compliance.

---

## CRITICAL

### SEC-C1: JWT Secret Key Has Insecure Default
**Location**: `config.py:103-104`
**Description**: `JWT_SECRET_KEY` defaults to `"change-this-to-a-strong-random-secret-min-32-chars"`. While `validate_config()` warns when this default is used with MySQL, it only raises for MySQL. SQLite deployments (including serverless) silently use the default.
**Impact**: If an attacker knows the default secret, they can forge JWT tokens and impersonate any user.
**Fix**: Remove the default value. Require `JWT_SECRET_KEY` to be set explicitly. Fail fast if missing.
**OWASP**: A02:2021 – Cryptographic Failures

### SEC-C2: API Key Encryption Derives Key from JWT Secret
**Location**: `shared/security.py:193-197`
**Description**: `_get_fernet_key()` derives the Fernet encryption key by SHA-256 hashing the `JWT_SECRET_KEY`. If the JWT secret is compromised, all encrypted API keys are also compromised.
**Impact**: Single point of failure. JWT secret compromise = total secret compromise.
**Fix**: Use a separate `ENCRYPTION_KEY` environment variable for Fernet encryption.
**OWASP**: A02:2021 – Cryptographic Failures

### SEC-C3: No CSRF Protection on State-Changing Endpoints
**Location**: Throughout backend
**Description**: The API relies on JWT Bearer tokens for auth, which provides some CSRF protection. However, if tokens are stored in cookies (future), CSRF protection would be needed. Currently, the frontend stores tokens in localStorage, which is vulnerable to XSS.
**Impact**: XSS attack can steal tokens from localStorage. No CSRF tokens for defense in depth.
**Fix**: Consider httpOnly cookie-based token storage with SameSite attribute. Add CSRF tokens for state-changing operations.
**OWASP**: A01:2021 – Broken Access Control, A07:2021 – Identification and Authentication Failures

---

## HIGH

### SEC-H1: No Input Sanitization on AI Endpoints
**Location**: `ai/routes.py`, `ai/enterprise_routes.py`
**Description**: AI chat endpoints accept user messages up to `AI_MAX_INPUT_LENGTH` (10,000 chars) but do not sanitize or validate content beyond length. Prompt injection attacks could manipulate AI behavior.
**Impact**: Prompt injection, data exfiltration via AI, manipulation of AI-generated reports.
**Fix**: Add input sanitization, content filtering, and prompt injection detection.
**OWASP**: A03:2021 – Injection

### SEC-H2: SQL Identifier Validation Not Used Everywhere
**Location**: `shared/security.py:174-182`, `api/main.py:544`
**Description**: `validate_sql_identifier()` exists but `api/main.py:544` uses `f"SELECT COUNT(*) FROM {table_name}"` with a hardcoded list of table names. While the list is controlled, the pattern is dangerous if copied.
**Impact**: SQL injection if pattern is reused with user input.
**Fix**: Use parameterized queries or ORM methods exclusively. Add linting rule against f-string SQL.
**OWASP**: A03:2021 – Injection

### SEC-H3: No Rate Limiting on Auth Endpoints
**Location**: `shared/middleware.py:99`
**Description**: Rate limiter skips `/health` and `/ready` but does not have special handling for `/auth/login` or `/auth/signup`. The global rate limit (120 RPM) applies, but this is per-IP, not per-account.
**Impact**: Brute-force attacks on login endpoint. Account enumeration via signup.
**Fix**: Add stricter rate limits for auth endpoints (e.g., 5 attempts per minute per IP for login).
**OWASP**: A07:2021 – Identification and Authentication Failures

### SEC-H4: No Security Headers on Frontend Static Assets
**Location**: `frontend/next.config.js:40-65`
**Description**: Security headers are set via Next.js config for all routes, but CSP is not included. The backend sets CSP via `SecurityHeadersMiddleware`, but the frontend does not.
**Impact**: XSS protection incomplete on frontend. Inline scripts can execute.
**Fix**: Add Content-Security-Policy header to Next.js config.
**OWASP**: A05:2021 – Security Misconfiguration

### SEC-H5: Tenant Isolation Not Enforced on All Routes
**Location**: Various route files
**Description**: While `shared/tenant.py` provides `get_tenant_context()` and `apply_organization_filter()`, not all routes handling organization-owned resources use them. Some routes trust `organization_id` from request body or query params.
**Impact**: Cross-tenant data access if user manipulates request parameters.
**Fix**: Audit all routes handling org-scoped resources. Enforce `get_tenant_context()` dependency.
**OWASP**: A01:2021 – Broken Access Control

### SEC-H6: Password Reset Tokens Not Single-Use Enforced at DB Level
**Location**: `authentication/models.py:111-119`
**Description**: `PasswordReset` table has `used_at` column but no database constraint preventing reuse. Application logic must check `used_at IS NULL` before allowing reset.
**Impact**: Password reset token replay if application logic has bugs.
**Fix**: Add database constraint or unique index on unused tokens.
**OWASP**: A07:2021 – Identification and Authentication Failures

---

## MEDIUM

### SEC-M1: Debug Mode Exposes Error Details
**Location**: `api/main.py:336-337`
**Description**: When `DEBUG=1`, the global exception handler returns the actual exception message in the response. If enabled in production, this leaks internal details.
**Impact**: Information disclosure in production if DEBUG is accidentally enabled.
**Fix**: Remove debug mode entirely for production. Use structured logging for errors instead.
**OWASP**: A05:2021 – Security Misconfiguration

### SEC-M2: No Account Enumeration Protection
**Location**: `authentication/routes.py`
**Description**: Login and password reset endpoints may return different responses for existing vs. non-existing accounts (e.g., "user not found" vs. "invalid password").
**Impact**: Attacker can enumerate valid email addresses.
**Fix**: Return generic messages like "Invalid credentials" for all auth failures.
**OWASP**: A07:2021 – Identification and Authentication Failures

### SEC-M3: Session Revocation Not Checked on Every Request
**Location**: `shared/dependencies.py:56-62`
**Description**: `get_current_user()` decodes the JWT and checks if the user is active, but does not check if the session is revoked in the `sessions` table. Revoked tokens remain valid until expiry.
**Impact**: Revoked users can continue accessing the API until token expiry (30 min).
**Fix**: Check session table on each request, or use short-lived tokens with refresh rotation.
**OWASP**: A01:2021 – Broken Access Control

### SEC-M4: No File Upload Validation Beyond Size
**Location**: `capture/routes.py`, `dataset/` routes
**Description**: File uploads are validated by size (`CAPTURE_MAX_FILE_SIZE_MB`, `AI_DOC_MAX_SIZE_MB`) but file type validation relies on extension lists only. No MIME type or magic byte verification.
**Impact**: Malicious file upload (e.g., executable renamed as .csv).
**Fix**: Validate file MIME type and magic bytes in addition to extension.
**OWASP**: A04:2021 – Insecure Design

### SEC-M5: No Audit Log for Security-Critical Events
**Location**: Various
**Description**: While `audit/services.py` exists, security-critical events like role changes, permission grants, password changes, and API key creation/deletion are not consistently logged.
**Impact**: Insufficient audit trail for compliance (GDPR, HIPAA, SOC 2).
**Fix**: Add audit log entries for all security-critical operations.
**OWASP**: A09:2021 – Security Logging and Monitoring Failures

---

## LOW

### SEC-L1: No HSTS on Frontend
**Location**: `frontend/next.config.js`
**Description**: The frontend does not set `Strict-Transport-Security` header. The backend sets it via `SecurityHeadersMiddleware`, but the frontend is served separately.
**Fix**: Add HSTS header in Next.js config.

### SEC-L2: No Content-Length Validation on Frontend
**Location**: `frontend/services/api/client.ts`
**Description**: The API client does not validate response size. A compromised backend could send extremely large responses.
**Fix**: Add response size limits in the API client.

### SEC-L3: No Subresource Integrity (SRI) for External Resources
**Location**: `frontend/app/layout.tsx`
**Description**: If external resources (fonts, scripts) are loaded, no SRI hashes are used.
**Fix**: Add SRI integrity attributes for external resources.

### SEC-L4: Test Database Files in Repository
**Location**: `alembic_v31_test.db`, `test_auth.db`
**Description**: Test database files may contain sensitive test data or schema information.
**Fix**: Remove from repository, add to `.gitignore`.

---

## Summary by Severity

| Severity | Count | OWASP Categories |
|----------|-------|-----------------|
| Critical | 3 | A01, A02, A07 |
| High | 6 | A01, A02, A03, A04, A05, A07, A09 |
| Medium | 5 | A01, A04, A05, A07, A09 |
| Low | 4 | A05 |
| **Total** | **18** | |
