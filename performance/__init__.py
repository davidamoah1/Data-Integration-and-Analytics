"""Performance & Global Scale Infrastructure.

Prepares the platform for millions of records, thousands of users,
and large organizations.

Modules:
  queue â€” Task queue with Redis backend + in-memory fallback
  workers â€” Background worker pool for ETL, reports, AI tasks
  cache â€” Redis caching layer with decorators and invalidation
  db_optimization â€” Indexes, connection pooling, query helpers
  routes â€” Performance monitoring and management endpoints
"""

from __future__ import annotations

from performance.cache import (
    CacheManager,
    CacheStats,
    cache_key,
    cached,
)
from performance.db_optimization import (
    ChunkedQuery,
    DBStats,
    IndexManager,
    QueryOptimizer,
)
from performance.queue import (
    QueueStats,
    Task,
    TaskPriority,
    TaskQueue,
    TaskStatus,
)
from performance.workers import (
    Worker,
    WorkerPool,
    WorkerStats,
)

__all__ = [
    "TaskQueue",
    "Task",
    "TaskStatus",
    "TaskPriority",
    "QueueStats",
    "WorkerPool",
    "Worker",
    "WorkerStats",
    "CacheManager",
    "cached",
    "cache_key",
    "CacheStats",
    "IndexManager",
    "QueryOptimizer",
    "ChunkedQuery",
    "DBStats",
]
