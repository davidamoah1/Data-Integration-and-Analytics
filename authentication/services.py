"""Authentication service layer — business logic for auth operations.

Orchestrates repositories, security utilities, and audit logging.
No business logic in route handlers.
"""

from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session as DbSession

from audit.models import AuditLog
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
    ScopedRoleAssign,
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

        # Audit log
        self.db.add(
            AuditLog(
                user_id=user.id,
                organization_id=user.organization_id,
                action="auth.login",
                resource_type="user",
                resource_id=user.id,
                ip_address=ip,
                new_values={"device": self._parse_device(user_agent)},
            )
        )

        # Security notification for new login
        self._create_security_notification(
            user_id=user.id,
            subject="New Login",
            body=f"A successful login to your account was recorded from {ip or 'an unknown IP'} on {self._parse_device(user_agent)}. If this was not you, please change your password immediately.",
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
        """Exchange a refresh token for a new access token.

        Implements refresh token rotation: the old refresh token is revoked
        and a new one is issued, preventing token reuse attacks.
        """
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

        # Rotate: revoke old session, create new one
        self.session_repo.revoke(session.id)

        new_access = create_access_token(
            subject=str(user.id),
            extra_claims={
                "email": user.email,
                "roles": role_names,
                "permissions": permission_names,
                "org_id": user.organization_id,
            },
        )
        new_refresh = create_refresh_token(
            subject=str(user.id),
            expires_days=JWT_REFRESH_EXPIRE_DAYS,
        )

        new_session = UserSession(
            user_id=user.id,
            refresh_token=new_refresh,
            ip_address=session.ip_address,
            user_agent=session.user_agent,
            device=session.device,
            expires_at=datetime.now(timezone.utc) + timedelta(days=JWT_REFRESH_EXPIRE_DAYS),
        )
        self.session_repo.create(new_session)

        self.db.commit()

        return {
            "access_token": new_access,
            "refresh_token": new_refresh,
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

        # Security notification
        self._create_security_notification(
            user_id=user_id,
            subject="Password Changed",
            body="Your account password was changed. If this was not you, please contact your administrator immediately.",
        )

        # Audit log
        self.db.add(
            AuditLog(
                user_id=user_id,
                organization_id=user.organization_id,
                action="security.password_changed",
                resource_type="user",
                resource_id=user_id,
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

        # Security notification
        self._create_security_notification(
            user_id=user.id,
            subject="Password Reset",
            body="Your account password was reset. If this was not you, please contact your administrator immediately.",
        )

        # Audit log
        self.db.add(
            AuditLog(
                user_id=user.id,
                organization_id=user.organization_id,
                action="security.password_reset",
                resource_type="user",
                resource_id=user.id,
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
        self.db.add(
            AuditLog(
                user_id=user_id,
                action="security.email_verified",
                resource_type="user",
                resource_id=user_id,
            )
        )
        self.db.commit()

    def resend_email_verification(self, email: str) -> str:
        """Generate a new email verification token.

        Returns the token (for email delivery). Returns empty string
        if user not found to prevent enumeration.
        """
        user = self.user_repo.get_by_email(email)
        if not user or user.email_verified_at:
            return ""

        token = generate_token()
        onboarding_data = user.onboarding_data or {}
        onboarding_data["email_verify_token"] = token
        self.user_repo.update(user.id, onboarding_data=onboarding_data)

        self.activity_repo.create(
            ActivityLog(
                user_id=user.id,
                action="email_verification_resent",
            )
        )
        self.db.commit()
        return token

    def activate_account(self, user_id: int, reason: str = None, activated_by: int = None):
        """Activate a deactivated user account."""
        user = self.user_repo.get_by_id(user_id)
        if not user:
            raise NotFoundError("User not found")
        if user.is_active:
            raise ValidationError("Account is already active")

        self.user_repo.update(user_id, is_active=1, failed_login_count=0, locked_until=None)
        self.activity_repo.create(
            ActivityLog(
                user_id=activated_by,
                action="account_activated",
                resource_type="user",
                resource_id=user_id,
            )
        )
        self.db.add(
            AuditLog(
                user_id=activated_by,
                organization_id=user.organization_id,
                action="user.activated",
                resource_type="user",
                resource_id=user_id,
                new_values={"reason": reason} if reason else None,
            )
        )
        self.db.commit()

    def deactivate_account(self, user_id: int, reason: str = None, deactivated_by: int = None):
        """Deactivate an active user account. Revokes all sessions."""
        user = self.user_repo.get_by_id(user_id)
        if not user:
            raise NotFoundError("User not found")
        if not user.is_active:
            raise ValidationError("Account is already deactivated")

        self.user_repo.update(user_id, is_active=0)
        self.session_repo.revoke_all_for_user(user_id)

        self.activity_repo.create(
            ActivityLog(
                user_id=deactivated_by,
                action="account_deactivated",
                resource_type="user",
                resource_id=user_id,
            )
        )
        self.db.add(
            AuditLog(
                user_id=deactivated_by,
                organization_id=user.organization_id,
                action="user.deactivated",
                resource_type="user",
                resource_id=user_id,
                new_values={"reason": reason} if reason else None,
            )
        )

        # Security notification
        self._create_security_notification(
            user_id=user_id,
            subject="Account Deactivated",
            body=f"Your account has been deactivated{f': {reason}' if reason else ''}. Contact your administrator if you believe this is an error.",
        )

        self.db.commit()

    def get_profile(self, user_id: int) -> dict:
        """Get user profile with roles and permissions."""
        user = self.user_repo.get_by_id(user_id)
        if not user:
            raise NotFoundError("User not found")

        roles = self.user_role_repo.get_roles_for_user(user_id)
        permissions = self.user_role_repo.get_all_permissions_for_user(user_id)

        org_name = None
        org_type = None
        industry = None
        if user.organization_id:
            from organizations.models import Organization

            org = (
                self.db.query(Organization).filter(Organization.id == user.organization_id).first()
            )
            if org:
                org_name = org.name
                org_type = org.organization_type
                industry = org.industry

        return {
            "id": user.id,
            "email": user.email,
            "full_name": user.full_name,
            "avatar_url": user.avatar_url,
            "phone": user.phone,
            "organization_id": user.organization_id,
            "organization_name": org_name,
            "organization_type": org_type,
            "industry": industry,
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

    def _create_security_notification(self, user_id: int, subject: str, body: str):
        """Create an in-app security notification for a user."""
        from notifications.models import Notification

        self.db.add(
            Notification(
                user_id=user_id,
                channel="in_app",
                subject=subject,
                body=body,
                status="sent",
                read=False,
                created_at=datetime.now(timezone.utc),
                sent_at=datetime.now(timezone.utc),
            )
        )

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

        self.db.add(
            AuditLog(
                user_id=created_by,
                organization_id=user.organization_id,
                action="user.created",
                resource_type="user",
                resource_id=user.id,
                new_values={"email": user.email, "full_name": user.full_name},
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
            self.db.add(
                AuditLog(
                    user_id=updated_by,
                    organization_id=user.organization_id,
                    action="user.updated",
                    resource_type="user",
                    resource_id=user_id,
                    new_values=kwargs,
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
        self.db.add(
            AuditLog(
                user_id=deleted_by,
                organization_id=user.organization_id,
                action="user.deleted",
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

    def list_users_by_org(self, org_id: int, page: int = 1, page_size: int = 20) -> dict:
        """List users within a specific organization."""
        users, total = self.user_repo.list_users_by_org(org_id, page, page_size)
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
        self.db.add(
            AuditLog(
                user_id=assigned_by,
                organization_id=user.organization_id,
                action="role.assigned",
                resource_type="user",
                resource_id=user_id,
                new_values={"roles": role_names},
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
            "level": role.level,
            "is_system": bool(role.is_system),
            "is_assignable": bool(role.is_assignable),
            "permissions": perms,
        }

    def list_roles_by_level(self, level: str) -> list[dict]:
        """List all roles at a specific level (platform, organization, department, personal)."""
        roles = self.role_repo.list_roles_by_level(level)
        return [self._role_to_dict(r) for r in roles]

    def list_assignable_roles(self) -> list[dict]:
        """List all roles that can be assigned to users."""
        roles = self.role_repo.list_assignable_roles()
        return [self._role_to_dict(r) for r in roles]

    def assign_scoped_role(self, request: ScopedRoleAssign, assigned_by: int) -> dict:
        """Assign a role to a user with optional scope (organization, department, resource)."""
        from authentication.repositories import UserRepository

        user_repo = UserRepository(self.db)
        user = user_repo.get_by_id(request.user_id)
        if not user:
            raise NotFoundError("User not found")

        role = self.role_repo.get_by_name(request.role_name)
        if not role:
            raise NotFoundError(f"Role '{request.role_name}' not found")

        if not role.is_assignable:
            raise AuthorizationError(f"Role '{request.role_name}' is not assignable")

        # Validate scope matches role level
        if role.level == "platform" and request.scope_type not in (None, "platform"):
            raise ValidationError("Platform roles can only have platform scope")
        if role.level == "organization" and request.scope_type not in (None, "organization"):
            raise ValidationError("Organization roles can only have organization scope")
        if role.level == "department" and request.scope_type != "department":
            raise ValidationError("Department roles require department scope")
        if role.level == "personal" and request.scope_type not in (None, "personal"):
            raise ValidationError("Personal roles can only have personal scope")

        # Use user's org as default scope for org-level roles
        scope_type = request.scope_type or (
            "organization" if role.level == "organization" else None
        )
        scope_id = request.scope_id or (
            user.organization_id if scope_type == "organization" else None
        )

        from authentication.repositories import UserRoleRepository

        user_role_repo = UserRoleRepository(self.db)
        user_role_repo.assign_role(
            user_id=request.user_id,
            role_id=role.id,
            assigned_by=assigned_by,
            scope_type=scope_type,
            scope_id=scope_id,
        )

        self.db.add(
            AuditLog(
                user_id=assigned_by,
                organization_id=user.organization_id,
                action="role.scoped_assign",
                resource_type="user",
                resource_id=request.user_id,
                new_values={
                    "role": request.role_name,
                    "scope_type": scope_type,
                    "scope_id": scope_id,
                },
            )
        )
        self.db.commit()
        return {
            "user_id": request.user_id,
            "role": request.role_name,
            "scope_type": scope_type,
            "scope_id": scope_id,
        }

    def get_user_permissions(self, user_id: int) -> dict:
        """Get a user's roles, permissions, and scoped role assignments."""
        from authentication.repositories import UserRepository, UserRoleRepository

        user_repo = UserRepository(self.db)
        user_role_repo = UserRoleRepository(self.db)

        user = user_repo.get_by_id(user_id)
        if not user:
            raise NotFoundError("User not found")

        roles = user_role_repo.get_roles_for_user(user_id)
        permissions = user_role_repo.get_all_permissions_for_user(user_id)
        scoped_roles = user_role_repo.get_scoped_roles_for_user(user_id)

        return {
            "user_id": user_id,
            "roles": roles,
            "permissions": sorted(permissions),
            "scoped_roles": scoped_roles,
        }

    def check_permission(
        self,
        user_id: int,
        permission: str,
        scope_type: str = None,
        scope_id: int = None,
        resource_type: str = None,
        resource_id: int = None,
    ) -> dict:
        """Check if a user has a specific permission, optionally within a scope or resource."""
        from authentication.repositories import (
            ResourceRepository,
            UserRepository,
            UserRoleRepository,
        )

        user_role_repo = UserRoleRepository(self.db)
        user_repo = UserRepository(self.db)

        user = user_repo.get_by_id(user_id)
        if not user:
            return {"has_permission": False, "reason": "User not found"}

        # Super admin / platform_owner has all permissions
        roles = user_role_repo.get_roles_for_user(user_id)
        if "super_admin" in roles or "platform_owner" in roles:
            return {"has_permission": True}

        # Check global permission
        has_perm = user_role_repo.has_permission(user_id, permission)
        if not has_perm and scope_type:
            # Check scoped permissions
            scoped_perms = user_role_repo.get_permissions_for_scope(user_id, scope_type, scope_id)
            has_perm = permission in scoped_perms

        if not has_perm:
            return {"has_permission": False, "reason": f"Missing permission: {permission}"}

        # Resource-level check
        if resource_type and resource_id:
            resource_repo = ResourceRepository(self.db)
            can_access = resource_repo.can_access(
                user_id=user_id,
                resource_type=resource_type,
                resource_id=resource_id,
                user_org_id=user.organization_id,
                user_dept_id=user.department_id,
            )
            if not can_access:
                return {"has_permission": False, "reason": "Resource access denied"}

        return {"has_permission": True}


def seed_default_data(db: DbSession):
    """Seed default roles, permissions, and super admin user.

    Called during database initialization.
    """
    perm_repo = PermissionRepository(db)
    role_repo = RoleRepository(db)
    role_perm_repo = RolePermissionRepository(db)
    user_repo = UserRepository(db)
    user_role_repo = UserRoleRepository(db)

    # Enterprise RBAC permissions
    permissions_def = [
        ("organization.create", "Create Organization", "organization", "Create new organizations"),
        (
            "organization.manage",
            "Manage Organization",
            "organization",
            "Manage organization settings",
        ),
        ("organization.read", "View Organization", "organization", "View organization details"),
        ("organization.delete", "Delete Organization", "organization", "Delete an organization"),
        ("department.create", "Create Department", "department", "Create departments"),
        ("department.manage", "Manage Departments", "department", "Manage department settings"),
        ("department.read", "View Departments", "department", "View department info"),
        ("member.invite", "Invite Members", "member", "Invite users to organization"),
        ("member.remove", "Remove Members", "member", "Remove users from organization"),
        ("member.read", "View Members", "member", "View organization members"),
        ("member.manage", "Manage Members", "member", "Manage member roles"),
        ("role.assign", "Assign Roles", "role", "Assign roles to users"),
        ("role.revoke", "Revoke Roles", "role", "Revoke roles from users"),
        ("role.create", "Create Roles", "role", "Create custom roles"),
        ("role.read", "View Roles", "role", "View roles and permissions"),
        ("role.manage", "Manage Roles", "role", "Full role management"),
        ("users.create", "Create Users", "users", "Create new user accounts"),
        ("users.read", "View Users", "users", "View user profiles"),
        ("users.edit", "Edit Users", "users", "Edit user information"),
        ("users.delete", "Delete Users", "users", "Delete user accounts"),
        ("users.manage", "Manage Users", "users", "Full user management"),
        ("dataset.create", "Create Dataset", "dataset", "Create and upload datasets"),
        ("dataset.read", "View Dataset", "dataset", "View datasets"),
        ("dataset.update", "Update Dataset", "dataset", "Edit dataset data"),
        ("dataset.delete", "Delete Dataset", "dataset", "Delete datasets"),
        ("dataset.share", "Share Dataset", "dataset", "Share datasets with others"),
        ("dataset.export", "Export Dataset", "dataset", "Export dataset data"),
        ("dashboard.create", "Create Dashboard", "dashboard", "Create dashboards"),
        ("dashboard.read", "View Dashboard", "dashboard", "View dashboards"),
        ("dashboard.update", "Update Dashboard", "dashboard", "Edit dashboards"),
        ("dashboard.delete", "Delete Dashboard", "dashboard", "Delete dashboards"),
        ("dashboard.export", "Export Dashboard", "dashboard", "Export dashboard as PDF/image"),
        ("dashboard.share", "Share Dashboard", "dashboard", "Share dashboards"),
        ("report.generate", "Generate Report", "report", "Generate reports"),
        ("report.read", "View Report", "report", "View reports"),
        ("report.update", "Update Report", "report", "Edit report configs"),
        ("report.delete", "Delete Report", "report", "Delete reports"),
        ("report.export", "Export Report", "report", "Export report files"),
        ("pipelines.create", "Create Pipelines", "pipelines", "Create ETL pipelines"),
        ("pipelines.execute", "Execute Pipelines", "pipelines", "Run ETL pipelines"),
        ("pipelines.view", "View Pipelines", "pipelines", "View pipeline status"),
        ("pipelines.delete", "Delete Pipelines", "pipelines", "Delete ETL pipelines"),
        ("etl.import", "Import Data", "etl", "Import data via ETL"),
        ("etl.export", "Export Data", "etl", "Export data from ETL"),
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
        ("ai.use", "Use AI Features", "ai", "Access AI predictions and insights"),
        ("settings.manage", "Manage Settings", "settings", "Manage system settings"),
        ("audit.view", "View Audit Logs", "audit", "View audit logs"),
        (
            "notifications.manage",
            "Manage Notifications",
            "notifications",
            "Manage notification settings",
        ),
        ("sessions.manage", "Manage Sessions", "sessions", "Revoke user sessions"),
        ("profile.update", "Update Profile", "profile", "Update own profile"),
        ("ml.read", "View ML Models", "ml", "View machine learning models and dashboards"),
        ("ml.write", "Create ML Models", "ml", "Create and edit machine learning models"),
        ("ml.execute", "Execute ML Training", "ml", "Train, predict, and run ML jobs"),
        ("ml.delete", "Delete ML Models", "ml", "Archive or delete ML models"),
        (
            "capture.upload",
            "Upload Documents",
            "capture",
            "Upload documents for smart data capture",
        ),
        ("capture.process", "Process Documents", "capture", "Run OCR and document processing"),
        ("capture.read", "View Captured Data", "capture", "View captured document data"),
        (
            "workspace.create",
            "Create Workspace",
            "workspace",
            "Create personal or shared workspaces",
        ),
        ("workspace.manage", "Manage Workspace", "workspace", "Manage workspace settings"),
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

    ALL_PERMS = [p[0] for p in permissions_def]

    # Enterprise roles: (name, display, desc, level, is_system, is_assignable, [perms])
    roles_def = [
        (
            "super_admin",
            "Super Administrator",
            "Full system access — backward compatible",
            "platform",
            True,
            False,
            ALL_PERMS,
        ),
        (
            "platform_owner",
            "Platform Owner",
            "Owns the platform, full control over all organizations",
            "platform",
            True,
            False,
            ALL_PERMS,
        ),
        (
            "platform_admin",
            "Platform Administrator",
            "Manages platform operations and all organizations",
            "platform",
            True,
            True,
            ALL_PERMS,
        ),
        (
            "org_admin",
            "Organization Administrator",
            "Manages users, roles, departments, and resources within an organization",
            "organization",
            True,
            True,
            [
                "organization.read",
                "organization.manage",
                "department.create",
                "department.manage",
                "department.read",
                "member.invite",
                "member.remove",
                "member.read",
                "member.manage",
                "role.assign",
                "role.revoke",
                "role.read",
                "users.create",
                "users.read",
                "users.edit",
                "users.delete",
                "users.manage",
                "dataset.create",
                "dataset.read",
                "dataset.update",
                "dataset.delete",
                "dataset.share",
                "dataset.export",
                "dashboard.create",
                "dashboard.read",
                "dashboard.update",
                "dashboard.delete",
                "dashboard.export",
                "dashboard.share",
                "report.generate",
                "report.read",
                "report.update",
                "report.delete",
                "report.export",
                "pipelines.create",
                "pipelines.execute",
                "pipelines.view",
                "pipelines.delete",
                "etl.import",
                "etl.export",
                "analytics.view",
                "analytics.manage",
                "analytics.export",
                "ai.use",
                "audit.view",
                "notifications.manage",
                "sessions.manage",
                "profile.update",
                "ml.read",
                "ml.write",
                "ml.execute",
                "ml.delete",
                "capture.upload",
                "capture.process",
                "capture.read",
                "workspace.create",
                "workspace.manage",
            ],
        ),
        (
            "dept_manager",
            "Department Manager",
            "Manages department operations, members, and resources",
            "department",
            True,
            True,
            [
                "organization.read",
                "department.read",
                "department.manage",
                "member.invite",
                "member.read",
                "role.read",
                "users.read",
                "dataset.create",
                "dataset.read",
                "dataset.update",
                "dataset.delete",
                "dataset.share",
                "dataset.export",
                "dashboard.create",
                "dashboard.read",
                "dashboard.update",
                "dashboard.export",
                "report.generate",
                "report.read",
                "report.export",
                "pipelines.create",
                "pipelines.execute",
                "pipelines.view",
                "etl.import",
                "etl.export",
                "analytics.view",
                "analytics.manage",
                "ai.use",
                "audit.view",
                "profile.update",
                "ml.read",
                "ml.execute",
                "capture.upload",
                "capture.process",
                "capture.read",
                "workspace.create",
                "workspace.manage",
            ],
        ),
        (
            "analyst",
            "Analyst",
            "Analyzes data, creates dashboards and reports, runs ML models",
            "organization",
            True,
            True,
            [
                "organization.read",
                "department.read",
                "member.read",
                "role.read",
                "users.read",
                "dataset.read",
                "dataset.update",
                "dataset.export",
                "dataset.share",
                "dashboard.create",
                "dashboard.read",
                "dashboard.update",
                "dashboard.export",
                "dashboard.share",
                "report.generate",
                "report.read",
                "report.update",
                "report.export",
                "pipelines.view",
                "etl.export",
                "analytics.view",
                "analytics.manage",
                "analytics.export",
                "ai.use",
                "profile.update",
                "ml.read",
                "ml.write",
                "ml.execute",
                "capture.read",
                "workspace.create",
                "workspace.manage",
            ],
        ),
        (
            "researcher",
            "Researcher",
            "Uploads research datasets, performs statistical analysis, generates reports",
            "organization",
            True,
            True,
            [
                "organization.read",
                "department.read",
                "member.read",
                "dataset.create",
                "dataset.read",
                "dataset.update",
                "dataset.export",
                "dashboard.create",
                "dashboard.read",
                "dashboard.export",
                "report.generate",
                "report.read",
                "report.export",
                "pipelines.view",
                "etl.import",
                "etl.export",
                "analytics.view",
                "analytics.export",
                "ai.use",
                "profile.update",
                "ml.read",
                "ml.execute",
                "capture.upload",
                "capture.read",
                "workspace.create",
            ],
        ),
        (
            "data_entry_officer",
            "Data Entry Officer",
            "Uploads documents, uses Smart Data Capture, enters and updates data",
            "department",
            True,
            True,
            [
                "organization.read",
                "department.read",
                "dataset.create",
                "dataset.read",
                "dataset.update",
                "dashboard.read",
                "report.read",
                "etl.import",
                "profile.update",
                "capture.upload",
                "capture.process",
                "capture.read",
            ],
        ),
        (
            "viewer",
            "Viewer",
            "Read-only access to dashboards, reports, and shared resources",
            "organization",
            True,
            True,
            [
                "organization.read",
                "member.read",
                "dataset.read",
                "dashboard.read",
                "report.read",
                "analytics.view",
                "profile.update",
            ],
        ),
        (
            "personal_user",
            "Personal Workspace User",
            "Individual user with personal workspace — limited to own resources",
            "personal",
            True,
            True,
            [
                "dataset.create",
                "dataset.read",
                "dataset.update",
                "dataset.delete",
                "dataset.export",
                "dashboard.create",
                "dashboard.read",
                "dashboard.update",
                "dashboard.export",
                "report.generate",
                "report.read",
                "report.export",
                "analytics.view",
                "ai.use",
                "profile.update",
                "ml.read",
                "ml.execute",
                "capture.upload",
                "capture.read",
                "workspace.create",
                "workspace.manage",
            ],
        ),
    ]

    for name, display, desc, level, is_system, is_assignable, perm_names in roles_def:
        role = role_repo.get_by_name(name)
        if not role:
            role = Role(
                name=name,
                display_name=display,
                description=desc,
                level=level,
                is_system=is_system,
                is_assignable=is_assignable,
            )
            role_repo.create(role)
        else:
            role_repo.update(
                role.id,
                level=level,
                is_assignable=is_assignable,
                display_name=display,
                description=desc,
            )
        perm_ids = role_perm_repo.get_permission_ids_by_names(perm_names)
        role_perm_repo.set_role_permissions(role.id, perm_ids)

    # Create default super admin user (credentials from env vars — no hardcoded passwords)
    import os as _os

    admin_email = _os.getenv("SUPER_ADMIN_EMAIL", "admin@dataflow.io")
    admin_password = _os.getenv("SUPER_ADMIN_PASSWORD", "")

    # Ensure a default organization exists for the super admin
    from organizations.models import Organization

    default_org = db.query(Organization).filter(Organization.slug == "system").first()
    if not default_org:
        default_org = Organization(
            name="System Administration",
            slug="system",
            description="Default organization for platform administration",
            is_active=1,
        )
        db.add(default_org)
        db.flush()

    if admin_password and not user_repo.get_by_email(admin_email):
        admin = User(
            email=admin_email,
            password_hash=hash_password(admin_password),
            full_name="System Administrator",
            is_active=1,
            email_verified_at=datetime.now(timezone.utc),
            organization_id=default_org.id,
        )
        user_repo.create(admin)
        super_admin_role = role_repo.get_by_name("super_admin")
        if super_admin_role:
            user_role_repo.assign_role(admin.id, super_admin_role.id)

    db.commit()
