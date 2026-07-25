"""Authentication service layer — business logic for auth operations.

Orchestrates repositories, security utilities, and audit logging.
No business logic in route handlers.
"""

from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session as DbSession

from authentication.models import (
    ActivityLog,
    LoginHistory,
    PasswordReset,
    Permission,
    Role,
    User,
)
from authentication.models import (
    Session as UserSession,
)
from authentication.repositories import (
    ActivityLogRepository,
    LoginHistoryRepository,
    PasswordHistoryRepository,
    PasswordResetRepository,
    PermissionRepository,
    RolePermissionRepository,
    RoleRepository,
    SessionRepository,
    UserRepository,
    UserRoleRepository,
)
from authentication.schemas import (
    ChangePasswordRequest,
    LoginRequest,
    ProfileUpdate,
    RoleCreate,
    RoleUpdate,
    UserCreate,
    UserUpdate,
)
from shared.exceptions import (
    AccountLockedError,
    AuthenticationError,
    AuthorizationError,
    ConflictError,
    NotFoundError,
    ValidationError,
)
from shared.security import (
    ACCOUNT_LOCKOUT_THRESHOLD,
    JWT_REFRESH_EXPIRE_DAYS,
    PASSWORD_HISTORY_COUNT,
    create_access_token,
    create_refresh_token,
    decode_token,
    generate_token,
    hash_password,
    validate_password,
    verify_password,
)


