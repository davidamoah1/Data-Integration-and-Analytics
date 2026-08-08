"""Workflow execution engine.

The engine takes a `WorkflowVersion` (a DAG of nodes and edges) and executes
it respecting dependencies, retries, timeouts, and conditional branching.
"""

from __future__ import annotations

import concurrent.futures
import logging
import time
import uuid
from dataclasses import dataclass
from typing import Any

from sqlalchemy.orm import Session as DbSession

from workflows.lineage import LineageBuilder
from workflows.models import WorkflowExecution, WorkflowJob, WorkflowLineage, WorkflowVersion
from workflows.nodes import WorkflowContext, create_node

logger = logging.getLogger(__name__)


@dataclass
class RetryPolicy:
    max_retries: int = 0
    backoff_seconds: float = 1.0
    backoff_multiplier: float = 2.0
    timeout_seconds: float | None = None

    @classmethod
    def from_config(cls, config: dict | None) -> RetryPolicy:
        if config is None:
            return cls()
        return cls(
            max_retries=int(config.get("max_retries", 0)),
            backoff_seconds=float(config.get("backoff_seconds", 1.0)),
            backoff_multiplier=float(config.get("backoff_multiplier", 2.0)),
            timeout_seconds=config.get("timeout_seconds"),
        )


class WorkflowEngine:
    """Execute workflow versions and record results."""

    def __init__(self, db: DbSession, max_workers: int = 4):
        self.db = db
        self.max_workers = max_workers

    def execute(
        self,
        workflow_id: int,
        version: WorkflowVersion,
        triggered_by: int | None,
        organization_id: int | None,
        trigger_type: str = "manual",
        initial_inputs: dict[str, Any] | None = None,
    ) -> WorkflowExecution:
        """Start and run a workflow execution synchronously."""
        execution_id = str(uuid.uuid4())
        execution = WorkflowExecution(
            execution_id=execution_id,
            workflow_id=workflow_id,
            version_id=version.id,
            organization_id=organization_id,
            triggered_by=triggered_by,
            trigger_type=trigger_type,
            status="running",
            started_at=datetime.now(timezone.utc),
            node_results={},
            context=initial_inputs or {},
            metrics={},
            errors=[],
            warnings=[],
        )
        self.db.add(execution)
        self.db.commit()

        # Create queue job for observability
        job = WorkflowJob(
            execution_id=execution_id,
            status="running",
            started_at=execution.started_at,
        )
        self.db.add(job)
        self.db.commit()

        try:
            self._run_version(execution, version, initial_inputs)
            if execution.status in ("paused", "failed"):
                pass  # already set by orchestration
            else:
                execution.status = "completed"
            if execution.node_results:
                final_node = max(
                    execution.node_results,
                    key=lambda k: execution.node_results[k].get("completed_at", ""),
                )
                execution.node_results[final_node]
                execution.ai_summary = self._generate_ai_summary(execution)
        except Exception as e:
            logger.exception("Workflow execution failed")
            execution.status = "failed"
            execution.errors.append(str(e))

        execution.completed_at = datetime.now(timezone.utc)
        execution.duration_seconds = (
            int((execution.completed_at - execution.started_at).total_seconds())
            if execution.started_at
            else None
        )
        job.status = execution.status
        job.completed_at = execution.completed_at
        self.db.commit()
        return execution

    def _run_version(
        self,
        execution: WorkflowExecution,
        version: WorkflowVersion,
        initial_inputs: dict[str, Any] | None,
    ) -> None:
        nodes = {n["id"]: n for n in version.nodes}
        edges = version.edges or []
        children = {nid: [] for nid in nodes}
        parents = {nid: [] for nid in nodes}
        for edge in edges:
            src = edge.get("source")
            tgt = edge.get("target")
            if src in children and tgt in parents:
                children[src].append(tgt)
                parents[tgt].append(src)

        ctx = WorkflowContext(execution.execution_id, version.config or {}, initial_inputs)
        completed: set[str] = set()
        failed: set[str] = set()
        pending_approval: set[str] = set()

        lineage = LineageBuilder(execution.execution_id, organization_id=execution.organization_id)

        remaining = set(nodes.keys())
        while remaining:
            ready = {
                nid
                for nid in remaining
                if all(p in completed for p in parents[nid])
                and not any(p in failed for p in parents[nid])
            }
            if not ready:
                # Cyclic dependency or all remaining blocked by failures
                for nid in remaining:
                    if nid not in execution.node_results:
                        self._record_node_result(
                            execution,
                            nid,
                            {
                                "status": "failed",
                                "errors": ["Dependency not satisfied or cycle detected"],
                            },
                        )
                execution.status = "failed"
                break

            # Separate independent nodes for potential parallel execution
            independent = [nid for nid in ready if len(parents[nid]) == 0]
            dependent_ready = [nid for nid in ready if nid not in independent]
            batch = independent[: self.max_workers] if independent else dependent_ready[:1]

            if len(batch) == 1:
                results = {batch[0]: self._execute_node(nodes[batch[0]], ctx, lineage)}
            else:
                with concurrent.futures.ThreadPoolExecutor(
                    max_workers=self.max_workers
                ) as executor:
                    futures = {
                        executor.submit(self._execute_node, nodes[nid], ctx, lineage): nid
                        for nid in batch
                    }
                    results = {}
                    for future in concurrent.futures.as_completed(futures):
                        nid = futures[future]
                        try:
                            results[nid] = future.result()
                        except Exception as exc:
                            logger.error(f"Node {nid} raised: {exc}")
                            results[nid] = {"status": "failed", "errors": [str(exc)]}

            for nid in batch:
                node_result = results[nid]
                self._record_node_result(execution, nid, node_result)
                ctx.set_output(nid, node_result)
                if node_result.status == "failed":
                    failed.add(nid)
                    execution.errors.extend(node_result.errors)
                    execution.status = "failed"
                elif node_result.status == "pending_approval":
                    pending_approval.add(nid)
                    execution.status = "paused"
                    break
                else:
                    completed.add(nid)
                    self._propagate_lineage(node_result, nodes[nid], lineage)

            remaining -= set(batch)
            if pending_approval:
                break

        execution.context = ctx.variables if ctx.variables else {}
        # Persist lineage edges
        for edge in lineage.edges:
            self.db.add(WorkflowLineage(**edge))
        self.db.commit()

    def _execute_node(self, node_def: dict, ctx: WorkflowContext, lineage: LineageBuilder) -> Any:
        node_id = node_def["id"]
        node_type = node_def["type"]
        config = node_def.get("config", {})
        retry = RetryPolicy.from_config(config.get("retry_policy"))

        node = create_node(node_type, node_id, config)
        last_exception: Exception | None = None
        for attempt in range(retry.max_retries + 1):
            try:
                if retry.timeout_seconds:
                    result = self._run_with_timeout(node, ctx, retry.timeout_seconds)
                else:
                    result = node.run(ctx)
                if result.status == "failed" and retry.max_retries and attempt < retry.max_retries:
                    wait = retry.backoff_seconds * (retry.backoff_multiplier**attempt)
                    logger.warning(
                        f"Node {node_id} failed, retrying in {wait}s (attempt {attempt + 1})"
                    )
                    time.sleep(wait)
                    continue
                return result
            except Exception as e:
                last_exception = e
                if attempt < retry.max_retries:
                    wait = retry.backoff_seconds * (retry.backoff_multiplier**attempt)
                    time.sleep(wait)
                else:
                    from workflows.nodes import NodeResult

                    return NodeResult(status="failed", errors=[str(last_exception)])

    def _run_with_timeout(self, node, ctx: WorkflowContext, timeout: float):
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(node.run, ctx)
            try:
                return future.result(timeout=timeout)
            except concurrent.futures.TimeoutError:
                return node.run(ctx).__class__(
                    status="failed", errors=[f"Timeout after {timeout}s"]
                )

    def _record_node_result(self, execution: WorkflowExecution, node_id: str, result: Any) -> None:
        execution.node_results[node_id] = {
            "status": result.status if hasattr(result, "status") else str(result),
            "rows_processed": result.rows_processed if hasattr(result, "rows_processed") else 0,
            "rows_failed": result.rows_failed if hasattr(result, "rows_failed") else 0,
            "errors": result.errors if hasattr(result, "errors") else [],
            "warnings": result.warnings if hasattr(result, "warnings") else [],
            "metadata": result.metadata if hasattr(result, "metadata") else {},
            "completed_at": datetime.now(timezone.utc).isoformat(),
        }
        execution.warnings.extend(result.warnings if hasattr(result, "warnings") else [])

    def _propagate_lineage(self, result: Any, node_def: dict, lineage: LineageBuilder) -> None:
        node_type = node_def["type"]
        node_id = node_def["id"]
        lineage.add_step(node_type, node_id, node_def.get("config", {}))

    def _generate_ai_summary(self, execution: WorkflowExecution) -> str:
        status = execution.status
        duration = execution.duration_seconds or 0
        node_count = len(execution.node_results)
        error_count = len(execution.errors)
        return f"Workflow {execution.execution_id} finished with status {status} in {duration}s across {node_count} nodes; {error_count} errors."


# Datetime imports must be at module level for runtime use in the engine above.
from datetime import datetime, timezone  # noqa: E402,F401
