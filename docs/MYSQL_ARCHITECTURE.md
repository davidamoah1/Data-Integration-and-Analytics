# MySQL Architecture

## Overview

The AEDIP platform uses SQLAlchemy as its ORM with Alembic for schema migrations.
The production database is MySQL 8.4+ with `utf8mb4` character set.

## Stack

| Component | Value |
|-----------|-------|
| ORM | SQLAlchemy 2.x (declarative_base) |
| Driver | PyMySQL (`mysql+pymysql://`) |
| Migration Tool | Alembic |
| Database | MySQL 8.4+ |
| Charset | `utf8mb4` |
| Collation | `utf8mb4_0900_ai_ci` |

## Connection Configuration

### Option 1: DATABASE_URL (recommended for production)

Set a single environment variable:

```
DATABASE_URL=mysql+pymysql://aedip_user:password@db-host:3306/aedip?charset=utf8mb4
```

When `DATABASE_URL` is set, it takes precedence over individual `MYSQL_*` variables.
The `DB_TYPE` is inferred from the URL scheme.

### Option 2: Individual variables

```
DB_TYPE=mysql
MYSQL_HOST=db-host
MYSQL_PORT=3306
MYSQL_DATABASE=aedip
MYSQL_USER=aedip_user
MYSQL_PASSWORD=********
```

The application constructs the URL as:
`mysql+pymysql://{user}:{pass}@{host}:{port}/{db}?charset=utf8mb4`

## Connection Pooling

Pool settings are configured in `config.py` and applied in `shared/database.py`:

| Setting | Default | Env Var |
|---------|---------|---------|
| `pool_pre_ping` | `True` (always on) | — |
| `pool_size` | 10 | `POOL_SIZE` |
| `max_overflow` | 20 | `MAX_OVERFLOW` |
| `pool_timeout` | 30s | `POOL_TIMEOUT` |
| `pool_recycle` | 3600s | `POOL_RECYCLE` |

- **`pool_pre_ping=True`**: SQLAlchemy tests each connection before use,
  preventing errors from stale connections after MySQL's `wait_timeout`.
- **`pool_recycle=3600`**: Connections are recycled every hour, well within
  MySQL's default `wait_timeout` of 8 hours.
- Pool settings are only applied for MySQL (`DB_TYPE=mysql`). SQLite uses
  SQLAlchemy's default `SingletonThreadPool`.

## Transaction Model

- Sessions are created via `sessionmaker(bind=engine, expire_on_commit=False)`.
- `expire_on_commit=False` prevents lazy-load errors after commit in
  detached-object scenarios.
- The FastAPI dependency `get_db()` yields a session per request and closes
  it in a `finally` block.
- `ensure_default_data()` seeds roles/permissions on first request.
- **No explicit `begin()` calls** — SQLAlchemy 2.x auto-begins transactions.
- Commits are explicit; rollbacks should be used in exception handlers.

## Schema Management

- **Production MySQL**: Schema is owned exclusively by Alembic migrations.
  `Base.metadata.create_all()` is a no-op when `DB_TYPE=mysql`.
- `init_db()` raises `RuntimeError` if called against MySQL.
- Migrations must be applied with `alembic upgrade head` before starting the app.
- `alembic check` detects schema drift between models and the database.

## Data Types

### Monetary Columns

Financial amounts use `Numeric(18, 2)` (DECIMAL) instead of `Float`:

- `sales.sales`, `sales.discount`, `sales.profit`
- `saas_subscription_plans.price_monthly`, `saas_subscription_plans.price_yearly`

This prevents floating-point rounding errors in financial calculations.

### BigInteger with SQLite Variant

Primary keys and foreign keys use `BigInteger().with_variant(Integer, "sqlite")`
(exported as `BigInt` from `shared/database.py`). This ensures 64-bit integers
on MySQL while keeping SQLite compatibility for local development.

### JSON Columns

JSON columns use SQLAlchemy's `JSON` type, which maps to MySQL's native `JSON`
type. On SQLite, it maps to `TEXT`. JSON columns must not have a `server_default`
on MySQL (BLOB/TEXT/JSON columns cannot have a DEFAULT value).

### Timestamps

- `TIMESTAMP` with `server_default=func.now()` or `server_default=text("CURRENT_TIMESTAMP")`.
- `onupdate=func.now()` for `updated_at` columns.

## Character Set

- The connection URL includes `?charset=utf8mb4`.
- Docker-compose sets `--character-set-server=utf8mb4` and
  `--collation-server=utf8mb4_0900_ai_ci`.
- This supports full Unicode including emoji and 4-byte characters.

## Health Checks

| Endpoint | Purpose |
|----------|---------|
| `GET /health` | Lightweight: API + DB connectivity + record count |
| `GET /health/db` | DB connectivity, migration version, pool stats |
| `GET /health/detailed` | All subsystems (DB, ETL, AI, scheduler, etc.) |

The `/health/db` endpoint reports:
- `status`: `ready` or `not_ready`
- `migration_version`: current Alembic revision
- `pool_size`, `pool_checked_in`, `pool_checked_out`

No credentials or connection strings are exposed in health check responses.