class AuthService:
    """Service for authentication operations."""

    def __init__(self, db: DbSession):
        self.db = db
        self.user_repo = UserRepository(db)
        self.role_repo = RoleRepository(db)
        self.session_repo = SessionRepository(db)
        self.login_history_repo = LoginHistoryRepository(db)
        self.activity_repo = ActivityLogRepository(db)
        self.user_role_repo = UserRoleRepository(db)
        self.role_perm_repo = RolePermissionRepository(db)

    def login(self, request: LoginRequest, ip: str = None, user_agent: str = None) -> dict:
        """Authenticate a user and return tokens.

        Returns:
            Dict with access_token, refresh_token, token_type, expires_in, user info.
        """
        user = self.user_repo.get_by_email(request.email)

        # Record login attempt
        self.login_history_repo.create(
            LoginHistory(
                user_id=user.id if user else None,
                email=request.email,
                ip_address=ip,
                user_agent=user_agent,
                success=False,
            )
        )

        if not user:
            raise AuthenticationError("Invalid email or password")

        if not user.is_active:
            raise AuthenticationError("Account is disabled")

        if self.user_repo.is_locked(user.id):
            raise AccountLockedError()

        if not verify_password(request.password, user.password_hash):
            count = self.user_repo.increment_failed_login(user.id)
            self.db.commit()
            if count >= ACCOUNT_LOCKOUT_THRESHOLD:
                raise AccountLockedError()
            raise AuthenticationError("Invalid email or password")

        # Success — reset failed logins
        self.user_repo.reset_failed_logins(user.id)
        self.user_repo.update_last_login(user.id)

        # Update login history as success
        self.login_history_repo.create(
            LoginHistory(
                user_id=user.id,
                email=user.email,
                ip_address=ip,
                user_agent=user_agent,
                success=True,
            )
        )

        # Get roles and permissions
        role_names = self.user_role_repo.get_roles_for_user(user.id)
        permission_names = self.user_role_repo.get_all_permissions_for_user(user.id)

        # Create tokens
        expire_days = 30 if request.remember_me else JWT_REFRESH_EXPIRE_DAYS
        access_token = create_access_token(
            subject=str(user.id),
            extra_claims={
                "email": user.email,
                "roles": role_names,
                "permissions": permission_names,
                "org_id": user.organization_id,
            },
        )
        refresh_token = create_refresh_token(
            subject=str(user.id),
            expires_days=expire_days,
        )

        # Store session
        session = UserSession(
            user_id=user.id,
            refresh_token=refresh_token,
            ip_address=ip,
            user_agent=user_agent,
            device=self._parse_device(user_agent),
            expires_at=datetime.now(timezone.utc) + timedelta(days=expire_days),
        )
        self.session_repo.create(session)

        # Log activity
        self.activity_repo.create(
            ActivityLog(
                user_id=user.id,
                action="login",
                ip_address=ip,
                user_agent=user_agent,
            )
        )

        self.db.commit()

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": 30 * 60,
            "user": {
                "id": user.id,
                "email": user.email,
                "full_name": user.full_name,
                "roles": role_names,
                "permissions": permission_names,
            },
        }

    def logout(self, refresh_token: str, ip: str = None):
        """Logout by revoking the session."""
        session = self.session_repo.get_by_token(refresh_token)
        if session:
            self.session_repo.revoke(session.id)
            self.activity_repo.create(
                ActivityLog(
                    user_id=session.user_id,
                    action="logout",
                    ip_address=ip,
                )
            )
        self.db.commit()

    def refresh_tokens(self, refresh_token: str) -> dict:
        """Exchange a refresh token for a new access token."""
        try:
            payload = decode_token(refresh_token)
        except Exception:
            raise AuthenticationError("Invalid or expired refresh token") from None
        if payload.get("type") != "refresh":
            raise AuthenticationError("Invalid token type")

        session = self.session_repo.get_by_token(refresh_token)
        if not session or not session.is_active or session.revoked_at:
            raise AuthenticationError("Session has been revoked")

        user = self.user_repo.get_by_id(int(payload["sub"]))
        if not user or not user.is_active:
            raise AuthenticationError("User not found or disabled")

        role_names = self.user_role_repo.get_roles_for_user(user.id)
        permission_names = self.user_role_repo.get_all_permissions_for_user(user.id)

        new_access = create_access_token(
            subject=str(user.id),
            extra_claims={
                "email": user.email,
                "roles": role_names,
                "permissions": permission_names,
                "org_id": user.organization_id,
            },
        )

        self.session_repo.update_activity(session.id)
        self.db.commit()

        return {
            "access_token": new_access,
            "token_type": "bearer",
            "expires_in": 30 * 60,
        }

    def change_password(self, user_id: int, request: ChangePasswordRequest):
        """Change password for the current user."""
        user = self.user_repo.get_by_id(user_id)
        if not user:
            raise NotFoundError("User not found")

        if not verify_password(request.current_password, user.password_hash):
            raise AuthenticationError("Current password is incorrect")

        errors = validate_password(request.new_password)
        if errors:
            raise ValidationError("; ".join(errors))

        # Check password history
        pwd_history_repo = PasswordHistoryRepository(self.db)
        old_hashes = pwd_history_repo.list_for_user(user_id, PASSWORD_HISTORY_COUNT)
        for old_hash in old_hashes:
            if verify_password(request.new_password, old_hash):
                raise ValidationError("Password has been used recently. Choose a different one.")

        # Save old password to history
        pwd_history_repo.add(user_id, user.password_hash)

        # Update password
        self.user_repo.update(user_id, password_hash=hash_password(request.new_password))

        # Revoke all sessions (force re-login)
        self.session_repo.revoke_all_for_user(user_id)

        # Log activity
        self.activity_repo.create(
            ActivityLog(
                user_id=user_id,
                action="password_change",
            )
        )

        self.db.commit()

    def forgot_password(self, email: str) -> str:
        """Generate a password reset token."""
        user = self.user_repo.get_by_email(email)
        if not user:
            # Don't reveal whether email exists
            return ""

        reset_repo = PasswordResetRepository(self.db)
        reset_repo.invalidate_all_for_user(user.id)

        token = generate_token()
        reset_repo.create(
            PasswordReset(
                user_id=user.id,
                token=token,
                expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
            )
        )

        self.activity_repo.create(
            ActivityLog(
                user_id=user.id,
                action="password_reset_requested",
            )
        )

        self.db.commit()
        return token

    def reset_password(self, token: str, new_password: str):
        """Reset password using a reset token."""
        reset_repo = PasswordResetRepository(self.db)
        reset = reset_repo.get_by_token(token)

        if not reset or reset.used_at:
            raise AuthenticationError("Invalid or expired reset token")

        if reset.expires_at < datetime.now(timezone.utc):
            raise AuthenticationError("Reset token has expired")

        errors = validate_password(new_password)
        if errors:
            raise ValidationError("; ".join(errors))

        user = self.user_repo.get_by_id(reset.user_id)
        if not user:
            raise NotFoundError("User not found")

        # Check password history
        pwd_history_repo = PasswordHistoryRepository(self.db)
        old_hashes = pwd_history_repo.list_for_user(user.id, PASSWORD_HISTORY_COUNT)
        for old_hash in old_hashes:
            if verify_password(new_password, old_hash):
                raise ValidationError("Password has been used recently. Choose a different one.")

        pwd_history_repo.add(user.id, user.password_hash)
        self.user_repo.update(user.id, password_hash=hash_password(new_password))
        reset_repo.mark_used(reset.id)
        self.session_repo.revoke_all_for_user(user.id)

        self.activity_repo.create(
            ActivityLog(
                user_id=user.id,
                action="password_reset_completed",
            )
        )

        self.db.commit()

    def verify_email(self, user_id: int):
        """Mark email as verified."""
        self.user_repo.verify_email(user_id)
        self.activity_repo.create(
            ActivityLog(
                user_id=user_id,
                action="email_verified",
            )
        )
        self.db.commit()

    def get_profile(self, user_id: int) -> dict:
        """Get user profile with roles and permissions."""
        user = self.user_repo.get_by_id(user_id)
        if not user:
            raise NotFoundError("User not found")

        roles = self.user_role_repo.get_roles_for_user(user_id)
        permissions = self.user_role_repo.get_all_permissions_for_user(user_id)

        return {
            "id": user.id,
            "email": user.email,
            "full_name": user.full_name,
            "avatar_url": user.avatar_url,
            "phone": user.phone,
            "organization_id": user.organization_id,
            "department_id": user.department_id,
            "position": user.position,
            "language": user.language,
            "timezone": user.timezone,
            "is_active": bool(user.is_active),
            "email_verified": user.email_verified_at is not None,
            "last_login_at": user.last_login_at,
            "created_at": user.created_at,
            "roles": roles,
            "permissions": permissions,
        }

    def update_profile(self, user_id: int, update: ProfileUpdate) -> dict:
        """Update user profile."""
        kwargs = {k: v for k, v in update.model_dump().items() if v is not None}
        if kwargs:
            self.user_repo.update(user_id, **kwargs)
            self.activity_repo.create(
                ActivityLog(
                    user_id=user_id,
                    action="profile_updated",
                )
            )
            self.db.commit()
        return self.get_profile(user_id)

    def get_sessions(self, user_id: int) -> list:
        """Get active sessions for a user."""
        sessions = self.session_repo.get_active_for_user(user_id)
        return [
            {
                "id": s.id,
                "ip_address": s.ip_address,
                "user_agent": s.user_agent,
                "device": s.device,
                "is_active": bool(s.is_active),
                "last_activity_at": s.last_activity_at,
                "created_at": s.created_at,
                "expires_at": s.expires_at,
            }
            for s in sessions
        ]

    def revoke_session(self, user_id: int, session_id: int):
        """Revoke a specific session."""
        sessions = self.session_repo.get_active_for_user(user_id)
        for s in sessions:
            if s.id == session_id:
                self.session_repo.revoke(s.id)
                self.activity_repo.create(
                    ActivityLog(
                        user_id=user_id,
                        action="session_revoked",
                        resource_type="session",
                        resource_id=session_id,
                    )
                )
                self.db.commit()
                return
        raise NotFoundError("Session not found")

    def get_login_history(self, user_id: int, limit: int = 20) -> list:
        """Get login history for a user."""
        records = self.login_history_repo.list_for_user(user_id, limit)
        return [
            {
                "id": r.id,
                "email": r.email,
                "ip_address": r.ip_address,
                "user_agent": r.user_agent,
                "success": bool(r.success),
                "failure_reason": r.failure_reason,
                "created_at": r.created_at,
            }
            for r in records
        ]

    def get_activity_history(self, user_id: int, limit: int = 50) -> list:
        """Get activity log for a user."""
        records = self.activity_repo.list_for_user(user_id, limit)
        return [
            {
                "id": r.id,
                "action": r.action,
                "resource_type": r.resource_type,
                "resource_id": r.resource_id,
                "ip_address": r.ip_address,
                "created_at": r.created_at,
            }
            for r in records
        ]

    @staticmethod
    def _parse_device(user_agent: str) -> str:
        """Extract device info from user agent string."""
        if not user_agent:
            return "Unknown"
        ua = user_agent.lower()
        if "mobile" in ua or "android" in ua or "iphone" in ua:
            return "Mobile"
        if "windows" in ua:
            return "Windows"
        if "mac" in ua:
            return "macOS"
        if "linux" in ua:
            return "Linux"
        return "Unknown"


