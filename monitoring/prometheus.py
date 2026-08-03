"""Prometheus-compatible metrics endpoint.

Provides a /metrics endpoint in Prometheus text exposition format
without requiring the prometheus_client library. All metrics are
tracked in-process and served on demand.

Usage:
    from monitoring.prometheus import metrics_registry, record_request
    # ... in middleware:
    record_request(method, path, status, duration_ms)
    # ... in route:
    return PlainTextResponse(metrics_registry.render(), media_type="text/plain")
"""

import os
import threading
import time
from collections import defaultdict
from dataclasses import dataclass, field


@dataclass
class CounterMetric:
    """A simple monotonically increasing counter."""

    name: str
    help_text: str
    labels: dict[str, int] = field(default_factory=lambda: defaultdict(int))

    def inc(self, label_values: dict | None = None, amount: int = 1) -> None:
        key = self._label_key(label_values)
        self.labels[key] += amount

    def render(self) -> str:
        lines = [f"# HELP {self.name} {self.help_text}", f"# TYPE {self.name} counter"]
        for key, value in sorted(self.labels.items()):
            if key:
                lines.append(f'{self.name}{{{key}}} {value}')
            else:
                lines.append(f"{self.name} {value}")
        return "\n".join(lines)

    @staticmethod
    def _label_key(labels: dict | None) -> str:
        if not labels:
            return ""
        return ",".join(f'{k}="{v}"' for k, v in sorted(labels.items()))


@dataclass
class HistogramMetric:
    """A simple histogram with fixed buckets."""

    name: str
    help_text: str
    buckets: list[float] = field(
        default_factory=lambda: [5, 10, 25, 50, 100, 250, 500, 1000, 2500, 5000, 10000]
    )
    counts: dict[str, list[int]] = field(default_factory=dict)
    sums: dict[str, float] = field(default_factory=dict)
    totals: dict[str, int] = field(default_factory=dict)

    def observe(self, value: float, label_values: dict | None = None) -> None:
        key = CounterMetric._label_key(label_values)
        if key not in self.counts:
            self.counts[key] = [0] * len(self.buckets)
            self.sums[key] = 0.0
            self.totals[key] = 0
        for i, bound in enumerate(self.buckets):
            if value <= bound:
                self.counts[key][i] += 1
                break
        else:
            # Value exceeds all buckets — increment last bucket
            if self.counts[key]:
                self.counts[key][-1] += 1
        self.sums[key] += value
        self.totals[key] += 1

    def render(self) -> str:
        lines = [f"# HELP {self.name} {self.help_text}", f"# TYPE {self.name} histogram"]
        for key in sorted(self.counts.keys()):
            cumulative = 0
            for i, bound in enumerate(self.buckets):
                cumulative += self.counts[key][i]
                bucket_label = f'{key},"le"="{bound}"' if key else f'le="{bound}"'
                lines.append(f'{self.name}_bucket{{{bucket_label}}} {cumulative}')
            # +Inf bucket
            total = self.totals.get(key, 0)
            inf_label = f'{key},"le"="+Inf"' if key else 'le="+Inf"'
            lines.append(f'{self.name}_bucket{{{inf_label}}} {total}')
            sum_label = key if key else ""
            if sum_label:
                lines.append(f'{self.name}_sum{{{sum_label}}} {self.sums.get(key, 0):.2f}')
                lines.append(f'{self.name}_count{{{sum_label}}} {total}')
            else:
                lines.append(f"{self.name}_sum {self.sums.get(key, 0):.2f}")
                lines.append(f"{self.name}_count {total}")
        return "\n".join(lines)


@dataclass
class GaugeMetric:
    """A gauge that can go up and down."""

    name: str
    help_text: str
    labels: dict[str, float] = field(default_factory=dict)

    def set(self, value: float, label_values: dict | None = None) -> None:
        key = CounterMetric._label_key(label_values)
        self.labels[key] = value

    def inc(self, label_values: dict | None = None, amount: float = 1) -> None:
        key = CounterMetric._label_key(label_values)
        self.labels[key] += amount

    def dec(self, label_values: dict | None = None, amount: float = 1) -> None:
        key = CounterMetric._label_key(label_values)
        self.labels[key] -= amount

    def render(self) -> str:
        lines = [f"# HELP {self.name} {self.help_text}", f"# TYPE {self.name} gauge"]
        for key, value in sorted(self.labels.items()):
            if key:
                lines.append(f'{self.name}{{{key}}} {value}')
            else:
                lines.append(f"{self.name} {value}")
        return "\n".join(lines)


