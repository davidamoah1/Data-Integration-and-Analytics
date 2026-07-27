"""Enterprise middleware for security, rate limiting, and observability.

Provides:
- SecurityHeadersMiddleware: Adds standard security headers to every response.
- RateLimitMiddleware: Simple in-memory rate limiter per client IP.
- RequestLoggingMiddleware: Logs request method, path, status, and duration.
"""

import logging
import time
from collections import defaultdict

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger("etl_project")


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security-related HTTP headers to every response."""

    _HEADERS = {
        "X-Content-Type-Options": "nosniff",
        "X-Frame-Options": "DENY",
        "X-XSS-Protection": "1; mode=block",
        "Referrer-Policy": "strict-origin-when-cross-origin",
        "Permissions-Policy": "geolocation=(), microphone=(), camera=()",
        "Content-Security-Policy": (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "font-src 'self'; "
            "connect-src 'self'; "
            "frame-ancestors 'none'; "
            "base-uri 'self'; "
            "form-action 'self';"
        ),
        "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
        "Cross-Origin-Resource-Policy": "same-origin",
        "Cross-Origin-Embedder-Policy": "require-corp",
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
    """Simple in-memory sliding-window rate limiter.

    Limits requests per client IP within a configurable window.
    For production with multiple workers, replace with Redis-backed limiter.
    """

    def __init__(self, app, requests_per_minute: int = 60):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self._hits: dict[str, list[float]] = defaultdict(list)

    async def dispatch(self, request: Request, call_next):
        if request.url.path in ("/health", "/ready", "/"):
            return await call_next(request)

        client_ip = request.client.host if request.client else "unknown"
        now = time.time()
        window_start = now - 60.0

        hits = self._hits[client_ip]
        hits[:] = [t for t in hits if t > window_start]
        hits.append(now)

        if len(hits) > self.requests_per_minute:
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
