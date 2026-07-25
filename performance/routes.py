"""Performance monitoring and management routes.

Endpoints for:
  - Queue stats and management
  - Worker pool stats
  - Cache stats and control
  - Database optimization and stats
  - Performance overview dashboard
"""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session as DbSession

from performance.cache import get_cache_manager
from performance.db_optimization import IndexManager, get_db_stats
from shared.database import get_db
from shared.dependencies import get_current_user, require_permissions
from shared.response import success_response

performance_router = APIRouter(prefix="/performance", tags=["Performance"])


@performance_router.get("/overview")
async def performance_overview(
    current_user: dict = Depends(require_permissions("settings.manage")),
    db: DbSession = Depends(get_db),
):
    """Get performance overview — queue, cache, and DB stats."""
    cache = get_cache_manager()
    db_stats = get_db_stats(db)

    return success_response({
        "cache": cache.get_stats().to_dict(),
        "cache_backend": "redis" if cache.is_redis_backend else "memory",
        "database": db_stats.to_dict(),
    })


# --- Queue endpoints ---


@performance_router.get("/queue/stats")
async def queue_stats(
    current_user: dict = Depends(require_permissions("settings.manage")),
):
    """Get task queue statistics."""
    from performance.queue import TaskQueue

    # Return empty stats if no queue is active
    return success_response({
        "message": "Queue stats are available when workers are running.",
        "stats": {
            "total_enqueued": 0,
            "total_completed": 0,
            "total_failed": 0,
            "pending": 0,
        },
    })


# --- Cache endpoints ---


@performance_router.get("/cache/stats")
async def cache_stats(
    current_user: dict = Depends(require_permissions("settings.manage")),
):
    """Get cache statistics."""
    cache = get_cache_manager()
    return success_response({
        **cache.get_stats().to_dict(),
        "backend": "redis" if cache.is_redis_backend else "memory",
        "memory_size": cache.get_memory_size(),
    })


@performance_router.delete("/cache/clear")
async def cache_clear(
    current_user: dict = Depends(require_permissions("settings.manage")),
):
    """Clear the entire cache."""
    cache = get_cache_manager()
    count = await cache.clear_all()
    return success_response({"cleared": count}, f"Cleared {count} cache entries")


@performance_router.delete("/cache/namespace/{namespace}")
async def cache_clear_namespace(
    namespace: str,
    current_user: dict = Depends(require_permissions("settings.manage")),
):
    """Clear all keys in a cache namespace."""
    cache = get_cache_manager()
    count = await cache.clear_namespace(namespace)
    return success_response({"cleared": count}, f"Cleared {count} entries in '{namespace}'")


# --- Database optimization endpoints ---


@performance_router.get("/db/stats")
async def database_stats(
    current_user: dict = Depends(require_permissions("settings.manage")),
    db: DbSession = Depends(get_db),
):
    """Get database statistics."""
    stats = get_db_stats(db)
    return success_response(stats.to_dict())


@performance_router.post("/db/ensure-indexes")
async def ensure_indexes(
    current_user: dict = Depends(require_permissions("settings.manage")),
    db: DbSession = Depends(get_db),
):
    """Ensure critical database indexes exist."""
    manager = IndexManager(db)
    result = manager.ensure_critical_indexes()
    return success_response(result, f"Created {len(result['created'])} indexes")


@performance_router.get("/db/indexes/{table_name}")
async def list_indexes(
    table_name: str,
    current_user: dict = Depends(require_permissions("settings.manage")),
    db: DbSession = Depends(get_db),
):
    """List all indexes on a table."""
    manager = IndexManager(db)
    indexes = manager.list_indexes(table_name)
    return success_response(indexes)