class MetricsRegistry:
    """Thread-safe registry for Prometheus metrics."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._counters: dict[str, CounterMetric] = {}
        self._histograms: dict[str, HistogramMetric] = {}
        self._gauges: dict[str, GaugeMetric] = {}
        self._init_metrics()

    def _init_metrics(self) -> None:
        """Register all standard application metrics."""
        self._counters["http_requests_total"] = CounterMetric(
            "http_requests_total", "Total HTTP requests"
        )
        self._histograms["http_request_duration_ms"] = HistogramMetric(
            "http_request_duration_ms", "HTTP request duration in milliseconds"
        )
        self._counters["db_queries_total"] = CounterMetric(
            "db_queries_total", "Total database queries"
        )
        self._histograms["db_query_duration_ms"] = HistogramMetric(
            "db_query_duration_ms", "Database query duration in milliseconds"
        )
        self._counters["pipeline_runs_total"] = CounterMetric(
            "pipeline_runs_total", "Total ETL pipeline runs"
        )
        self._counters["errors_total"] = CounterMetric(
            "errors_total", "Total application errors"
        )
        self._gauges["active_sessions"] = GaugeMetric(
            "active_sessions", "Number of active user sessions"
        )
        self._gauges["db_pool_size"] = GaugeMetric(
            "db_pool_size", "Database connection pool size"
        )
        self._gauges["db_pool_checked_out"] = GaugeMetric(
            "db_pool_checked_out", "Database connections checked out"
        )
        self._gauges["process_uptime_seconds"] = GaugeMetric(
            "process_uptime_seconds", "Process uptime in seconds"
        )
        self._gauges["db_record_count"] = GaugeMetric(
            "db_record_count", "Total records in sales table"
        )
        self._gauges["pipeline_success_rate"] = GaugeMetric(
            "pipeline_success_rate", "Pipeline success rate (0-1)"
        )
        self._start_time = time.time()

    def record_request(self, method: str, path: str, status: int, duration_ms: float) -> None:
        labels = {"method": method, "path": self._normalize_path(path), "status": str(status)}
        with self._lock:
            self._counters["http_requests_total"].inc(labels)
            self._histograms["http_request_duration_ms"].observe(duration_ms, labels)

    def record_db_query(self, operation: str, table: str, duration_ms: float) -> None:
        labels = {"operation": operation, "table": table}
        with self._lock:
            self._counters["db_queries_total"].inc(labels)
            self._histograms["db_query_duration_ms"].observe(duration_ms, labels)

    def record_pipeline_run(self, status: str) -> None:
        with self._lock:
            self._counters["pipeline_runs_total"].inc({"status": status})

    def record_error(self, error_type: str, component: str = "api") -> None:
        with self._lock:
            self._counters["errors_total"].inc({"error_type": error_type, "component": component})

    def set_active_sessions(self, count: int) -> None:
        with self._lock:
            self._gauges["active_sessions"].set(float(count))

    def set_db_pool_stats(self, pool_size: int, checked_out: int) -> None:
        with self._lock:
            self._gauges["db_pool_size"].set(float(pool_size))
            self._gauges["db_pool_checked_out"].set(float(checked_out))

    def set_record_count(self, count: int) -> None:
        with self._lock:
            self._gauges["db_record_count"].set(float(count))

    def set_pipeline_success_rate(self, rate: float) -> None:
        with self._lock:
            self._gauges["pipeline_success_rate"].set(rate)

    def update_uptime(self) -> None:
        with self._lock:
            self._gauges["process_uptime_seconds"].set(time.time() - self._start_time)

    @staticmethod
    def _normalize_path(path: str) -> str:
        """Normalize paths to reduce cardinality (strip IDs)."""
        parts = path.split("/")
        normalized = []
        for part in parts:
            if part and not part.isdigit() and len(part) > 20:
                normalized.append(":param")
            elif part and part.isdigit():
                normalized.append(":id")
            else:
                normalized.append(part)
        return "/".join(normalized)

    def render(self) -> str:
        """Render all metrics in Prometheus text exposition format."""
        self.update_uptime()
        sections = []
        with self._lock:
            for counter in self._counters.values():
                sections.append(counter.render())
            for histogram in self._histograms.values():
                sections.append(histogram.render())
            for gauge in self._gauges.values():
                sections.append(gauge.render())
        return "\n\n".join(sections) + "\n"


metrics_registry = MetricsRegistry()
