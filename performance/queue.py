"""Task Queue System.

Multi-priority task queue with Redis backend and in-memory fallback.
Supports:
  - Priority queues (high, normal, low, etl, reports, notifications)
  - Task retry with exponential backoff
  - Dead letter queue for failed tasks
  - Task status tracking (pending, running, completed, failed)
  - Queue statistics

Redis backend is used when REDIS_URL is set; otherwise falls back to
an in-memory queue for development and testing.
"""

from __future__ import annotations

import asyncio
import importlib
import json
import logging
import time
import uuid
from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

try:
    import redis as redis_lib

    HAS_REDIS = True
except ImportError:
    HAS_REDIS = False

logger = logging.getLogger(__name__)


class TaskStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRYING = "retrying"
    CANCELLED = "cancelled"


class TaskPriority(str, Enum):
    HIGH = "high_priority"
    NORMAL = "normal"
    LOW = "low_priority"
    ETL = "etl"
    REPORTS = "reports"
    NOTIFICATIONS = "notifications"


@dataclass
class Task:
    """A unit of work for the queue."""

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    func: Callable | None = None
    func_path: str | None = None
    """Dotted "module:qualname" path used to re-import `func` in a separate
    worker process when using the Redis backend (functions themselves are
    not JSON-serializable)."""
    args: tuple = ()
    kwargs: dict = field(default_factory=dict)
    priority: TaskPriority = TaskPriority.NORMAL
    status: TaskStatus = TaskStatus.PENDING
    result: Any = None
    error: str | None = None
    retries: int = 0
    max_retries: int = 3
    created_at: float = field(default_factory=time.time)
    started_at: float | None = None
    completed_at: float | None = None
    timeout: int = 300  # seconds
    metadata: dict = field(default_factory=dict)

    @property
    def duration(self) -> float | None:
        if self.started_at and self.completed_at:
            return self.completed_at - self.started_at
        return None

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "func_path": self.func_path,
            "args": list(self.args),
            "kwargs": self.kwargs,
            "priority": self.priority.value,
            "status": self.status.value,
            "retries": self.retries,
            "max_retries": self.max_retries,
            "timeout": self.timeout,
            "error": self.error,
            "duration": self.duration,
            "created_at": self.created_at,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "metadata": self.metadata,
        }


def _resolve_func_path(func: Callable) -> str | None:
    """Return a "module:qualname" path that can later re-import `func`.

    Only works for plain module-level (or nested-class) functions — not
    lambdas, closures, or bound methods on instances. Returns None if the
    function cannot be resolved this way.
    """
    module = getattr(func, "__module__", None)
    qualname = getattr(func, "__qualname__", None)
    if not module or not qualname or "<lambda>" in qualname or "<locals>" in qualname:
        return None
    return f"{module}:{qualname}"


def _import_from_path(path: str) -> Callable:
    """Re-import a function previously resolved by `_resolve_func_path`."""
    module_name, _, qualname = path.partition(":")
    obj = importlib.import_module(module_name)
    for part in qualname.split("."):
        obj = getattr(obj, part)
    return obj


@dataclass
class QueueStats:
    """Queue statistics."""

    total_enqueued: int = 0
    total_completed: int = 0
    total_failed: int = 0
    total_retried: int = 0
    by_priority: dict[str, int] = field(default_factory=dict)
    by_status: dict[str, int] = field(default_factory=dict)
    dead_letter_count: int = 0

    def to_dict(self) -> dict:
        return {
            "total_enqueued": self.total_enqueued,
            "total_completed": self.total_completed,
            "total_failed": self.total_failed,
            "total_retried": self.total_retried,
            "by_priority": self.by_priority,
            "by_status": self.by_status,
            "dead_letter_count": self.dead_letter_count,
        }


