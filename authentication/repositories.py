"""Data access layer for authentication domain.

Repository pattern abstracting all database operations for
users, roles, permissions, sessions, and related entities.
"""

from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy import select, update, delete, func
from sqlalchemy.orm import Session as DbSession

from authentication.models import (
    User, Role, Permission, RolePermission, UserRole,
    Session, PasswordReset, LoginHistory, ActivityLog, PasswordHistory,
)
from shared.security import (
    ACCOUNT_LOCKOUT_THRESHOLD,
    ACCOUNT_LOCKOUT_DURATION_MINUTES,
)


class UserRepository:
    """Repository for user CRUD operations."""

    def __init__(self, db: DbSession):
        self.db = db

    def get_by_id(self, user_id: int) -> Optional[User]:
        return self.db.execute(
            select(User).where(User.id == user_id, User.is_deleted == 0)
        ).scalar_one_or_none()

    def get_by_email(self, email: str) -> Optional[User]:
        return self.db.execute(
            select(User).where(User.email == email, User.is_deleted == 0)
        ).scalar_one_or_none()

    def create(self, user: User) -> User:
        self.db.add(user)
        self.db.flush()
        return user

    def update(self, user_id: int, **kwargs) -> Optional[User]:
        kwargs["updated_at"] = datetime.now(timezone.utc)
        self.db.execute(
            update(User).where(User.id == user_id).values(**kwargs)
        )
        self.db.flush()
        return self.get_by_id(user_id)

    def soft_delete(self, user_id: int):
        self.db.execute(
            update(User).where(User.id == user_id).values(
                is_deleted=1, deleted_at=datetime.now(timezone.utc), is_active=0
            )
        )
        self.db.flush()

    def list_users(self, page: int = 1, page_size: int = 20) -> tuple[list[User], int]:
        offset = (page - 1) * page_size
        total = self.db.execute(
            select(func.count()).select_from(User).where(User.is_deleted == 0)
        ).scalar()
        users = self.db.execute(
            select(User).where(User.is_deleted == 0)
            .offset(offset).limit(page_size)
        ).scalars().all()
        return list(users), total

    def increment_failed_login(self, user_id: int) -> int:
        user = self.get_by_id(user_id)
        if not user:
            return 0
        count = user.failed_login_count + 1
        lock_until = None
        if count >= ACCOUNT_LOCKOUT_THRESHOLD:
            lock_until = datetime.now(timezone.utc) + timedelta(
                minutes=ACCOUNT_LOCKOUT_DURATION_MINUTES
            )
        self.db.execute(
            update(User).where(User.id == user_id).values(
                failed_login_count=count,
                locked_until=lock_until,
            )
        )
        self.db.flush()
        return count

    def reset_failed_logins(self, user_id: int):
        self.db.execute(
            update(User).where(User.id == user_id).values(
                failed_login_count=0, locked_until=None
            )
        )
        self.db.flush()

    def is_locked(self, user_id: int) -> bool:
        user = self.get_by_id(user_id)
        if not user or not user.locked_until:
            return False
        return user.locked_until > datetime.now(timezone.utc)

    def update_last_login(self, user_id: int):
        self.db.execute(
            update(User).where(User.id == user_id).values(
                last_login_at=datetime.now(timezone.utc)
            )
        )
        self.db.flush()

    def verify_email(self, user_id: int):
        self.db.execute(
            update(User).where(User.id == user_id).values(
                email_verified_at=datetime.now(timezone.utc)
            )
        )
        self.db.flush()


class RoleRepository:
    """Repository for role operations."""

    def __init__(self, db: DbSession):
        self.db = db

    def get_by_id(self, role_id: int) -> Optional[Role]:
        return self.db.execute(
            select(Role).where(Role.id == role_id, Role.is_deleted == 0)
        ).scalar_one_or_none()

    def get_by_name(self, name: str) -> Optional[Role]:
        return self.db.execute(
            select(Role).where(Role.name == name, Role.is_deleted == 0)
        ).scalar_one_or_none()

    def list_roles(self) -> list[Role]:
        return list(self.db.execute(
            select(Role).where(Role.is_deleted == 0).order_by(Role.id)
        ).scalars().all())

    def create(self, role: Role) -> Role:
        self.db.add(role)
        self.db.flush()
        return role

    def update(self, role_id: int, **kwargs) -> Optional[Role]:
        self.db.execute(
            update(Role).where(Role.id == role_id).values(**kwargs)
        )
        self.db.flush()
        return self.get_by_id(role_id)

    def soft_delete(self, role_id: int):
        self.db.execute(
            update(Role).where(Role.id == role_id).values(
                is_deleted=1, deleted_at=datetime.now(timezone.utc)
            )
        )
        self.db.flush()


