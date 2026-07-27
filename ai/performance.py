"""AI Performance Optimization.

Provides:
  - Lazy context loading (only gather relevant data for the query)
  - Token budget management (prioritize critical context within limits)
  - Response latency monitoring
  - AI failure rate tracking with retry logic
"""

from __future__ import annotations

import logging
import time
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from ai.context_engine import EnterpriseAIContext
from ai.prompt_orchestrator import PromptTaskType

logger = logging.getLogger(__name__)


@dataclass
class LatencyRecord:
    """Record of a single AI request latency."""

    task_type: str
    duration_ms: float
    success: bool
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class PerformanceMonitor:
    """Monitors AI response latency and failure rates."""

    def __init__(self, max_records: int = 1000):
        self._records: deque[LatencyRecord] = deque(maxlen=max_records)
        self._failure_counts: dict[str, int] = defaultdict(int)
        self._total_counts: dict[str, int] = defaultdict(int)

    def record(self, task_type: str, duration_ms: float, success: bool = True):
        """Record a request result."""
        self._records.append(LatencyRecord(task_type, duration_ms, success))
        self._total_counts[task_type] += 1
        if not success:
            self._failure_counts[task_type] += 1

    def get_stats(self) -> dict:
        """Get performance statistics."""
        stats = {}
        for task_type in self._total_counts:
            records = [r for r in self._records if r.task_type == task_type]
            if records:
                latencies = [r.duration_ms for r in records]
                stats[task_type] = {
                    "total_requests": self._total_counts[task_type],
                    "failures": self._failure_counts[task_type],
                    "failure_rate": round(self._failure_counts[task_type] / self._total_counts[task_type], 4),
                    "avg_latency_ms": round(sum(latencies) / len(latencies), 2),
                    "min_latency_ms": round(min(latencies), 2),
                    "max_latency_ms": round(max(latencies), 2),
                    "p95_latency_ms": round(sorted(latencies)[int(len(latencies) * 0.95)] if len(latencies) > 1 else latencies[0], 2),
                }
        return stats

    def get_alerts(self, latency_threshold_ms: float = 5000, failure_rate_threshold: float = 0.1) -> list[dict]:
        """Get performance alerts for slow or failing task types."""
        alerts = []
        stats = self.get_stats()
        for task_type, s in stats.items():
            if s["avg_latency_ms"] > latency_threshold_ms:
                alerts.append({
                    "type": "high_latency",
                    "task_type": task_type,
                    "avg_latency_ms": s["avg_latency_ms"],
                    "threshold": latency_threshold_ms,
                })
            if s["failure_rate"] > failure_rate_threshold:
                alerts.append({
                    "type": "high_failure_rate",
                    "task_type": task_type,
                    "failure_rate": s["failure_rate"],
                    "threshold": failure_rate_threshold,
                })
        return alerts