class UserService:
    """Service for user management operations."""

    def __init__(self, db: DbSession):
        self.db = db
        self.user_repo = UserRepository(db)
        self.role_repo = RoleRepository(db)
        self.user_role_repo = UserRoleRepository(db)
        self.role_perm_repo = RolePermissionRepository(db)
        self.perm_repo = PermissionRepository(db)
        self.activity_repo = ActivityLogRepository(db)

    def create_user(self, request: UserCreate, created_by: int = None) -> dict:
        """Create a new user with optional role assignments."""
        existing = self.user_repo.get_by_email(request.email)
        if existing:
            raise ConflictError("User with this email already exists")

        errors = validate_password(request.password)
        if errors:
            raise ValidationError("; ".join(errors))

        user = User(
            email=request.email,
            password_hash=hash_password(request.password),
            full_name=request.full_name,
            phone=request.phone,
            organization_id=request.organization_id,
            department_id=request.department_id,
            position=request.position,
        )
        self.user_repo.create(user)

        # Assign roles
        if request.role_names:
            role_ids = []
            for role_name in request.role_names:
                role = self.role_repo.get_by_name(role_name)
                if role:
                    role_ids.append(role.id)
            if role_ids:
                self.user_role_repo.set_user_roles(user.id, role_ids, assigned_by=created_by)

        # Save password to history
        pwd_history = PasswordHistoryRepository(self.db)
        pwd_history.add(user.id, user.password_hash)

        self.activity_repo.create(
            ActivityLog(
                user_id=created_by,
                action="user_created",
                resource_type="user",
                resource_id=user.id,
            )
        )

        self.db.commit()
        return self._user_to_dict(user)

    def update_user(self, user_id: int, request: UserUpdate, updated_by: int = None) -> dict:
        """Update user information."""
        user = self.user_repo.get_by_id(user_id)
        if not user:
            raise NotFoundError("User not found")

        kwargs = {k: v for k, v in request.model_dump().items() if v is not None}
        if kwargs:
            self.user_repo.update(user_id, **kwargs)
            self.activity_repo.create(
                ActivityLog(
                    user_id=updated_by,
                    action="user_updated",
                    resource_type="user",
                    resource_id=user_id,
                )
            )

        self.db.commit()
        return self._user_to_dict(self.user_repo.get_by_id(user_id))

    def delete_user(self, user_id: int, deleted_by: int = None):
        """Soft delete a user."""
        user = self.user_repo.get_by_id(user_id)
        if not user:
            raise NotFoundError("User not found")

        self.user_repo.soft_delete(user_id)
        self.session_repo = SessionRepository(self.db)
        self.session_repo.revoke_all_for_user(user_id)
        self.activity_repo.create(
            ActivityLog(
                user_id=deleted_by,
                action="user_deleted",
                resource_type="user",
                resource_id=user_id,
            )
        )
        self.db.commit()

    def list_users(self, page: int = 1, page_size: int = 20) -> dict:
        """List users with pagination."""
        users, total = self.user_repo.list_users(page, page_size)
        return {
            "users": [self._user_to_dict(u) for u in users],
            "total": total,
            "page": page,
            "page_size": page_size,
        }

    def assign_roles(self, user_id: int, role_names: list[str], assigned_by: int = None):
        """Assign roles to a user."""
        user = self.user_repo.get_by_id(user_id)
        if not user:
            raise NotFoundError("User not found")

        role_ids = []
        for name in role_names:
            role = self.role_repo.get_by_name(name)
            if not role:
                raise NotFoundError(f"Role '{name}' not found")
            role_ids.append(role.id)

        self.user_role_repo.set_user_roles(user_id, role_ids, assigned_by)
        self.activity_repo.create(
            ActivityLog(
                user_id=assigned_by,
                action="user_roles_changed",
                resource_type="user",
                resource_id=user_id,
            )
        )
        self.db.commit()

    def _user_to_dict(self, user: User) -> dict:
        """Convert a User model to a response dict."""
        roles = self.user_role_repo.get_roles_for_user(user.id)
        return {
            "id": user.id,
            "email": user.email,
            "full_name": user.full_name,
            "avatar_url": user.avatar_url,
            "phone": user.phone,
            "organization_id": user.organization_id,
            "department_id": user.department_id,
            "position": user.position,
            "language": user.language,
            "timezone": user.timezone,
            "is_active": bool(user.is_active),
            "email_verified": user.email_verified_at is not None,
            "last_login_at": user.last_login_at,
            "created_at": user.created_at,
            "roles": roles,
        }


