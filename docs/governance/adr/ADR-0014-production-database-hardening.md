# ADR-0014: Production Database Hardening

| Field | Value |
|-------|-------|
| **Status** | Accepted |
| **Date** | 2026-08-01 |
| **Decision Maker** | Enterprise Architecture Board |
| **Related ADRs** | ADR-0013 (Multi-Env Config), ADR-0015 (Slow Query Logging), ADR-0016 (Backup Strategy) |

## Context

The platform's database was initially designed for development convenience (SQLite, no indexes beyond ORM defaults, no backup system). As the platform moves to production, the database requires:

- Comprehensive indexing for query performance at scale
- Automated backup and recovery system
- Migration system that is safe across environments
- Connection pooling tuned for production traffic
- Database management tooling (CLI + API)

Without these, the platform would suffer from slow queries, data loss risk, and operational complexity.

## Decision

Implement a comprehensive production database hardening package:

1. **Production indexes**: 56 indexes across all major tables via Alembic migration (`0016_prod_indexes`), using conditional creation to handle environments where tables/columns may not exist
2. **Backup system**: `BackupManager` class supporting MySQL (`mysqldump`) and SQLite (file copy), with gzip compression, retention-based cleanup, and backup verification
3. **Migration safety**: All migrations use `_table_exists()` and `_column_exists()` helpers to conditionally apply changes
4. **Connection pooling**: Production-tuned pool size (10+), max overflow (20+), pool recycle, pool pre-ping
5. **Management tooling**: CLI (`database/manage.py`) and FastAPI routes (`database/routes.py`) for DB init, migrate, backup, restore, status, indexes, cleanup

## Alternatives Considered

1. **External backup tools only**: Rejected — needed integrated, application-aware backups
2. **Manual indexing**: Rejected — not reproducible or version-controlled
3. **Third-party DB management**: Rejected — over-engineered for current scale
4. **ORM-level indexes only**: Rejected — ORM indexes don't cover composite or conditional indexes well

## Consequences

**Positive:**
- Query performance optimized for production workloads
- Data loss risk mitigated by automated backups
- Database operations are scriptable and API-accessible
- Migrations are safe to run in any environment
- Recovery procedures are documented and tested

**Negative:**
- 56 additional indexes increase write latency slightly
- Backup system requires disk space and maintenance
- More complex migration files with conditional logic
- Additional operational training needed for backup/restore

## Implementation Notes

- Migration `0016_prod_indexes` uses `_safe_create_index()` helper that checks table and column existence
- `BackupManager` in `database/backup.py` handles both MySQL and SQLite
- CLI commands: `init`, `migrate`, `backup`, `restore`, `status`, `indexes`, `cleanup`, `list-backups`
- API routes require super_admin permissions
- Recovery plan documented in `database/RECOVERY_PLAN.md`

## Future Considerations

- Point-in-time recovery for MySQL (binlog-based)
- Read replicas for query offloading
- Database connection pooling via PgBouncer/ProxySQL
- Automated backup verification with test restore
