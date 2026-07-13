"""FastAPI dependencies for authentication and authorization.

Provides:
- get_current_user: Extract and verify JWT from request
- require_permissions: Dependency factory for permission checks
- get_current_user_optional: Optional auth (for public endpoints)
"""

from typing import Optional, Callable
from functools import wraps

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session as DbSession

from shared.database import get_db
from shared.security import decode_token
from shared.exceptions import AuthenticationError, AuthorizationError
from authentication.repositories import (
    UserRepository, UserRoleRepository,
)

security_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_scheme),
    db: DbSession = Depends(get_db),
) -> dict:
    """Extract and verify the JWT access token from the request.

    Returns:
        Dict with user_id, email, roles, permissions.

    Raises:
        HTTPException 401 if token is missing or invalid.
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        payload = decode_token(credentials.credentials)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = int(payload["sub"])
    user_repo = UserRepository(db)
    user = user_repo.get_by_id(user_id)

    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or disabled",
        )

    user_role_repo = UserRoleRepository(db)
    roles = user_role_repo.get_roles_for_user(user_id)
    permissions = user_role_repo.get_all_permissions_for_user(user_id)

    return {
        "id": user_id,
        "email": user.email,
        "roles": roles,
        "permissions": permissions,
        "organization_id": user.organization_id,
    }


async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_scheme),
    db: DbSession = Depends(get_db),
) -> Optional[dict]:
    """Optional auth — returns None if no token provided (for public endpoints)."""
    if not credentials:
        return None
    try:
        return await get_current_user(credentials, db)
    except HTTPException:
        return None


def require_permissions(*required_perms: str) -> Callable:
    """Dependency factory that checks if the current user has required permissions.

    Usage in routes:
        @router.get("/users", dependencies=[Depends(require_permissions("users.read"))])

    The user must have at least ONE of the required permissions.
    Super admin role bypasses all checks.
    """
    async def permission_checker(
        current_user: dict = Depends(get_current_user),
    ) -> dict:
        if "super_admin" in current_user["roles"]:
            return current_user

        user_perms = set(current_user["permissions"])
        required = set(required_perms)

        if not required & user_perms:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Missing required permissions: {', '.join(required_perms)}",
            )

        return current_user

    return permission_checker


def require_any_role(*roles: str) -> Callable:
    """Dependency factory that checks if the current user has any of the specified roles."""
    async def role_checker(
        current_user: dict = Depends(get_current_user),
    ) -> dict:
        user_roles = set(current_user["roles"])
        required = set(roles)

        if not required & user_roles and "super_admin" not in user_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Missing required role: {', '.join(roles)}",
            )

        return current_user

    return role_checker
