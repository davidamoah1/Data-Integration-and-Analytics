# MySQL Migration Runbook

## Pre-Migration Checklist

- [ ] MySQL 8.4+ instance provisioned and accessible
- [ ] `utf8mb4` character set configured (`--character-set-server=utf8mb4`)
- [ ] `utf8mb4_0900_ai_ci` collation configured (`--collation-server=utf8mb4_0900_ai_ci`)
- [ ] Dedicated application database user created (NOT `root`)
- [ ] Application user granted: `CREATE, ALTER, DROP, INDEX, INSERT, UPDATE, DELETE, SELECT` on the target database
- [ ] `MYSQL_ROOT_PASSWORD` set and stored in a secret manager
- [ ] Application environment variables configured (see `.env.example`)
- [ ] `JWT_SECRET_KEY` set to a strong random secret (min 32 chars)
- [ ] `ENCRYPTION_KEY` set to a separate Fernet key
- [ ] `CORS_ORIGINS` set to allowed frontend domains (never `*`)
- [ ] Backup of any existing data completed
- [ ] `alembic heads` shows exactly one head revision

## Step 1: Verify Migration History

```bash
# Should show exactly one head
alembic heads

# Review migration chain
alembic history --verbose
```

## Step 2: Configure Environment

```bash
# Option A: Use DATABASE_URL (recommended)
export DATABASE_URL="mysql+pymysql://aedip_user:password@mysql-host:3306/aedip?charset=utf8mb4"

# Option B: Use individual variables
export DB_TYPE=mysql
export MYSQL_HOST=mysql-host
export MYSQL_PORT=3306
export MYSQL_DATABASE=aedip
export MYSQL_USER=aedip_user
export MYSQL_PASSWORD=********
```

## Step 3: Validate Configuration

```bash
python -c "import config; config.validate_config(); print('Config valid')"
```

This checks:
- `DB_TYPE` is `mysql`
- All `MYSQL_*` variables are set
- `JWT_SECRET_KEY` is set and >= 32 chars
- `CORS_ORIGINS` is not `*`
- `ENCRYPTION_KEY` is set (warns if not)

## Step 4: Run Migrations

```bash
# Apply all migrations to head
alembic upgrade head

# Verify schema matches models (no drift)
alembic check
```

### Expected Output

```
INFO  [alembic.runtime.migration] Running upgrade  -> 0001_phase4_iam, ...
...
INFO  [alembic.runtime.migration] Running upgrade eb32b7fc465a -> e0342a5584d1, convert_monetary_float_to_decimal
```

`alembic check` should report: `No new upgrade operations detected.`

## Step 5: Verify Health

```bash
# Start the application
uvicorn api.main:app --host 0.0.0.0 --port 8000

# Check database health
curl http://localhost:8000/health/db
```

Expected response:
```json
{
  "status": "ready",
  "database": "connected",
  "migration_version": "e0342a5584d1",
  "pool_size": 10,
  "pool_checked_in": 10,
  "pool_checked_out": 0
}
```

## Step 6: Seed Default Data

On first request, the application seeds:
- Default roles (platform_owner, org_admin, analyst, viewer)
- Default permissions
- Super admin user (if `SUPER_ADMIN_EMAIL` and `SUPER_ADMIN_PASSWORD` are set)

This happens automatically via `get_db()` dependency.

## Step 7: Run Tests

```bash
# Unit tests
pytest tests/ -x -q

# Integration tests (requires MySQL)
DB_TYPE=mysql pytest tests/ -x -q
```

## Rollback Procedure

If a migration fails or causes issues:

```bash
# Roll back one migration
alembic downgrade -1

# Roll back to specific revision
alembic downgrade <revision_id>

# Roll back all migrations (DESTRUCTIVE)
alembic downgrade base
```

**Never roll back without a fresh backup.**

## Docker Deployment

```bash
# Start all services (API, dashboard, MySQL, Redis, worker)
docker-compose up -d

# Run migrations inside the API container
docker-compose exec api alembic upgrade head

# Check health
docker-compose exec api curl http://localhost:8000/health/db
```

## Troubleshooting

### "Target database is not up to date"

The `alembic_version` table in the database doesn't match the migration head.
Run `alembic upgrade head` first.

### "table users already exists"

The database already has tables but no `alembic_version` table.
This happens when tables were created via `create_all()` instead of migrations.
Fix: stamp the current state and then upgrade:

```bash
alembic stamp head  # Mark current schema as up-to-date
```

### "Access denied for user"

- Verify `MYSQL_USER` and `MYSQL_PASSWORD` are correct.
- Verify the user has permissions on the target database.
- Check that the user can connect from the application host.

### "Can't connect to MySQL server"

- Verify `MYSQL_HOST` and `MYSQL_PORT`.
- Check network connectivity: `telnet mysql-host 3306`.
- Check MySQL is running: `mysqladmin ping -h mysql-host`.
- Check firewall rules.

### Schema Drift Detected

Run `alembic check` to identify drift. Common causes:
- Model changes without a corresponding migration
- Missing model imports in `alembic/env.py`
- `server_default` mismatch between model and migration

Fix: Create a new migration with `alembic revision --autogenerate`.
