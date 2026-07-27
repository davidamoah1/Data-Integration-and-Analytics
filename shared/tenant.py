"""Tenant context helpers for multi-organization isolation.

Provides centralized utilities to extract the current user's organization,
enforce organization-scoped access, and build organization-filtered queries.
Every route that handles organization-owned resources should use these helpers
instead of trusting IDs from the request body or query string.
"""

from collections.abc import Callable
from typing import Any

from fastapi import Depends, HTTPException, status
from sqlalchemy import Select
from sqlalchemy.orm import Session as DbSession

from shared.database import get_db
from shared.dependencies import get_current_user
from shared.exceptions import AuthorizationError, NotFoundError


def get_current_organization_id(current_user: dict) -> int:
    """Return the organization id bound to the authenticated user.

    Raises:
        HTTPException: 403 if the user is not assigned to an organization.
    """
    org_id = current_user.get("organization_id")
    if org_id is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is not assigned to an organization.",
        )
    return int(org_id)


def is_super_admin(current_user: dict) -> bool:
    """Return True if the user has the super_admin platform role."""
    roles = set(current_user.get("roles", []))
    return "super_admin" in roles


def require_organization_access(current_user: dict, organization_id: int | None = None) -> int:
    """Ensure the user is allowed to access the requested organization.

    - Super admins may access any organization.
    - Other users may only access their own organization_id.

    Args:
        current_user: Decoded user dict from get_current_user.
        organization_id: Optional organization id to check. If None, the user's
            own organization is returned and no cross-org check is performed.

    Returns:
        The organization id the user is authorized to access.

    Raises:
        AuthorizationError: If the user is forbidden from the target org.
    """
    user_org_id = get_current_organization_id(current_user)

    if organization_id is None:
        return user_org_id

    if organization_id != user_org_id and not is_super_admin(current_user):
        raise AuthorizationError("Access to this organization is not permitted.")

    return organization_id


def require_super_admin(current_user: dict) -> None:
    """Raise an authorization error if the user is not a super admin."""
    if not is_super_admin(current_user):
        raise AuthorizationError("Super admin privileges required.")


def apply_organization_filter(
    query: Select,
    model: Any,
    organization_id: int,
) -> Select:
    """Add an organization_id filter to a SQLAlchemy select query.

    The model must expose an `organization_id` column. This is a safe,
    explicit alternative to implicit query rewriting and keeps the access
    control visible in the repository layer.
    """
    return query.where(model.organization_id == organization_id)


async def get_tenant_context(
    current_user: dict = Depends(get_current_user),
    db: DbSession = Depends(get_db),
) -> dict:
    """Dependency that returns the authenticated user and resolved org id.

    Usage:
        @router.get("/datasets")
        async def list_datasets(tenant: dict = Depends(get_tenant_context)):
            org_id = tenant["organization_id"]
            ...
    """
    return {
        "user": current_user,
        "user_id": current_user["id"],
        "organization_id": get_current_organization_id(current_user),
        "is_super_admin": is_super_admin(current_user),
        "db": db,
    }


def tenant_scoped_dependency() -> Callable:
    """Factory for a FastAPI dependency that injects the tenant organization id.

    Returns a dependency that resolves to the current user's organization id.
    """

    async def _resolve(current_user: dict = Depends(get_current_user)) -> int:
        return get_current_organization_id(current_user)

    return _resolve
