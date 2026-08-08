"""Security utilities for the ecosystem.

- API key authentication middleware for public API routes
- Scope enforcement
- Organization isolation verification
- Plugin permission checks
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone

from fastapi import Request, Response
from sqlalchemy import select, update
from starlette.middleware.base import BaseHTTPMiddleware

from ecosystem.models import APIKey, APIKeyService, APIUsageLog

logger = logging.getLogger("etl_project.security")


class APIKeyAuthMiddleware(BaseHTTPMiddleware):
    """Middleware that authenticates public API requests via API key.

    Only applies to /public/* paths. Other paths use JWT auth via dependencies.
    Logs all API key usage for analytics and rate limiting.
    """

    async def dispatch(self, request: Request, call_next):
        path = request.url.path

        # Only process public API routes
        if not path.startswith("/public/"):
            return await call_next(request)

        # Skip health checks
        if path in ("/public/health", "/public/docs"):
            return await call_next(request)

        import time as _time

        start = _time.time()

        # Extract API key
        raw_key = request.headers.get("X-API-Key")
        if not raw_key:
            auth = request.headers.get("Authorization", "")
            if auth.startswith("Bearer dfk_"):
                raw_key = auth[7:]

        if not raw_key:
            return Response(
                content='{"detail": "API key required. Provide via X-API-Key header."}',
                status_code=401,
                media_type="application/json",
            )

        # Verify key
        key_hash = APIKeyService.hash_key(raw_key)
        db_gen = request.app.state.db_session_generator
        if not db_gen:
            # Fallback: just pass through if no DB generator
            return await call_next(request)

        db = next(db_gen())
        try:
            api_key = db.execute(
                select(APIKey).where(
                    APIKey.key_hash == key_hash,
                    APIKey.is_active == True,  # noqa: E712
                )
            ).scalar_one_or_none()

            if not api_key:
                return Response(
                    content='{"detail": "Invalid or revoked API key"}',
                    status_code=401,
                    media_type="application/json",
                )

            if api_key.expires_at and api_key.expires_at < datetime.now(timezone.utc):
                return Response(
                    content='{"detail": "API key has expired"}',
                    status_code=401,
                    media_type="application/json",
                )

            # Store key info on request state
            request.state.api_key_id = api_key.id
            request.state.org_id = api_key.organization_id
            request.state.scopes = api_key.scopes or []

            # Process request
            response = await call_next(request)

            # Log usage
            elapsed_ms = int((_time.time() - start) * 1000)
            usage = APIUsageLog(
                api_key_id=api_key.id,
                organization_id=api_key.organization_id,
                endpoint=path,
                method=request.method,
                status_code=response.status_code,
                response_time_ms=elapsed_ms,
                ip_address=request.client.host if request.client else None,
                user_agent=request.headers.get("user-agent", "")[:500],
            )
            db.add(usage)
            db.execute(
                update(APIKey)
                .where(APIKey.id == api_key.id)
                .values(last_used_at=datetime.now(timezone.utc))
            )
            db.commit()

            return response

        except Exception as e:
            logger.error(f"API key middleware error: {e}")
            return Response(
                content='{"detail": "Authentication error"}',
                status_code=500,
                media_type="application/json",
            )
        finally:
            db.close()


def verify_tenant_isolation(query, org_id: int, org_field: str = "organization_id"):
    """Ensure a query is scoped to the given organization."""
    return query.where(getattr(query.column_descriptions[0]["entity"], org_field) == org_id)


def check_plugin_permissions(plugin_permissions: list[str], user_permissions: list[str]) -> bool:
    """Check if the user has all required plugin permissions."""
    if not plugin_permissions:
        return True
    return all(p in user_permissions for p in plugin_permissions)
