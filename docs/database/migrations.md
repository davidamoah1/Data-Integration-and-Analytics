# Database Migrations

> **Version**: 2.0.0  
> **Last Updated**: 2026-08-01  
> **Status**: Active  
> **Owner**: Database Architect

---

## Purpose

Document the database migration strategy.

## Scope

How schema changes are managed and deployed.

## Audience

Developers and DevOps engineers.

---

## 1. Migration Strategy

The platform uses **Alembic** for database migration management, supplemented by `Base.metadata.create_all()` for initial table creation.

### Alembic Configuration

- **Config file**: `alembic.ini`
- **Environment**: `alembic/env.py` — dynamically loads database URL from `config.py`
- **Script location**: `alembic/versions/`
- **Compare type**: Enabled (`compare_type=True`)
- **Compare server default**: Enabled (`compare_server_default=True`)

### Model Registration

All ORM models are imported in `alembic/env.py` to ensure they are discoverable for autogenerate:

```python
# alembic/env.py
import database.db_setup
import authentication.models
import audit.models
import organizations.models
import organizations.workspace_models
import etl.models
import analytics.models
import ai.models
import capture.models
import jobs.models
import notifications.models
import scheduler.models
import storage.models
import enterprise.models
import enterprise.subscription
# ... and more
```

### Startup Flow

```python
# api/main.py (lifespan)
engine = get_engine()
import all_models()  # Register models with Base.metadata
Base.metadata.create_all(engine)  # Create tables if not exist
seed_default_data(db)  # Seed roles, permissions, super admin
```

For production deployments, run migrations explicitly:

```bash
alembic upgrade head
```

## 2. Migration History

| Migration | Description | Date |
|-----------|-------------|------|
| 0001-0014 | Initial schema, auth, orgs, ETL, analytics, AI, capture | 2026-07 |
| 0015 | Audit enhancements — additional indexes and columns | 2026-07 |
| 0016 | Production indexes — 56 indexes across all major tables | 2026-08 |

### Migration 0016: Production Indexes

This migration adds 56 production-grade indexes using conditional creation:

- Uses `_table_exists()` and `_column_exists()` helpers
- Safe to run in any environment (development, testing, production)
- Creates indexes only if the table and all referenced columns exist
- Covers tenant scoping, time-based queries, composite lookups, status filters

## 3. Running Migrations

### Apply All Migrations

```bash
alembic upgrade head
```

### Apply to Specific Revision

```bash
alembic upgrade 0016
```

### Check Current Revision

```bash
alembic current
```

### Check if Schema Matches Models

```bash
alembic check
```

### Generate New Migration

```bash
alembic revision --autogenerate -m "description of change"
```

### Rollback One Migration

```bash
alembic downgrade -1
```

## 4. Conditional Migration Pattern

Production migrations use conditional creation to handle environments where tables may not exist:

```python
def _safe_create_index(op, inspector, index_name, table_name, columns):
    """Create an index only if the table and all columns exist."""
    if not _table_exists(inspector, table_name):
        return
    for col in columns:
        if not _column_exists(inspector, table_name, col):
            return
    existing = inspector.get_indexes(table_name)
    if not any(idx["name"] == index_name for idx in existing):
        op.create_index(index_name, table_name, columns)
```

## 5. Adding New Tables

1. Create a new model class in the appropriate `models.py` file
2. Import the model in `alembic/env.py` (so it registers with `Base.metadata`)
3. Generate a migration: `alembic revision --autogenerate -m "add new_table"`
4. Review and test the generated migration
5. Apply: `alembic upgrade head`

## 6. Adding New Columns to Existing Tables

1. Add the column to the SQLAlchemy model
2. Generate a migration: `alembic revision --autogenerate -m "add column to table"`
3. Review the generated migration (ensure it uses `server_default` for NOT NULL columns)
4. Test on development database
5. Apply: `alembic upgrade head`

## 7. CI/CD Integration

Migrations are verified in the CI pipeline:

- **Integration tests**: `alembic upgrade head` runs before test suite
- **Build verification**: `alembic upgrade head` + `alembic check` verifies schema matches models
- **Database CLI**: `python -m database.manage migrate` wraps Alembic commands

## Related Documents

- [schema.md](schema.md) — Complete schema
- [../architecture/system-design.md](../architecture/system-design.md) — System design
- [../deployment/production.md](../deployment/production.md) — Production deployment