class RoleService:
    """Service for role and permission management."""

    def __init__(self, db: DbSession):
        self.db = db
        self.role_repo = RoleRepository(db)
        self.perm_repo = PermissionRepository(db)
        self.role_perm_repo = RolePermissionRepository(db)

    def create_role(self, request: RoleCreate, created_by: int = None) -> dict:
        """Create a new role with permissions."""
        existing = self.role_repo.get_by_name(request.name)
        if existing:
            raise ConflictError("Role with this name already exists")

        role = Role(
            name=request.name,
            display_name=request.display_name,
            description=request.description,
        )
        self.role_repo.create(role)

        if request.permission_names:
            perm_ids = self.role_perm_repo.get_permission_ids_by_names(request.permission_names)
            self.role_perm_repo.set_role_permissions(role.id, perm_ids)

        self.db.commit()
        return self._role_to_dict(role)

    def update_role(self, role_id: int, request: RoleUpdate) -> dict:
        """Update a role."""
        role = self.role_repo.get_by_id(role_id)
        if not role:
            raise NotFoundError("Role not found")

        kwargs = {}
        if request.display_name is not None:
            kwargs["display_name"] = request.display_name
        if request.description is not None:
            kwargs["description"] = request.description
        if kwargs:
            self.role_repo.update(role_id, **kwargs)

        if request.permission_names is not None:
            perm_ids = self.role_perm_repo.get_permission_ids_by_names(request.permission_names)
            self.role_perm_repo.set_role_permissions(role_id, perm_ids)

        self.db.commit()
        return self._role_to_dict(self.role_repo.get_by_id(role_id))

    def delete_role(self, role_id: int):
        """Soft delete a role (system roles cannot be deleted)."""
        role = self.role_repo.get_by_id(role_id)
        if not role:
            raise NotFoundError("Role not found")
        if role.is_system:
            raise AuthorizationError("System roles cannot be deleted")
        self.role_repo.soft_delete(role_id)
        self.db.commit()

    def list_roles(self) -> list[dict]:
        """List all roles with their permissions."""
        roles = self.role_repo.list_roles()
        return [self._role_to_dict(r) for r in roles]

    def list_permissions(self) -> list[dict]:
        """List all permissions."""
        perms = self.perm_repo.list_permissions()
        return [
            {
                "id": p.id,
                "name": p.name,
                "display_name": p.display_name,
                "module": p.module,
                "description": p.description,
            }
            for p in perms
        ]

    def _role_to_dict(self, role: Role) -> dict:
        """Convert a Role model to a response dict."""
        perms = self.role_perm_repo.get_permissions_for_role(role.id)
        return {
            "id": role.id,
            "name": role.name,
            "display_name": role.display_name,
            "description": role.description,
            "is_system": bool(role.is_system),
            "permissions": perms,
        }


