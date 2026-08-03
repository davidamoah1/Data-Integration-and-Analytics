"""Enhanced monitoring middleware for request tracing, metrics, and error tracking.

Combines:
- Prometheus metrics collection (request count, duration, errors)
- OpenTelemetry span creation
- Sentry error capture for unhandled exceptions
- Correlation ID propagation
"""

import time
import uuid

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from shared.context import correlation_id, request_id
from monitoring.prometheus import metrics_registry
from monitoring.otel import record_request as otel_record_request
from monitoring.sentry_integration import capture_exception, add_breadcrumb


# Paths that should be excluded from detailed metrics
_SKIP_PATHS = {"/health", "/ready", "/metrics", "/", "/favicon.ico"}


class MonitoringMiddleware(BaseHTTPMiddleware):
    """Unified monitoring middleware: metrics + tracing + error capture."""

    async def dispatch(self, request: Request, call_next):
        # Set request context
        req_token = request_id.set(str(uuid.uuid4()))
        corr_value = request.headers.get("X-Correlation-ID")
        corr_token = correlation_id.set(corr_value or str(uuid.uuid4()))

        start = time.time()
        status_code = 500
        response: Response | None = None

        try:
            response = await call_next(request)
            status_code = response.status_code
            return response
        except Exception as exc:
            # Capture in Sentry
            capture_exception(exc)
            # Record error metric
            metrics_registry.record_error(
                error_type=type(exc).__name__,
                component="middleware",
            )
            raise
        finally:
            duration_ms = (time.time() - start) * 1000
            path = request.url.path

            # Record metrics (skip health/metrics endpoints to reduce noise)
            if path not in _SKIP_PATHS:
                metrics_registry.record_request(
                    method=request.method,
                    path=path,
                    status=status_code,
                    duration_ms=duration_ms,
                )
                # Record in OpenTelemetry if initialised
                otel_record_request(
                    method=request.method,
                    path=path,
                    status=status_code,
                    duration_ms=duration_ms,
                )

            # Add Sentry breadcrumb for non-trivial requests
            if path not in _SKIP_PATHS and status_code < 500:
                add_breadcrumb(
                    message=f"{request.method} {path} -> {status_code}",
                    category="http",
                    level="info" if status_code < 400 else "warning",
                    data={
                        "duration_ms": round(duration_ms, 1),
                        "request_id": request_id.get(),
                    },
                )

            # Set response headers
            if response is not None:
                response.headers["X-Request-ID"] = request_id.get() or ""
                if corr_value:
                    response.headers["X-Correlation-ID"] = corr_value

            request_id.reset(req_token)
            correlation_id.reset(corr_token)
