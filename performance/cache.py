"""Redis Caching Layer.

Provides:
  - CacheManager: Get/set/delete with TTL, Redis or in-memory backend
  - cached: Decorator for automatic caching of function results
  - cache_key: Helper to build consistent cache keys
  - CacheStats: Hit/miss tracking

Redis backend is used when REDIS_URL is set; otherwise falls back to
an in-memory dict with TTL for development and testing.

Usage:
    from performance.cache import cached, CacheManager

    @cached(ttl=300, key_prefix="user_stats")
    async def get_user_stats(user_id: int):
        # Expensive DB query
        return {"views": 1000, "reports": 50}

    # Manual cache control:
    manager = CacheManager()
    await manager.set("my_key", {"data": 1}, ttl=60)
    value = await manager.get("my_key")
    await manager.delete("my_key")
    await manager.invalidate_pattern("user_stats:*")
"""

from __future__ import annotations

import asyncio
import functools
import json
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

try:
    import redis as redis_lib

    HAS_REDIS = True
except ImportError:
    HAS_REDIS = False


@dataclass
class CacheStats:
    """Cache hit/miss statistics."""

    hits: int = 0
    misses: int = 0
    sets: int = 0
    deletes: int = 0
    errors: int = 0
    by_namespace: dict[str, dict[str, int]] = field(default_factory=dict)

    @property
    def hit_rate(self) -> float:
        total = self.hits + self.misses
        return round(self.hits / total * 100, 1) if total > 0 else 0.0

    def to_dict(self) -> dict:
        return {
            "hits": self.hits,
            "misses": self.misses,
            "sets": self.sets,
            "deletes": self.deletes,
            "errors": self.errors,
            "hit_rate": self.hit_rate,
            "by_namespace": self.by_namespace,
        }

    def record_hit(self, namespace: str = "default") -> None:
        self.hits += 1
        self._record_ns(namespace, "hits")

    def record_miss(self, namespace: str = "default") -> None:
        self.misses += 1
        self._record_ns(namespace, "misses")

    def _record_ns(self, namespace: str, metric: str) -> None:
        if namespace not in self.by_namespace:
            self.by_namespace[namespace] = {"hits": 0, "misses": 0}
        self.by_namespace[namespace][metric] = self.by_namespace[namespace].get(metric, 0) + 1


