"""Tests for Performance & Global Scale infrastructure.

Tests cover:
  - Task queue: enqueue, dequeue, execute, retry, dead letter, stats
  - Worker pool: start, stop, scaling, stats
  - Cache manager: get, set, delete, invalidate, stats, cached decorator
  - DB optimization: index manager, query optimizer, chunked query
  - API endpoints: overview, cache stats, DB stats, indexes
"""

from __future__ import annotations

import asyncio

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
    get_db_stats,
)
from performance.queue import (
    QueueStats,
    Task,
    TaskPriority,
    TaskQueue,
    TaskStatus,
)
from performance.workers import (
    WorkerPool,
    WorkerStats,
)

# â”€â”€ Task Queue Tests â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€


class TestTask:
    def test_task_defaults(self):
        task = Task(name="test")
        assert task.name == "test"
        assert task.status == TaskStatus.PENDING
        assert task.priority == TaskPriority.NORMAL
        assert task.max_retries == 3
        assert task.timeout == 300

    def test_task_to_dict(self):
        task = Task(name="test", priority=TaskPriority.HIGH)
        d = task.to_dict()
        assert d["name"] == "test"
        assert d["priority"] == "high_priority"
        assert d["status"] == "pending"

    def test_task_duration(self):
        task = Task(name="test")
        task.started_at = 100.0
        task.completed_at = 105.0
        assert task.duration == 5.0

    def test_task_duration_none(self):
        task = Task(name="test")
        assert task.duration is None


class TestTaskQueue:
    def test_enqueue_and_get_task(self):
        queue = TaskQueue()

        async def run():
            task = Task(name="test", func=lambda: 42)
            task_id = await queue.enqueue(task)
            assert task_id == task.id
            retrieved = queue.get_task(task_id)
            assert retrieved is not None
            assert retrieved.name == "test"

        asyncio.run(run())

    def test_enqueue_increments_stats(self):
        queue = TaskQueue()

        async def run():
            task = Task(name="test", func=lambda: 42)
            await queue.enqueue(task)
            stats = queue.get_stats()
            assert stats.total_enqueued == 1

        asyncio.run(run())

    def test_execute_sync_function(self):
        queue = TaskQueue()

        async def run():
            task = Task(name="test", func=lambda x, y: x + y, args=(3, 4))
            await queue.enqueue(task)
            result = await queue.execute(task)
            assert result == 7
            assert task.status == TaskStatus.COMPLETED
            assert task.completed_at is not None

        asyncio.run(run())

    def test_execute_async_function(self):
        queue = TaskQueue()

        async def async_func(x):
            await asyncio.sleep(0.01)
            return x * 2

        async def run():
            task = Task(name="test", func=async_func, args=(5,))
            await queue.enqueue(task)
            result = await queue.execute(task)
            assert result == 10
            assert task.status == TaskStatus.COMPLETED

        asyncio.run(run())

    def test_execute_failure(self):
        queue = TaskQueue()

        def failing_func():
            raise ValueError("test error")

        async def run():
            task = Task(name="test", func=failing_func, max_retries=0)
            await queue.enqueue(task)
            await queue.execute(task)
            assert task.status == TaskStatus.FAILED
            assert "test error" in task.error

        asyncio.run(run())

    def test_retry_logic(self):
        queue = TaskQueue()
        call_count = 0

        def flaky_func():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise ValueError("flaky")
            return "success"

        async def run():
            task = Task(name="test", func=flaky_func, max_retries=3)
            await queue.enqueue(task)
            # First execution fails and triggers retry
            await queue.execute(task)
            assert task.retries == 1
            assert task.status == TaskStatus.PENDING  # Re-enqueued

        asyncio.run(run())

    def test_dead_letter_queue(self):
        queue = TaskQueue()

        def always_fail():
            raise ValueError("always fails")

        async def run():
            task = Task(name="test", func=always_fail, max_retries=0)
            await queue.enqueue(task)
            await queue.execute(task)
            assert task.status == TaskStatus.FAILED
            dlq = queue.get_dead_letter_queue()
            assert len(dlq) == 1

        asyncio.run(run())

    def test_cancel_task(self):
        queue = TaskQueue()

        async def run():
            task = Task(name="test", func=lambda: 42)
            await queue.enqueue(task)
            assert queue.cancel_task(task.id) is True
            assert task.status == TaskStatus.CANCELLED

        asyncio.run(run())

    def test_cancel_nonexistent_task(self):
        queue = TaskQueue()
        assert queue.cancel_task("nonexistent") is False

    def test_clear_dead_letter(self):
        queue = TaskQueue()

        def always_fail():
            raise ValueError("fail")

        async def run():
            task = Task(name="test", func=always_fail, max_retries=0)
            await queue.enqueue(task)
            await queue.execute(task)
            count = queue.clear_dead_letter()
            assert count == 1
            assert len(queue.get_dead_letter_queue()) == 0

        asyncio.run(run())

    def test_dequeue_empty_queue(self):
        queue = TaskQueue()

        async def run():
            task = await queue.dequeue(timeout=0.1)
            assert task is None

        asyncio.run(run())

    def test_dequeue_priority_order(self):
        queue = TaskQueue()

        async def run():
            high_task = Task(name="high", func=lambda: "high", priority=TaskPriority.HIGH)
            normal_task = Task(name="normal", func=lambda: "normal", priority=TaskPriority.NORMAL)
            await queue.enqueue(normal_task)
            await queue.enqueue(high_task)
            # Should get high priority first
            first = await queue.dequeue(timeout=0.5)
            assert first is not None
            assert first.name == "high"

        asyncio.run(run())

    def test_queue_stats_to_dict(self):
        stats = QueueStats()
        stats.total_enqueued = 10
        stats.total_completed = 8
        d = stats.to_dict()
        assert d["total_enqueued"] == 10
        assert d["total_completed"] == 8

    def test_is_redis_backend_false(self):
        queue = TaskQueue()
        assert queue.is_redis_backend is False

    def test_pending_count(self):
        queue = TaskQueue()

        async def run():
            assert queue.pending_count == 0
            task = Task(name="test", func=lambda: 42)
            await queue.enqueue(task)
            assert queue.pending_count == 1

        asyncio.run(run())


