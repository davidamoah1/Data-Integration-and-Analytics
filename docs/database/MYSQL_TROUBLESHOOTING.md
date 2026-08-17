# MySQL Troubleshooting Guide

**Version:** 2.0.0
**Last Updated:** 2025-01-17
**Status:** Active

---

## Connection Issues

### `OperationalError: Can't connect to MySQL server`

**Cause:** MySQL server is not running or not reachable.

**Fix:**
```bash
# Check MySQL is running
systemctl status mysql
# or
mysqladmin -u root ping

# Check host/port
mysql -u dataflow_app -p -h $MYSQL_HOST -P $MYSQL_PORT -e "SELECT 1;"

# Check firewall
telnet $MYSQL_HOST $MYSQL_PORT
```

### `OperationalError: Access denied for user`

**Cause:** Wrong credentials or missing privileges.

**Fix:**
```bash
# Verify credentials work
mysql -u $MYSQL_USER -p$MYSQL_PASSWORD $MYSQL_DATABASE -e "SELECT 1;"

# Re-grant privileges if needed
mysql -u root -e "GRANT ALL PRIVILEGES ON dataflow.* TO 'dataflow_app'@'localhost'; FLUSH PRIVILEGES;"
```

### `TimeoutError: Pool timeout exceeded`

**Cause:** All connections in the pool are in use.

**Fix:**
```bash
# Increase pool size
export POOL_SIZE=20
export MAX_OVERFLOW=40

# Check for connection leaks
mysql -u root -e "SHOW PROCESSLIST;"

# Kill idle connections
mysql -u root -e "SELECT CONCAT('KILL ', id, ';') FROM information_schema.processlist WHERE command='Sleep' AND time > 300;"
```

### `OperationalError: MySQL server has gone away`

**Cause:** Connection was idle longer than MySQL's `wait_timeout`.

**Fix:**
The application already uses `pool_pre_ping=True` which validates connections
before use. If this still occurs:

```bash
# Reduce recycle interval
export POOL_RECYCLE=1800  # 30 minutes instead of 1 hour

# Check MySQL timeout
mysql -u root -e "SHOW VARIABLES LIKE 'wait_timeout';"
```

## Migration Issues

### `Multiple heads detected`

**Cause:** Two developers created migrations from the same parent.

**Fix:**
```bash
# View the heads
alembic heads

# Merge them
alembic merge heads -m "merge_branches"

# Apply
alembic upgrade head
```

### `Can't locate revision`

**Cause:** A migration file was deleted or the `down_revision` points to a non-existent file.

**Fix:**
```bash
# Check git for the missing file
git log --all --follow -- alembic/versions/

# If truly lost, stamp to skip it
alembic stamp <next_known_revision>
```

### `Table already exists`

**Cause:** Partial migration run or `create_all()` was accidentally invoked.

**Fix:**
```bash
# Check what Alembic thinks is current
alembic current

# If migration partially applied, stamp to the correct version
alembic stamp <revision_that_created_the_table>

# Then continue
alembic upgrade head
```

### `Key too long (max 3072 bytes)`

**Cause:** VARCHAR column in a unique index exceeds MySQL's utf8mb4 key limit
(768 characters max for a single-column index).

**Fix:**
- Reduce the column length: `String(768)` max for indexed columns
- Or use a prefix index in the migration:
```python
op.create_index('ix_name', 'table', [sa.text('column(191)')])
```

## Performance Issues

### Slow Queries

The application logs queries exceeding `SLOW_QUERY_THRESHOLD_MS` (default 500ms).

```bash
# Enable MySQL slow query log
mysql -u root -e "SET GLOBAL slow_query_log = 'ON'; SET GLOBAL long_query_time = 1;"

# View slow queries
mysqladmin -u root proc

# Check for missing indexes
EXPLAIN SELECT ... FROM ... WHERE ...;
```

### High Connection Count

```bash
# Check current connections
mysql -u root -e "SHOW STATUS LIKE 'Threads_connected';"

# Check max connections setting
mysql -u root -e "SHOW VARIABLES LIKE 'max_connections';"

# Increase if needed
mysql -u root -e "SET GLOBAL max_connections = 200;"
```

### Large Table Operations

For tables with millions of rows:

```bash
# Check table sizes
mysql -u root -e "
  SELECT table_name, 
         ROUND(data_length/1024/1024, 2) AS data_mb,
         ROUND(index_length/1024/1024, 2) AS index_mb,
         table_rows
  FROM information_schema.tables
  WHERE table_schema = 'dataflow'
  ORDER BY data_length DESC
  LIMIT 20;"
```

## Application Issues

### `DB_TYPE=mysql; skipping create_all()` but tables missing

**Cause:** Alembic migrations were not run.

**Fix:**
```bash
alembic upgrade head
```

### `RuntimeError: init_db() must not be run against MySQL`

**Cause:** Development utility was invoked in production mode.

**Fix:** Use `alembic upgrade head` instead of `init_db()` for MySQL.

### JSON column returns string instead of dict

**Cause:** MySQL JSON column working correctly, but application code expects
different deserialization.

**Fix:** MySQL natively stores JSON. SQLAlchemy's `JSON` type handles
serialization/deserialization automatically. If you see string values, check
that the column type is `JSON` (not `Text`) in both the model and migration.

### `IntegrityError: Duplicate entry`

**Cause:** Unique constraint violation.

**Fix:**
```bash
# Check existing data
mysql -u dataflow_app -p dataflow -e "SELECT * FROM <table> WHERE <unique_column> = '<value>';"

# If it's a seeding issue, the application handles duplicates gracefully
# via INSERT ... ON DUPLICATE KEY or try/except
```

## Monitoring

### Key Metrics to Watch

```sql
-- Active connections
SHOW STATUS LIKE 'Threads_connected';

-- Connection errors
SHOW STATUS LIKE 'Connection_errors%';

-- Slow queries count
SHOW STATUS LIKE 'Slow_queries';

-- Table lock waits
SHOW STATUS LIKE 'Table_locks_waited';

-- InnoDB buffer pool hit rate
SHOW STATUS LIKE 'Innodb_buffer_pool_read_requests';
SHOW STATUS LIKE 'Innodb_buffer_pool_reads';
```

### Application-Level Monitoring

- Slow query listener logs to application logger (threshold: `SLOW_QUERY_THRESHOLD_MS`)
- Pool exhaustion triggers warning logs
- Connection failures are logged with details (no credentials exposed)

## Emergency Procedures

### Database Unresponsive

```bash
# 1. Check if MySQL is running
systemctl status mysql

# 2. Check disk space
df -h /var/lib/mysql

# 3. Check memory
free -m

# 4. If OOM, restart with reduced buffer pool
mysqld --innodb-buffer-pool-size=256M

# 5. Check error log
tail -100 /var/log/mysql/error.log
```

### Corrupted Table

```bash
# 1. Check table
mysqlcheck -u root -p dataflow <table_name>

# 2. Repair if possible
mysqlcheck -u root -p --repair dataflow <table_name>

# 3. If repair fails, restore from backup
# See MYSQL_BACKUP_RECOVERY.md
```

## Related Documents

- [MYSQL_ARCHITECTURE.md](MYSQL_ARCHITECTURE.md) — Architecture overview
- [MYSQL_MIGRATION_RUNBOOK.md](MYSQL_MIGRATION_RUNBOOK.md) — Migration guide
- [MYSQL_BACKUP_RECOVERY.md](MYSQL_BACKUP_RECOVERY.md) — Backup procedures
