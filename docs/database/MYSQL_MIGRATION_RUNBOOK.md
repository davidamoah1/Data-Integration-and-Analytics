# MySQL Migration Runbook

**Version:** 2.0.0
**Last Updated:** 2025-01-17
**Status:** Active

---

## Pre-Migration Checklist

- [ ] Backup current database (verify backup restores correctly)
- [ ] Notify team of maintenance window
- [ ] Verify MySQL 8.x is running and accessible
- [ ] Verify application user credentials
- [ ] Review pending migrations with `alembic history`
- [ ] Run migration against staging/test first
- [ ] Confirm rollback plan

## Initial Setup (Fresh Installation)

### 1. Create Database

```sql
CREATE DATABASE dataflow
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;
```

### 2. Create Application User

```sql
-- Application user (DML only)
CREATE USER 'dataflow_app'@'localhost'
  IDENTIFIED BY '<strong_password>';
GRANT SELECT, INSERT, UPDATE, DELETE
  ON dataflow.* TO 'dataflow_app'@'localhost';

-- Migration user (DDL + DML)
CREATE USER 'dataflow_migrate'@'localhost'
  IDENTIFIED BY '<migration_password>';
GRANT ALL PRIVILEGES
  ON dataflow.* TO 'dataflow_migrate'@'localhost';

FLUSH PRIVILEGES;
```

### 3. Set Environment Variables

```bash
export DB_TYPE=mysql
export MYSQL_HOST=localhost
export MYSQL_PORT=3306
export MYSQL_DATABASE=dataflow
export MYSQL_USER=dataflow_app
export MYSQL_PASSWORD=<strong_password>
export JWT_SECRET_KEY=<min_32_char_random_secret>
export CORS_ORIGINS=https://app.yourdomain.com
```

### 4. Run Migrations

```bash
# Verify connection
alembic current
# Expected: (empty if fresh database)

# Apply all migrations
alembic upgrade head

# Verify
alembic current
# Expected: 0018_dataset_workflow_runs (head)
```

### 5. Start Application

```bash
uvicorn api.main:app --host 0.0.0.0 --port 8000
```

Expected startup logs:
```
DB_TYPE=mysql; skipping create_all(), relying on Alembic migrations.
Auth tables created, default data seeded, subscriptions initialized.
Application startup complete.
Uvicorn running on http://0.0.0.0:8000
```

## Upgrading (Existing Installation)

### 1. Pre-Flight

```bash
# Check current migration version
alembic current

# Check what will be applied
alembic history --indicate-current

# Verify exactly one head
alembic heads
```

### 2. Create Backup

```bash
# Via built-in manager
python -m database.manage backup pre_upgrade_$(date +%Y%m%d)

# Or via mysqldump
mysqldump --single-transaction --routines --triggers \
  -u dataflow_migrate dataflow | gzip > pre_upgrade.sql.gz
```

### 3. Apply Migrations

```bash
# Stop the application gracefully
# Apply migrations
alembic upgrade head

# Verify
alembic current
# Should show the latest head revision
```

### 4. Restart Application

```bash
uvicorn api.main:app --host 0.0.0.0 --port 8000
```

### 5. Smoke Test

```bash
# Health check
curl http://localhost:8000/health

# Login
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@dataflow.io", "password": "..."}'
```

## Rollback Procedure

### Single Migration Rollback

```bash
# Downgrade one step
alembic downgrade -1

# Verify
alembic current
```

### Full Rollback (Restore from Backup)

```bash
# Stop the application
# Drop and recreate database
mysql -u root -e "DROP DATABASE dataflow; CREATE DATABASE dataflow CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"

# Restore backup
gunzip -c pre_upgrade.sql.gz | mysql -u dataflow_migrate dataflow

# Verify
alembic current

# Restart application
```

## Creating New Migrations

### Auto-Generate from Model Changes

```bash
# After modifying SQLAlchemy models:
alembic revision --autogenerate -m "description_of_change"

# Review the generated migration file
# Edit if needed (especially for data migrations)

# Test against a fresh database
alembic upgrade head
alembic downgrade -1
alembic upgrade head
```

### Rules

1. **Never delete existing migrations**
2. **Never squash migrations** in production
3. **Never create multiple heads** (resolve with `alembic merge`)
4. **Always test downgrade** path
5. **Never run `create_all()`** against MySQL

## Migration Verification Commands

```bash
# Verify single head
alembic heads
# Expected: exactly one revision

# Verify migration history is linear
alembic history

# Verify current matches head
alembic current
# Should match output of `alembic heads`

# Check for model/schema drift
alembic check
# If available (Alembic 1.14+)
```

## Troubleshooting

| Issue | Cause | Fix |
|-------|-------|-----|
| `Multiple heads` | Branching migrations | `alembic merge heads -m "merge"` |
| `Can't locate revision` | Missing migration file | Restore from git or backup |
| `Target database is not up to date` | Pending migrations | `alembic upgrade head` |
| `Table already exists` | Partial migration | Manual schema fix or restore |
| `Key too long` | VARCHAR > 768 on utf8mb4 | Reduce column length or use prefix index |

## Environment-Specific Notes

### Development

- Use `DB_TYPE=sqlite` (default)
- Tables auto-created via `create_all()`
- No Alembic required for local dev

### Staging

- Use `DB_TYPE=mysql` with a test database
- Always run migrations here before production
- Safe to reset: `DROP DATABASE; CREATE DATABASE; alembic upgrade head`

### Production

- Use `DB_TYPE=mysql` with production credentials
- Always backup before migration
- Never use root user for application connections
- Monitor slow query log after migration
