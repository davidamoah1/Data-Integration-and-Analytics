# Backup and Recovery

> **Version**: 1.0.0  
> **Last Updated**: 2026-07-30  
> **Status**: Active  
> **Owner**: DevOps Engineer

---

## Purpose

Document backup and recovery procedures for the database.

## Scope

Backup strategy, recovery procedures, and data retention.

## Audience

DevOps engineers and database administrators.

---

## 1. Backup Strategy

### Automated Backups

- **Schedule**: Daily at 02:00 UTC via APScheduler
- **Implementation**: `services/backup_service.py:BackupService.create_backup()`
- **Disabled on serverless** (Vercel) — must use external backup solution

### Manual Backups

```bash
pg_dump $DATABASE_URL > backup_$(date +%Y%m%d).sql
```

## 2. Recovery Procedure

### From SQL Dump

```bash
# Stop the application
# Restore the database
psql $DATABASE_URL < backup_YYYYMMDD.sql
# Restart the application
```

### From Cloud Provider Backup

1. Identify the backup point in the cloud provider console
2. Create a new database instance from the backup
3. Update `DATABASE_URL` environment variable
4. Restart the application

## 3. Data Retention

> **⚠️ Planned**: No formal retention policy yet. Recommended:

| Data Type | Retention Period | Notes |
|-----------|-----------------|-------|
| Audit logs | 7 years | Compliance requirement |
| Activity logs | 90 days | Operational analytics |
| Security logs | 1 year | Security investigations |
| Login history | 90 days | Security review |
| Sessions | Until expiry | Auto-cleaned |
| Password history | 5 entries | Prevent reuse |

## 4. Backup Verification

> **⚠️ Planned**: No automated backup verification yet. Recommended:

- Weekly backup restore test
- Verify table counts match production
- Verify latest audit logs are present

## Related Documents

- [../operations/backups.md](../operations/backups.md) — Operational backup procedures
- [../operations/disaster-recovery.md](../operations/disaster-recovery.md) — Disaster recovery plan
- [../deployment/production.md](../deployment/production.md) — Production deployment
