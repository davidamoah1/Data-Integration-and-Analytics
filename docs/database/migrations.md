# Database Migrations

> **Version**: 1.0.0  
> **Last Updated**: 2026-07-30  
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

## 1. Current Strategy

DataFlow uses a **code-first** approach — no Alembic migrations.

- All models inherit from `Base` (defined in `shared/database.py`)
- On application startup (non-serverless), `Base.metadata.create_all(engine)` creates all tables
- If a table already exists, it is skipped (no schema diff)
- New columns must be added manually via SQL or by dropping and recreating the table

### Startup Flow

```python
# api/main.py (lifespan)
engine = get_engine()
import all_models()  # Register models with Base.metadata
Base.metadata.create_all(engine)  # Create tables if not exist
seed_default_data(db)  # Seed roles, permissions, super admin
```

## 2. Limitations

- **No schema diff**: `create_all` only creates missing tables — it does not add new columns to existing tables
- **No rollback**: No way to revert schema changes
- **No migration history**: No record of when schema changes were applied
- **Manual column additions**: New columns on existing tables require manual SQL

## 3. Adding New Tables

1. Create a new model class in the appropriate `models.py` file
2. Import the model in `api/main.py` lifespan (so it registers with `Base.metadata`)
3. On next startup, the table will be auto-created

## 4. Adding New Columns to Existing Tables

> **⚠️ Manual step required**: `create_all` does not add columns to existing tables.

1. Add the column to the SQLAlchemy model
2. Run a manual SQL `ALTER TABLE` on the database:

```sql
ALTER TABLE users ADD COLUMN new_column VARCHAR(255) NULL;
```

3. Deploy the updated code

## 5. Future: Alembic Migration

> **⚠️ Planned**: Migrating to Alembic for proper migration management.

Benefits:
- Automatic schema diff generation
- Migration version history
- Rollback support
- Zero-downtime migrations

## Related Documents

- [schema.md](schema.md) — Complete schema
- [../architecture/system-design.md](../architecture/system-design.md) — System design
- [../deployment/production.md](../deployment/production.md) — Production deployment