class PermissionRepository:
    """Repository for permission operations."""

    def __init__(self, db: DbSession):
        self.db = db

    def get_by_name(self, name: str) -> Optional[Permission]:
        return self.db.execute(
            select(Permission).where(Permission.name == name)
        ).scalar_one_or_none()

    def list_permissions(self) -> list[Permission]:
        return list(self.db.execute(
            select(Permission).order_by(Permission.module, Permission.name)
        ).scalars().all())

    def list_by_module(self, module: str) -> list[Permission]:
        return list(self.db.execute(
            select(Permission).where(Permission.module == module)
        ).scalars().all())

    def create(self, permission: Permission) -> Permission:
        self.db.add(permission)
        self.db.flush()
        return permission

    def create_many(self, permissions: list[Permission]):
        for p in permissions:
            self.db.add(p)
        self.db.flush()


class RolePermissionRepository:
    """Repository for role-permission mappings."""

    def __init__(self, db: DbSession):
        self.db = db

    def get_permissions_for_role(self, role_id: int) -> list[str]:
        results = self.db.execute(
            select(Permission.name)
            .join(RolePermission, RolePermission.permission_id == Permission.id)
            .where(RolePermission.role_id == role_id)
        ).scalars().all()
        return list(results)

    def set_role_permissions(self, role_id: int, permission_ids: list[int]):
        self.db.execute(
            delete(RolePermission).where(RolePermission.role_id == role_id)
        )
        for pid in permission_ids:
            self.db.add(RolePermission(role_id=role_id, permission_id=pid))
        self.db.flush()

    def get_permission_ids_by_names(self, names: list[str]) -> list[int]:
        results = self.db.execute(
            select(Permission.id).where(Permission.name.in_(names))
        ).scalars().all()
        return list(results)


class UserRoleRepository:
    """Repository for user-role mappings."""

    def __init__(self, db: DbSession):
        self.db = db

    def get_roles_for_user(self, user_id: int) -> list[str]:
        results = self.db.execute(
            select(Role.name)
            .join(UserRole, UserRole.role_id == Role.id)
            .where(UserRole.user_id == user_id, Role.is_deleted == 0)
        ).scalars().all()
        return list(results)

    def get_role_ids_for_user(self, user_id: int) -> list[int]:
        results = self.db.execute(
            select(UserRole.role_id).where(UserRole.user_id == user_id)
        ).scalars().all()
        return list(results)

    def assign_role(self, user_id: int, role_id: int, assigned_by: int = None):
        existing = self.db.execute(
            select(UserRole).where(
                UserRole.user_id == user_id, UserRole.role_id == role_id
            )
        ).scalar_one_or_none()
        if not existing:
            self.db.add(UserRole(user_id=user_id, role_id=role_id, assigned_by=assigned_by))
            self.db.flush()

    def remove_role(self, user_id: int, role_id: int):
        self.db.execute(
            delete(UserRole).where(
                UserRole.user_id == user_id, UserRole.role_id == role_id
            )
        )
        self.db.flush()

    def set_user_roles(self, user_id: int, role_ids: list[int], assigned_by: int = None):
        self.db.execute(
            delete(UserRole).where(UserRole.user_id == user_id)
        )
        for rid in role_ids:
            self.db.add(UserRole(user_id=user_id, role_id=rid, assigned_by=assigned_by))
        self.db.flush()

    def get_all_permissions_for_user(self, user_id: int) -> list[str]:
        """Get all permission names for a user via their roles."""
        results = self.db.execute(
            select(Permission.name)
            .join(RolePermission, RolePermission.permission_id == Permission.id)
            .join(UserRole, UserRole.role_id == RolePermission.role_id)
            .where(UserRole.user_id == user_id)
        ).scalars().all()
        return list(results)


