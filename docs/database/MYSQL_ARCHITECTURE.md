# MySQL Production Architecture

**Version:** 2.0.0
**Last Updated:** 2025-01-17
**Status:** Active

---

## Overview

DataFlow uses MySQL 8.x as the production database backend. The architecture
separates schema management (Alembic) from application data access (SQLAlchemy
ORM), with multi-tenant isolation enforced at the query layer.

## Architecture Diagram

```
                    +------------------+
                    |   Next.js 14     |
                    |   Frontend       |
                    +--------+---------+
                             |
                             | HTTP/REST
                             v
                    +------------------+
                    |   FastAPI API    |
                    |   (Uvicorn)      |
                    +--------+---------+
                             |
              +--------------+--------------+
              |                             |
              v                             v
     +--------+--------+          +--------+--------+
     |  SQLAlchemy ORM  |          |  Redis Queue    |
     |  Session Pool    |          |  (Jobs/Cache)   |
     +--------+---------+          +--------+--------+
              |                             |
              v                             v
     +--------+---------+          +--------+--------+
     |  MySQL 8.x       |          |  Worker Process |
     |  (Production)    |<---------+  (Background)   |
     |                  |          +------------------+
     +------------------+
```

## Connection Architecture

### Engine Configuration

```python
# shared/database.py
engine = create_engine(
    "mysql+pymysql://user:pass@host:port/db?charset=utf8mb4",
    pool_pre_ping=True,      # Validate connections before use
    pool_size=10,            # Maintained connection count
    pool_recycle=3600,       # Recycle connections after 1 hour
    max_overflow=20,         # Allow up to 30 total connections
    pool_timeout=30,         # Wait 30s for a connection from pool
)
```

### Pool Behavior

| Setting | Default | Purpose |
|---------|---------|---------|
| `pool_pre_ping` | `True` | Validates connections before reuse (handles MySQL `wait_timeout`) |
| `pool_size` | `10` | Steady-state connection count |
| `max_overflow` | `20` | Extra connections under load (up to 30 total) |
| `pool_recycle` | `3600` | Prevents stale connections (MySQL default timeout: 28800s) |
| `pool_timeout` | `30` | Max wait time for a connection slot |

### Session Management

- **Factory:** `sessionmaker(bind=engine, expire_on_commit=False)`
- **Dependency:** `get_db()` yields a session per request
- **Cleanup:** `finally: db.close()` on every request
- **No lazy loading after close:** `expire_on_commit=False` allows safe attribute access

## Schema Management

### Ownership Model

```
+------------------+     +------------------+
|  Alembic         |---->|  MySQL Schema    |
|  (migrations)    |     |  (DDL owner)     |
+------------------+     +------------------+
         |                        ^
         |                        |
         v                        |
+------------------+     +------------------+
|  SQLAlchemy      |     |  Application     |
|  Models (ORM)    |---->|  (DML only)      |
+------------------+     +------------------+
```

- **DDL (schema changes):** Exclusively via `alembic upgrade head`
- **DML (data operations):** Via SQLAlchemy ORM in application code
- **`create_all()`:** Disabled for MySQL — guarded in `shared/database.py`, `api/main.py`, and `database/db_setup.py`

### Migration Chain

```
0001_phase4_iam -> 0002_phase5_etl -> 0003_phase6_ai -> ... -> 0018_dataset_workflow_runs (HEAD)
```

- 21 migrations total
- Single linear chain (no branches)
- Batch mode disabled for MySQL (used for SQLite only)

## Multi-Tenant Architecture

### Isolation Strategy

Every data-bearing table includes `organization_id`:

```sql
-- 82 tables with organization_id, all indexed
SELECT * FROM datasets WHERE organization_id = :org_id;
```

### Enforcement Points

1. **API Layer:** `get_current_organization_id()` extracts org from JWT
2. **Service Layer:** All queries filter by `organization_id`
3. **Route Guards:** `require_permissions()`, `require_any_role()`
4. **Database:** Foreign key constraints prevent orphan records

