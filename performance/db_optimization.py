"""Database Optimization.

Provides:
  - IndexManager: Define and create optimized indexes for large tables
  - QueryOptimizer: Query analysis and optimization suggestions
  - ChunkedQuery: Process large result sets in chunks to avoid memory issues
  - DBStats: Database size, table counts, slow query tracking

Usage:
    from performance.db_optimization import IndexManager, ChunkedQuery

    # Create indexes for performance
    manager = IndexManager(db)
    manager.ensure_index("users", ["organization_id", "is_deleted"], name="idx_users_org_active")
    manager.ensure_index("audit_logs", ["created_at"], name="idx_audit_created")

    # Process millions of rows in chunks
    for chunk in ChunkedQuery.iter_chunks(db, select(User), chunk_size=5000):
        for user in chunk:
            process(user)
"""

from __future__ import annotations

import logging
import time
from collections.abc import Generator, Iterable
from dataclasses import dataclass, field

from sqlalchemy import inspect, text
from sqlalchemy.orm import Session as DbSession

logger = logging.getLogger("performance.db")


@dataclass
class DBStats:
    """Database statistics for monitoring."""

    table_count: int = 0
    total_rows: int = 0
    index_count: int = 0
    db_size_mb: float = 0.0
    slow_queries: list[dict] = field(default_factory=list)
    table_stats: dict[str, dict] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "table_count": self.table_count,
            "total_rows": self.total_rows,
            "index_count": self.index_count,
            "db_size_mb": round(self.db_size_mb, 2),
            "slow_queries": self.slow_queries[-20:],
            "table_stats": self.table_stats,
        }


class IndexManager:
    """Manages database indexes for performance optimization.

    Ensures critical indexes exist without manual migration.
    Idempotent â€” safe to call multiple times.
    """

    # Critical indexes for production performance
    CRITICAL_INDEXES: list[dict] = [
        {
            "table": "users",
            "columns": ["organization_id", "is_deleted"],
            "name": "idx_users_org_active",
        },
        {"table": "users", "columns": ["email"], "name": "idx_users_email"},
        {
            "table": "activity_logs",
            "columns": ["user_id", "created_at"],
            "name": "idx_activity_user_date",
        },
        {"table": "activity_logs", "columns": ["action"], "name": "idx_activity_action"},
        {
            "table": "audit_logs",
            "columns": ["organization_id", "created_at"],
            "name": "idx_audit_org_date",
        },
        {"table": "audit_logs", "columns": ["user_id"], "name": "idx_audit_user"},
        {
            "table": "security_logs",
            "columns": ["organization_id", "created_at"],
            "name": "idx_security_org_date",
        },
        {"table": "organizations", "columns": ["slug"], "name": "idx_org_slug"},
        {"table": "sales", "columns": ["order_date"], "name": "idx_sales_date"},
        {"table": "pipeline_runs", "columns": ["started_at"], "name": "idx_pipeline_runs_date"},
    ]

    def __init__(self, db: DbSession):
        self.db = db
        self._inspector = inspect(db.bind)

    def ensure_index(self, table_name: str, columns: list[str], name: str) -> bool:
        """Ensure an index exists on a table. Returns True if created."""
        try:
            existing = self._inspector.get_indexes(table_name)
            for idx in existing:
                if idx["name"] == name:
                    return False  # Already exists

            # Get the table's columns to build index
            table_columns = {col["name"]: col for col in self._inspector.get_columns(table_name)}

            # Only create if all columns exist
            for col in columns:
                if col not in table_columns:
                    logger.warning(
                        f"Column '{col}' not found on table '{table_name}', skipping index '{name}'"
                    )
                    return False

            column_defs = ", ".join(columns)
            sql = f"CREATE INDEX {name} ON {table_name} ({column_defs})"
            self.db.execute(text(sql))
            self.db.commit()
            logger.info(f"Created index '{name}' on {table_name}({column_defs})")
            return True

        except Exception as e:
            logger.warning(f"Could not create index '{name}': {e}")
            return False

    def ensure_critical_indexes(self) -> dict:
        """Ensure all critical indexes exist. Returns summary."""
        created = []
        skipped = []
        failed = []

        for idx_def in self.CRITICAL_INDEXES:
            result = self.ensure_index(idx_def["table"], idx_def["columns"], idx_def["name"])
            if result:
                created.append(idx_def["name"])
            else:
                skipped.append(idx_def["name"])

        return {
            "created": created,
            "skipped": skipped,
            "failed": failed,
            "total": len(self.CRITICAL_INDEXES),
        }

    def list_indexes(self, table_name: str) -> list[dict]:
        """List all indexes on a table."""
        try:
            return self._inspector.get_indexes(table_name)
        except Exception:
            return []

    def drop_index(self, name: str) -> bool:
        """Drop an index by name."""
        try:
            self.db.execute(text(f"DROP INDEX IF EXISTS {name}"))
            self.db.commit()
            return True
        except Exception as e:
            logger.warning(f"Could not drop index '{name}': {e}")
            return False


