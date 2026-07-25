"""Performance & Global Scale Infrastructure.

Prepares the platform for millions of records, thousands of users,
and large organizations.

Modules:
  queue — Task queue with Redis backend + in-memory fallback
  workers — Background worker pool for ETL, reports, AI tasks
  cache — Redis caching layer with decorators and invalidation
  db_optimization — Indexes, connection pooling, query helpers
  routes — Performance monitoring and management endpoints
"""

from __future__ import annotations

from performance.queue import (
    TaskQueue,
    Task,
    TaskStatus,
    TaskPriority,
    QueueStats,
)
from performance.workers import (
    WorkerPool,
    Worker,
    WorkerStats,
)
from performance.cache import (
    CacheManager,
    cached,
    cache_key,
    CacheStats,
)
from performance.db_optimization import (
    IndexManager,
    QueryOptimizer,
    ChunkedQuery,
    DBStats,
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
