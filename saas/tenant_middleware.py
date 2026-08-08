"""Tenant isolation enforcement middleware.

Ensures every API request that touches organization-owned resources
is scoped to the authenticated user's organization.
"""

from __future__ import annotations

import logging

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger("etl_project.tenant")


# Paths that don't require tenant isolation
PUBLIC_PATHS = {
    "/",
    "/health",
    "/ready",
    "/docs",
    "/openapi.json",
    "/redoc",
    "/auth/login",
    "/auth/register",
    "/auth/refresh",
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
    """Middleware that enforces tenant isolation on every request.

    Extracts the JWT token from the Authorization header, decodes it,
    and injects the user's organization_id into request.state.tenant_org_id.
    This allows downstream handlers and repositories to access the tenant
    context without re-decoding the token.

    Defense-in-depth layers:
    1. This middleware — sets request.state.tenant_org_id
    2. Route-level — get_tenant_context / require_organization_access
    3. Query-level — TenantQueryManager / apply_organization_filter
    4. Resource-level — verify_resource_ownership
    """

    async def dispatch(self, request: Request, call_next):
        path = request.url.path

        # Skip public paths
        if path in PUBLIC_PATHS or any(path.startswith(p) for p in EXEMPT_PREFIXES):
            return await call_next(request)

        # Extract organization_id from JWT and inject into request state
        request.state.tenant_org_id = None
        request.state.tenant_user_id = None
        request.state.tenant_is_super_admin = False

        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header[7:]
            try:
                from shared.security import decode_token

                payload = decode_token(token)
                if payload and payload.get("type") == "access":
                    request.state.tenant_user_id = int(payload["sub"])
                    # Fetch user's organization_id from DB
                    from sqlalchemy.orm import Session as DbSession

                    from authentication.repositories import UserRepository
                    from shared.database import get_engine

                    engine = get_engine()
                    db = DbSession(engine)
                    try:
                        user_repo = UserRepository(db)
                        user = user_repo.get_by_id(int(payload["sub"]))
                        if user and user.is_active:
                            request.state.tenant_org_id = user.organization_id
                            # Check super_admin role
                            from authentication.repositories import UserRoleRepository

                            user_role_repo = UserRoleRepository(db)
                            roles = user_role_repo.get_roles_for_user(user.id)
                            request.state.tenant_is_super_admin = "super_admin" in set(roles)
                    finally:
                        db.close()
            except Exception:
                # Token invalid or expired — let downstream auth handle the 401
                pass

        # Process request
        response = await call_next(request)

        # Log cross-tenant access attempts (4xx on org-scoped endpoints)
        response_body = getattr(response, "body", b"")
        if response.status_code == 403 and "organization" in str(response_body).lower():
            logger.warning(
                f"Cross-tenant access blocked: path={path}, "
                f"ip={request.client.host if request.client else 'unknown'}, "
                f"user_id={getattr(request.state, 'tenant_user_id', None)}, "
                f"org_id={getattr(request.state, 'tenant_org_id', None)}"
            )

        return response