class TaskQueue:
    """Multi-priority task queue with Redis or in-memory backend.

    Usage:
        queue = TaskQueue()
        task = Task(name="etl_import", func=my_func, args=(1, 2))
        await queue.enqueue(task)
        # Worker picks it up:
        task = await queue.dequeue()
        result = await queue.execute(task)
    """

    PRIORITY_ORDER = [
        TaskPriority.HIGH,
        TaskPriority.ETL,
        TaskPriority.NORMAL,
        TaskPriority.REPORTS,
        TaskPriority.NOTIFICATIONS,
        TaskPriority.LOW,
    ]

    def __init__(self, redis_url: str | None = None, max_size: int = 10000):
        self._redis = None
        self._redis_url = redis_url
        self._max_size = max_size
        self._stats = QueueStats()
        self._tasks: dict[str, Task] = {}  # All tasks by ID
        self._dead_letter: list[Task] = []

        # In-memory queues per priority
        self._queues: dict[TaskPriority, asyncio.Queue] = {
            p: asyncio.Queue(maxsize=max_size) for p in TaskPriority
        }

        # Try Redis connection
        if redis_url and HAS_REDIS:
            try:
                self._redis = redis_lib.from_url(redis_url, decode_responses=True)
                self._redis.ping()
            except Exception:
                self._redis = None

    @property
    def is_redis_backend(self) -> bool:
        return self._redis is not None

    async def enqueue(self, task: Task) -> str:
        """Add a task to the appropriate priority queue."""
        task.status = TaskStatus.PENDING
        self._tasks[task.id] = task
        self._stats.total_enqueued += 1
        self._stats.by_priority[task.priority.value] = (
            self._stats.by_priority.get(task.priority.value, 0) + 1
        )

        if self._redis:
            if task.func_path is None and task.func is not None:
                task.func_path = _resolve_func_path(task.func)
                if task.func_path is None:
                    logger.warning(
                        "Task '%s' function is not re-importable (lambda/closure); it will "
                        "only run if dequeued by this same process.",
                        task.name,
                    )
            self._redis.lpush(
                f"queue:{task.priority.value}",
                json.dumps(task.to_dict()),
            )
        else:
            await self._queues[task.priority].put(task)

        return task.id

    async def dequeue(self, timeout: float = 1.0) -> Task | None:
        """Get the next task from the highest-priority non-empty queue."""
        for priority in self.PRIORITY_ORDER:
            try:
                if self._redis:
                    raw = self._redis.brpop(f"queue:{priority.value}", timeout=int(timeout))
                    if raw:
                        _, data = raw
                        task_dict = json.loads(data)
                        task = self._tasks.get(task_dict["id"])
                        if task:
                            return task
                        # Not in this process's local cache — likely dequeued
                        # by a separate worker process. Reconstruct the task
                        # from the serialized payload so it can still run.
                        task = self._reconstruct_task(task_dict)
                        if task:
                            self._tasks[task.id] = task
                            return task
                        logger.error(
                            "Could not reconstruct task %s from queue payload "
                            "(missing/unresolvable func_path); dropping.",
                            task_dict.get("id"),
                        )
                else:
                    task = await asyncio.wait_for(
                        self._queues[priority].get(),
                        timeout=timeout / len(self.PRIORITY_ORDER),
                    )
                    return task
            except (asyncio.TimeoutError, Exception):
                continue
        return None

    def _reconstruct_task(self, task_dict: dict) -> Task | None:
        """Rebuild a runnable Task from a Redis-serialized payload.

        Used when a task is dequeued by a process other than the one that
        enqueued it (the normal case for a separate worker container).
        """
        func_path = task_dict.get("func_path")
        if not func_path:
            return None
        try:
            func = _import_from_path(func_path)
        except Exception as e:
            logger.error("Failed to import function for task from '%s': %s", func_path, e)
            return None

        return Task(
            id=task_dict["id"],
            name=task_dict.get("name", ""),
            func=func,
            func_path=func_path,
            args=tuple(task_dict.get("args", [])),
            kwargs=task_dict.get("kwargs", {}) or {},
            priority=TaskPriority(task_dict["priority"]),
            retries=task_dict.get("retries", 0),
            max_retries=task_dict.get("max_retries", 3),
            timeout=task_dict.get("timeout", 300),
            metadata=task_dict.get("metadata", {}) or {},
        )

    async def execute(self, task: Task) -> Any:
        """Execute a task with timeout and retry logic."""
        task.status = TaskStatus.RUNNING
        task.started_at = time.time()
        self._stats.by_status[task.status.value] = (
            self._stats.by_status.get(task.status.value, 0) + 1
        )

        try:
            if task.func is None:
                raise ValueError(f"Task '{task.name}' has no function")

            result = await asyncio.wait_for(
                self._call_func(task),
                timeout=task.timeout,
            )

            task.result = result
            task.status = TaskStatus.COMPLETED
            task.completed_at = time.time()
            self._stats.total_completed += 1
            return result

        except asyncio.TimeoutError:
            task.error = f"Task timed out after {task.timeout}s"
            task.status = TaskStatus.FAILED
            self._stats.total_failed += 1
            await self._handle_failure(task)
        except Exception as e:
            task.error = str(e)
            task.status = TaskStatus.FAILED
            self._stats.total_failed += 1
            await self._handle_failure(task)

        return None

    async def _call_func(self, task: Task) -> Any:
        """Call the task function (sync or async)."""
        if asyncio.iscoroutinefunction(task.func):
            return await task.func(*task.args, **task.kwargs)
        else:
            return task.func(*task.args, **task.kwargs)

    async def _handle_failure(self, task: Task) -> None:
        """Handle task failure with retry logic."""
        if task.retries < task.max_retries:
            task.retries += 1
            task.status = TaskStatus.RETRYING
            self._stats.total_retried += 1
            # Exponential backoff
            delay = 2**task.retries
            await asyncio.sleep(delay)
            task.status = TaskStatus.PENDING
            task.error = None
            await self.enqueue(task)
        else:
            self._dead_letter.append(task)
            self._stats.dead_letter_count += 1

    def get_task(self, task_id: str) -> Task | None:
        """Get a task by ID."""
        return self._tasks.get(task_id)

    def get_stats(self) -> QueueStats:
        """Get queue statistics."""
        # Update by_status from current tasks
        self._stats.by_status = {}
        for task in self._tasks.values():
            self._stats.by_status[task.status.value] = (
                self._stats.by_status.get(task.status.value, 0) + 1
            )
        return self._stats

    def get_dead_letter_queue(self) -> list[dict]:
        """Get dead letter queue contents."""
        return [t.to_dict() for t in self._dead_letter]

    def clear_dead_letter(self) -> int:
        """Clear the dead letter queue, return count removed."""
        count = len(self._dead_letter)
        self._dead_letter.clear()
        self._stats.dead_letter_count = 0
        return count

    def cancel_task(self, task_id: str) -> bool:
        """Cancel a pending task."""
        task = self._tasks.get(task_id)
        if task and task.status == TaskStatus.PENDING:
            task.status = TaskStatus.CANCELLED
            return True
        return False

    @property
    def pending_count(self) -> int:
        """Count of pending tasks across all queues."""
        if self._redis:
            return sum(self._redis.llen(f"queue:{p.value}") for p in TaskPriority)
        return sum(q.qsize() for q in self._queues.values())
