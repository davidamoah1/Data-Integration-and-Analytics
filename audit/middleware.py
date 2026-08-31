"""Audit middleware â€” automatically logs API requests.

Intercepts all mutating requests (POST, PUT, PATCH, DELETE) and creates
audit log entries with user, action, resource, IP, and metadata. This
ensures comprehensive audit coverage without requiring manual log calls
in every route handler.

Excluded paths:
  - GET requests (read-only, no audit needed)
  - /docs, /openapi.json (API documentation)
  - /health (health checks)
  - Authentication endpoints (logged separately via log_security_event)
"""

from __future__ import annotations

import asyncio
import logging
import time

from fastapi import Request, Response
from sqlalchemy.orm import Session as DbSession
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

from audit.models import AuditLog
from shared.database import get_session_factory

logger = logging.getLogger(__name__)

# Paths to exclude from automatic audit logging
EXCLUDED_PATHS = {
    "/docs",
    "/openapi.json",
    "/redoc",
    "/health",
    "/api/auth/login",
    "/api/auth/refresh",
    "/api/auth/register",
}

# Action mapping based on HTTP method
METHOD_ACTIONS = {
    "POST": "create",
    "PUT": "update",
    "PATCH": "update",
    "DELETE": "delete",
}


def _extract_resource_info(path: str) -> tuple[str | None, str | None]:
    """Extract resource_type and action from URL path.

    Examples:
      /api/datasets/upload  â†’ ("dataset", "upload")
      /api/reports/42/export â†’ ("report", "export")
      /api/users/42/roles    â†’ ("user", "roles")
    """
    parts = [p for p in path.strip("/").split("/") if p]
    if not parts:
        return None, None

    # Skip "api" prefix
    if parts[0] == "api":
        parts = parts[1:]
    if not parts:
        return None, None

    resource_type = parts[0]
    # Remove trailing 's' for singular form (datasets â†’ dataset)
    if resource_type.endswith("s") and len(resource_type) > 3:
        resource_type = resource_type[:-1]

    # Determine sub-action from path
    action_suffix = None
    if len(parts) >= 3:
        # e.g., /reports/42/export â†’ action = "export"
        action_suffix = parts[-1]
    elif len(parts) == 2 and not parts[1].isdigit():
        # e.g., /files/upload â†’ action = "upload"
        action_suffix = parts[1]

    return resource_type, action_suffix


class AuditMiddleware(BaseHTTPMiddleware):
    """Middleware that logs mutating API requests to the audit table."""

    async def dispatch(
        self,
        request: Request,
        call_next: RequestResponseEndpoint,
    ) -> Response:
        # Skip GET requests and excluded paths
        if request.method == "GET":
            return await call_next(request)

        path = request.url.path
        if path in EXCLUDED_PATHS or path.startswith("/docs") or path.startswith("/api/auth"):
            return await call_next(request)

        # Process the request first
        start_time = time.time()
        response = await call_next(request)
        duration_ms = int((time.time() - start_time) * 1000)

        # Only log successful and common error responses
        if response.status_code >= 500:
            return response

        # Extract user info from request state (set by auth middleware)
        user_id: int | None = None
        organization_id: int | None = None
        try:
            user = getattr(request.state, "user", None)
            if user and isinstance(user, dict):
                user_id = user.get("id")
                organization_id = user.get("organization_id")
        except Exception:
            pass

        # Build action string
        resource_type, action_suffix = _extract_resource_info(path)
        base_action = METHOD_ACTIONS.get(request.method, request.method.lower())
        if action_suffix and action_suffix.isdigit():
            action = f"{resource_type}.{base_action}" if resource_type else base_action
        elif action_suffix:
            action = f"{resource_type}.{action_suffix}" if resource_type else action_suffix
        else:
            action = f"{resource_type}.{base_action}" if resource_type else base_action

        # Extract resource_id from path if present
        resource_id: int | None = None
        parts = [p for p in path.strip("/").split("/") if p]
        for part in parts:
            if part.isdigit():
                resource_id = int(part)
                break

        # Get client IP
        ip_address = None
        if request.client:
            ip_address = request.client.host

        user_agent = request.headers.get("user-agent", "")[:500] or None

        # Offload audit DB write to a background thread so the response
        # is returned immediately without waiting for the DB round-trip.
        audit_payload = {
            "user_id": user_id,
            "organization_id": organization_id,
            "action": action,
            "resource_type": resource_type,
            "resource_id": resource_id,
            "ip_address": ip_address,
            "user_agent": user_agent,
            "audit_metadata": {
                "method": request.method,
                "path": path,
                "status_code": response.status_code,
                "duration_ms": duration_ms,
                "auto_logged": True,
            },
        }

        async def _write_audit():
            try:
                await asyncio.to_thread(_persist_audit, audit_payload)
            except Exception as e:
                logger.debug("Auto-audit log failed for %s %s: %s", request.method, path, e)

        asyncio.create_task(_write_audit())

        return response


def _persist_audit(payload: dict) -> None:
    """Write an audit log entry in a synchronous context (called via to_thread)."""
    factory = get_session_factory()
    db: DbSession = factory()
    try:
        entry = AuditLog(
            user_id=payload["user_id"],
            organization_id=payload["organization_id"],
            action=payload["action"],
            resource_type=payload["resource_type"],
            resource_id=payload["resource_id"],
            ip_address=payload["ip_address"],
            user_agent=payload["user_agent"],
            audit_metadata=payload["audit_metadata"],
        )
        db.add(entry)
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
