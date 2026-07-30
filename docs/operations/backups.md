# Backups

> **Version**: 1.0.0  
> **Last Updated**: 2026-07-30  
> **Status**: Active  
> **Owner**: DevOps Engineer

---

## Purpose

Backup strategy and procedures.

## Scope

Database backups, verification, and retention.

## Audience

DevOps engineers and database administrators.

---

## 1. Backup Strategy

| Type | Frequency | Method | Retention |
|------|-----------|--------|-----------|
| Full database | Daily (02:00 UTC) | `BackupService.create_backup()` | 30 days |
| Manual | On demand | `pg_dump` | As needed |
| Cloud provider | Per provider | Managed backup | Per provider |

## 2. Automated Backup

- **Implementation**: `services/backup_service.py:BackupService.create_backup()`
- **Schedule**: APScheduler cron job at 02:00 UTC
- **Disabled on serverless** (Vercel) — use external backup solution

## 3. Manual Backup

```bash
# Full database dump
pg_dump $DATABASE_URL > backup_$(date +%Y%m%d_%H%M%S).sql

# Compressed backup
pg_dump $DATABASE_URL | gzip > backup_$(date +%Y%m%d).sql.gz

# Specific tables only
pg_dump $DATABASE_URL -t users -t roles -t permissions > auth_backup.sql
```

## 4. Backup Verification

> **⚠️ Planned**: No automated verification yet.

Recommended:
1. Weekly: Restore backup to test database
2. Verify table counts match production
3. Verify latest audit logs present
4. Verify super admin can log in

## 5. Retention Policy

| Data | Retention | Disposal |
|------|-----------|----------|
| Daily backups | 30 days | Auto-delete after 30 days |
| Manual backups | As needed | Manual deletion |
| Audit logs | 7 years | Archive to cold storage |
| Application logs | 90 days | Auto-rotate |

## Related Documents

- [../database/backup-recovery.md](../database/backup-recovery.md) — Database backup
- [disaster-recovery.md](disaster-recovery.md) — Disaster recovery
- [maintenance.md](maintenance.md) — Maintenance schedule
