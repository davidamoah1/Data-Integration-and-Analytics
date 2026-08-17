# MySQL Backup and Recovery

**Version:** 2.0.0
**Last Updated:** 2025-01-17
**Status:** Active

---

## Backup Strategy

### Automated Backups

The `BackupManager` (`database/backup.py`) runs daily:

| Setting | Default | Variable |
|---------|---------|----------|
| Schedule | 02:00 UTC | `BACKUP_SCHEDULE` |
| Retention | 30 days | `BACKUP_RETENTION_DAYS` |
| Storage | `backups/` | `BACKUP_STORAGE_PATH` |
| Compression | gzip | `BACKUP_COMPRESS=true` |
| Method | `mysqldump --single-transaction` | Automatic |

### Backup Types

| Type | Method | Use Case | RPO |
|------|--------|----------|-----|
| Full dump | `mysqldump` | Daily automated | 24 hours |
| Point-in-time | MySQL binlog | Continuous | Minutes |
| Snapshot | Cloud provider | Before maintenance | Immediate |
| Logical | Application CLI | Before deployment | Immediate |

### Creating Backups

```bash
# Built-in manager (recommended)
python -m database.manage backup pre_deploy_20250117

# Raw mysqldump
mysqldump --single-transaction --routines --triggers \
  -u dataflow_migrate -p dataflow | gzip > backup_$(date +%Y%m%d_%H%M%S).sql.gz

# Cloud provider snapshot (AWS RDS example)
aws rds create-db-snapshot \
  --db-instance-identifier dataflow-prod \
  --db-snapshot-identifier pre-deploy-20250117
```

## Recovery Procedures

### Restore from SQL Dump

```bash
# 1. Stop the application
systemctl stop dataflow-api

# 2. Verify backup integrity
gunzip -t backup_20250117.sql.gz

# 3. Restore
gunzip -c backup_20250117.sql.gz | mysql -u dataflow_migrate -p dataflow

# 4. Verify Alembic state
alembic current

# 5. Restart application
systemctl start dataflow-api

# 6. Smoke test
curl http://localhost:8000/health
```

### Restore via Built-in Manager

```bash
# List available backups
python -m database.manage list-backups

# Verify backup before restore
python -m database.manage verify pre_deploy_20250117

# Restore
python -m database.manage restore pre_deploy_20250117
```

### Point-in-Time Recovery (MySQL Binlog)

```bash
# 1. Identify the binlog position before the incident
mysqlbinlog --start-datetime="2025-01-17 09:00:00" \
  --stop-datetime="2025-01-17 10:00:00" \
  /var/lib/mysql/binlog.000042

# 2. Restore from last full backup
gunzip -c last_full_backup.sql.gz | mysql -u root dataflow

# 3. Replay binlog up to the incident
mysqlbinlog --stop-position=12345 \
  /var/lib/mysql/binlog.000042 | mysql -u root dataflow
```

### Cloud Provider Recovery (AWS RDS)

```bash
# Restore from snapshot
aws rds restore-db-instance-from-db-snapshot \
  --db-instance-identifier dataflow-restored \
  --db-snapshot-identifier pre-deploy-20250117

# Update application to point to restored instance
# Update MYSQL_HOST environment variable
# Restart application
```

## Verification

### After Every Restore

1. **Alembic version matches expected:**
   ```bash
   alembic current
   # Expected: 0018_dataset_workflow_runs (head)
   ```

2. **Table count is correct:**
   ```sql
   SELECT COUNT(*) FROM information_schema.tables
   WHERE table_schema = 'dataflow';
   -- Expected: 135 (134 app tables + alembic_version)
   ```

3. **Critical data exists:**
   ```sql
   SELECT COUNT(*) FROM users;
   SELECT COUNT(*) FROM organizations;
   SELECT COUNT(*) FROM roles;
   ```

4. **Application starts cleanly:**
   ```bash
   uvicorn api.main:app --host 0.0.0.0 --port 8000
   # Watch for startup errors
   ```

5. **E2E smoke test passes:**
   ```bash
   curl http://localhost:8000/health
   curl -X POST http://localhost:8000/api/auth/login -H "Content-Type: application/json" -d '...'
   ```

### Test Restore (Non-Production)

Run quarterly:

```bash
# Create test database
mysql -u root -e "CREATE DATABASE dataflow_restore_test CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"

# Restore latest backup
gunzip -c /path/to/latest_backup.sql.gz | mysql -u root dataflow_restore_test

# Verify
mysql -u root -e "SELECT COUNT(*) FROM dataflow_restore_test.users;"

# Cleanup
mysql -u root -e "DROP DATABASE dataflow_restore_test;"
```

## Retention Policy

| Data | Retention | Enforcement |
|------|-----------|-------------|
| Database backups | 30 days | `BackupManager.cleanup_old_backups()` |
| Audit logs | 7 years | No auto-purge (compliance) |
| Activity logs | 90 days | Planned auto-purge |
| Security logs | 7 years | No auto-purge (compliance) |
| Binlog | 7 days | MySQL `expire_logs_days=7` |

## Disaster Recovery

### RTO and RPO Targets

| Scenario | RTO | RPO |
|----------|-----|-----|
| Single table corruption | 1 hour | 0 (binlog) |
| Full database loss | 4 hours | 24 hours (last backup) |
| Complete infrastructure loss | 8 hours | 24 hours |
| Region failure (cloud) | 12 hours | Minutes (cross-region) |

### Recovery Priority

1. Authentication (users, roles, sessions)
2. Organization data (orgs, workspaces)
3. Active workflows and jobs
4. Dataset metadata and analysis results
5. Audit trail
6. Historical analytics

## Related Documents

- [backup-recovery.md](backup-recovery.md) — General backup documentation
- [MYSQL_MIGRATION_RUNBOOK.md](MYSQL_MIGRATION_RUNBOOK.md) — Migration procedures
- [MYSQL_TROUBLESHOOTING.md](MYSQL_TROUBLESHOOTING.md) — Common issues
