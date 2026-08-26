"""Regression tests for cross-process task execution via the Redis-backed queue.

Background: `Task.func` is a Python callable and cannot be JSON-serialized.
Before the fix, `TaskQueue.dequeue()` on the Redis backend looked up the
task by ID in a process-local `_tasks` dict â€” which is always empty in a
separate worker process, silently dropping every job. The fix serializes a
"module:qualname" `func_path` and reconstructs the Task (re-importing the
function) when it isn't found locally.

These tests simulate two separate `TaskQueue` instances (as would exist in
the API process and a separate worker container) sharing an in-memory fake
Redis, to prove a task enqueued by one process can be dequeued and executed
by the other.
"""

from __future__ import annotations

import asyncio

from performance.queue import Task, TaskPriority, TaskQueue, _resolve_func_path

# â”€â”€ A real, importable module-level function to use as a job "handler" â”€â”€â”€â”€


def _sample_job_handler(a: int, b: int) -> int:
    return a + b


class FakeRedis:
    """Minimal in-memory stand-in for redis-py's list operations."""

    def __init__(self):
        self._lists: dict[str, list[str]] = {}

    def ping(self):
        return True

    def lpush(self, key: str, value: str) -> None:
        self._lists.setdefault(key, []).insert(0, value)

    def brpop(self, key: str, timeout: int = 0):
        values = self._lists.get(key)
        if values:
            return key, values.pop()
        return None

    def llen(self, key: str) -> int:
        return len(self._lists.get(key, []))


def _make_queue_with_shared_fake_redis(shared: FakeRedis) -> TaskQueue:
    """Create a TaskQueue wired to the given fake Redis instance."""
    queue = TaskQueue()  # no real redis_url â€” avoids a real connection attempt
    queue._redis = shared
    return queue


def test_resolve_func_path_for_module_level_function():
    path = _resolve_func_path(_sample_job_handler)
    assert path == "tests.test_queue_cross_process:_sample_job_handler"


def test_resolve_func_path_returns_none_for_lambda():
    assert _resolve_func_path(lambda: 42) is None


def test_task_dequeued_by_separate_queue_instance_is_reconstructed():
    """Simulates the API process enqueuing and a separate worker process dequeuing."""
    shared_redis = FakeRedis()
    api_process_queue = _make_queue_with_shared_fake_redis(shared_redis)
    worker_process_queue = _make_queue_with_shared_fake_redis(FakeRedis())
    worker_process_queue._redis = shared_redis  # same backing store, separate _tasks cache

    async def run():
        task = Task(
            name="add",
            func=_sample_job_handler,
            args=(3, 4),
            priority=TaskPriority.NORMAL,
        )
        await api_process_queue.enqueue(task)

        # The worker process has never seen this task locally.
        assert task.id not in worker_process_queue._tasks

        dequeued = await worker_process_queue.dequeue(timeout=0.5)
        assert dequeued is not None
        assert dequeued.id == task.id
        assert dequeued.func is not None

        result = await worker_process_queue.execute(dequeued)
        assert result == 7

    asyncio.run(run())


def test_task_with_unresolvable_func_is_dropped_not_crashed():
    """A lambda-based task can't survive cross-process â€” dequeue must not raise."""
    shared_redis = FakeRedis()
    api_process_queue = _make_queue_with_shared_fake_redis(shared_redis)
    worker_process_queue = _make_queue_with_shared_fake_redis(shared_redis)

    async def run():
        task = Task(name="lambda_task", func=lambda: 1, priority=TaskPriority.NORMAL)
        await api_process_queue.enqueue(task)
        assert task.func_path is None

        result = await worker_process_queue.dequeue(timeout=0.5)
        assert result is None  # dropped gracefully, no exception

    asyncio.run(run())
