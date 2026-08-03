# Production Security Checklist

> **Version**: 1.0.0  
> **Last Updated**: 2026-08-01  
> **Status**: Active  
> **Owner**: Security Architect

---

## Purpose

Pre-deployment security checklist to ensure production environments are properly hardened.

## Scope

All security controls that must be verified before going live.

## Audience

DevOps engineers, security architects, and release managers.

---

## 1. Environment Configuration

- [ ] `APP_ENV` set to `production`
- [ ] `DB_TYPE` set to `mysql` (SQLite is blocked in production)
- [ ] `JWT_SECRET_KEY` set to a strong, unique value (min 32 characters)
- [ ] `ENCRYPTION_KEY` set to a 32-byte base64-encoded key
- [ ] `CORS_ORIGINS` set to specific allowed domains (no wildcards)
- [ ] `API_KEY` set to a strong, unique value
- [ ] `DISABLE_CONFIG_VALIDATION` is NOT set (validation must be active)
- [ ] All secrets stored in environment variables (never in code or config files)
- [ ] `.env` file is in `.gitignore` and not committed

## 2. Database Security

- [ ] MySQL 8.0 or later
- [ ] Database user has least-privilege permissions (no `GRANT ALL`)
- [ ] Database connection uses TLS
- [ ] `POOL_SIZE` set to 10+ for production
- [ ] `MAX_OVERFLOW` set to 20+ for production
- [ ] `SLOW_QUERY_THRESHOLD_MS` set (default 500ms)
- [ ] `QUERY_TIMEOUT_SECONDS` set (default 30)
- [ ] All migrations applied (`alembic upgrade head`)
- [ ] Production indexes created (`alembic upgrade 0016_prod_indexes`)
- [ ] Database backup enabled (`BACKUP_ENABLED=true`)
- [ ] `BACKUP_STORAGE_PATH` set to an absolute path
- [ ] `BACKUP_RETENTION_DAYS` set (default 30)

## 3. Authentication & Authorization

- [ ] Super admin password is strong and unique
- [ ] MFA enabled for all admin accounts
- [ ] Default `SUPER_ADMIN_PASSWORD` changed from default
- [ ] Email verification required for new users
- [ ] Account lockout is active (5 attempts / 15 minutes)
- [ ] Session timeout configured (access: 30min, refresh: 7d)
- [ ] All platform roles assigned intentionally (no accidental super_admin)

## 4. API Security

- [ ] HTTPS enforced (HSTS header active)
- [ ] Rate limiting active (120 RPM default)
- [ ] Security headers middleware active
- [ ] CORS origins restricted to known domains
- [ ] File upload size limit set (`CAPTURE_MAX_FILE_SIZE_MB`)
- [ ] API key required for service-to-service calls
- [ ] Error responses do not leak stack traces or internal paths

## 5. Infrastructure

- [ ] Docker containers run as non-root user (`appuser`)
- [ ] Container resource limits set (memory, CPU)
- [ ] Health check endpoints accessible
- [ ] Redis requires authentication (if exposed)
- [ ] MySQL port not exposed to public internet
- [ ] Nginx (or equivalent) configured as reverse proxy
- [ ] TLS certificates valid and auto-renewing
- [ ] Firewall rules restrict access to internal services

## 6. Monitoring & Logging

- [ ] Application logging at INFO level (not DEBUG)
- [ ] Log format is JSON (for log aggregation)
- [ ] Audit logs are being written
- [ ] Security logs are being written
- [ ] Slow query logging is active
- [ ] Health check monitoring is configured
- [ ] Alert on repeated 5xx errors
- [ ] Alert on security log entries with severity `critical`

## 7. CI/CD Security

- [ ] Branch protection enabled on `main` (required reviews + status checks)
- [ ] `production` environment requires manual approval
- [ ] Vercel secrets configured (`VERCEL_TOKEN`, `VERCEL_ORG_ID`, `VERCEL_PROJECT_ID`)
- [ ] Dependabot is active
- [ ] Security scanning workflows are passing
- [ ] No secrets in GitHub Actions logs

## 8. Backup & Recovery

- [ ] Backup schedule configured (default: daily at 2 AM)
- [ ] Backup compression enabled
- [ ] Backup retention set (default: 30 days)
- [ ] Recovery plan documented and tested
- [ ] Backup verification (restore test) performed
- [ ] Off-site backup storage configured (recommended)

## 9. Vulnerability Management

- [ ] pip-audit: 0 critical/high vulnerabilities
- [ ] npm audit: 0 high vulnerabilities
- [ ] Bandit: 0 new medium+ findings
- [ ] Trivy: 0 critical findings
- [ ] All dependencies up to date (or risk-accepted)

## 10. Sign-Off

| Role | Name | Date | Signature |
|------|------|------|-----------|
| Security Architect | | | |
| DevOps Engineer | | | |
| Release Manager | | | |

## Related Documents

- [overview.md](overview.md) — Security architecture overview
- [vulnerability-management.md](vulnerability-management.md) — Vulnerability management
- [../deployment/production.md](../deployment/production.md) — Production deployment
- [../database/backup-recovery.md](../database/backup-recovery.md) — Backup procedures