class CacheManager:
    """Redis or in-memory cache with TTL support.

    Args:
        redis_url: Redis connection URL. If None or unreachable,
                   falls back to in-memory cache.
        default_ttl: Default TTL in seconds (default: 300).
        key_prefix: Global prefix for all keys (default: "aedip").
    """

    def __init__(
        self,
        redis_url: str | None = None,
        default_ttl: int = 300,
        key_prefix: str = "aedip",
    ):
        self._redis = None
        self.default_ttl = default_ttl
        self.key_prefix = key_prefix
        self.stats = CacheStats()
        self._memory: dict[str, tuple[Any, float]] = {}  # key â†’ (value, expiry)
        self._lock = asyncio.Lock()

        if redis_url and HAS_REDIS:
            try:
                self._redis = redis_lib.from_url(redis_url, decode_responses=True)
                self._redis.ping()
            except Exception:
                self._redis = None

    @property
    def is_redis_backend(self) -> bool:
        return self._redis is not None

    def _make_key(self, key: str) -> str:
        return f"{self.key_prefix}:{key}"

    async def get(self, key: str, namespace: str = "default") -> Any:
        """Get a value from the cache. Returns None if not found or expired."""
        full_key = self._make_key(f"{namespace}:{key}")

        if self._redis:
            try:
                raw = self._redis.get(full_key)
                if raw is not None:
                    self.stats.record_hit(namespace)
                    return json.loads(raw)
            except Exception:
                self.stats.errors += 1
        else:
            async with self._lock:
                if full_key in self._memory:
                    value, expiry = self._memory[full_key]
                    if time.time() < expiry:
                        self.stats.record_hit(namespace)
                        return value
                    else:
                        del self._memory[full_key]

        self.stats.record_miss(namespace)
        return None

    async def set(
        self, key: str, value: Any, ttl: int | None = None, namespace: str = "default"
    ) -> None:
        """Set a value in the cache with TTL."""
        full_key = self._make_key(f"{namespace}:{key}")
        ttl = ttl or self.default_ttl
        self.stats.sets += 1

        if self._redis:
            try:
                self._redis.setex(full_key, ttl, json.dumps(value, default=str))
            except Exception:
                self.stats.errors += 1
        else:
            async with self._lock:
                self._memory[full_key] = (value, time.time() + ttl)

    async def delete(self, key: str, namespace: str = "default") -> bool:
        """Delete a key from the cache."""
        full_key = self._make_key(f"{namespace}:{key}")
        self.stats.deletes += 1

        if self._redis:
            try:
                deleted = self._redis.delete(full_key)
                return deleted > 0
            except Exception:
                self.stats.errors += 1
                return False
        else:
            async with self._lock:
                if full_key in self._memory:
                    del self._memory[full_key]
                    return True
                return False

    async def invalidate_pattern(self, pattern: str, namespace: str = "default") -> int:
        """Invalidate all keys matching a pattern (e.g., 'user_stats:*')."""
        full_pattern = self._make_key(f"{namespace}:{pattern}")
        count = 0

        if self._redis:
            try:
                keys = self._redis.keys(full_pattern)
                if keys:
                    count = self._redis.delete(*keys)
                self.stats.deletes += count
            except Exception:
                self.stats.errors += 1
        else:
            async with self._lock:
                # Pattern like "aedip:user:*" â†’ match keys starting with "aedip:user:"
                search_prefix = full_pattern.rstrip("*")
                to_delete = [k for k in self._memory if k.startswith(search_prefix)]
                for k in to_delete:
                    del self._memory[k]
                    count += 1
                self.stats.deletes += count

        return count

    async def clear_namespace(self, namespace: str) -> int:
        """Clear all keys in a namespace."""
        return await self.invalidate_pattern("*", namespace=namespace)

    async def clear_all(self) -> int:
        """Clear the entire cache."""
        count = 0
        if self._redis:
            try:
                keys = self._redis.keys(f"{self.key_prefix}:*")
                if keys:
                    count = self._redis.delete(*keys)
            except Exception:
                self.stats.errors += 1
        else:
            async with self._lock:
                count = len(self._memory)
                self._memory.clear()

        self.stats.deletes += count
        return count

    def get_stats(self) -> CacheStats:
        return self.stats

    def get_memory_size(self) -> int:
        """Get number of cached items (in-memory mode only)."""
        if self._redis:
            return -1  # Not applicable
        return len(self._memory)


# Singleton instance
_cache_manager: CacheManager | None = None


def get_cache_manager() -> CacheManager:
    """Get or create the singleton CacheManager."""
    global _cache_manager
    if _cache_manager is None:
        import os

        redis_url = os.getenv("REDIS_URL")
        _cache_manager = CacheManager(redis_url=redis_url)
    return _cache_manager


def cache_key(*args, **kwargs) -> str:
    """Build a consistent cache key from arguments.

    Usage:
        key = cache_key("user", user_id, "stats", period="monthly")
        # â†’ "user:123:stats:period=monthly"
    """
    parts = [str(a) for a in args]
    for k, v in sorted(kwargs.items()):
        parts.append(f"{k}={v}")
    return ":".join(parts)


def cached(
    ttl: int = 300,
    key_prefix: str = "",
    namespace: str = "default",
    manager: CacheManager | None = None,
) -> Callable:
    """Decorator for automatic caching of async function results.

    Args:
        ttl: Cache TTL in seconds.
        key_prefix: Prefix for cache keys (defaults to function name).
        namespace: Cache namespace.
        manager: CacheManager instance (uses singleton if None).

    Usage:
        @cached(ttl=60, key_prefix="user_stats")
        async def get_user_stats(user_id: int):
            ...
    """

    def decorator(func: Callable) -> Callable:
        prefix = key_prefix or func.__name__
        cache = manager or get_cache_manager()

        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # Build cache key from all args
            key_parts = [str(a) for a in args]
            for k, v in sorted(kwargs.items()):
                key_parts.append(f"{k}={v}")
            key = f"{prefix}:{':'.join(key_parts)}" if key_parts else prefix

            # Try cache
            result = await cache.get(key, namespace=namespace)
            if result is not None:
                return result

            # Call function and cache result
            result = await func(*args, **kwargs)
            await cache.set(key, result, ttl=ttl, namespace=namespace)
            return result

        # Expose cache control methods
        wrapper.cache_invalidate = lambda *a, **kw: cache.delete(
            f"{prefix}:{':'.join(str(x) for x in a[1:])}" if a else prefix,
            namespace=namespace,
        )
        wrapper.cache_clear = lambda: cache.clear_namespace(namespace)

        return wrapper

    return decorator