### Shared Data

System/demo datasets have `organization_id = NULL` and are visible to all
organizations (read-only). No tenant data leaks across organizations.

## Table Statistics

| Category | Count | Examples |
|----------|-------|---------|
| Authentication | 12 | users, roles, permissions, sessions |
| Analytics | 6 | dashboards, widgets, kpis |
| AI Platform | 15 | conversations, insights, forecasts |
| ETL Pipeline | 10 | pipelines, jobs, profiles |
| Studios | 18 | workspaces, experiments, presentations |
| SaaS/Billing | 11 | plans, subscriptions, invoices |
| Organizations | 5 | organizations, branches, teams |
| Capture | 6 | batches, documents, templates |
| Workflows | 6 | definitions, executions, lineage |
| ML Models | 6 | models, training runs, predictions |
| Validation | 5 | sessions, findings, rules |
| Other | 34 | jobs, files, connectors, notifications |
| **Total** | **134** | |

## Environment Variables

| Variable | Default | Required | Description |
|----------|---------|----------|-------------|
| `DB_TYPE` | `sqlite` | Yes (production) | Must be `mysql` for production |
| `MYSQL_HOST` | `localhost` | Yes | Database server hostname |
| `MYSQL_PORT` | `3306` | No | Database server port |
| `MYSQL_DATABASE` | - | Yes | Database name |
| `MYSQL_USER` | - | Yes | Database user |
| `MYSQL_PASSWORD` | - | Yes | Database password |
| `POOL_SIZE` | `10` | No | Connection pool size |
| `POOL_TIMEOUT` | `30` | No | Pool wait timeout (seconds) |
| `POOL_RECYCLE` | `3600` | No | Connection recycle interval (seconds) |
| `MAX_OVERFLOW` | `20` | No | Extra connections beyond pool_size |
| `SLOW_QUERY_THRESHOLD_MS` | `500` | No | Log queries slower than this |

## Security

### Connection Security

- PyMySQL with `charset=utf8mb4` (prevents encoding attacks)
- TLS connection supported (MySQL 8 default: auto-generated certs)
- No credentials in source code or logs
- Environment variable injection only

### Application User Privileges

```sql
-- Least privilege: application user has DML only on its database
CREATE USER 'dataflow_app'@'%' IDENTIFIED BY '<strong_password>';
GRANT SELECT, INSERT, UPDATE, DELETE ON dataflow.* TO 'dataflow_app'@'%';
-- Alembic migration user needs DDL
GRANT ALL PRIVILEGES ON dataflow.* TO 'dataflow_migrate'@'%';
```

### Observability Guards

- Slow query logging (configurable threshold)
- Connection pool exhaustion warnings
- No SQL in error responses to clients
- No credentials in application logs

## Performance Characteristics

### Tested Metrics (Development MySQL 8.4.9)

| Operation | Duration |
|-----------|----------|
| Full 21-migration upgrade | < 15s |
| E2E workflow (25 rows) | < 30s |
| PPTX generation | < 5s |
| Startup (563 routes) | < 5s |

### Index Strategy

- All `organization_id` columns indexed (82 tables)
- Composite indexes on frequently filtered pairs
- Foreign key indexes auto-created by MySQL
- Production indexes added in migration `0016_prod_indexes`

## Related Documents

- [MYSQL_MIGRATION_RUNBOOK.md](MYSQL_MIGRATION_RUNBOOK.md) — Step-by-step migration guide
- [MYSQL_BACKUP_RECOVERY.md](MYSQL_BACKUP_RECOVERY.md) — Backup and restore procedures
- [MYSQL_TROUBLESHOOTING.md](MYSQL_TROUBLESHOOTING.md) — Common issues and solutions
- [backup-recovery.md](backup-recovery.md) — General backup documentation
- [indexing.md](indexing.md) — Index strategy documentation
