"""FastAPI routes for authentication and user management.

All endpoints use standard response format and proper permission checks.
"""

from fastapi import APIRouter, Depends, Request, HTTPException, status
from sqlalchemy.orm import Session as DbSession

from shared.database import get_db
from shared.dependencies import get_current_user, require_permissions
from shared.response import success_response, error_response
from authentication.services import AuthService, UserService, RoleService
from authentication.schemas import (
    LoginRequest, TokenResponse, RefreshTokenRequest,
    ChangePasswordRequest, ForgotPasswordRequest, ResetPasswordRequest,
    UserCreate, UserUpdate, UserResponse, UserListResponse,
    RoleCreate, RoleUpdate, RoleResponse,
    ProfileUpdate, SessionResponse, LoginHistoryResponse,
)

router = APIRouter(prefix="/auth", tags=["Authentication"])


# --- Authentication endpoints ------------------------------------------------

@router.post("/login")
async def login(request: LoginRequest, req: Request, db: DbSession = Depends(get_db)):
    """Authenticate user and return JWT tokens."""
    service = AuthService(db)
    ip = req.client.host if req.client else None
    ua = req.headers.get("user-agent")
    result = service.login(request, ip=ip, user_agent=ua)
    return success_response(result, "Login successful")


@router.post("/logout")
async def logout(
    request: RefreshTokenRequest,
    req: Request,
    db: DbSession = Depends(get_db),
):
    """Logout and revoke the current session."""
    service = AuthService(db)
    ip = req.client.host if req.client else None
    service.logout(request.refresh_token, ip=ip)
    return success_response(None, "Logout successful")


@router.post("/refresh")
async def refresh_token(request: RefreshTokenRequest, db: DbSession = Depends(get_db)):
    """Exchange a refresh token for a new access token."""
    service = AuthService(db)
    result = service.refresh_tokens(request.refresh_token)
    return success_response(result, "Token refreshed")


@router.post("/change-password")
async def change_password(
    request: ChangePasswordRequest,
    current_user: dict = Depends(get_current_user),
    db: DbSession = Depends(get_db),
):
    """Change the current user's password."""
    service = AuthService(db)
    service.change_password(current_user["id"], request)
    return success_response(None, "Password changed successfully")


@router.post("/forgot-password")
async def forgot_password(
    request: ForgotPasswordRequest,
    db: DbSession = Depends(get_db),
):
    """Request a password reset token."""
    service = AuthService(db)
    service.forgot_password(request.email)
    return success_response(None, "If the email exists, a reset link has been sent")


@router.post("/reset-password")
async def reset_password(
    request: ResetPasswordRequest,
    db: DbSession = Depends(get_db),
):
    """Reset password using a reset token."""
    service = AuthService(db)
    service.reset_password(request.token, request.new_password)
    return success_response(None, "Password reset successful")


# --- Profile endpoints ------------------------------------------------------

@router.get("/profile")
async def get_profile(
    current_user: dict = Depends(get_current_user),
    db: DbSession = Depends(get_db),
):
    """Get the current user's profile."""
    service = AuthService(db)
    profile = service.get_profile(current_user["id"])
    return success_response(profile)


@router.put("/profile")
async def update_profile(
    request: ProfileUpdate,
    current_user: dict = Depends(get_current_user),
    db: DbSession = Depends(get_db),
):
    """Update the current user's profile."""
    service = AuthService(db)
    profile = service.update_profile(current_user["id"], request)
    return success_response(profile, "Profile updated")


@router.get("/sessions")
async def get_sessions(
    current_user: dict = Depends(get_current_user),
    db: DbSession = Depends(get_db),
):
    """Get active sessions for the current user."""
    service = AuthService(db)
    sessions = service.get_sessions(current_user["id"])
    return success_response(sessions)


@router.delete("/sessions/{session_id}")
async def revoke_session(
    session_id: int,
    current_user: dict = Depends(get_current_user),
    db: DbSession = Depends(get_db),
):
    """Revoke a specific session."""
    service = AuthService(db)
    service.revoke_session(current_user["id"], session_id)
    return success_response(None, "Session revoked")


@router.get("/login-history")
async def get_login_history(
    current_user: dict = Depends(get_current_user),
    db: DbSession = Depends(get_db),
):
    """Get login history for the current user."""
    service = AuthService(db)
    history = service.get_login_history(current_user["id"])
    return success_response(history)


