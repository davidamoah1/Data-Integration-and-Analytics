"""Data access layer for authentication domain.

Repository pattern abstracting all database operations for
users, roles, permissions, sessions, and related entities.
"""

from datetime import datetime, timedelta, timezone

from sqlalchemy import delete, func, select, update
from sqlalchemy.orm import Session as DbSession

from authentication.models import (
    ActivityLog,
    LoginHistory,
    PasswordHistory,
    PasswordReset,
    Permission,
    Resource,
    Role,
    RolePermission,
    Session,
    User,
    UserRole,
)
from shared.security import (
    ACCOUNT_LOCKOUT_DURATION_MINUTES,
    ACCOUNT_LOCKOUT_THRESHOLD,
)


class UserRepository:
    """Repository for user CRUD operations."""

    def __init__(self, db: DbSession):
        self.db = db

    def get_by_id(self, user_id: int) -> User | None:
        return self.db.execute(
            select(User).where(User.id == user_id, User.is_deleted == 0)
        ).scalar_one_or_none()

    def get_by_email(self, email: str) -> User | None:
        return self.db.execute(
            select(User).where(User.email == email, User.is_deleted == 0)
        ).scalar_one_or_none()

    def create(self, user: User) -> User:
        self.db.add(user)
        self.db.flush()
        return user

    def update(self, user_id: int, **kwargs) -> User | None:
        kwargs["updated_at"] = datetime.now(timezone.utc)
        self.db.execute(update(User).where(User.id == user_id).values(**kwargs))
        self.db.flush()
        return self.get_by_id(user_id)

    def soft_delete(self, user_id: int):
        self.db.execute(
            update(User)
            .where(User.id == user_id)
            .values(is_deleted=1, deleted_at=datetime.now(timezone.utc), is_active=0)
        )
        self.db.flush()

    def list_users(self, page: int = 1, page_size: int = 20) -> tuple[list[User], int]:
        offset = (page - 1) * page_size
        total = self.db.execute(
            select(func.count()).select_from(User).where(User.is_deleted == 0)
        ).scalar()
        users = (
            self.db.execute(
                select(User).where(User.is_deleted == 0).offset(offset).limit(page_size)
            )
            .scalars()
            .all()
        )
        return list(users), total

    def list_users_by_org(
        self, org_id: int, page: int = 1, page_size: int = 20
    ) -> tuple[list[User], int]:
        offset = (page - 1) * page_size
        total = self.db.execute(
            select(func.count())
            .select_from(User)
            .where(User.is_deleted == 0, User.organization_id == org_id)
        ).scalar()
        users = (
            self.db.execute(
                select(User)
                .where(User.is_deleted == 0, User.organization_id == org_id)
                .offset(offset)
                .limit(page_size)
            )
            .scalars()
            .all()
        )
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
            update(User)
            .where(User.id == user_id)
            .values(
                failed_login_count=count,
                locked_until=lock_until,
            )
        )
        self.db.flush()
        return count

    def reset_failed_logins(self, user_id: int):
        self.db.execute(
            update(User).where(User.id == user_id).values(failed_login_count=0, locked_until=None)
        )
        self.db.flush()

    def reset_failed_logins_and_update_last_login(self, user_id: int):
        """Combine reset_failed_logins and update_last_login into a single UPDATE."""
        self.db.execute(
            update(User)
            .where(User.id == user_id)
            .values(
                failed_login_count=0,
                locked_until=None,
                last_login_at=datetime.now(timezone.utc),
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
            update(User).where(User.id == user_id).values(last_login_at=datetime.now(timezone.utc))
        )
        self.db.flush()

    def verify_email(self, user_id: int):
        self.db.execute(
            update(User)
            .where(User.id == user_id)
            .values(email_verified_at=datetime.now(timezone.utc))
        )
        self.db.flush()


class RoleRepository:
    """Repository for role operations."""

    def __init__(self, db: DbSession):
        self.db = db

    def get_by_id(self, role_id: int) -> Role | None:
        return self.db.execute(
            select(Role).where(Role.id == role_id, Role.is_deleted == 0)
        ).scalar_one_or_none()

    def get_by_name(self, name: str) -> Role | None:
        return self.db.execute(
            select(Role).where(Role.name == name, Role.is_deleted == 0)
        ).scalar_one_or_none()

    def list_roles(self) -> list[Role]:
        return list(
            self.db.execute(select(Role).where(Role.is_deleted == 0).order_by(Role.id))
            .scalars()
            .all()
        )

    def list_roles_by_level(self, level: str) -> list[Role]:
        return list(
            self.db.execute(
                select(Role).where(Role.is_deleted == 0, Role.level == level).order_by(Role.id)
            )
            .scalars()
            .all()
        )

    def list_assignable_roles(self) -> list[Role]:
        return list(
            self.db.execute(
                select(Role).where(Role.is_deleted == 0, Role.is_assignable == 1).order_by(Role.id)
            )
            .scalars()
            .all()
        )

    def create(self, role: Role) -> Role:
        self.db.add(role)
        self.db.flush()
        return role

    def update(self, role_id: int, **kwargs) -> Role | None:
        self.db.execute(update(Role).where(Role.id == role_id).values(**kwargs))
        self.db.flush()
        return self.get_by_id(role_id)

    def soft_delete(self, role_id: int):
        self.db.execute(
            update(Role)
            .where(Role.id == role_id)
            .values(is_deleted=1, deleted_at=datetime.now(timezone.utc))
        )
        self.db.flush()


class PermissionRepository:
    """Repository for permission operations."""

    def __init__(self, db: DbSession):
        self.db = db

    def get_by_name(self, name: str) -> Permission | None:
        return self.db.execute(
            select(Permission).where(Permission.name == name)
        ).scalar_one_or_none()

    def list_permissions(self) -> list[Permission]:
        return list(
            self.db.execute(select(Permission).order_by(Permission.module, Permission.name))
            .scalars()
            .all()
        )

    def list_by_module(self, module: str) -> list[Permission]:
        return list(
            self.db.execute(select(Permission).where(Permission.module == module)).scalars().all()
        )

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
        results = (
            self.db.execute(
                select(Permission.name)
                .join(RolePermission, RolePermission.permission_id == Permission.id)
                .where(RolePermission.role_id == role_id)
            )
            .scalars()
            .all()
        )
        return list(results)

    def set_role_permissions(self, role_id: int, permission_ids: list[int]):
        self.db.execute(delete(RolePermission).where(RolePermission.role_id == role_id))
        for pid in permission_ids:
            self.db.add(RolePermission(role_id=role_id, permission_id=pid))
        self.db.flush()

    def get_permission_ids_by_names(self, names: list[str]) -> list[int]:
        results = (
            self.db.execute(select(Permission.id).where(Permission.name.in_(names))).scalars().all()
        )
        return list(results)


class UserRoleRepository:
    """Repository for user-role mappings."""

    def __init__(self, db: DbSession):
        self.db = db

    def get_roles_for_user(self, user_id: int) -> list[str]:
        results = (
            self.db.execute(
                select(Role.name)
                .join(UserRole, UserRole.role_id == Role.id)
                .where(UserRole.user_id == user_id, Role.is_deleted == 0)
            )
            .scalars()
            .all()
        )
        return list(results)

    def get_role_ids_for_user(self, user_id: int) -> list[int]:
        results = (
            self.db.execute(select(UserRole.role_id).where(UserRole.user_id == user_id))
            .scalars()
            .all()
        )
        return list(results)

    def assign_role(
        self,
        user_id: int,
        role_id: int,
        assigned_by: int = None,
        scope_type: str = None,
        scope_id: int = None,
    ):
        existing = self.db.execute(
            select(UserRole).where(
                UserRole.user_id == user_id,
                UserRole.role_id == role_id,
                UserRole.scope_type == scope_type if scope_type else UserRole.scope_type.is_(None),
                UserRole.scope_id == scope_id if scope_id else UserRole.scope_id.is_(None),
            )
        ).scalar_one_or_none()
        if not existing:
            self.db.add(
                UserRole(
                    user_id=user_id,
                    role_id=role_id,
                    assigned_by=assigned_by,
                    scope_type=scope_type,
                    scope_id=scope_id,
                )
            )
            self.db.flush()

    def remove_role(self, user_id: int, role_id: int):
        self.db.execute(
            delete(UserRole).where(UserRole.user_id == user_id, UserRole.role_id == role_id)
        )
        self.db.flush()

    def set_user_roles(
        self,
        user_id: int,
        role_ids: list[int],
        assigned_by: int = None,
        scope_type: str = None,
        scope_id: int = None,
    ):
        # Only remove roles matching the same scope
        if scope_type:
            self.db.execute(
                delete(UserRole).where(
                    UserRole.user_id == user_id,
                    UserRole.scope_type == scope_type,
                    UserRole.scope_id == scope_id if scope_id else UserRole.scope_id.is_(None),
                )
            )
        else:
            self.db.execute(
                delete(UserRole).where(
                    UserRole.user_id == user_id,
                    UserRole.scope_type.is_(None),
                )
            )
        for rid in role_ids:
            self.db.add(
                UserRole(
                    user_id=user_id,
                    role_id=rid,
                    assigned_by=assigned_by,
                    scope_type=scope_type,
                    scope_id=scope_id,
                )
            )
        self.db.flush()

    def get_all_permissions_for_user(self, user_id: int) -> list[str]:
        """Get all permission names for a user via their roles (global + scoped)."""
        results = (
            self.db.execute(
                select(Permission.name)
                .join(RolePermission, RolePermission.permission_id == Permission.id)
                .join(UserRole, UserRole.role_id == RolePermission.role_id)
                .where(UserRole.user_id == user_id)
            )
            .scalars()
            .all()
        )
        return list(set(results))

    def get_roles_and_permissions_for_user(self, user_id: int) -> tuple[list[str], list[str]]:
        """Get role names and permission names in a single DB round trip.

        Uses UNION ALL to fetch both role names and permission names in one
        query, reducing network latency for remote MySQL connections.
        Returns (role_names, permission_names).
        """
        from sqlalchemy import literal_column, union_all

        roles_q = (
            select(literal_column("'role'").label("type"), Role.name.label("name"))
            .join(UserRole, UserRole.role_id == Role.id)
            .where(UserRole.user_id == user_id, Role.is_deleted == 0)
        )
        perms_q = (
            select(literal_column("'permission'").label("type"), Permission.name.label("name"))
            .join(RolePermission, RolePermission.permission_id == Permission.id)
            .join(UserRole, UserRole.role_id == RolePermission.role_id)
            .where(UserRole.user_id == user_id)
        )
        combined = union_all(roles_q, perms_q)
        results = self.db.execute(combined).all()

        role_names = list({r[1] for r in results if r[0] == "role"})
        permission_names = list({r[1] for r in results if r[0] == "permission"})
        return role_names, permission_names

    def get_scoped_roles_for_user(self, user_id: int) -> list[dict]:
        """Get all role assignments for a user including scope information."""
        results = self.db.execute(
            select(
                Role.name,
                Role.display_name,
                Role.level,
                UserRole.scope_type,
                UserRole.scope_id,
            )
            .join(UserRole, UserRole.role_id == Role.id)
            .where(UserRole.user_id == user_id, Role.is_deleted == 0)
        ).all()
        return [
            {
                "role_name": r[0],
                "display_name": r[1],
                "level": r[2],
                "scope_type": r[3],
                "scope_id": r[4],
            }
            for r in results
        ]

    def get_permissions_for_scope(
        self, user_id: int, scope_type: str, scope_id: int = None
    ) -> list[str]:
        """Get permissions for a user within a specific scope (e.g., department)."""
        if scope_id:
            results = (
                self.db.execute(
                    select(Permission.name)
                    .join(RolePermission, RolePermission.permission_id == Permission.id)
                    .join(UserRole, UserRole.role_id == RolePermission.role_id)
                    .where(
                        UserRole.user_id == user_id,
                        UserRole.scope_type == scope_type,
                        UserRole.scope_id == scope_id,
                    )
                )
                .scalars()
                .all()
            )
        else:
            results = (
                self.db.execute(
                    select(Permission.name)
                    .join(RolePermission, RolePermission.permission_id == Permission.id)
                    .join(UserRole, UserRole.role_id == RolePermission.role_id)
                    .where(
                        UserRole.user_id == user_id,
                        UserRole.scope_type == scope_type,
                    )
                )
                .scalars()
                .all()
            )
        return list(set(results))

    def has_permission(self, user_id: int, permission_name: str) -> bool:
        """Check if a user has a specific permission via any of their roles."""
        result = self.db.execute(
            select(func.count())
            .select_from(Permission)
            .join(RolePermission, RolePermission.permission_id == Permission.id)
            .join(UserRole, UserRole.role_id == RolePermission.role_id)
            .where(UserRole.user_id == user_id, Permission.name == permission_name)
        ).scalar()
        return result > 0


class SessionRepository:
    """Repository for session management."""

    def __init__(self, db: DbSession):
        self.db = db

    def create(self, session: Session) -> Session:
        self.db.add(session)
        self.db.flush()
        return session

    def get_by_token(self, token: str) -> Session | None:
        return self.db.execute(
            select(Session).where(Session.refresh_token == token)
        ).scalar_one_or_none()

    def get_active_for_user(self, user_id: int) -> list[Session]:
        return list(
            self.db.execute(
                select(Session)
                .where(
                    Session.user_id == user_id,
                    Session.is_active == 1,
                    Session.revoked_at.is_(None),
                )
                .order_by(Session.created_at.desc())
            )
            .scalars()
            .all()
        )

    def revoke(self, session_id: int):
        self.db.execute(
            update(Session)
            .where(Session.id == session_id)
            .values(is_active=0, revoked_at=datetime.now(timezone.utc))
        )
        self.db.flush()

    def revoke_all_for_user(self, user_id: int):
        self.db.execute(
            update(Session)
            .where(
                Session.user_id == user_id,
                Session.is_active == 1,
            )
            .values(is_active=0, revoked_at=datetime.now(timezone.utc))
        )
        self.db.flush()

    def update_activity(self, session_id: int):
        self.db.execute(
            update(Session)
            .where(Session.id == session_id)
            .values(last_activity_at=datetime.now(timezone.utc))
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

    def get_by_token(self, token: str) -> PasswordReset | None:
        return self.db.execute(
            select(PasswordReset).where(PasswordReset.token == token)
        ).scalar_one_or_none()

    def mark_used(self, reset_id: int):
        self.db.execute(
            update(PasswordReset)
            .where(PasswordReset.id == reset_id)
            .values(used_at=datetime.now(timezone.utc))
        )
        self.db.flush()

    def invalidate_all_for_user(self, user_id: int):
        self.db.execute(
            update(PasswordReset)
            .where(
                PasswordReset.user_id == user_id,
                PasswordReset.used_at.is_(None),
            )
            .values(used_at=datetime.now(timezone.utc))
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
        return list(
            self.db.execute(
                select(LoginHistory)
                .where(LoginHistory.user_id == user_id)
                .order_by(LoginHistory.created_at.desc())
                .limit(limit)
            )
            .scalars()
            .all()
        )

    def list_all(self, limit: int = 50) -> list[LoginHistory]:
        return list(
            self.db.execute(
                select(LoginHistory).order_by(LoginHistory.created_at.desc()).limit(limit)
            )
            .scalars()
            .all()
        )


class ActivityLogRepository:
    """Repository for user activity logs."""

    def __init__(self, db: DbSession):
        self.db = db

    def create(self, log: ActivityLog) -> ActivityLog:
        self.db.add(log)
        self.db.flush()
        return log

    def list_for_user(self, user_id: int, limit: int = 50) -> list[ActivityLog]:
        return list(
            self.db.execute(
                select(ActivityLog)
                .where(ActivityLog.user_id == user_id)
                .order_by(ActivityLog.created_at.desc())
                .limit(limit)
            )
            .scalars()
            .all()
        )


class PasswordHistoryRepository:
    """Repository for password history (prevents reuse)."""

    def __init__(self, db: DbSession):
        self.db = db

    def add(self, user_id: int, password_hash: str):
        self.db.add(PasswordHistory(user_id=user_id, password_hash=password_hash))
        self.db.flush()

    def list_for_user(self, user_id: int, limit: int = 5) -> list[str]:
        return list(
            self.db.execute(
                select(PasswordHistory.password_hash)
                .where(PasswordHistory.user_id == user_id)
                .order_by(PasswordHistory.created_at.desc())
                .limit(limit)
            )
            .scalars()
            .all()
        )


class ResourceRepository:
    """Repository for resource-level access control."""

    def __init__(self, db: DbSession):
        self.db = db

    def get(self, resource_type: str, resource_id: int) -> Resource | None:
        return self.db.execute(
            select(Resource).where(
                Resource.resource_type == resource_type,
                Resource.resource_id == resource_id,
            )
        ).scalar_one_or_none()

    def create(self, resource: Resource) -> Resource:
        self.db.add(resource)
        self.db.flush()
        return resource

    def update(self, resource_id: int, **kwargs) -> Resource | None:
        self.db.execute(update(Resource).where(Resource.id == resource_id).values(**kwargs))
        self.db.flush()
        return self.db.execute(
            select(Resource).where(Resource.id == resource_id)
        ).scalar_one_or_none()

    def upsert(self, resource_type: str, resource_id: int, **kwargs) -> Resource:
        existing = self.get(resource_type, resource_id)
        if existing:
            for k, v in kwargs.items():
                setattr(existing, k, v)
            self.db.flush()
            return existing
        resource = Resource(resource_type=resource_type, resource_id=resource_id, **kwargs)
        return self.create(resource)

    def can_access(
        self,
        user_id: int,
        resource_type: str,
        resource_id: int,
        user_org_id: int = None,
        user_dept_id: int = None,
    ) -> bool:
        """Check if a user can access a specific resource."""
        resource = self.get(resource_type, resource_id)
        if not resource:
            return True  # No resource record = no restriction

        if resource.is_public:
            return True

        if resource.owner_id == user_id:
            return True

        if resource.access_level == "organization" and resource.organization_id == user_org_id:
            return True

        return bool(
            resource.access_level == "department" and resource.department_id == user_dept_id
        )