# â”€â”€ Worker Pool Tests â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€


class TestWorkerStats:
    def test_to_dict(self):
        stats = WorkerStats(worker_id="w-1")
        stats.tasks_started = 5
        stats.tasks_completed = 3
        d = stats.to_dict()
        assert d["worker_id"] == "w-1"
        assert d["tasks_started"] == 5
        assert d["tasks_completed"] == 3
        assert d["is_busy"] is False


class TestWorkerPool:
    def test_start_and_stop(self):
        queue = TaskQueue()
        pool = WorkerPool(queue, min_workers=2, max_workers=5)

        async def run():
            await pool.start()
            assert len(pool._workers) == 2
            await pool.stop()
            assert len(pool._workers) == 0

        asyncio.run(run())

    def test_get_stats(self):
        queue = TaskQueue()
        pool = WorkerPool(queue, min_workers=2, max_workers=5)

        async def run():
            await pool.start()
            stats = pool.get_stats()
            assert stats["total_workers"] == 2
            assert stats["min_workers"] == 2
            assert stats["max_workers"] == 5
            await pool.stop()

        asyncio.run(run())

    def test_worker_processes_task(self):
        queue = TaskQueue()
        pool = WorkerPool(queue, min_workers=1, max_workers=2)

        async def run():
            await pool.start()
            task = Task(name="compute", func=lambda: 42)
            await queue.enqueue(task)
            # Wait for processing
            await asyncio.sleep(0.5)
            assert task.status == TaskStatus.COMPLETED
            assert task.result == 42
            await pool.stop()

        asyncio.run(run())


# â”€â”€ Cache Manager Tests â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€


