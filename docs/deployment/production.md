# Production Deployment

> **Version**: 1.0.0  
> **Last Updated**: 2026-07-30  
> **Status**: Active  
> **Owner**: DevOps Engineer

---

## Purpose

Production deployment checklist and best practices.

## Scope

All steps and checks for production deployment.

## Audience

DevOps engineers and CTO.

---

## 1. Pre-Deployment Checklist

### Infrastructure
- [ ] PostgreSQL provisioned (external or managed)
- [ ] Database connection string configured
- [ ] JWT secret generated (strong random value)
- [ ] CORS origins configured (production domains only)
- [ ] SSL/TLS certificates configured
- [ ] DNS records configured

### Application
- [ ] `SEED_DEMO_DATA=false` (no demo data in production)
- [ ] `DEBUG` not set (no detailed error messages)
- [ ] `RATE_LIMIT_RPM` configured appropriately
- [ ] `MAX_REQUEST_BODY_BYTES` configured
- [ ] All environment variables set

### Database
- [ ] Database created and accessible
- [ ] Tables created (run application once or manual SQL)
- [ ] Default data seeded (roles, permissions, super admin)
- [ ] Super admin email and password configured
- [ ] Backup schedule configured

### Security
- [ ] HTTPS enforced
- [ ] Security headers verified
- [ ] CORS restricted to production domains
- [ ] Rate limiting enabled
- [ ] Super admin credentials secured

## 2. Post-Deployment Verification

- [ ] Health check passes: `GET /api/health`
- [ ] Readiness check passes: `GET /api/ready`
- [ ] Login works with super admin credentials
- [ ] Can create organization
- [ ] Can invite users
- [ ] Can upload datasets
- [ ] Can create dashboards
- [ ] Audit logs being written
- [ ] No errors in application logs

## 3. Production Configuration

```bash
# Recommended production environment
DATABASE_URL=postgresql://user:pass@host:5432/dataflow
JWT_SECRET_KEY=<strong-random-secret>
CORS_ORIGINS=https://app.dataflow.io
SEED_DEMO_DATA=false
RATE_LIMIT_RPM=120
MAX_REQUEST_BODY_BYTES=52428800
# DEBUG should NOT be set
```

## Related Documents

- [vercel.md](vercel.md) — Vercel deployment
- [docker.md](docker.md) — Docker deployment
- [environments.md](environments.md) — Environment configuration
- [../operations/monitoring.md](../operations/monitoring.md) — Monitoring