class SessionRepository:
    """Repository for session management."""

    def __init__(self, db: DbSession):
        self.db = db

    def create(self, session: Session) -> Session:
        self.db.add(session)
        self.db.flush()
        return session

    def get_by_token(self, token: str) -> Optional[Session]:
        return self.db.execute(
            select(Session).where(Session.refresh_token == token)
        ).scalar_one_or_none()

    def get_active_for_user(self, user_id: int) -> list[Session]:
        return list(self.db.execute(
            select(Session).where(
                Session.user_id == user_id,
                Session.is_active == 1,
                Session.revoked_at.is_(None),
            ).order_by(Session.created_at.desc())
        ).scalars().all())

    def revoke(self, session_id: int):
        self.db.execute(
            update(Session).where(Session.id == session_id).values(
                is_active=0, revoked_at=datetime.now(timezone.utc)
            )
        )
        self.db.flush()

    def revoke_all_for_user(self, user_id: int):
        self.db.execute(
            update(Session).where(
                Session.user_id == user_id,
                Session.is_active == 1,
            ).values(is_active=0, revoked_at=datetime.now(timezone.utc))
        )
        self.db.flush()

    def update_activity(self, session_id: int):
        self.db.execute(
            update(Session).where(Session.id == session_id).values(
                last_activity_at=datetime.now(timezone.utc)
            )
        )
        self.db.flush()


class PasswordResetRepository:
    """Repository for password reset tokens."""

    def __init__(self, db: DbSession):
        self.db = db

    def create(self, reset: PasswordReset) -> PasswordReset:
        self.db.add(reset)
        self.db.flush()
        return reset

    def get_by_token(self, token: str) -> Optional[PasswordReset]:
        return self.db.execute(
            select(PasswordReset).where(PasswordReset.token == token)
        ).scalar_one_or_none()

    def mark_used(self, reset_id: int):
        self.db.execute(
            update(PasswordReset).where(PasswordReset.id == reset_id).values(
                used_at=datetime.now(timezone.utc)
            )
        )
        self.db.flush()

    def invalidate_all_for_user(self, user_id: int):
        self.db.execute(
            update(PasswordReset).where(
                PasswordReset.user_id == user_id,
                PasswordReset.used_at.is_(None),
            ).values(used_at=datetime.now(timezone.utc))
        )
        self.db.flush()


class LoginHistoryRepository:
    """Repository for login history records."""

    def __init__(self, db: DbSession):
        self.db = db

    def create(self, record: LoginHistory) -> LoginHistory:
        self.db.add(record)
        self.db.flush()
        return record

    def list_for_user(self, user_id: int, limit: int = 20) -> list[LoginHistory]:
        return list(self.db.execute(
            select(LoginHistory)
            .where(LoginHistory.user_id == user_id)
            .order_by(LoginHistory.created_at.desc())
            .limit(limit)
        ).scalars().all())

    def list_all(self, limit: int = 50) -> list[LoginHistory]:
        return list(self.db.execute(
            select(LoginHistory)
            .order_by(LoginHistory.created_at.desc())
            .limit(limit)
        ).scalars().all())


class ActivityLogRepository:
    """Repository for user activity logs."""

    def __init__(self, db: DbSession):
        self.db = db

    def create(self, log: ActivityLog) -> ActivityLog:
        self.db.add(log)
        self.db.flush()
        return log

    def list_for_user(self, user_id: int, limit: int = 50) -> list[ActivityLog]:
        return list(self.db.execute(
            select(ActivityLog)
            .where(ActivityLog.user_id == user_id)
            .order_by(ActivityLog.created_at.desc())
            .limit(limit)
        ).scalars().all())


class PasswordHistoryRepository:
    """Repository for password history (prevents reuse)."""

    def __init__(self, db: DbSession):
        self.db = db

    def add(self, user_id: int, password_hash: str):
        self.db.add(PasswordHistory(user_id=user_id, password_hash=password_hash))
        self.db.flush()

    def list_for_user(self, user_id: int, limit: int = 5) -> list[str]:
        return list(self.db.execute(
            select(PasswordHistory.password_hash)
            .where(PasswordHistory.user_id == user_id)
            .order_by(PasswordHistory.created_at.desc())
            .limit(limit)
        ).scalars().all())