class TestCacheManager:
    def test_set_and_get(self):
        cache = CacheManager(default_ttl=60)

        async def run():
            await cache.set("key1", {"value": 42})
            result = await cache.get("key1")
            assert result is not None
            assert result["value"] == 42

        asyncio.run(run())

    def test_get_miss(self):
        cache = CacheManager()

        async def run():
            result = await cache.get("nonexistent")
            assert result is None
            assert cache.stats.misses == 1

        asyncio.run(run())

    def test_delete(self):
        cache = CacheManager()

        async def run():
            await cache.set("key1", "value1")
            deleted = await cache.delete("key1")
            assert deleted is True
            result = await cache.get("key1")
            assert result is None

        asyncio.run(run())

    def test_delete_nonexistent(self):
        cache = CacheManager()

        async def run():
            deleted = await cache.delete("nonexistent")
            assert deleted is False

        asyncio.run(run())

    def test_ttl_expiry(self):
        cache = CacheManager(default_ttl=1)

        async def run():
            await cache.set("key1", "value1", ttl=0.1)
            await asyncio.sleep(0.15)
            result = await cache.get("key1")
            assert result is None

        asyncio.run(run())

    def test_invalidate_pattern(self):
        cache = CacheManager(key_prefix="testpat")

        async def run():
            await cache.set("user:1", "a")
            await cache.set("user:2", "b")
            await cache.set("other:1", "c")
            count = await cache.invalidate_pattern("user:*")
            assert count == 2
            assert await cache.get("user:1") is None
            assert await cache.get("user:2") is None
            assert await cache.get("other:1") is not None

        asyncio.run(run())

    def test_clear_namespace(self):
        cache = CacheManager()

        async def run():
            await cache.set("k1", "v1", namespace="ns1")
            await cache.set("k2", "v2", namespace="ns1")
            await cache.set("k3", "v3", namespace="ns2")
            count = await cache.clear_namespace("ns1")
            assert count == 2
            assert await cache.get("k1", namespace="ns1") is None
            assert await cache.get("k3", namespace="ns2") is not None

        asyncio.run(run())

    def test_clear_all(self):
        cache = CacheManager()

        async def run():
            await cache.set("k1", "v1")
            await cache.set("k2", "v2")
            count = await cache.clear_all()
            assert count >= 2

        asyncio.run(run())

    def test_hit_rate(self):
        cache = CacheManager()

        async def run():
            await cache.set("k1", "v1")
            await cache.get("k1")  # hit
            await cache.get("k2")  # miss
            assert cache.stats.hit_rate == 50.0

        asyncio.run(run())

    def test_cache_stats_to_dict(self):
        stats = CacheStats()
        stats.hits = 10
        stats.misses = 5
        d = stats.to_dict()
        assert d["hits"] == 10
        assert d["hit_rate"] == 66.7

    def test_is_redis_backend_false(self):
        cache = CacheManager()
        assert cache.is_redis_backend is False

    def test_memory_size(self):
        cache = CacheManager()

        async def run():
            await cache.set("k1", "v1")
            await cache.set("k2", "v2")
            assert cache.get_memory_size() == 2

        asyncio.run(run())


class TestCacheKey:
    def test_simple_key(self):
        key = cache_key("user", 123)
        assert key == "user:123"

    def test_with_kwargs(self):
        key = cache_key("user", 123, period="monthly")
        assert "user:123" in key
        assert "period=monthly" in key

    def test_empty_args(self):
        key = cache_key()
        assert key == ""


class TestCachedDecorator:
    def test_cached_function(self):
        call_count = 0
        cache = CacheManager(key_prefix="testcache1")

        @cached(ttl=60, namespace="test", manager=cache)
        async def expensive_func(x):
            nonlocal call_count
            call_count += 1
            return x * 2

        async def run():
            result1 = await expensive_func(5)
            assert result1 == 10
            assert call_count == 1

            # Second call should be cached
            result2 = await expensive_func(5)
            assert result2 == 10
            assert call_count == 1  # Not called again

        asyncio.run(run())

    def test_cached_different_args(self):
        call_count = 0
        cache = CacheManager(key_prefix="testdiff")

        @cached(ttl=60, namespace="test2", manager=cache)
        async def func(x):
            nonlocal call_count
            call_count += 1
            return x * 3

        async def run():
            await func(1)
            await func(2)
            assert call_count == 2  # Different args = different cache keys

        asyncio.run(run())


# â”€â”€ DB Optimization Tests â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€


class TestIndexManager:
    def test_critical_indexes_defined(self):
        assert len(IndexManager.CRITICAL_INDEXES) > 0

    def test_list_indexes(self, db_session):
        manager = IndexManager(db_session)
        # Should not crash even if table doesn't exist
        result = manager.list_indexes("nonexistent_table")
        assert isinstance(result, list)

    def test_ensure_critical_indexes(self, db_session):
        manager = IndexManager(db_session)
        result = manager.ensure_critical_indexes()
        assert "created" in result
        assert "skipped" in result
        assert "total" in result