def seed_default_data(db: DbSession):
    """Seed default roles, permissions, and super admin user.

    Called during database initialization.
    """
    perm_repo = PermissionRepository(db)
    role_repo = RoleRepository(db)
    role_perm_repo = RolePermissionRepository(db)
    user_repo = UserRepository(db)
    user_role_repo = UserRoleRepository(db)

    # Define all permissions
    permissions_def = [
        # User management
        ("users.create", "Create Users", "users", "Create new user accounts"),
        ("users.read", "View Users", "users", "View user profiles"),
        ("users.edit", "Edit Users", "users", "Edit user information"),
        ("users.delete", "Delete Users", "users", "Delete user accounts"),
        ("users.manage", "Manage Users", "users", "Full user management"),
        # Role management
        ("roles.create", "Create Roles", "roles", "Create new roles"),
        ("roles.read", "View Roles", "roles", "View roles and permissions"),
        ("roles.manage", "Manage Roles", "roles", "Full role management"),
        # Pipeline
        ("pipelines.create", "Create Pipelines", "pipelines", "Create ETL pipelines"),
        ("pipelines.execute", "Execute Pipelines", "pipelines", "Run ETL pipelines"),
        ("pipelines.view", "View Pipelines", "pipelines", "View pipeline status"),
        # ETL
        ("etl.import", "Import Data", "etl", "Import data via ETL"),
        ("etl.export", "Export Data", "etl", "Export data from ETL"),
        # Dashboard
        ("dashboard.view", "View Dashboard", "dashboard", "View dashboards"),
        ("dashboard.manage", "Manage Dashboard", "dashboard", "Create and edit dashboards"),
        # Reports
        ("reports.generate", "Generate Reports", "reports", "Generate reports"),
        ("reports.export", "Export Reports", "reports", "Export report files"),
        ("reports.view", "View Reports", "reports", "View reports"),
        # Datasets
        ("datasets.upload", "Upload Datasets", "datasets", "Upload new datasets"),
        ("datasets.delete", "Delete Datasets", "datasets", "Delete datasets"),
        ("datasets.view", "View Datasets", "datasets", "View datasets"),
        # Analytics
        ("analytics.view", "View Analytics", "analytics", "View analytics"),
        (
            "analytics.manage",
            "Manage Analytics",
            "analytics",
            "Create and manage dashboards and KPIs",
        ),
        (
            "analytics.export",
            "Export Analytics",
            "analytics",
            "Export dashboards and analytics data",
        ),
        # AI
        ("ai.use", "Use AI Features", "ai", "Access AI predictions and insights"),
        # Settings
        ("settings.manage", "Manage Settings", "settings", "Manage system settings"),
        # Audit
        ("audit.view", "View Audit Logs", "audit", "View audit logs"),
        # Notifications
        (
            "notifications.manage",
            "Manage Notifications",
            "notifications",
            "Manage notification settings",
        ),
        # Organization
        ("organizations.manage", "Manage Organizations", "organizations", "Manage organizations"),
        ("departments.manage", "Manage Departments", "departments", "Manage departments"),
        # Sessions
        ("sessions.manage", "Manage Sessions", "sessions", "Revoke user sessions"),
        # Profile
        ("profile.update", "Update Profile", "profile", "Update own profile"),
    ]

    for name, display, module, desc in permissions_def:
        if not perm_repo.get_by_name(name):
            perm_repo.create(
                Permission(
                    name=name,
                    display_name=display,
                    module=module,
                    description=desc,
                )
            )

    # Define roles and their permissions
    roles_def = [
        (
            "super_admin",
            "Super Administrator",
            "Full system access with all permissions",
            True,
            [p[0] for p in permissions_def],
        ),
        (
            "org_owner",
            "Organization Owner",
            "Owner of an organization with full org access",
            True,
            [p[0] for p in permissions_def if not p[0].startswith("settings.manage")],
        ),
        (
            "org_admin",
            "Organization Administrator",
            "Manage users and data within organization",
            True,
            [
                "users.create",
                "users.read",
                "users.edit",
                "users.delete",
                "users.manage",
                "roles.read",
                "pipelines.create",
                "pipelines.execute",
                "pipelines.view",
                "etl.import",
                "etl.export",
                "dashboard.view",
                "dashboard.manage",
                "reports.generate",
                "reports.export",
                "reports.view",
                "datasets.upload",
                "datasets.view",
                "analytics.view",
                "notifications.manage",
                "departments.manage",
                "sessions.manage",
                "profile.update",
                "audit.view",
            ],
        ),
        (
            "dept_manager",
            "Department Manager",
            "Manage department operations",
            True,
            [
                "users.read",
                "pipelines.view",
                "etl.import",
                "etl.export",
                "dashboard.view",
                "reports.view",
                "reports.generate",
                "reports.export",
                "datasets.view",
                "analytics.view",
                "profile.update",
            ],
        ),
        (
            "data_engineer",
            "Data Engineer",
            "Build and run ETL pipelines",
            True,
            [
                "pipelines.create",
                "pipelines.execute",
                "pipelines.view",
                "etl.import",
                "etl.export",
                "datasets.upload",
                "datasets.view",
                "dashboard.view",
                "profile.update",
            ],
        ),
        (
            "data_analyst",
            "Data Analyst",
            "Analyze data and create reports",
            True,
            [
                "dashboard.view",
                "reports.generate",
                "reports.view",
                "datasets.view",
                "analytics.view",
                "etl.export",
                "profile.update",
            ],
        ),
        (
            "business_analyst",
            "Business Analyst",
            "View dashboards and reports",
            True,
            ["dashboard.view", "reports.view", "datasets.view", "analytics.view", "profile.update"],
        ),
        (
            "executive",
            "Executive",
            "View high-level analytics and reports",
            True,
            ["dashboard.view", "reports.view", "analytics.view", "profile.update"],
        ),
        (
            "dept_officer",
            "Department Officer",
            "Department-level operations",
            True,
            ["dashboard.view", "reports.view", "datasets.view", "profile.update"],
        ),
        (
            "auditor",
            "Auditor",
            "View audit logs and security events",
            True,
            ["audit.view", "users.read", "profile.update"],
        ),
        (
            "viewer",
            "Viewer",
            "Read-only access to dashboards",
            True,
            ["dashboard.view", "profile.update"],
        ),
    ]

    for name, display, desc, is_system, perm_names in roles_def:
        role = role_repo.get_by_name(name)
        if not role:
            role = Role(name=name, display_name=display, description=desc, is_system=is_system)
            role_repo.create(role)
        perm_ids = role_perm_repo.get_permission_ids_by_names(perm_names)
        role_perm_repo.set_role_permissions(role.id, perm_ids)

    # Create default super admin user (credentials from env vars — no hardcoded passwords)
    import os as _os
    admin_email = _os.getenv("SUPER_ADMIN_EMAIL", "admin@dataflow.io")
    admin_password = _os.getenv("SUPER_ADMIN_PASSWORD", "")
    if admin_password and not user_repo.get_by_email(admin_email):
        admin = User(
            email=admin_email,
            password_hash=hash_password(admin_password),
            full_name="System Administrator",
            is_active=1,
            email_verified_at=datetime.now(timezone.utc),
        )
        user_repo.create(admin)
        super_admin_role = role_repo.get_by_name("super_admin")
        if super_admin_role:
            user_role_repo.assign_role(admin.id, super_admin_role.id)

    db.commit()
