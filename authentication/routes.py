"""FastAPI routes for authentication and user management.

All endpoints use standard response format and proper permission checks.
"""

# ruff: noqa: B008  # FastAPI Depends() calls in default arguments are intentional

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session as DbSession

from authentication.schemas import (
    ChangePasswordRequest,
    ForgotPasswordRequest,
    LoginRequest,
    OnboardingRequest,
    ProfileUpdate,
    RefreshTokenRequest,
    ResetPasswordRequest,
    RoleCreate,
    RoleUpdate,
    SignupRequest,
    UserCreate,
    UserUpdate,
    VerifyEmailRequest,
)
from authentication.services import AuthService, RoleService, UserService
from shared.database import get_db
from shared.dependencies import get_current_user, require_permissions
from shared.tenant import get_current_organization_id, is_super_admin
from datetime import datetime, timedelta, timezone

from shared.response import success_response

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


# --- Authentication endpoints ------------------------------------------------


@router.post("/login")
async def login(request: LoginRequest, req: Request, db: DbSession = Depends(get_db)):
    """Authenticate user and return JWT tokens."""
    service = AuthService(db)
    ip = req.client.host if req.client else None
    ua = req.headers.get("user-agent")
    result = service.login(request, ip=ip, user_agent=ua)
    return success_response(result, "Login successful")


@router.post("/signup")
async def signup(request: SignupRequest, db: DbSession = Depends(get_db)):
    """Public self-registration. Creates a user and optionally a new organization.

    Returns JWT tokens so the user is auto-logged in and can proceed to onboarding.
    """
    from authentication.models import User
    from authentication.repositories import UserRepository, RoleRepository, UserRoleRepository
    from authentication.services import AuthService, validate_password
    from organizations.models import Organization
    from shared.security import hash_password, create_access_token, create_refresh_token, generate_token

    user_repo = UserRepository(db)
    existing = user_repo.get_by_email(request.email)
    if existing:
        raise HTTPException(status_code=409, detail="User with this email already exists")

    errors = validate_password(request.password)
    if errors:
        raise HTTPException(status_code=422, detail="; ".join(errors))

    org_id = None
    if request.organization_name:
        slug = request.organization_name.lower().strip().replace(" ", "-").replace("&", "and")
        existing_org = db.query(Organization).filter(Organization.slug == slug).first()
        if existing_org:
            raise HTTPException(
                status_code=409,
                detail="This organization already exists. Please request an invitation from your administrator.",
            )
        org = Organization(
            name=request.organization_name,
            slug=slug,
            is_active=1,
        )
        db.add(org)
        db.flush()
        org_id = org.id

        from organizations.workspace_models import Workspace
        workspace = Workspace(
            organization_id=org.id,
            name=f"{request.organization_name} Workspace",
            type="organization",
        )
        db.add(workspace)
        db.flush()

    # Store signup extras in onboarding_data
    onboarding_data: dict = {}
    if request.country:
        onboarding_data["country"] = request.country
    if request.industry:
        onboarding_data["industry"] = request.industry
    if request.organization_type:
        onboarding_data["organization_type"] = request.organization_type

    user = User(
        email=request.email,
        password_hash=hash_password(request.password),
        full_name=request.full_name,
        organization_id=org_id,
        email_verified_at=datetime.now(timezone.utc),
        is_active=1,
        onboarding_data=onboarding_data if onboarding_data else None,
    )
    user_repo.create(user)

    # Assign org_admin role when creating an org, viewer for personal accounts
    role_repo = RoleRepository(db)
    if org_id:
        assigned_role = role_repo.get_by_name("org_admin") or role_repo.get_by_name("viewer")
    else:
        assigned_role = role_repo.get_by_name("viewer")
    if assigned_role:
        UserRoleRepository(db).set_user_roles(user.id, [assigned_role.id])

    # Audit log
    from audit.models import AuditLog
    if org_id:
        db.add(AuditLog(
            user_id=user.id,
            organization_id=org_id,
            action="organization.created",
            resource_type="organization",
            resource_id=org_id,
            new_values={"name": request.organization_name},
        ))
        db.add(AuditLog(
            user_id=user.id,
            organization_id=org_id,
            action="role.assigned",
            resource_type="user",
            resource_id=user.id,
            new_values={"role": assigned_role.name if assigned_role else "viewer"},
        ))
    db.add(AuditLog(
        user_id=user.id,
        organization_id=org_id,
        action="user.registered",
        resource_type="user",
        resource_id=user.id,
        new_values={"email": user.email, "mode": "create_organization" if org_id else "personal"},
    ))

    # Generate a verification token (stored in onboarding_data for now)
    verify_token = generate_token()
    onboarding_data["email_verify_token"] = verify_token
    user_repo.update(user.id, onboarding_data=onboarding_data)

    # Auto-login: issue tokens
    role_names = UserRoleRepository(db).get_roles_for_user(user.id)
    permission_names = UserRoleRepository(db).get_all_permissions_for_user(user.id)
    access_token = create_access_token(
        subject=str(user.id),
        extra_claims={
            "email": user.email,
            "roles": role_names,
            "permissions": permission_names,
            "org_id": org_id,
        },
    )
    refresh_token = create_refresh_token(subject=str(user.id))

    # Create session
    from authentication.models import Session as UserSession

    session = UserSession(
        user_id=user.id,
        refresh_token=refresh_token,
        expires_at=datetime.now(timezone.utc) + timedelta(days=7),
    )
    db.add(session)

    db.commit()

    return success_response(
        {
            "id": user.id,
            "email": user.email,
            "full_name": user.full_name,
            "organization_id": org_id,
            "onboarding_completed": False,
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
        },
        "Account created successfully",
    )


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


