"""OpenTelemetry tracing and metrics integration.

Sets up distributed tracing, metrics collection, and auto-instrumentation
for FastAPI, SQLAlchemy, and Redis when OTEL_EXPORTER_OTLP_ENDPOINT is configured.

Usage:
    from monitoring.otel import init_otel, get_tracer, get_meter, record_request_metrics

    init_otel()  # call once at startup (no-op if not configured)
"""

import os
from typing import Any

_otel_initialised = False
_tracer = None
_meter = None
_metrics: dict[str, Any] = {}


def init_otel() -> bool:
    """Initialise OpenTelemetry SDK if OTEL_EXPORTER_OTLP_ENDPOINT is set.

    Returns True if OTel was initialised, False otherwise.
    """
    global _otel_initialised, _tracer, _meter

    if _otel_initialised:
        return True

    endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "").strip()
    if not endpoint:
        return False

    try:
        from opentelemetry import trace, metrics
        from opentelemetry.sdk.resources import Resource
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor
        from opentelemetry.sdk.metrics import MeterProvider
        from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
        from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
        from opentelemetry.exporter.otlp.proto.http.metric_exporter import OTLPMetricExporter
        from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
        from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
        from opentelemetry.instrumentation.redis import RedisInstrumentor
        from opentelemetry.instrumentation.logging import LoggingInstrumentor
    except ImportError:
        return False

    service_name = os.getenv("OTEL_SERVICE_NAME", "aedip-api")
    service_version = os.getenv("OTEL_SERVICE_VERSION", "1.0.0")
    deployment_env = os.getenv("APP_ENV", "development")

    resource = Resource.create(
        {
            "service.name": service_name,
            "service.version": service_version,
            "deployment.environment": deployment_env,
        }
    )

    # Tracing
    trace_provider = TracerProvider(resource=resource)
    span_exporter = OTLPSpanExporter(endpoint=f"{endpoint}/v1/traces")
    span_processor = BatchSpanProcessor(span_exporter)
    trace_provider.add_span_processor(span_processor)
    trace.set_tracer_provider(trace_provider)
    _tracer = trace.get_tracer(service_name)

    # Metrics
    metric_exporter = OTLPMetricExporter(endpoint=f"{endpoint}/v1/metrics")
    metric_reader = PeriodicExportingMetricReader(
        metric_exporter,
        export_interval_millis=int(os.getenv("OTEL_METRIC_EXPORT_INTERVAL", "60000")),
    )
    meter_provider = MeterProvider(
        resource=resource,
        metric_readers=[metric_reader],
    )
    metrics.set_meter_provider(meter_provider)
    _meter = metrics.get_meter(service_name)

    # Auto-instrumentation
    LoggingInstrumentor().instrument(set_logging_format=True)

    # Register custom metrics
    _register_custom_metrics()

    _otel_initialised = True
    return True


def instrument_fastapi(app: Any) -> None:
    """Instrument a FastAPI application for OpenTelemetry tracing."""
    if not _otel_initialised:
        return
    try:
        from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
        FastAPIInstrumentor.instrument_app(app)
    except Exception:
        pass


def instrument_sqlalchemy(engine: Any) -> None:
    """Instrument a SQLAlchemy engine for OpenTelemetry tracing."""
    if not _otel_initialised:
        return
    try:
        from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
        SQLAlchemyInstrumentor.instrument_engine(engine)
    except Exception:
        pass


def instrument_redis(client: Any) -> None:
    """Instrument a Redis client for OpenTelemetry tracing."""
    if not _otel_initialised:
        return
    try:
        from opentelemetry.instrumentation.redis import RedisInstrumentor
        RedisInstrumentor.instrument_redis(client)
    except Exception:
        pass


def _register_custom_metrics() -> None:
    """Register custom application metrics."""
    global _metrics
    if _meter is None:
        return

    _metrics["request_counter"] = _meter.create_counter(
        "aedip_http_requests_total",
        description="Total HTTP requests",
        unit="1",
    )
    _metrics["request_duration"] = _meter.create_histogram(
        "aedip_http_request_duration_ms",
        description="HTTP request duration in milliseconds",
        unit="ms",
    )
    _metrics["db_query_counter"] = _meter.create_counter(
        "aedip_db_queries_total",
        description="Total database queries",
        unit="1",
    )
    _metrics["db_query_duration"] = _meter.create_histogram(
        "aedip_db_query_duration_ms",
        description="Database query duration in milliseconds",
        unit="ms",
    )
    _metrics["active_sessions"] = _meter.create_up_down_counter(
        "aedip_active_sessions",
        description="Number of active user sessions",
        unit="1",
    )
    _metrics["pipeline_runs"] = _meter.create_counter(
        "aedip_pipeline_runs_total",
        description="Total ETL pipeline runs",
        unit="1",
    )
    _metrics["errors_counter"] = _meter.create_counter(
        "aedip_errors_total",
        description="Total application errors",
        unit="1",
    )


def get_tracer():
    """Return the OTel tracer (None if not initialised)."""
    return _tracer


def get_meter():
    """Return the OTel meter (None if not initialised)."""
    return _meter


def record_request(method: str, path: str, status: int, duration_ms: float) -> None:
    """Record HTTP request metrics."""
    if not _otel_initialised:
        return
    counter = _metrics.get("request_counter")
    histogram = _metrics.get("request_duration")
    if counter:
        counter.add(1, {"method": method, "path": path, "status": str(status)})
    if histogram:
        histogram.record(duration_ms, {"method": method, "path": path})


def record_db_query(operation: str, table: str, duration_ms: float) -> None:
    """Record database query metrics."""
    if not _otel_initialised:
        return
    counter = _metrics.get("db_query_counter")
    histogram = _metrics.get("db_query_duration")
    if counter:
        counter.add(1, {"operation": operation, "table": table})
    if histogram:
        histogram.record(duration_ms, {"operation": operation, "table": table})


def record_error(error_type: str, component: str = "api") -> None:
    """Record an application error."""
    if not _otel_initialised:
        return
    counter = _metrics.get("errors_counter")
    if counter:
        counter.add(1, {"error_type": error_type, "component": component})


def record_pipeline_run(status: str) -> None:
    """Record a pipeline run."""
    if not _otel_initialised:
        return
    counter = _metrics.get("pipeline_runs")
    if counter:
        counter.add(1, {"status": status})


def update_session_count(delta: int) -> None:
    """Update the active session count (delta: +1 for new, -1 for ended)."""
    if not _otel_initialised:
        return
    counter = _metrics.get("active_sessions")
    if counter:
        counter.add(delta)


def is_initialised() -> bool:
    """Return True if OTel has been initialised."""
    return _otel_initialised


def start_span(name: str, attributes: dict | None = None):
    """Context manager for creating a span. No-op if OTel is not initialised."""
    if _tracer is None:
        from contextlib import nullcontext
        return nullcontext()
    return _tracer.start_as_current_span(name, attributes=attributes)
