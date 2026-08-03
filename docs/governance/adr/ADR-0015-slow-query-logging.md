# ADR-0015: Slow Query Logging and Query Optimization

| Field | Value |
|-------|-------|
| **Status** | Accepted |
| **Date** | 2026-08-01 |
| **Decision Maker** | Enterprise Architecture Board |
| **Related ADRs** | ADR-0014 (Production DB Hardening) |

## Context

As the platform scales, database query performance becomes critical. Without visibility into slow queries, performance issues are difficult to diagnose and fix. The platform needed:

- Automatic detection of slow-running queries
- Configurable threshold for what constitutes "slow"
- Logging that integrates with the existing log infrastructure
- Query timeout support to prevent runaway queries

## Decision

Implement slow query logging via SQLAlchemy event listeners:

1. **Event listener**: `_attach_slow_query_listener()` hooks into `before_cursor_execute` and `after_cursor_execute` events
2. **Threshold**: Configurable via `SLOW_QUERY_THRESHOLD_MS` (default 500ms)
3. **Logging**: Slow queries logged at WARNING level with SQL text, duration, and parameters
4. **Query timeout**: `QUERY_TIMEOUT_SECONDS` (default 30s) applied via engine options
5. **Toggle**: `ENABLE_QUERY_LOGGING` env var to enable/disable (default: enabled)

## Alternatives Considered

1. **Database-level slow query log (MySQL)**: Rejected — not portable across SQLite/MySQL
2. **Application-level timing in each query**: Rejected — too invasive and error-prone
3. **External APM tool (Datadog, New Relic)**: Rejected — over-engineered for current scale, deferred to future

## Consequences

**Positive:**
- Automatic detection without code changes in query locations
- Works across all database operations (ORM, raw SQL, migrations)
- Configurable threshold allows tuning per environment
- Query timeout prevents resource exhaustion from runaway queries
- Logs integrate with existing JSON log format

**Negative:**
- Event listeners add minimal overhead to every query
- Threshold must be tuned per environment (too low = noise, too high = miss issues)
- SQL text in logs may contain sensitive data (mitigated by parameterized queries)

## Implementation Notes

- Implemented in `shared/database.py` in the `get_engine()` function
- Listener uses `time.perf_counter()` for high-resolution timing
- Slow query log includes: SQL statement, execution duration (ms), parameters
- In development, threshold defaults to 500ms; in production, can be lowered to 200ms
- Query timeout uses SQLAlchemy's `connect_args` for MySQL and engine-level for SQLite

## Future Considerations

- Query analysis dashboard (aggregate slow queries by pattern)
- Automatic EXPLAIN on slow queries
- Integration with APM tool when scale warrants it
- Per-route query budgets