class QueryOptimizer:
    """Query analysis and optimization suggestions.

    Provides:
      - analyze_query: Inspect a SQLAlchemy query and suggest optimizations
      - suggest_indexes: Recommend indexes based on query patterns
      - track_slow_query: Record slow queries for analysis
    """

    def __init__(self):
        self._slow_queries: list[dict] = []
        self._slow_threshold_ms = 1000  # 1 second

    def analyze_query(self, query, model_class) -> dict:
        """Analyze a SQLAlchemy query and provide optimization suggestions."""
        suggestions = []

        # Check for missing WHERE clause
        query_str = str(query)
        if "WHERE" not in query_str.upper() and "LIMIT" not in query_str.upper():
            suggestions.append(
                {
                    "type": "missing_filter",
                    "message": "Query has no WHERE clause â€” will scan entire table. Add filters or use LIMIT.",
                    "severity": "high",
                }
            )

        # Check for SELECT *
        if "SELECT" in query_str.upper() and "*" not in query_str.upper():
            suggestions.append(
                {
                    "type": "column_selection",
                    "message": "Good â€” query selects specific columns.",
                    "severity": "info",
                }
            )

        # Check for missing LIMIT on potentially large queries
        if "LIMIT" not in query_str.upper():
            suggestions.append(
                {
                    "type": "missing_limit",
                    "message": "Consider adding LIMIT for large result sets. Use ChunkedQuery for processing.",
                    "severity": "medium",
                }
            )

        return {
            "query": query_str[:500],
            "suggestions": suggestions,
            "model": model_class.__name__ if hasattr(model_class, "__name__") else str(model_class),
        }

    def track_slow_query(self, query_str: str, duration_ms: float, module: str = "") -> None:
        """Record a slow query for analysis."""
        if duration_ms >= self._slow_threshold_ms:
            self._slow_queries.append(
                {
                    "query": query_str[:500],
                    "duration_ms": round(duration_ms, 1),
                    "module": module,
                    "timestamp": time.time(),
                }
            )
            # Keep last 100 slow queries
            if len(self._slow_queries) > 100:
                self._slow_queries = self._slow_queries[-100:]

    def get_slow_queries(self) -> list[dict]:
        """Get recorded slow queries."""
        return self._slow_queries

    def suggest_indexes(self, table_name: str, columns: list[str]) -> dict:
        """Suggest indexes for a table based on query patterns."""
        return {
            "table": table_name,
            "suggested_index": {
                "columns": columns,
                "name": f"idx_{table_name}_{'_'.join(columns)}",
                "reason": "Frequently queried together",
            },
            "sql": f"CREATE INDEX idx_{table_name}_{'_'.join(columns)} ON {table_name} ({', '.join(columns)})",
        }


class ChunkedQuery:
    """Process large result sets in chunks to avoid memory issues.

    Usage:
        from sqlalchemy import select
        from performance.db_optimization import ChunkedQuery

        for chunk in ChunkedQuery.iter_chunks(db, select(User), chunk_size=5000):
            for user in chunk:
                process(user)

        # Or process with a callback:
        ChunkedQuery.process_in_chunks(
            db, select(User), callback=process_user, chunk_size=1000
        )
    """

    @staticmethod
    def iter_chunks(
        db: DbSession,
        query,
        chunk_size: int = 5000,
        model_class=None,
    ) -> Generator[list, None, None]:
        """Yield chunks of results from a query.

        Args:
            db: Database session.
            query: SQLAlchemy select query.
            chunk_size: Number of rows per chunk.
            model_class: Optional model class for offset-based chunking.

        Yields:
            Lists of model instances, chunk_size at a time.
        """
        offset = 0
        while True:
            chunk_query = query.offset(offset).limit(chunk_size)
            results = db.execute(chunk_query).scalars().all()

            if not results:
                break

            yield list(results)

            if len(results) < chunk_size:
                break

            offset += chunk_size

    @staticmethod
    def process_in_chunks(
        db: DbSession,
        query,
        callback: callable,
        chunk_size: int = 5000,
    ) -> int:
        """Process query results in chunks with a callback.

        Args:
            db: Database session.
            query: SQLAlchemy select query.
            callback: Function called for each row.
            chunk_size: Number of rows per chunk.

        Returns:
            Total number of rows processed.
        """
        total = 0
        for chunk in ChunkedQuery.iter_chunks(db, query, chunk_size):
            for row in chunk:
                callback(row)
                total += 1
        return total

    @staticmethod
    def batch_insert(
        db: DbSession,
        model_class,
        records: Iterable[dict],
        batch_size: int = 1000,
    ) -> int:
        """Insert records in batches for better performance.

        Args:
            db: Database session.
            model_class: SQLAlchemy model class.
            records: Iterable of dicts with column â†’ value.
            batch_size: Number of records per insert batch.

        Returns:
            Total number of records inserted.
        """
        total = 0
        batch = []

        for record in records:
            batch.append(model_class(**record))
            if len(batch) >= batch_size:
                db.bulk_save_objects(batch)
                db.flush()
                total += len(batch)
                batch = []

        if batch:
            db.bulk_save_objects(batch)
            db.flush()
            total += len(batch)

        db.commit()
        return total


def get_db_stats(db: DbSession) -> DBStats:
    """Collect database statistics for monitoring."""
    stats = DBStats()
    inspector = inspect(db.bind)

    try:
        table_names = inspector.get_table_names()
        stats.table_count = len(table_names)

        for table_name in table_names:
            try:
                indexes = inspector.get_indexes(table_name)
                stats.index_count += len(indexes)

                # Get row count (approximate for MySQL, exact for SQLite)
                count_result = db.execute(
                    text(f"SELECT COUNT(*) FROM {table_name}")
                )  # nosec B608 â€” table_name from inspector.get_table_names()
                row_count = count_result.scalar() or 0
                stats.total_rows += row_count

                stats.table_stats[table_name] = {
                    "rows": row_count,
                    "indexes": len(indexes),
                }
            except Exception:
                stats.table_stats[table_name] = {"rows": 0, "indexes": 0}

    except Exception as e:
        logger.warning(f"Could not collect DB stats: {e}")

    return stats
