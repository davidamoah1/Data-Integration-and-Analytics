"""AI Cache — response caching to reduce redundant API calls.

Uses an in-memory LRU cache with TTL for AI responses.
Can be extended to use Redis or database-backed caching.
"""

import time
from collections import OrderedDict
from threading import Lock
from typing import Any

from ai.config import AI_CACHE_MAX_ENTRIES, AI_CACHE_TTL_SECONDS


class AICache:
    """Thread-safe LRU cache with TTL for AI responses."""

    def __init__(
        self, max_entries: int = AI_CACHE_MAX_ENTRIES, ttl_seconds: int = AI_CACHE_TTL_SECONDS
    ):
        self._cache: OrderedDict[str, dict] = OrderedDict()
        self._max_entries = max_entries
        self._ttl = ttl_seconds
        self._lock = Lock()

    def get(self, key: str) -> Any | None:
        """Get a value from the cache. Returns None if not found or expired."""
        with self._lock:
            if key not in self._cache:
                return None
            entry = self._cache[key]
            if time.time() - entry["timestamp"] > self._ttl:
                # Expired
                del self._cache[key]
                return None
            # Move to end (most recently used)
            self._cache.move_to_end(key)
            return entry["value"]

    def set(self, key: str, value: Any) -> None:
        """Set a value in the cache."""
        with self._lock:
            if key in self._cache:
                self._cache.move_to_end(key)
            self._cache[key] = {
                "value": value,
                "timestamp": time.time(),
            }
            # Evict oldest entries if over capacity
            while len(self._cache) > self._max_entries:
                self._cache.popitem(last=False)

    def delete(self, key: str) -> None:
        """Delete a key from the cache."""
        with self._lock:
            self._cache.pop(key, None)

    def clear(self) -> None:
        """Clear all cached entries."""
        with self._lock:
            self._cache.clear()

    def stats(self) -> dict:
        """Get cache statistics."""
        with self._lock:
            current_time = time.time()
            active = sum(
                1
                for entry in self._cache.values()
                if current_time - entry["timestamp"] <= self._ttl
            )
            return {
                "total_entries": len(self._cache),
                "active_entries": active,
                "max_entries": self._max_entries,
                "ttl_seconds": self._ttl,
            }
