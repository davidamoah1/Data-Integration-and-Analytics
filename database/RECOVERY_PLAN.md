# Database Recovery Plan

## Overview

This document outlines the procedures for recovering the AEDIP database from
backups in various failure scenarios. The backup system is managed by
`database/backup.py` and can be invoked via `python -m database.manage`.

## Backup Strategy

### Schedule
- **Automated**: Daily at 2:00 AM (configurable via `BACKUP_SCHEDULE`)
- **Manual**: `python -m database.manage backup [label]`
- **Pre-deployment**: Always create a backup before schema migrations

### Retention
- Default: 30 days (configurable via `BACKUP_RETENTION_DAYS`)
- Cleanup: `python -m database.manage cleanup`
- Pre-restore safety backups are created automatically

### Storage
- Local filesystem at `BACKUP_STORAGE_PATH` (default: `backups/`)
- Compressed by default (gzip)
- For production: configure `BACKUP_STORAGE_PATH` to an absolute path on a
  separate volume or network-attached storage

### Backup Format
- **MySQL**: `mysqldump` output (`.sql` or `.sql.gz`)
- **SQLite**: File copy (`.db` or `.db.gz`)

## Recovery Procedures

### Scenario 1: Corrupted Database (Partial Loss)

**Symptoms**: Application errors, inconsistent data, connection failures.

**Steps**:
1. Stop the application server
2. Create a safety backup: `python -m database.manage backup pre_recovery`
3. List available backups: `python -m database.manage list-backups`
4. Verify the backup: check file size > 0 and is not corrupt
5. Restore: `python -m database.manage restore backup_YYYYMMDD_HHMMSS.sql.gz`
6. Restart the application server
7. Verify data integrity by checking key tables

### Scenario 2: Complete Database Loss

**Symptoms**: Database server is down, disk failure, accidental deletion.

**Steps**:
1. Provision a new database server (MySQL)
2. Create the target database: `CREATE DATABASE aedip_prod;`
3. Configure environment variables (`.env.prod`)
4. Restore from the most recent backup:
   ```
   python -m database.manage restore backup_YYYYMMDD_HHMMSS.sql.gz
   ```
5. Run migrations to ensure schema is current:
   ```
   python -m database.manage migrate
   ```
6. Start the application server
7. Verify all services are operational

### Scenario 3: Point-in-Time Recovery (MySQL)

**Prerequisites**: MySQL binary logging must be enabled.

**Steps**:
1. Restore from the most recent full backup (Scenario 2, steps 1-4)
2. Identify the binlog position from the backup file header
3. Apply binlog events up to the desired point:
   ```sql
   mysqlbinlog --start-position=<pos> --stop-datetime="<datetime>" \
     /var/lib/mysql/mysql-bin.* | mysql -u root -p aedip_prod
   ```
4. Verify data consistency

### Scenario 4: Migration Failure

**Symptoms**: Alembic migration fails mid-way, schema is in inconsistent state.

**Steps**:
1. Restore from the pre-migration backup
2. Fix the migration script
3. Re-run: `python -m database.manage migrate`
4. If the migration is partially applied, use:
   ```
   alembic downgrade <previous_revision>
   alembic upgrade head
   ```

## Verification Checklist

After any recovery:
- [ ] Application starts without errors
- [ ] User authentication works
- [ ] Key business operations function (ETL, reports, capture)
- [ ] Audit logs are being written
- [ ] No missing tables or columns (run `python -m database.manage status`)
- [ ] Indexes are present (run `python -m database.manage indexes`)
- [ ] Backup system is operational (create a test backup)

## Disaster Recovery (RTO/RPO)

| Metric | Target | Notes |
|--------|--------|-------|
| RPO (Recovery Point Objective) | 24 hours | Based on daily backup schedule |
| RTO (Recovery Time Objective) | 2 hours | From backup availability to full service |

For tighter RPO, consider:
- Increasing backup frequency (e.g., every 6 hours)
- Enabling MySQL replication with a standby server
- Using MySQL binlog for continuous backup

## Environment-Specific Notes

### Development
- SQLite database file can be copied manually
- No automated backup needed — use version control for schema

### Testing
- In-memory or ephemeral database — no backups needed
- Test data is seeded from fixtures

### Production
- MySQL with `mysqldump --single-transaction` for consistent backups
- Backups should be stored on separate storage (S3, R2, network volume)
- Enable MySQL binary logging for point-in-time recovery
- Consider read replica for backup offloading
