"""Admin management service.

Provides organization and user administration operations used by the
enterprise admin panel. All operations are scoped by the caller's role:
super admins may act across tenants, while organization admins are limited
to their own organization.
"""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session as DbSession

from authentication.models import User
from authentication.repositories import UserRepository, UserRoleRepository
from organizations.models import Organization
from shared.exceptions import AuthorizationError, NotFoundError
from shared.tenant import is_super_admin


class AdminService:
    """Service for administrative operations."""

    def __init__(self, db: DbSession, current_user: dict):
        self.db = db
        self.current_user = current_user
        self.user_repo = UserRepository(db)
        self.user_role_repo = UserRoleRepository(db)

    # --- Organization administration ---------------------------------------

    def list_organizations(self) -> list[dict]:
        """List organizations accessible to the admin."""
        query = select(Organization).where(Organization.is_deleted == 0)
        if not is_super_admin(self.current_user):
            user_org_id = self.current_user.get("organization_id")
            query = query.where(Organization.id == user_org_id)
        orgs = self.db.execute(query.order_by(Organization.name)).scalars().all()
        return [self._org_to_dict(o) for o in orgs]

    def suspend_organization(self, org_id: int) -> dict:
        """Suspend an organization (super admin only)."""
        if not is_super_admin(self.current_user):
            raise AuthorizationError("Only super admins can suspend organizations.")
        org = self._get_organization(org_id)
        org.is_active = 0
        org.updated_at = datetime.now(timezone.utc)
        self.db.commit()
        return self._org_to_dict(org)

    def activate_organization(self, org_id: int) -> dict:
        """Activate a suspended organization (super admin only)."""
        if not is_super_admin(self.current_user):
            raise AuthorizationError("Only super admins can activate organizations.")
        org = self._get_organization(org_id)
        org.is_active = 1
        org.updated_at = datetime.now(timezone.utc)
        self.db.commit()
        return self._org_to_dict(org)

    def get_organization_usage(self, org_id: int) -> dict:
        """Return usage metrics for an organization."""
        self._ensure_org_access(org_id)
        user_count = self.db.execute(
            select(func.count(User.id)).where(
                User.organization_id == org_id,
                User.is_deleted == 0,
            )
        ).scalar()
        active_user_count = self.db.execute(
            select(func.count(User.id)).where(
                User.organization_id == org_id,
                User.is_active == 1,
                User.is_deleted == 0,
            )
        ).scalar()
        return {
            "organization_id": org_id,
            "total_users": user_count or 0,
            "active_users": active_user_count or 0,
        }

    # --- User administration -------------------------------------------------

    def list_users(self, org_id: int | None = None) -> list[dict]:
        """List users scoped to the admin's accessible organizations."""
        if is_super_admin(self.current_user):
            effective_org_id = org_id
        else:
            user_org_id = self.current_user.get("organization_id")
            if org_id is not None and org_id != user_org_id:
                raise AuthorizationError("Cannot view users outside your organization.")
            effective_org_id = user_org_id

        query = select(User).where(User.is_deleted == 0)
        if effective_org_id is not None:
            query = query.where(User.organization_id == effective_org_id)
        users = self.db.execute(query.order_by(User.email)).scalars().all()
        return [self._user_to_dict(u) for u in users]

    def disable_user(self, user_id: int) -> dict:
        """Disable a user account."""
        user = self._get_user(user_id)
        self._ensure_user_org_access(user.organization_id)
        user.is_active = 0
        user.updated_at = datetime.now(timezone.utc)
        self.db.commit()
        return self._user_to_dict(user)

    def enable_user(self, user_id: int) -> dict:
        """Enable a user account."""
        user = self._get_user(user_id)
        self._ensure_user_org_access(user.organization_id)
        user.is_active = 1
        user.updated_at = datetime.now(timezone.utc)
        self.db.commit()
        return self._user_to_dict(user)

    def assign_user_roles(self, user_id: int, role_names: list[str]) -> dict:
        """Assign roles to a user."""
        from authentication.repositories import RoleRepository, UserRoleRepository

        user = self._get_user(user_id)
        self._ensure_user_org_access(user.organization_id)

        role_repo = RoleRepository(self.db)
        user_role_repo = UserRoleRepository(self.db)

        role_ids = []
        for name in role_names:
            role = role_repo.get_by_name(name)
            if not role:
                raise NotFoundError(f"Role '{name}' not found")
            role_ids.append(role.id)

        user_role_repo.set_user_roles(user.id, role_ids, assigned_by=self.current_user.get("id"))
        self.db.commit()
        return self._user_to_dict(user)

    # --- System monitoring ---------------------------------------------------

    def get_system_metrics(self) -> dict:
        """Return high-level system metrics."""
        org_count = self.db.execute(
            select(func.count(Organization.id)).where(Organization.is_deleted == 0)
        ).scalar()
        total_users = self.db.execute(
            select(func.count(User.id)).where(User.is_deleted == 0)
        ).scalar()
        active_users = self.db.execute(
            select(func.count(User.id)).where(User.is_active == 1, User.is_deleted == 0)
        ).scalar()
        return {
            "total_organizations": org_count or 0,
            "total_users": total_users or 0,
            "active_users": active_users or 0,
        }

    # --- Helpers -------------------------------------------------------------

    def _get_organization(self, org_id: int) -> Organization:
        org = self.db.execute(
            select(Organization).where(Organization.id == org_id, Organization.is_deleted == 0)
        ).scalar_one_or_none()
        if not org:
            raise NotFoundError("Organization not found")
        return org

    def _get_user(self, user_id: int) -> User:
        user = self.db.execute(
            select(User).where(User.id == user_id, User.is_deleted == 0)
        ).scalar_one_or_none()
        if not user:
            raise NotFoundError("User not found")
        return user

    def _ensure_org_access(self, org_id: int) -> None:
        if is_super_admin(self.current_user):
            return
        if self.current_user.get("organization_id") != org_id:
            raise AuthorizationError("Access denied for this organization.")

    def _ensure_user_org_access(self, user_org_id: int | None) -> None:
        if is_super_admin(self.current_user):
            return
        if self.current_user.get("organization_id") != user_org_id:
            raise AuthorizationError("Access denied for this user.")

    def _org_to_dict(self, org: Organization) -> dict:
        return {
            "id": org.id,
            "name": org.name,
            "slug": org.slug,
            "is_active": bool(org.is_active),
            "created_at": org.created_at,
            "updated_at": org.updated_at,
        }

    def _user_to_dict(self, user: User) -> dict:
        roles = self.user_role_repo.get_roles_for_user(user.id)
        return {
            "id": user.id,
            "email": user.email,
            "full_name": user.full_name,
            "organization_id": user.organization_id,
            "department_id": user.department_id,
            "is_active": bool(user.is_active),
            "last_login_at": user.last_login_at,
            "created_at": user.created_at,
            "roles": roles,
        }