@router.get("/activity")
async def get_activity(
    current_user: dict = Depends(get_current_user),
    db: DbSession = Depends(get_db),
):
    """Get activity log for the current user."""
    service = AuthService(db)
    activity = service.get_activity_history(current_user["id"])
    return success_response(activity)


# --- User management endpoints ----------------------------------------------

users_router = APIRouter(prefix="/users", tags=["User Management"])


@users_router.get("")
async def list_users(
    page: int = 1,
    page_size: int = 20,
    current_user: dict = Depends(require_permissions("users.read")),
    db: DbSession = Depends(get_db),
):
    """List all users (requires users.read permission)."""
    service = UserService(db)
    result = service.list_users(page, page_size)
    return success_response(result)


@users_router.post("")
async def create_user(
    request: UserCreate,
    current_user: dict = Depends(require_permissions("users.create")),
    db: DbSession = Depends(get_db),
):
    """Create a new user (requires users.create permission)."""
    service = UserService(db)
    user = service.create_user(request, created_by=current_user["id"])
    return success_response(user, "User created")


@users_router.get("/{user_id}")
async def get_user(
    user_id: int,
    current_user: dict = Depends(require_permissions("users.read")),
    db: DbSession = Depends(get_db),
):
    """Get a specific user by ID."""
    service = UserService(db)
    user_model = service.user_repo.get_by_id(user_id)
    if not user_model:
        raise HTTPException(status_code=404, detail="User not found")
    user = service._user_to_dict(user_model)
    return success_response(user)


@users_router.put("/{user_id}")
async def update_user(
    user_id: int,
    request: UserUpdate,
    current_user: dict = Depends(require_permissions("users.edit")),
    db: DbSession = Depends(get_db),
):
    """Update a user."""
    service = UserService(db)
    user = service.update_user(user_id, request, updated_by=current_user["id"])
    return success_response(user, "User updated")


@users_router.delete("/{user_id}")
async def delete_user(
    user_id: int,
    current_user: dict = Depends(require_permissions("users.delete")),
    db: DbSession = Depends(get_db),
):
    """Soft delete a user."""
    service = UserService(db)
    service.delete_user(user_id, deleted_by=current_user["id"])
    return success_response(None, "User deleted")


@users_router.post("/{user_id}/roles")
async def assign_roles(
    user_id: int,
    role_names: list[str],
    current_user: dict = Depends(require_permissions("users.manage")),
    db: DbSession = Depends(get_db),
):
    """Assign roles to a user."""
    service = UserService(db)
    service.assign_roles(user_id, role_names, assigned_by=current_user["id"])
    return success_response(None, "Roles assigned")


# --- Role management endpoints ---------------------------------------------

roles_router = APIRouter(prefix="/roles", tags=["Role Management"])


@roles_router.get("")
async def list_roles(
    current_user: dict = Depends(require_permissions("roles.read")),
    db: DbSession = Depends(get_db),
):
    """List all roles with their permissions."""
    service = RoleService(db)
    roles = service.list_roles()
    return success_response(roles)


@roles_router.post("")
async def create_role(
    request: RoleCreate,
    current_user: dict = Depends(require_permissions("roles.manage")),
    db: DbSession = Depends(get_db),
):
    """Create a new role."""
    service = RoleService(db)
    role = service.create_role(request, created_by=current_user["id"])
    return success_response(role, "Role created")


@roles_router.put("/{role_id}")
async def update_role(
    role_id: int,
    request: RoleUpdate,
    current_user: dict = Depends(require_permissions("roles.manage")),
    db: DbSession = Depends(get_db),
):
    """Update a role."""
    service = RoleService(db)
    role = service.update_role(role_id, request)
    return success_response(role, "Role updated")


@roles_router.delete("/{role_id}")
async def delete_role(
    role_id: int,
    current_user: dict = Depends(require_permissions("roles.manage")),
    db: DbSession = Depends(get_db),
):
    """Delete a role (system roles cannot be deleted)."""
    service = RoleService(db)
    service.delete_role(role_id)
    return success_response(None, "Role deleted")


@roles_router.get("/permissions")
async def list_permissions(
    current_user: dict = Depends(require_permissions("roles.read")),
    db: DbSession = Depends(get_db),
):
    """List all available permissions."""
    service = RoleService(db)
    perms = service.list_permissions()
    return success_response(perms)
