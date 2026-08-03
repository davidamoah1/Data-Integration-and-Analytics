# API Security

> **Version**: 1.0.0  
> **Last Updated**: 2026-08-01  
> **Status**: Active  
> **Owner**: Security Architect

---

## Purpose

Document API-level security controls including CORS, rate limiting, security headers, and input validation.

## Scope

All HTTP API endpoints, middleware, and request/response security.

## Audience

Backend developers, security architects, and DevOps engineers.

---

## 1. CORS Configuration

| Parameter | Value | Configurable |
|-----------|-------|-------------|
| Allowed origins | `CORS_ORIGINS` env var | Yes |
| Default (dev) | `http://localhost:8501` | Yes |
| Production | Must be set explicitly | Yes |
| Methods | GET, POST, PUT, PATCH, DELETE, OPTIONS | No |
| Headers | Authorization, Content-Type | No |
| Credentials | Enabled | No |

### Production CORS

Production environments must set `CORS_ORIGINS` to specific allowed domains. Wildcard (`*`) is not permitted in production.

## 2. Rate Limiting

| Parameter | Value | Configurable |
|-----------|-------|-------------|
| Library | `slowapi` | No |
| Default limit | 120 requests per minute | Yes (`RATE_LIMIT_RPM`) |
| Storage | In-memory (dev), Redis (prod) | Yes |
| Response on exceed | 429 Too Many Requests | No |
| Headers | X-RateLimit-Remaining, X-RateLimit-Reset | No |

### Endpoint-Specific Limits

| Endpoint | Limit | Notes |
|----------|-------|-------|
| `/auth/login` | 10 RPM | Brute force protection |
| `/auth/register` | 5 RPM | Spam protection |
| `/auth/forgot-password` | 3 RPM | Abuse protection |
| Default | 120 RPM | All other endpoints |

## 3. Security Headers

Added by `SecurityHeadersMiddleware` on all responses:

| Header | Value | Purpose |
|--------|-------|---------|
| Content-Security-Policy | Restrictive policy | XSS prevention |
| X-Content-Type-Options | nosniff | MIME type sniffing prevention |
| X-Frame-Options | DENY | Clickjacking prevention |
| Strict-Transport-Security | max-age=31536000; includeSubDomains | HTTPS enforcement |
| X-XSS-Protection | 1; mode=block | Legacy XSS protection |
| Referrer-Policy | strict-origin-when-cross-origin | Referrer control |
| Permissions-Policy | camera=(), microphone=(), geolocation=() | Feature restriction |

## 4. Input Validation

### Pydantic Schema Validation

All API endpoints use Pydantic models for request validation:

- Type checking (string, int, float, bool, datetime)
- Length constraints (min_length, max_length)
- Range constraints (ge, le)
- Pattern matching (regex)
- Email format validation
- Enum value validation

### SQL Injection Prevention

- All database queries use SQLAlchemy ORM with parameterized queries
- No raw SQL is used in application code
- User input is never concatenated into SQL strings

### XSS Prevention

- React auto-escapes all rendered content
- Content-Security-Policy header restricts script sources
- User-generated content is sanitized before storage

### File Upload Security

| Control | Implementation |
|---------|---------------|
| File size limit | 50MB default (`CAPTURE_MAX_FILE_SIZE_MB`) |
| Allowed file types | Whitelist enforced |
| MIME type check | Verified against content, not just extension |
| Filename sanitization | Special characters stripped |
| Storage isolation | Uploads stored outside web root |

## 5. Authentication on API

### Token Requirements

- All endpoints except `/auth/login`, `/auth/register`, `/health`, `/ready` require JWT
- Token must be in `Authorization: Bearer <token>` header
- Token must be valid (signature + not expired)
- User must be active (not deleted, not locked)

### API Key Support

- `X-API-Key` header for service-to-service authentication
- API key validated against `API_KEY` env var
- Used for internal integrations and webhooks

## 6. Error Handling Security

- Error responses never include stack traces in production
- Error responses never include database schema details
- Error responses never include internal file paths
- 404 responses are identical for "not found" and "no permission" (prevents enumeration)

## 7. Request/Response Logging

| What is logged | What is NOT logged |
|----------------|-------------------|
| Request method + path | Request body (may contain PII) |
| Response status code | Passwords, tokens |
| Request ID | API keys |
| User ID (if authenticated) | PII fields |
| Response time | Response body |

## Related Documents

- [overview.md](overview.md) — Security architecture overview
- [authentication.md](authentication.md) — Authentication details
- [../backend/error-handling.md](../backend/error-handling.md) — Error handling patterns
- [../backend/endpoints.md](../backend/endpoints.md) — Endpoint catalog
