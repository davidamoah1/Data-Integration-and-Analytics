"""Request-scoped context variables for correlation and observability.

Provides:
- request_id: unique identifier for the current request
- correlation_id: identifier passed by upstream services/callers
"""

from contextvars import ContextVar

request_id: ContextVar[str | None] = ContextVar("request_id", default=None)
correlation_id: ContextVar[str | None] = ContextVar("correlation_id", default=None)
