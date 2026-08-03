# ADR-0017: Backup and Recovery Strategy

| Field | Value |
|-------|-------|
| **Status** | Accepted |
| **Date** | 2026-08-01 |
| **Decision Maker** | Enterprise Architecture Board |
| **Related ADRs** | ADR-0014 (Production DB Hardening) |

## Context

The platform had no formal backup strategy. Data loss would be catastrophic for organizations relying on the platform for their data intelligence workflows. A comprehensive backup and recovery system was needed that:

- Works with both MySQL (production) and SQLite (development)
- Is automated and requires minimal manual intervention
- Supports compression to minimize storage costs
- Has retention policies to prevent unlimited growth
- Includes verification to ensure backups are restorable
- Provides both CLI and API access for operations teams

## Decision

Implement a `BackupManager` class with the following capabilities:

1. **Backup**: `mysqldump` for MySQL, file copy for SQLite, with gzip compression
2. **Restore**: Reverse of backup process, with pre-restore safety checks
3. **Retention**: Automatic cleanup of backups older than `BACKUP_RETENTION_DAYS` (default 30)
4. **Verification**: Backup file integrity check (size, gzip validity, SQL syntax)
5. **Scheduling**: Configurable schedule via `BACKUP_SCHEDULE` (cron expression, default daily 2 AM)
6. **CLI access**: `python -m database.manage backup [name]`, `restore`, `list-backups`, `cleanup`
7. **API access**: FastAPI routes under `/api/database/*` (super_admin only)
8. **Documentation**: Recovery plan with 4 scenarios (corruption, total loss, point-in-time, migration failure)

## Alternatives Considered

1. **Cloud-managed backups (RDS automated backups)**: Rejected — not portable, vendor lock-in
2. **Third-party backup tools**: Rejected — over-engineered, needed application-aware backups
3. **Manual backups only**: Rejected — human error risk too high
4. **Filesystem snapshots only**: Rejected — not application-aware, can't restore individual tables

## Consequences

**Positive:**
- Data loss risk significantly mitigated
- Backups are automated and require no manual intervention
- Both CLI and API access for operational flexibility
- Recovery procedures are documented and testable
- Compression reduces storage costs
- Retention prevents storage bloat

**Negative:**
- Backup storage requires disk space (mitigated by compression + retention)
- `mysqldump` can lock tables during backup (mitigated by `--single-transaction` flag)
- Restore requires downtime (accepted for current scale)
- No point-in-time recovery yet (deferred to future)

## Implementation Notes

- `BackupManager` in `database/backup.py`
- MySQL backup: `mysqldump --single-transaction --routines --triggers`
- SQLite backup: File copy with WAL checkpoint
- Compression: gzip with configurable level
- Retention: Files older than `BACKUP_RETENTION_DAYS` are deleted on cleanup
- Recovery plan: `database/RECOVERY_PLAN.md` with RTO/RPO targets
- API routes: `/api/database/backup`, `/api/database/restore`, `/api/database/backups`

## Future Considerations

- Point-in-time recovery via MySQL binlog
- Incremental backups to reduce backup time
- Off-site backup replication (S3, GCS)
- Automated restore testing in CI
- Backup encryption at rest
