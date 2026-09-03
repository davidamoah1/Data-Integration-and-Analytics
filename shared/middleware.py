"""Enterprise middleware for security, rate limiting, and observability.

Provides:
- SecurityHeadersMiddleware: Adds standard security headers to every response.
- RateLimitMiddleware: Redis-backed (or in-memory fallback) rate limiter per
  client IP.
- RequestLoggingMiddleware: Logs request method, path, status, and duration.
"""

import logging
import os
import time
from collections import defaultdict

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

try:
    import redis as redis_lib

    HAS_REDIS = True
except ImportError:
    HAS_REDIS = False

logger = logging.getLogger("etl_project")


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security-related HTTP headers to every response."""

    _extra_connect_src = os.getenv("CSP_CONNECT_SRC", "")
    _connect_src = "'self'" + (f" {_extra_connect_src}" if _extra_connect_src else "")
    _corp = os.getenv("CROSS_ORIGIN_RESOURCE_POLICY", "same-origin")
    _coep = os.getenv("CROSS_ORIGIN_EMBEDDER_POLICY", "require-corp")
    _HEADERS = {
        "X-Content-Type-Options": "nosniff",
        "X-Frame-Options": "DENY",
        "X-XSS-Protection": "1; mode=block",
        "Referrer-Policy": "strict-origin-when-cross-origin",
        "Permissions-Policy": "geolocation=(), microphone=(), camera=()",
        "Content-Security-Policy": (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "font-src 'self'; "
            f"connect-src {_connect_src}; "
            "frame-ancestors 'none'; "
            "base-uri 'self'; "
            "form-action 'self'; "
            "object-src 'none'; "
            "upgrade-insecure-requests;"
        ),
        "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
        "Cross-Origin-Resource-Policy": _corp,
        "Cross-Origin-Embedder-Policy": _coep,
        "Cross-Origin-Opener-Policy": "same-origin",
    }

    async def dispatch(self, request: Request, call_next):
        response: Response = await call_next(request)
        for key, value in self._HEADERS.items():
            response.headers.setdefault(key, value)
        return response


class RequestSizeLimitMiddleware(BaseHTTPMiddleware):
    """Reject requests whose Content-Length exceeds a configured maximum.

    This protects against memory exhaustion from oversized uploads before the
    request body is read. The default maximum (50 MB) matches the platform's
    file upload limit.
    """

    def __init__(self, app, max_bytes: int = 50 * 1024 * 1024):
        super().__init__(app)
        self.max_bytes = max_bytes

    async def dispatch(self, request: Request, call_next):
        # The batch upload endpoints accept up to 50 files and are validated
        # per-file by the route handler. Skip the global body-size check for
        # these paths so legitimate batch uploads aren't rejected.
        if (
            "/api/capture/documents/batch-upload" in request.url.path
            or "/api/certificates/upload" in request.url.path
        ):
            return await call_next(request)

        content_length = request.headers.get("content-length")
        if content_length:
            try:
                size = int(content_length)
            except ValueError:
                return Response(
                    status_code=400,
                    content='{"success":false,"message":"Invalid Content-Length","data":null}',
                    media_type="application/json",
                )
            if size > self.max_bytes:
                return Response(
                    status_code=413,
                    content='{"success":false,"message":"Request body too large","data":null}',
                    media_type="application/json",
                    headers={"Retry-After": "0"},
                )
        return await call_next(request)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiter per client IP, Redis-backed with in-memory fallback.

    When ``REDIS_URL`` is set and reachable, uses a Redis fixed-window
    counter (``INCR`` + ``EXPIRE``) so the limit is enforced consistently
    across multiple worker processes/instances â€” required for correctness
    once the app runs behind more than a single uvicorn worker (e.g. behind
    gunicorn/uvicorn workers, multiple containers, or serverless
    invocations sharing the same Redis).

    Falls back to the original in-memory sliding-window limiter (per-process
    only) when Redis is unavailable, so single-worker/dev/test setups keep
    working with no external dependency.
    """

    def __init__(self, app, requests_per_minute: int = 60, redis_url: str | None = None):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self._hits: dict[str, list[float]] = defaultdict(list)

        self._redis = None
        if redis_url is None:
            import os

            redis_url = os.getenv("REDIS_URL") or None
        if redis_url and HAS_REDIS:
            try:
                client = redis_lib.from_url(redis_url, decode_responses=True, socket_timeout=1)
                client.ping()
                self._redis = client
            except Exception:
                self._redis = None

        logger.info(
            "RateLimitMiddleware initialized (backend: %s, limit: %d/min)",
            "redis" if self._redis is not None else "memory",
            requests_per_minute,
        )

    @property
    def is_redis_backend(self) -> bool:
        return self._redis is not None

    def _check_redis(self, client_ip: str) -> bool:
        """Return True if request is allowed, False if rate limit exceeded.

        Falls back to allowing the request (fail-open) if Redis errors
        mid-check, so a transient Redis outage does not take down the API.
        """
        key = f"aedip:ratelimit:{client_ip}"
        try:
            count = self._redis.incr(key)
            if count == 1:
                self._redis.expire(key, 60)
            return count <= self.requests_per_minute
        except Exception:
            logger.warning("Redis rate-limit check failed for %s; failing open", client_ip)
            return True

    def _check_memory(self, client_ip: str) -> bool:
        now = time.time()
        window_start = now - 60.0

        hits = self._hits[client_ip]
        hits[:] = [t for t in hits if t > window_start]
        hits.append(now)

        return len(hits) <= self.requests_per_minute

    async def dispatch(self, request: Request, call_next):
        if request.url.path in ("/health", "/ready", "/"):
            return await call_next(request)

        client_ip = request.client.host if request.client else "unknown"

        allowed = (
            self._check_redis(client_ip)
            if self._redis is not None
            else self._check_memory(client_ip)
        )

        if not allowed:
            return Response(
                content='{"success":false,"message":"Rate limit exceeded","data":null}',
                status_code=429,
                media_type="application/json",
                headers={"Retry-After": "60"},
            )

        return await call_next(request)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Log each request with method, path, status code, and duration."""

    async def dispatch(self, request: Request, call_next):
        start = time.time()
        response: Response = await call_next(request)
        duration_ms = (time.time() - start) * 1000
        logger.info(
            f"{request.method} {request.url.path} "
            f"-> {response.status_code} ({duration_ms:.0f}ms)"
        )
        return response
