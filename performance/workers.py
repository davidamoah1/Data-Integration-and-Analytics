"""Background Worker Pool.

Manages a pool of workers that process tasks from the queue.
Features:
  - Dynamic scaling (min/max workers based on queue depth)
  - Worker health monitoring
  - Graceful shutdown
  - Task execution metrics

Usage:
    pool = WorkerPool(task_queue, min_workers=2, max_workers=10)
    await pool.start()  # Starts workers in background
    # ... tasks get processed ...
    await pool.stop()   # Graceful shutdown
"""

from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass, field
from typing import Any

from performance.queue import Task, TaskQueue, TaskStatus

logger = logging.getLogger("performance.workers")


@dataclass
class WorkerStats:
    """Statistics for a single worker."""

    worker_id: str
    tasks_started: int = 0
    tasks_completed: int = 0
    tasks_failed: int = 0
    tasks_timeout: int = 0
    is_busy: bool = False
    current_task: str | None = None
    uptime: float = field(default_factory=time.time)

    def to_dict(self) -> dict:
        return {
            "worker_id": self.worker_id,
            "tasks_started": self.tasks_started,
            "tasks_completed": self.tasks_completed,
            "tasks_failed": self.tasks_failed,
            "tasks_timeout": self.tasks_timeout,
            "is_busy": self.is_busy,
            "current_task": self.current_task,
            "uptime": round(time.time() - self.uptime, 1),
        }


class Worker:
    """Individual background worker that processes tasks."""

    def __init__(self, worker_id: str, task_queue: TaskQueue, stats: WorkerStats):
        self.worker_id = worker_id
        self.task_queue = task_queue
        self.stats = stats
        self._running = False
        self._task: asyncio.Task | None = None

    async def start(self) -> None:
        """Start the worker loop."""
        self._running = True
        self._task = asyncio.create_task(self._loop())
        logger.info(f"Worker {self.worker_id} started")

    async def stop(self) -> None:
        """Stop the worker gracefully."""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info(f"Worker {self.worker_id} stopped")

    async def _loop(self) -> None:
        """Main worker loop — dequeue and execute tasks."""
        while self._running:
            try:
                task = await self.task_queue.dequeue(timeout=1.0)
                if task is None:
                    continue

                self.stats.is_busy = True
                self.stats.current_task = task.name
                self.stats.tasks_started += 1

                await self.task_queue.execute(task)

                if task.status == TaskStatus.COMPLETED:
                    self.stats.tasks_completed += 1
                elif task.status == TaskStatus.FAILED:
                    self.stats.tasks_failed += 1

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Worker {self.worker_id} error: {e}")
                self.stats.tasks_failed += 1
            finally:
                self.stats.is_busy = False
                self.stats.current_task = None


class WorkerPool:
    """Managed pool of background workers with dynamic scaling.

    Args:
        task_queue: The TaskQueue to pull work from.
        min_workers: Minimum number of workers to maintain.
        max_workers: Maximum number of workers allowed.
        scale_up_threshold: Queue depth to trigger scaling up.
        scale_down_threshold: Queue depth to trigger scaling down.
        scale_check_interval: Seconds between scale checks.
    """

    def __init__(
        self,
        task_queue: TaskQueue,
        min_workers: int = 2,
        max_workers: int = 20,
        scale_up_threshold: int = 10,
        scale_down_threshold: int = 2,
        scale_check_interval: int = 30,
    ):
        self.task_queue = task_queue
        self.min_workers = min_workers
        self.max_workers = max_workers
        self.scale_up_threshold = scale_up_threshold
        self.scale_down_threshold = scale_down_threshold
        self.scale_check_interval = scale_check_interval

        self._workers: dict[str, Worker] = {}
        self._worker_stats: dict[str, WorkerStats] = {}
        self._running = False
        self._manager_task: asyncio.Task | None = None
        self._worker_counter = 0

    async def start(self) -> None:
        """Start the worker pool with initial workers."""
        self._running = True
        for _ in range(self.min_workers):
            await self._add_worker()
        self._manager_task = asyncio.create_task(self._manage_pool())
        logger.info(
            f"WorkerPool started with {self.min_workers} workers "
            f"(max: {self.max_workers})"
        )

    async def stop(self) -> None:
        """Stop all workers gracefully."""
        self._running = False
        if self._manager_task:
            self._manager_task.cancel()
            try:
                await self._manager_task
            except asyncio.CancelledError:
                pass

        # Stop all workers
        stop_tasks = [worker.stop() for worker in self._workers.values()]
        await asyncio.gather(*stop_tasks, return_exceptions=True)
        self._workers.clear()
        self._worker_stats.clear()
        logger.info("WorkerPool stopped")

    async def _add_worker(self) -> str:
        """Add a new worker to the pool."""
        self._worker_counter += 1
        worker_id = f"worker-{self._worker_counter}"
        stats = WorkerStats(worker_id=worker_id)
        worker = Worker(worker_id, self.task_queue, stats)
        self._workers[worker_id] = worker
        self._worker_stats[worker_id] = stats
        await worker.start()
        return worker_id

    async def _remove_worker(self) -> None:
        """Remove a worker from the pool (gracefully)."""
        if len(self._workers) <= self.min_workers:
            return
        # Remove the last added worker
        worker_id = list(self._workers.keys())[-1]
        worker = self._workers.pop(worker_id)
        await worker.stop()
        self._worker_stats.pop(worker_id, None)
        logger.info(f"Scaled down: removed {worker_id}, {len(self._workers)} workers remaining")

    async def _manage_pool(self) -> None:
        """Dynamic pool scaling based on queue depth."""
        while self._running:
            try:
                await asyncio.sleep(self.scale_check_interval)
                if not self._running:
                    break

                queue_depth = self.task_queue.pending_count
                active_workers = sum(
                    1 for s in self._worker_stats.values() if s.is_busy
                )
                total_workers = len(self._workers)

                # Scale up
                if (
                    queue_depth > self.scale_up_threshold
                    and total_workers < self.max_workers
                    and active_workers / max(total_workers, 1) > 0.7
                ):
                    new_id = await self._add_worker()
                    logger.info(
                        f"Scaled up: added {new_id}, "
                        f"{len(self._workers)} workers now"
                    )

                # Scale down
                elif (
                    queue_depth < self.scale_down_threshold
                    and total_workers > self.min_workers
                    and active_workers / max(total_workers, 1) < 0.3
                ):
                    await self._remove_worker()

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Pool manager error: {e}")

    def get_stats(self) -> dict:
        """Get pool statistics."""
        total_started = sum(s.tasks_started for s in self._worker_stats.values())
        total_completed = sum(s.tasks_completed for s in self._worker_stats.values())
        total_failed = sum(s.tasks_failed for s in self._worker_stats.values())
        active = sum(1 for s in self._worker_stats.values() if s.is_busy)

        return {
            "total_workers": len(self._workers),
            "active_workers": active,
            "idle_workers": len(self._workers) - active,
            "min_workers": self.min_workers,
            "max_workers": self.max_workers,
            "total_tasks_started": total_started,
            "total_tasks_completed": total_completed,
            "total_tasks_failed": total_failed,
            "queue_depth": self.task_queue.pending_count,
            "workers": [s.to_dict() for s in self._worker_stats.values()],
        }
