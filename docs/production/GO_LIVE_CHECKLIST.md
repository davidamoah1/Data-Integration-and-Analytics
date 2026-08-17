# Production Go-Live Checklist

**Version:** 1.0.0
**Last Updated:** 2025-01-17

---

## Pre-Deployment

- [x] Security audit completed (no CRITICAL/HIGH issues)
- [x] RBAC audit completed (all routes protected)
- [x] Organization isolation verified (HTTP 403)
- [x] MySQL health verified (135 tables, migrations applied)
- [ ] Redis configured (REDIS_URL set)
- [ ] Worker process running (background job processor)
- [ ] Object storage configured (S3/GCS or local)
- [x] Backup verified (backup + restore tested)
- [x] E2E workflow passing (40/40 on MySQL)
- [x] Regression tests passing (1,468 backend + 25 frontend)
- [x] Large dataset tested (100K rows in 6.7s)
- [x] PPTX generation verified (42,845 bytes, 6 slides)
- [x] Report generation verified
- [ ] SSL/TLS configured
- [ ] DNS configured
- [x] Docker production compose reviewed
- [ ] CI/CD pipeline active
- [x] Rollback plan documented

## Environment Variables (Required)

- [ ] `DB_TYPE=mysql`
- [ ] `MYSQL_HOST` (production hostname)
- [ ] `MYSQL_PORT` (default 3306)
- [ ] `MYSQL_DATABASE` (production database name)
- [ ] `MYSQL_USER` (application user, NOT root)
- [ ] `MYSQL_PASSWORD` (strong, random)
- [ ] `JWT_SECRET_KEY` (min 32 chars, cryptographically random)
- [ ] `ENCRYPTION_KEY` (separate from JWT, random)
- [ ] `CORS_ORIGINS` (explicit production domain)
- [ ] `REDIS_URL` (production Redis instance)
- [ ] `BACKUP_STORAGE_PATH` (absolute path, not in repo)

## Environment Variables (Recommended)

- [ ] `RATE_LIMIT_RPM=120` (adjust per expected traffic)
- [ ] `POOL_SIZE=10` (adjust per server resources)
- [ ] `MAX_OVERFLOW=20`
- [ ] `POOL_RECYCLE=3600`
- [ ] `SLOW_QUERY_THRESHOLD_MS=500`
- [ ] `LOG_LEVEL=INFO`
- [ ] `SENTRY_DSN` (for error tracking)
- [ ] `OTEL_EXPORTER_OTLP_ENDPOINT` (for observability)

## Security Verification

- [x] No secrets in source code
- [x] No wildcard CORS (`*`)
- [x] API docs considered (disable `/docs` in production if not needed)
- [x] Rate limiting enabled
- [x] Security headers enabled (CSP, HSTS, X-Frame-Options)
- [x] File upload size limited (50 MB)
- [x] Password hashing: Argon2 (memory: 64MB, time: 3, parallelism: 4)
- [x] Account lockout: 5 attempts / 30 minutes
- [x] JWT expiry: 30 min access, 7 day refresh
- [x] Refresh token rotation enabled
- [x] Session revocation on logout
- [x] No stack traces in production error responses
- [x] No user input reflected in error responses (XSS)

## Database

- [x] Alembic migrations applied (`alembic upgrade head`)
- [x] `alembic_version` shows correct head
- [x] Application user has DML-only privileges
- [x] `create_all()` disabled for MySQL
- [ ] Automated daily backups configured
- [ ] Backup retention policy active (30 days)
- [ ] Backup restore tested quarterly

## Monitoring

- [x] `/health` endpoint accessible
- [x] `/ready` endpoint returns 503 when DB unavailable
- [ ] External uptime monitoring configured
- [ ] Alert on error rate spike
- [ ] Alert on response time degradation
- [ ] Alert on disk space low
- [ ] Alert on connection pool exhaustion

## Post-Deployment

- [ ] Smoke test: health check passes
- [ ] Smoke test: login works
- [ ] Smoke test: upload + workflow works
- [ ] Smoke test: dashboard loads
- [ ] Monitor error rates for 24 hours
- [ ] Monitor response times for 24 hours
- [ ] Verify backup runs at scheduled time
