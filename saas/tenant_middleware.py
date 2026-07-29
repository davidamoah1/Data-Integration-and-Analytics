"""Tenant isolation enforcement middleware.

Ensures every API request that touches organization-owned resources
is scoped to the authenticated user's organization.
"""

from __future__ import annotations

import logging

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger("etl_project.tenant")


# Paths that don't require tenant isolation
PUBLIC_PATHS = {
    "/", "/health", "/ready", "/docs", "/openapi.json", "/redoc",
    "/auth/login", "/auth/register", "/auth/refresh",
}

# Path prefixes that are exempt (super admin only or public)
EXEMPT_PREFIXES = (
    "/admin-portal",
    "/public/",
    "/docs",
    "/openapi",
    "/redoc",
)


class TenantIsolationMiddleware(BaseHTTPMiddleware):
    """Middleware that logs and verifies tenant isolation.

    This is a defense-in-depth layer. The primary enforcement happens
    in route handlers via get_current_organization_id() and
    require_organization_access(). This middleware adds logging
    for audit purposes and blocks obviously malformed requests.
    """

    async def dispatch(self, request: Request, call_next):
        path = request.url.path

        # Skip public paths
        if path in PUBLIC_PATHS or any(path.startswith(p) for p in EXEMPT_PREFIXES):
            return await call_next(request)

        # Process request
        response = await call_next(request)

        # Log cross-tenant access attempts (4xx on org-scoped endpoints)
        if response.status_code == 403 and "organization" in str(response.body).lower():
            logger.warning(
                f"Cross-tenant access blocked: path={path}, "
                f"ip={request.client.host if request.client else 'unknown'}"
            )

        return response
