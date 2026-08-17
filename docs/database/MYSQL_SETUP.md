# MySQL Setup Guide

## Overview

DataFlow supports both SQLite (development) and MySQL 8.0 (production).
The database backend is selected via the `DB_TYPE` environment variable.

## Configuration

### SQLite (Default — Development)

No configuration needed. The database is created automatically at
`database/etl_database.db` using `create_all()`.

```bash
# No DB_TYPE needed, or explicitly:
DB_TYPE=sqlite
```

### MySQL (Production)

```bash
DB_TYPE=mysql
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_DATABASE=dataflow
MYSQL_USER=dataflow_user
MYSQL_PASSWORD=<strong_password>
```

The connection string is built as:
```
mysql+pymysql://{user}:{password}@{host}:{port}/{database}?charset=utf8mb4
```

## Database Initialization

### SQLite

Tables are created automatically via `create_all()` on first startup.
This is guarded and only runs in SQLite mode — it is never called
against MySQL to prevent accidental schema changes.

### MySQL

Schema management uses Alembic migrations:

```bash
# Create a new migration
alembic revision --autogenerate -m "Description"

# Apply migrations
alembic upgrade head

# Check current version
alembic current

# Rollback one step
alembic downgrade -1
```

The Alembic configuration is at `alembic.ini` with migrations in
`alembic/versions/`.

## Schema Architecture

Key tables:

| Table | Module | Purpose |
|-------|--------|---------|
| `users` | `authentication/models.py` | User accounts |
| `roles` | `authentication/models.py` | Role definitions |
| `user_roles` | `authentication/models.py` | User-role assignments |
| `organizations` | `organizations/models.py` | Tenant organizations |
| `sessions` | `authentication/models.py` | Active sessions |
| `audit_logs` | `audit/models.py` | Audit trail |
| `datasets` | `etl/models.py` | Dataset metadata |
| `jobs` | `jobs/models.py` | Background job tracking |
| `dataset_workflow_runs` | `services/dataset_workflow_models.py` | Workflow state persistence |
| `dashboards` | `analytics/models.py` | Dashboard configurations |
| `reports` | `analytics/models.py` | Report records |
| `kpi_definitions` | `analytics/models.py` | KPI definitions |
| `cleaning_jobs` | `studios/models.py` | Cleaning job tracking |
| `statistical_analyses` | `studios/models.py` | Statistical analysis records |
| `presentations` | `studios/models.py` | Presentation records |
| `file_metadata` | `storage/models.py` | File storage metadata |

## Multi-Tenant Isolation

Every data table includes an `organization_id` column. All queries filter
by the current user's organization, enforced via `get_current_organization_id()`.

## Safety Guards

- `create_all()` is only called for SQLite — never for MySQL
- Alembic migrations are the only way to modify MySQL schema
- Connection pooling uses PyMySQL with `charset=utf8mb4`
- SQL injection is prevented by SQLAlchemy's parameterized queries