@router.post("/verify-email")
async def verify_email(
    request: VerifyEmailRequest,
    db: DbSession = Depends(get_db),
):
    """Verify a user's email using a verification token."""
    from authentication.repositories import UserRepository

    user_repo = UserRepository(db)
    # Search for user with matching verify token in onboarding_data
    from sqlalchemy import select
    from authentication.models import User

    users = db.execute(select(User).where(User.is_deleted == 0)).scalars().all()
    matched_user = None
    for u in users:
        data = u.onboarding_data or {}
        if data.get("email_verify_token") == request.token:
            matched_user = u
            break

    if not matched_user:
        raise HTTPException(status_code=400, detail="Invalid verification token")

    if matched_user.email_verified_at:
        return success_response(None, "Email already verified")

    service = AuthService(db)
    service.verify_email(matched_user.id)

    # Remove the verify token from onboarding_data
    data = matched_user.onboarding_data or {}
    data.pop("email_verify_token", None)
    user_repo.update(matched_user.id, onboarding_data=data)
    db.commit()

    return success_response(None, "Email verified successfully")


@router.get("/onboarding-status")
async def get_onboarding_status(
    current_user: dict = Depends(get_current_user),
    db: DbSession = Depends(get_db),
):
    """Check if the current user has completed onboarding."""
    from authentication.repositories import UserRepository

    user = UserRepository(db).get_by_id(current_user["id"])
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return success_response({
        "onboarding_completed": bool(user.onboarding_completed),
        "onboarding_data": user.onboarding_data or {},
    })


@router.post("/onboarding")
async def complete_onboarding(
    request: OnboardingRequest,
    current_user: dict = Depends(get_current_user),
    db: DbSession = Depends(get_db),
):
    """Save onboarding selections and mark onboarding as complete."""
    from authentication.repositories import UserRepository

    user_repo = UserRepository(db)
    user = user_repo.get_by_id(current_user["id"])
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Merge existing onboarding data with new data
    existing = user.onboarding_data or {}
    if request.industry:
        existing["industry"] = request.industry
    if request.organization_type:
        existing["organization_type"] = request.organization_type
    if request.primary_goal:
        existing["primary_goal"] = request.primary_goal
    if request.country:
        existing["country"] = request.country
    existing["skip_dataset"] = request.skip_dataset

    user_repo.update(
        user.id,
        onboarding_data=existing,
        onboarding_completed=1,
    )
    db.commit()

    return success_response(
        {"onboarding_completed": True, "onboarding_data": existing},
        "Onboarding complete",
    )


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

users_router = APIRouter(prefix="/api/users", tags=["User Management"])


@users_router.get("")
async def list_users(
    page: int = 1,
    page_size: int = 20,
    current_user: dict = Depends(require_permissions("users.read")),
    db: DbSession = Depends(get_db),
):
    """List users (requires users.read permission). Super admins see all; others see only their org."""
    service = UserService(db)
    if is_super_admin(current_user):
        result = service.list_users(page, page_size)
    else:
        org_id = get_current_organization_id(current_user, db)
        result = service.list_users_by_org(org_id, page, page_size)
    return success_response(result)


@users_router.post("")
async def create_user(
    request: UserCreate,
    current_user: dict = Depends(require_permissions("users.create")),
    db: DbSession = Depends(get_db),
):
    """Create a new user (requires users.create permission)."""
    if not is_super_admin(current_user):
        org_id = get_current_organization_id(current_user, db)
        if request.organization_id and request.organization_id != org_id:
            raise HTTPException(status_code=403, detail="Cannot create users outside your organization")
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
    if not is_super_admin(current_user):
        org_id = get_current_organization_id(current_user, db)
        if user_model.organization_id != org_id:
            raise HTTPException(status_code=403, detail="Access to this user is not permitted")
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
    user_model = service.user_repo.get_by_id(user_id)
    if not user_model:
        raise HTTPException(status_code=404, detail="User not found")
    if not is_super_admin(current_user):
        org_id = get_current_organization_id(current_user, db)
        if user_model.organization_id != org_id:
            raise HTTPException(status_code=403, detail="Access to this user is not permitted")
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
    user_model = service.user_repo.get_by_id(user_id)
    if not user_model:
        raise HTTPException(status_code=404, detail="User not found")
    if not is_super_admin(current_user):
        org_id = get_current_organization_id(current_user, db)
        if user_model.organization_id != org_id:
            raise HTTPException(status_code=403, detail="Access to this user is not permitted")
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
    user_model = service.user_repo.get_by_id(user_id)
    if not user_model:
        raise HTTPException(status_code=404, detail="User not found")
    if not is_super_admin(current_user):
        org_id = get_current_organization_id(current_user, db)
        if user_model.organization_id != org_id:
            raise HTTPException(status_code=403, detail="Access to this user is not permitted")
        if "super_admin" in role_names or "org_owner" in role_names:
            raise HTTPException(status_code=403, detail="Cannot assign platform-level roles")
    service.assign_roles(user_id, role_names, assigned_by=current_user["id"])
    return success_response(None, "Roles assigned")


# --- Role management endpoints ---------------------------------------------

roles_router = APIRouter(prefix="/api/roles", tags=["Role Management"])


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