class TestQueryOptimizer:
    def test_analyze_query_no_where(self):
        optimizer = QueryOptimizer()
        from sqlalchemy import text

        class FakeModel:
            __name__ = "FakeModel"

        result = optimizer.analyze_query(text("SELECT * FROM users"), FakeModel)
        assert len(result["suggestions"]) > 0
        assert any(s["type"] == "missing_filter" for s in result["suggestions"])

    def test_track_slow_query(self):
        optimizer = QueryOptimizer()
        optimizer.track_slow_query("SELECT * FROM big_table", 2000.0, "test_module")
        slow = optimizer.get_slow_queries()
        assert len(slow) == 1
        assert slow[0]["duration_ms"] == 2000.0

    def test_suggest_indexes(self):
        optimizer = QueryOptimizer()
        suggestion = optimizer.suggest_indexes("users", ["org_id", "status"])
        assert "sql" in suggestion
        assert "idx_users_org_id_status" in suggestion["sql"]


class TestChunkedQuery:
    def test_iter_chunks(self, db_session):
        from sqlalchemy import select

        from authentication.models import User

        # Count existing users (seeded super admin)
        existing = db_session.query(User).count()
        total_needed = 15
        to_create = total_needed - existing
        if to_create > 0:
            for i in range(to_create):
                db_session.add(
                    User(
                        email=f"chunk{i}@test.com",
                        password_hash="hash",
                        full_name=f"Chunk {i}",
                        is_active=1,
                    )
                )
            db_session.commit()

        chunks = list(ChunkedQuery.iter_chunks(db_session, select(User), chunk_size=5))
        # Should have at least 3 chunks (15 users / 5 per chunk)
        assert len(chunks) >= 3
        assert all(len(c) <= 5 for c in chunks)

    def test_iter_chunks_empty(self, db_session):
        from sqlalchemy import select

        from authentication.models import User

        chunks = list(
            ChunkedQuery.iter_chunks(db_session, select(User).where(User.id < 0), chunk_size=10)
        )
        assert len(chunks) == 0

    def test_process_in_chunks(self, db_session):
        from sqlalchemy import select

        from authentication.models import User

        processed = []
        for i in range(10):
            db_session.add(
                User(
                    email=f"proc{i}@test.com",
                    password_hash="hash",
                    full_name=f"Proc {i}",
                    is_active=1,
                )
            )
        db_session.commit()

        count = ChunkedQuery.process_in_chunks(
            db_session,
            select(User).where(User.email.like("proc%@test.com")),
            callback=lambda u: processed.append(u.email),
            chunk_size=3,
        )
        assert count == 10
        assert len(processed) == 10


class TestDBStats:
    def test_get_db_stats(self, db_session):
        stats = get_db_stats(db_session)
        assert stats.table_count > 0
        assert isinstance(stats.total_rows, int)
        assert isinstance(stats.index_count, int)

    def test_db_stats_to_dict(self):
        stats = DBStats(table_count=5, total_rows=100, index_count=10)
        d = stats.to_dict()
        assert d["table_count"] == 5
        assert d["total_rows"] == 100
        assert d["index_count"] == 10


# â”€â”€ API Endpoint Tests â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€


class TestPerformanceAPI:
    def test_overview(self, auth_headers, client):
        response = client.get("/performance/overview", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()["data"]
        assert "cache" in data
        assert "database" in data

    def test_cache_stats(self, auth_headers, client):
        response = client.get("/performance/cache/stats", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()["data"]
        assert "hits" in data
        assert "misses" in data
        assert "backend" in data

    def test_cache_clear(self, auth_headers, client):
        response = client.delete("/performance/cache/clear", headers=auth_headers)
        assert response.status_code == 200

    def test_db_stats(self, auth_headers, client):
        response = client.get("/performance/db/stats", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()["data"]
        assert "table_count" in data
        assert "total_rows" in data

    def test_ensure_indexes(self, auth_headers, client):
        response = client.post("/performance/db/ensure-indexes", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()["data"]
        assert "created" in data
        assert "total" in data

    def test_unauthorized(self, client):
        response = client.get("/performance/overview")
        assert response.status_code == 401

    def test_cache_stats_unauthorized(self, client):
        response = client.get("/performance/cache/stats")
        assert response.status_code == 401
