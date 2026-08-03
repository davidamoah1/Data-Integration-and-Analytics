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


def get_current_organization_id(current_user: dict, db: DbSession | None = None) -> int:
    """Return the organization id bound to the authenticated user.

    Super admins without an organization fall back to the "system" org
    when a db session is available.

    Raises:
        HTTPException: 403 if the user is not assigned to an organization.
    """
    org_id = current_user.get("organization_id")
    if org_id is None and is_super_admin(current_user) and db is not None:
        from organizations.models import Organization
        org = db.query(Organization).filter(Organization.slug == "system").first()
        if org:
            return org.id
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


def require_organization_access(
    current_user: dict,
    organization_id: int | None = None,
    db: DbSession | None = None,
) -> int:
    """Ensure the user is allowed to access the requested organization.

    - Super admins may access any organization.
    - Other users may only access their own organization_id.

    Args:
        current_user: Decoded user dict from get_current_user.
        organization_id: Optional organization id to check. If None, the user's
            own organization is returned and no cross-org check is performed.
        db: Optional database session for super admin org fallback.

    Returns:
        The organization id the user is authorized to access.

    Raises:
        AuthorizationError: If the user is forbidden from the target org.
    """
    if is_super_admin(current_user):
        if organization_id is not None:
            return organization_id
        user_org_id = current_user.get("organization_id")
        if user_org_id is not None:
            return int(user_org_id)
        if db is not None:
            from organizations.models import Organization
            org = db.query(Organization).filter(Organization.slug == "system").first()
            if org:
                return org.id
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Super admin without organization must specify an organization.",
        )

    user_org_id = get_current_organization_id(current_user, db)

    if organization_id is None:
        return user_org_id

    if organization_id != user_org_id:
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
    org_id = current_user.get("organization_id")
    if org_id is None and is_super_admin(current_user):
        from organizations.models import Organization
        org = db.query(Organization).filter(Organization.slug == "system").first()
        if org:
            org_id = org.id
    if org_id is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is not assigned to an organization.",
        )
    return {
        "user": current_user,
        "user_id": current_user["id"],
        "organization_id": int(org_id),
        "is_super_admin": is_super_admin(current_user),
        "db": db,
    }


def tenant_scoped_dependency() -> Callable:
    """Factory for a FastAPI dependency that injects the tenant organization id.

    Returns a dependency that resolves to the current user's organization id.
    """

    async def _resolve(
        current_user: dict = Depends(get_current_user),
        db: DbSession = Depends(get_db),
    ) -> int:
        return get_current_organization_id(current_user, db)

    return _resolve


# ─── Automatic Tenant Query Filtering ────────────────────────────────


class TenantQueryManager:
    """Automatic tenant isolation for SQLAlchemy queries.

    Provides scoped query helpers that automatically filter by organization_id.
    All customer-owned resource queries should go through this manager to
    guarantee no cross-organization data leakage.

    Usage:
        mgr = TenantQueryManager(db, org_id)
        dashboards = mgr.list(Dashboard)
        dataset = mgr.get(Dashboard, dataset_id)
    """

    def __init__(self, db: DbSession, organization_id: int, *, allow_cross_org: bool = False):
        self.db = db
        self.organization_id = organization_id
        self.allow_cross_org = allow_cross_org

    def _apply_filter(self, model_cls: Any, query: Any) -> Any:
        """Apply organization_id filter if the model has the column."""
        if self.allow_cross_org:
            return query
        if hasattr(model_cls, "organization_id"):
            return query.where(model_cls.organization_id == self.organization_id)
        return query

    def list(self, model_cls: Any, **filters: Any) -> list[Any]:
        """List all records for the current organization with optional filters."""
        query = self.db.query(model_cls)
        query = self._apply_filter(model_cls, query)
        for key, value in filters.items():
            col = getattr(model_cls, key, None)
            if col is not None:
                query = query.where(col == value)
        return query.all()

    def get(self, model_cls: Any, resource_id: int) -> Any | None:
        """Get a single record by ID, scoped to the current organization.

        Returns None if the record doesn't exist OR belongs to a different org.
        This prevents both ID manipulation and cross-org access.
        """
        query = self.db.query(model_cls).where(model_cls.id == resource_id)
        query = self._apply_filter(model_cls, query)
        return query.first()

    def get_or_404(self, model_cls: Any, resource_id: int) -> Any:
        """Get a single record by ID or raise NotFoundError."""
        record = self.get(model_cls, resource_id)
        if record is None:
            raise NotFoundError(
                f"{model_cls.__name__} with id {resource_id} not found in your organization."
            )
        return record

    def create(self, model_cls: Any, **data: Any) -> Any:
        """Create a new record with organization_id automatically set."""
        if hasattr(model_cls, "organization_id") and "organization_id" not in data:
            data["organization_id"] = self.organization_id
        record = model_cls(**data)
        self.db.add(record)
        self.db.flush()
        return record

    def update(self, model_cls: Any, resource_id: int, **data: Any) -> Any:
        """Update a record scoped to the current organization."""
        record = self.get_or_404(model_cls, resource_id)
        for key, value in data.items():
            if hasattr(record, key):
                setattr(record, key, value)
        self.db.flush()
        return record

    def delete(self, model_cls: Any, resource_id: int) -> None:
        """Delete a record scoped to the current organization."""
        record = self.get_or_404(model_cls, resource_id)
        self.db.delete(record)
        self.db.flush()

    def count(self, model_cls: Any, **filters: Any) -> int:
        """Count records for the current organization."""
        query = self.db.query(model_cls)
        query = self._apply_filter(model_cls, query)
        for key, value in filters.items():
            col = getattr(model_cls, key, None)
            if col is not None:
                query = query.where(col == value)
        return query.count()


def verify_resource_ownership(
    db: DbSession,
    model_cls: Any,
    resource_id: int,
    organization_id: int,
) -> Any:
    """Verify that a resource belongs to the current organization.

    This is the core cross-org access prevention guard. It fetches the resource
    by ID and checks that its organization_id matches the caller's org.

    Raises:
        NotFoundError: If the resource doesn't exist or belongs to another org.
    """
    record = db.query(model_cls).filter(model_cls.id == resource_id).first()
    if record is None:
        raise NotFoundError(f"{model_cls.__name__} with id {resource_id} not found.")

    if hasattr(record, "organization_id") and record.organization_id is not None:
        if int(record.organization_id) != int(organization_id):
            raise NotFoundError(
                f"{model_cls.__name__} with id {resource_id} not found in your organization."
            )
    return record


def assert_same_organization(
    current_user: dict,
    resource_organization_id: int,
    resource_type: str = "Resource",
) -> None:
    """Assert that a resource belongs to the same organization as the user.

    Raises:
        AuthorizationError: If the resource belongs to a different organization.
    """
    if is_super_admin(current_user):
        return
    user_org_id = current_user.get("organization_id")
    if user_org_id is None or int(user_org_id) != int(resource_organization_id):
        raise AuthorizationError(
            f"{resource_type} does not belong to your organization."
        )
