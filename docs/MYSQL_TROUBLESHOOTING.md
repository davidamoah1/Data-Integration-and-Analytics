# MySQL Troubleshooting

## Common Issues

### Connection Refused

**Symptom**: `Can't connect to MySQL server on 'host:3306'`

**Solutions**:
1. Verify MySQL is running: `mysqladmin ping -h host`
2. Check `MYSQL_HOST` and `MYSQL_PORT` environment variables
3. Test network connectivity: `telnet host 3306` or `nc -zv host 3306`
4. Check firewall rules allow inbound 3306
5. Verify MySQL is listening on the expected address (`bind-address`)

### Access Denied

**Symptom**: `Access denied for user 'aedip_user'@'app-host'`

**Solutions**:
1. Verify `MYSQL_USER` and `MYSQL_PASSWORD` are correct
2. Check user exists: `SELECT user, host FROM mysql.user WHERE user='aedip_user';`
3. Verify grants: `SHOW GRANTS FOR 'aedip_user'@'%';`
4. Ensure user can connect from the application host (wildcard `%` or specific IP)
5. For MySQL 8.4+, check authentication plugin: `caching_sha2_password` is default

### Stale Connections

**Symptom**: `MySQL server has gone away` or `OperationalError: (2013, ...)`

**Solutions**:
- `pool_pre_ping=True` is enabled by default — connections are tested before use
- `pool_recycle=3600` recycles connections every hour
- If MySQL's `wait_timeout` is lower than `pool_recycle`, reduce `POOL_RECYCLE`:
  ```
  POOL_RECYCLE=300
  ```
- Check MySQL `wait_timeout`: `SHOW VARIABLES LIKE 'wait_timeout';`

### Pool Exhaustion

**Symptom**: `TimeoutError: QueuePool limit of size X overflow Y reached`

**Solutions**:
1. Increase pool size:
   ```
   POOL_SIZE=20
   MAX_OVERFLOW=40
   POOL_TIMEOUT=60
   ```
2. Check for connection leaks (unclosed sessions)
3. Monitor pool status via `/health/db` endpoint:
   ```json
   {"pool_size": 10, "pool_checked_in": 5, "pool_checked_out": 5}
   ```
4. If `pool_checked_out` equals `pool_size + max_overflow`, the pool is exhausted

### Schema Drift

**Symptom**: `alembic check` reports `New upgrade operations detected`

**Solutions**:
1. Run `alembic check` to identify the drift
2. Common causes:
   - Model changes without a migration → create one: `alembic revision --autogenerate`
   - Missing model imports in `alembic/env.py` → add `import <module>.models`
   - `server_default` mismatch → align model with migration
3. After fixing, verify: `alembic check` should report `No new upgrade operations detected`

### Migration Conflicts

**Symptom**: `alembic heads` shows multiple heads

**Solutions**:
1. Identify the heads: `alembic heads`
2. Create a merge revision: `alembic merge -m "merge_heads" head1 head2`
3. Run `alembic upgrade head`
4. Verify single head: `alembic heads`

### Character Set Issues

**Symptom**: Garbled text, `???` characters, or emoji storage errors

**Solutions**:
1. Verify database charset: `SHOW VARIABLES LIKE 'character_set_database';`
2. Should be `utf8mb4` — if not:
   ```sql
   ALTER DATABASE aedip CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci;
   ```
3. Verify connection URL includes `?charset=utf8mb4`
4. Check table charsets: `SHOW TABLE STATUS FROM aedip;`
5. Convert specific table if needed:
   ```sql
   ALTER TABLE users CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci;
   ```

### Slow Queries

**Symptom**: Application latency, timeout errors

**Solutions**:
1. Check slow query log (application-level):
   - Slow queries are logged at `WARNING` level by `database` logger
   - Threshold: `SLOW_QUERY_THRESHOLD_MS` (default 500ms)
2. Enable MySQL slow query log:
   ```sql
   SET GLOBAL slow_query_log = 'ON';
   SET GLOBAL long_query_time = 1;
   ```
3. Use `EXPLAIN` to analyze slow queries:
   ```sql
   EXPLAIN SELECT * FROM sales WHERE region = 'West' AND category = 'Furniture';
   ```
4. Add missing indexes identified by `EXPLAIN`
5. Consider increasing `QUERY_TIMEOUT_SECONDS` if legitimate long-running queries exist

### Lock Contention

**Symptom**: `Lock wait timeout exceeded`

**Solutions**:
1. Identify blocking transaction:
   ```sql
   SELECT * FROM information_schema.innodb_trx WHERE trx_state = 'LOCK WAIT';
   SELECT * FROM information_schema.innodb_trx WHERE trx_state = 'RUNNING' AND trx_mysql_thread_id != CONNECTION_ID();
   ```
2. Kill the blocking session if necessary:
   ```sql
   KILL <connection_id>;
   ```
3. Review long-running transactions in application code
4. Consider shorter transaction scopes

### JSON Column Default Error

**Symptom**: `BLOB/TEXT/JSON column can't have a default value`

**Solutions**:
- MySQL does not allow `DEFAULT` on JSON/BLOB/TEXT columns
- Use Python-side `default=` on the model instead of `server_default=`
- Example: `Column(JSON, default=dict, nullable=False)` (no `server_default`)

### Docker MySQL Won't Start

**Symptom**: `docker-compose up db` fails or health check never passes

**Solutions**:
1. Check logs: `docker-compose logs db`
2. Verify data volume is not corrupted: `docker-compose down -v` and restart
3. Ensure `MYSQL_ROOT_PASSWORD` is set (MySQL refuses to start without it)
4. Check disk space: `docker system df`
5. Increase `start_period` in healthcheck if MySQL is slow to initialize

## Diagnostic Queries

```sql
-- Database version and charset
SELECT VERSION();
SHOW VARIABLES LIKE 'character_set%';
SHOW VARIABLES LIKE 'collation%';

-- Connection count
SHOW STATUS LIKE 'Threads_connected';
SHOW VARIABLES LIKE 'max_connections';

-- Migration version
SELECT version_num FROM alembic_version;

-- Table sizes
SELECT table_name, table_rows, data_length, index_length
FROM information_schema.tables
WHERE table_schema = 'aedip'
ORDER BY data_length DESC;

-- Index usage
SELECT table_name, index_name, cardinality
FROM information_schema.statistics
WHERE table_schema = 'aedip'
ORDER BY table_name, index_name;
```

## Log Locations

| Log | Location |
|-----|----------|
| Application | `logs/pipeline.log` (or stdout in Docker) |
| Slow queries | Application log at `WARNING` level |
| MySQL error log | `/var/lib/mysql/<hostname>.err` (Docker: `docker-compose logs db`) |
| Alembic | stdout (capture with `alembic upgrade head 2>&1`) |
