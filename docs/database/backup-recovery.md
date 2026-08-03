# Backup and Recovery

> **Version**: 2.0.0  
> **Last Updated**: 2026-08-01  
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

### BackupManager

The platform includes a built-in `BackupManager` class (`database/backup.py`) that supports both MySQL and SQLite:

| Database | Method | Compression |
|----------|--------|-------------|
| MySQL | `mysqldump --single-transaction --routines --triggers` | gzip |
| SQLite | File copy with WAL checkpoint | gzip |

### Automated Backups

- **Schedule**: Daily at 02:00 UTC via APScheduler (configurable via `BACKUP_SCHEDULE`)
- **Implementation**: `database/backup.py:BackupManager.create_backup()`
- **Storage**: `BACKUP_STORAGE_PATH` (must be absolute path in production)
- **Compression**: gzip (level 6 by default)
- **Retention**: `BACKUP_RETENTION_DAYS` (default 30 days)
- **Disabled on serverless** (Vercel) — must use external backup solution

### Manual Backups

**Via CLI:**

```bash
# Create a named backup
python -m database.manage backup my_pre_deploy_backup

# List all backups
python -m database.manage list-backups

# Verify a backup
python -m database.manage verify my_pre_deploy_backup
```

**Via API (super_admin only):**

```bash
# Create backup
curl -X POST http://localhost:8000/api/database/backup \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": "pre_deploy"}'

# List backups
curl http://localhost:8000/api/database/backups \
  -H "Authorization: Bearer $TOKEN"
```

**Via raw command (MySQL):**

```bash
mysqldump --single-transaction --routines --triggers $DB_NAME | gzip > backup_$(date +%Y%m%d).sql.gz
```

## 2. Recovery Procedure

### From BackupManager Backup

**Via CLI:**

```bash
# Stop the application first
# Restore from a named backup
python -m database.manage restore my_pre_deploy_backup
# Restart the application
```

**Via API (super_admin only):**

```bash
curl -X POST http://localhost:8000/api/database/restore \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": "my_pre_deploy_backup"}'
```

### From SQL Dump (MySQL)

```bash
# Stop the application
# Decompress and restore
gunzip -c backup_YYYYMMDD.sql.gz | mysql $DB_NAME
# Restart the application
```

### From SQLite Backup

```bash
# Stop the application
cp backup_YYYYMMDD.db.gz /tmp/restore.db.gz
gunzip /tmp/restore.db.gz
cp /tmp/restore.db $SQLITE_DB_PATH
# Restart the application
```

### From Cloud Provider Backup

1. Identify the backup point in the cloud provider console
2. Create a new database instance from the backup
3. Update `DB_URL` / `MYSQL_HOST` environment variables
4. Restart the application
5. Run `alembic upgrade head` to ensure schema is current

### Recovery Scenarios

See `database/RECOVERY_PLAN.md` for detailed recovery scenarios:
- Database corruption
- Total data loss
- Point-in-time recovery (MySQL binlog)
- Migration failure rollback

## 3. Data Retention

| Data Type | Retention Period | Enforcement |
|-----------|-----------------|-------------|
| Database backups | 30 days (configurable) | `BackupManager.cleanup_old_backups()` |
| Audit logs | 7 years | Compliance requirement (no auto-purge) |
| Activity logs | 90 days | Planned auto-purge |
| Security logs | 7 years | Compliance requirement (no auto-purge) |
| Sessions | Until token expiry | Automatic cleanup |
| Captured documents | 365 days (configurable) | `CAPTURE_RETENTION_DAYS` |

### Backup Retention

The `BackupManager` automatically purges backup files older than `BACKUP_RETENTION_DAYS`:

```bash
# Manually trigger cleanup
python -m database.manage cleanup
```

## 4. Backup Verification

### Automated Verification

The `BackupManager.verify_backup()` method checks:
- File exists and is readable
- gzip integrity (decompression test)
- Minimum file size (non-empty backup)
- SQL syntax validity (for SQL dumps)

### Manual Verification

```bash
# Verify a specific backup
python -m database.manage verify my_pre_deploy_backup

# Test restore to a temporary database
python -m database.manage restore my_pre_deploy_backup --target /tmp/test_restore.db
```

## 5. Database Management CLI

The `database/manage.py` CLI provides the following commands:

| Command | Description |
|---------|-------------|
| `init` | Initialize database (create tables, seed data) |
| `migrate` | Run Alembic migrations |
| `backup [name]` | Create a named backup |
| `restore [name]` | Restore from a named backup |
| `status` | Show database status and statistics |
| `indexes` | Show index status and missing critical indexes |
| `cleanup` | Purge old backups per retention policy |
| `list-backups` | List all available backups |

## Related Documents

- [../operations/backups.md](../operations/backups.md) — Operational backup procedures
- [../operations/disaster-recovery.md](../operations/disaster-recovery.md) — Disaster recovery plan
- [../deployment/production.md](../deployment/production.md) — Production deployment