class TokenBudgetManager:
    """Manages token budget for AI prompts.

    Prioritizes critical context within token limits to avoid
    truncation of important information.
    """

    # Priority levels (higher = more important)
    PRIORITY_CRITICAL = 0  # System prompt, task prompt
    PRIORITY_HIGH = 1      # Dataset schema, semantic mappings
    PRIORITY_MEDIUM = 2    # KPI values, active filters
    PRIORITY_LOW = 3       # Industry knowledge, conversation history
    PRIORITY_MINIMAL = 4   # Extra context, sample data

    def __init__(self, max_tokens: int = 8000):
        self.max_tokens = max_tokens

    def estimate_tokens(self, text: str) -> int:
        """Estimate token count for a text string.

        Uses a rough heuristic: ~4 characters per token.
        """
        return len(text) // 4

    def allocate_budget(self, context: EnterpriseAIContext, task_type: PromptTaskType) -> dict:
        """Allocate token budget across context sections.

        Returns a dict with token limits per section, ensuring
        critical sections get priority.
        """
        # Reserve tokens for system prompt and task prompt
        system_reserve = 500
        task_reserve = 500
        user_message_reserve = 500
        response_reserve = 2000

        available = self.max_tokens - system_reserve - task_reserve - user_message_reserve - response_reserve

        # Allocate by priority
        allocation = {
            "system_prompt": system_reserve,
            "task_prompt": task_reserve,
            "user_message": user_message_reserve,
            "response": response_reserve,
            "dataset_schema": min(available // 3, 1000),
            "semantic_mappings": min(available // 5, 500),
            "kpi_values": min(available // 6, 300),
            "active_filters": min(available // 8, 200),
            "industry_knowledge": min(available // 6, 300),
            "conversation_history": min(available // 8, 200),
            "sample_data": min(available // 10, 100),
            "extra_context": min(available // 10, 100),
        }

        return allocation

    def truncate_context(self, context_str: str, max_tokens: int) -> str:
        """Truncate context string to fit within token budget."""
        estimated = self.estimate_tokens(context_str)
        if estimated <= max_tokens:
            return context_str

        # Truncate to fit
        max_chars = max_tokens * 4
        if len(context_str) > max_chars:
            return context_str[:max_chars] + "\n...[context truncated for token budget]"
        return context_str


class LazyContextLoader:
    """Lazy-loads context sections only when needed.

    Instead of gathering all context upfront, this loader only
    retrieves the sections relevant to the current query, improving
    performance for simple questions.
    """

    # Task types that need full context
    FULL_CONTEXT_TASKS = {
        PromptTaskType.EXECUTIVE_SUMMARY,
        PromptTaskType.REPORT_GENERATION,
        PromptTaskType.ROOT_CAUSE_ANALYSIS,
    }

    # Task types that need minimal context
    LIGHT_CONTEXT_TASKS = {
        PromptTaskType.GENERAL_CHAT,
        PromptTaskType.DASHBOARD_ASSISTANCE,
    }

    def __init__(self, context_engine):
        self.context_engine = context_engine

    def should_load_section(self, task_type: PromptTaskType, section: str, user_message: str) -> bool:
        """Determine if a context section should be loaded for this request.

        Args:
            task_type: The AI task type.
            section: Context section name (dataset, dashboard, industry, conversation).
            user_message: The user's question.

        Returns:
            True if the section should be loaded.
        """
        if task_type in self.FULL_CONTEXT_TASKS:
            return True

        if task_type in self.LIGHT_CONTEXT_TASKS:
            # Only load dataset context if the message references data
            if section == "dataset":
                msg_lower = user_message.lower()
                return any(kw in msg_lower for kw in ["data", "column", "row", "table", "metric", "value"])
            if section == "industry":
                return False
            if section == "conversation":
                return True
            return False

        # For other task types, load relevant sections
        if section == "dataset":
            return task_type in {
                PromptTaskType.KPI_EXPLANATION,
                PromptTaskType.TREND_ANALYSIS,
                PromptTaskType.FORECASTING,
                PromptTaskType.ANOMALY_DETECTION,
                PromptTaskType.NL_ANALYTICS,
                PromptTaskType.DATA_QUALITY,
            }
        if section == "industry":
            return task_type in {
                PromptTaskType.RISK_ANALYSIS,
                PromptTaskType.REPORT_GENERATION,
            }
        if section == "dashboard":
            return task_type == PromptTaskType.DASHBOARD_ASSISTANCE
        if section == "conversation":
            return True

        return True


# ── Global instances ───────────────────────────────────

_performance_monitor: PerformanceMonitor | None = None
_token_manager: TokenBudgetManager | None = None


def get_performance_monitor() -> PerformanceMonitor:
    """Get the global performance monitor."""
    global _performance_monitor
    if _performance_monitor is None:
        _performance_monitor = PerformanceMonitor()
    return _performance_monitor


def get_token_manager() -> TokenBudgetManager:
    """Get the global token budget manager."""
    global _token_manager
    if _token_manager is None:
        _token_manager = TokenBudgetManager()
    return _token_manager


def track_performance(task_type: str):
    """Decorator to track AI request performance.

    Usage:
        @track_performance("executive_summary")
        def generate_summary(...):
            ...
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            monitor = get_performance_monitor()
            start = time.time()
            success = True
            try:
                result = func(*args, **kwargs)
                return result
            except Exception:
                success = False
                raise
            finally:
                duration_ms = (time.time() - start) * 1000
                monitor.record(task_type, duration_ms, success)
        return wrapper
    return decorator
