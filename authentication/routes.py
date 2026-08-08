"""FastAPI routes for authentication and user management.

All endpoints use standard response format and proper permission checks.
"""

# ruff: noqa: B008  # FastAPI Depends() calls in default arguments are intentional

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session as DbSession

from audit.models import AuditLog
from audit.service import log_audit_event
from authentication.mfa_service import MFAService
from authentication.models import ActivityLog
from authentication.schemas import (
    AccountStatusUpdate,
    ChangePasswordRequest,
    ForgotPasswordRequest,
    LoginRequest,
    MFADisableRequest,
    MFALoginRequest,
    MFAVerifyRequest,
    OnboardingRequest,
    PermissionCheckRequest,
    ProfileUpdate,
    RefreshTokenRequest,
    ResendVerificationRequest,
    ResetPasswordRequest,
    RoleCreate,
    RoleUpdate,
    ScopedRoleAssign,
    SignupRequest,
    SSOCallbackRequest,
    SSOConnectionCreate,
    SSOInitiateRequest,
    UserCreate,
    UserUpdate,
    VerifyEmailRequest,
)
from authentication.services import AuthService, RoleService, UserService
from authentication.sso_service import SSOService
from shared.database import get_db
from shared.dependencies import get_current_user, require_permissions
from shared.response import success_response
from shared.security import create_access_token, create_refresh_token, verify_password
from shared.tenant import get_current_organization_id, is_super_admin

router = APIRouter(prefix="/api/auth", tags=["Authentication"])

# MFA router
mfa_router = APIRouter(prefix="/api/auth/mfa", tags=["MFA"])

# SSO router
sso_router = APIRouter(prefix="/api/auth/sso", tags=["SSO"])


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
    from authentication.repositories import RoleRepository, UserRepository, UserRoleRepository
    from authentication.services import validate_password
    from organizations.models import Organization
    from shared.security import (
        create_access_token,
        create_refresh_token,
        generate_token,
        hash_password,
    )

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
    if org_id:
        db.add(
            AuditLog(
                user_id=user.id,
                organization_id=org_id,
                action="organization.created",
                resource_type="organization",
                resource_id=org_id,
                new_values={"name": request.organization_name},
            )
        )
        db.add(
            AuditLog(
                user_id=user.id,
                organization_id=org_id,
                action="role.assigned",
                resource_type="user",
                resource_id=user.id,
                new_values={"role": assigned_role.name if assigned_role else "viewer"},
            )
        )
    db.add(
        AuditLog(
            user_id=user.id,
            organization_id=org_id,
            action="user.registered",
            resource_type="user",
            resource_id=user.id,
            new_values={
                "email": user.email,
                "mode": "create_organization" if org_id else "personal",
            },
        )
    )

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


@router.post("/resend-verification")
async def resend_verification(
    request: ResendVerificationRequest,
    db: DbSession = Depends(get_db),
):
    """Resend email verification token."""
    service = AuthService(db)
    service.resend_email_verification(request.email)
    return success_response(
        None, "If the email exists and is not verified, a verification link has been sent"
    )


@router.post("/activate/{user_id}")
async def activate_account(
    user_id: int,
    request: AccountStatusUpdate,
    current_user: dict = Depends(require_permissions("users.edit")),
    db: DbSession = Depends(get_db),
):
    """Activate a deactivated user account (requires users.edit permission)."""
    service = AuthService(db)
    service.activate_account(user_id, reason=request.reason, activated_by=current_user["id"])
    return success_response(None, "Account activated")


@router.post("/deactivate/{user_id}")
async def deactivate_account(
    user_id: int,
    request: AccountStatusUpdate,
    current_user: dict = Depends(require_permissions("users.edit")),
    db: DbSession = Depends(get_db),
):
    """Deactivate a user account (requires users.edit permission)."""
    service = AuthService(db)
    service.deactivate_account(user_id, reason=request.reason, deactivated_by=current_user["id"])
    return success_response(None, "Account deactivated")


# --- MFA endpoints ----------------------------------------------------------


@mfa_router.get("/status")
async def get_mfa_status(
    current_user: dict = Depends(get_current_user),
    db: DbSession = Depends(get_db),
):
    """Get MFA status for the current user."""
    service = MFAService(db)
    status = service.get_status(current_user["id"])
    return success_response(status)


@mfa_router.post("/setup")
async def setup_mfa(
    current_user: dict = Depends(get_current_user),
    db: DbSession = Depends(get_db),
):
    """Begin MFA setup — generates TOTP secret and backup codes."""
    service = MFAService(db)
    result = service.setup(current_user["id"])
    return success_response(result, "MFA setup initiated. Verify with a code to enable.")


@mfa_router.post("/verify")
async def verify_mfa(
    request: MFAVerifyRequest,
    current_user: dict = Depends(get_current_user),
    db: DbSession = Depends(get_db),
):
    """Verify MFA setup code and enable MFA."""
    service = MFAService(db)
    service.verify_and_enable(current_user["id"], request.code)
    return success_response(None, "MFA enabled successfully")


@mfa_router.post("/disable")
async def disable_mfa(
    request: MFADisableRequest,
    current_user: dict = Depends(get_current_user),
    db: DbSession = Depends(get_db),
):
    """Disable MFA for the current user. Requires a valid TOTP code."""
    service = MFAService(db)
    service.disable(current_user["id"], request.code)
    return success_response(None, "MFA disabled")


@mfa_router.post("/login-challenge")
async def mfa_login_challenge(
    request: LoginRequest,
    db: DbSession = Depends(get_db),
):
    """Step 1 of MFA login: verify credentials, return MFA challenge if enabled.

    If MFA is not enabled, returns tokens directly (standard login).
    """
    auth_service = AuthService(db)
    mfa_service = MFAService(db)

    # First verify credentials without issuing tokens
    user = auth_service.user_repo.get_by_email(request.email)
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    if auth_service.user_repo.is_locked(user.id):
        raise HTTPException(status_code=423, detail="Account is locked")
    if not verify_password(request.password, user.password_hash):
        count = auth_service.user_repo.increment_failed_login(user.id)
        db.commit()
        if count >= 5:
            raise HTTPException(status_code=423, detail="Account is locked")
        raise HTTPException(status_code=401, detail="Invalid email or password")

    # Check if MFA is enabled
    if mfa_service.is_mfa_enabled(user.id):
        challenge_token = mfa_service.create_challenge(user.id)
        return success_response(
            {
                "mfa_required": True,
                "challenge_token": challenge_token,
                "method": "totp",
            },
            "MFA verification required",
        )

    # MFA not enabled — proceed with standard login
    result = auth_service.login(request, ip=None, user_agent=None)
    result["mfa_required"] = False
    return success_response(result, "Login successful")


@mfa_router.post("/login-verify")
async def mfa_login_verify(
    request: MFALoginRequest,
    req: Request,
    db: DbSession = Depends(get_db),
):
    """Step 2 of MFA login: verify TOTP code and issue tokens."""
    mfa_service = MFAService(db)
    auth_service = AuthService(db)

    result = mfa_service.verify_challenge(request.challenge_token, request.code)
    user_id = result["user_id"]

    # Reset failed logins and update last login
    auth_service.user_repo.reset_failed_logins(user_id)
    auth_service.user_repo.update_last_login(user_id)

    # Get roles and permissions
    role_names = auth_service.user_role_repo.get_roles_for_user(user_id)
    permission_names = auth_service.user_role_repo.get_all_permissions_for_user(user_id)
    user = auth_service.user_repo.get_by_id(user_id)

    ip = req.client.host if req.client else None
    ua = req.headers.get("user-agent")

    # Create tokens
    access_token = create_access_token(
        subject=str(user_id),
        extra_claims={
            "email": user.email,
            "roles": role_names,
            "permissions": permission_names,
            "org_id": user.organization_id,
        },
    )
    refresh_token = create_refresh_token(subject=str(user_id))

    # Store session
    from authentication.models import Session as UserSession

    session = UserSession(
        user_id=user_id,
        refresh_token=refresh_token,
        ip_address=ip,
        user_agent=ua,
        device=auth_service._parse_device(ua),
        expires_at=datetime.now(timezone.utc) + timedelta(days=7),
    )
    auth_service.session_repo.create(session)

    # Log activity
    auth_service.activity_repo.create(
        ActivityLog(
            user_id=user_id,
            action="login_mfa",
            ip_address=ip,
            user_agent=ua,
        )
    )

    db.commit()

    return success_response(
        {
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
        "Login successful",
    )


# --- SSO endpoints ----------------------------------------------------------


@sso_router.get("/providers")
async def list_sso_providers(
    current_user: dict = Depends(get_current_user),
    db: DbSession = Depends(get_db),
):
    """List available SSO providers for the user's organization."""
    service = SSOService(db)
    org_id = current_user.get("org_id")
    if not org_id:
        return success_response([], "No organization configured")
    providers = service.list_connections(org_id)
    return success_response(providers)


@sso_router.post("/initiate")
async def initiate_sso(
    request: SSOInitiateRequest,
    db: DbSession = Depends(get_db),
):
    """Initiate SSO login flow."""
    service = SSOService(db)
    result = service.initiate(request.provider, request.redirect_url)
    return success_response(result, "SSO flow initiated")


@sso_router.post("/callback")
async def sso_callback(
    request: SSOCallbackRequest,
    db: DbSession = Depends(get_db),
):
    """Handle SSO provider callback."""
    service = SSOService(db)
    result = service.handle_callback(
        provider=request.provider,
        code=request.code,
        state=request.state,
        saml_response=request.saml_response,
    )
    return success_response(result, "SSO login successful")


@sso_router.post("/connections")
async def create_sso_connection(
    request: SSOConnectionCreate,
    current_user: dict = Depends(require_permissions("organization.manage")),
    db: DbSession = Depends(get_db),
):
    """Configure an SSO provider for the organization."""
    service = SSOService(db)
    org_id = get_current_organization_id(current_user, db)
    conn = service.create_connection(
        org_id=org_id,
        provider=request.provider,
        client_id=request.client_id,
        client_secret=request.client_secret,
        metadata_url=request.metadata_url,
        scopes=request.scopes,
        field_mapping=request.field_mapping,
    )
    return success_response(conn, "SSO connection created")


@sso_router.get("/identities")
async def list_sso_identities(
    current_user: dict = Depends(get_current_user),
    db: DbSession = Depends(get_db),
):
    """List SSO identities linked to the current user."""
    service = SSOService(db)
    identities = service.get_user_sso_identities(current_user["id"])
    return success_response(identities)


@sso_router.delete("/identities/{provider}")
async def unlink_sso_identity(
    provider: str,
    current_user: dict = Depends(get_current_user),
    db: DbSession = Depends(get_db),
):
    """Unlink an SSO identity from the current user."""
    service = SSOService(db)
    service.unlink_identity(current_user["id"], provider)
    return success_response(None, "SSO identity unlinked")


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
    return success_response(
        {
            "onboarding_completed": bool(user.onboarding_completed),
            "onboarding_data": user.onboarding_data or {},
        }
    )


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


@router.get("/navigation")
async def get_navigation(
    current_user: dict = Depends(get_current_user),
    db: DbSession = Depends(get_db),
):
    """Get role-aware navigation configuration for the current user.

    Returns navigation groups with items filtered by:
    - Role (platform owner, org admin, analyst, researcher, data entry, viewer)
    - Permissions
    - Organization type and industry
    - Workspace type (organization vs personal)
    """
    service = AuthService(db)
    profile = service.get_profile(current_user["id"])

    roles = profile.get("roles", [])
    permissions = profile.get("permissions", [])
    org_type = profile.get("organization_type")
    industry = profile.get("industry")
    org_id = profile.get("organization_id")
    dept_id = profile.get("department_id")

    is_super_admin = "super_admin" in roles or "platform_owner" in roles

    ROLE_NAVIGATION: dict[str, dict] = {
        "super_admin": {
            "purpose": "Operate the platform",
            "groups": [
                {
                    "label": "Platform",
                    "order": 0,
                    "items": [
                        {
                            "label": "Dashboard",
                            "href": "/dashboard",
                            "icon": "LayoutDashboard",
                            "order": 0,
                        },
                        {
                            "label": "Organizations",
                            "href": "/admin-portal/organizations",
                            "icon": "Building2",
                            "order": 1,
                        },
                        {
                            "label": "Platform Analytics",
                            "href": "/admin-portal/analytics",
                            "icon": "TrendingUp",
                            "order": 2,
                        },
                        {
                            "label": "Monitoring",
                            "href": "/admin-portal/monitoring",
                            "icon": "Activity",
                            "order": 3,
                        },
                        {
                            "label": "Security",
                            "href": "/admin-portal/security",
                            "icon": "Shield",
                            "order": 4,
                        },
                    ],
                },
                {
                    "label": "Administration",
                    "order": 1,
                    "items": [
                        {
                            "label": "Admin Portal",
                            "href": "/admin-portal",
                            "icon": "Crown",
                            "order": 0,
                        },
                        {"label": "Members", "href": "/admin", "icon": "Users", "order": 1},
                        {"label": "Audit Logs", "href": "/audit", "icon": "ScrollText", "order": 2},
                        {
                            "label": "Feature Flags",
                            "href": "/admin-portal/feature-flags",
                            "icon": "Zap",
                            "order": 3,
                        },
                        {
                            "label": "Platform Settings",
                            "href": "/admin-portal/settings",
                            "icon": "Server",
                            "order": 4,
                        },
                    ],
                },
                {
                    "label": "Platform Tools",
                    "order": 2,
                    "items": [
                        {"label": "Studios", "href": "/studios", "icon": "Sparkles", "order": 0},
                        {
                            "label": "Templates",
                            "href": "/templates",
                            "icon": "LayoutTemplate",
                            "order": 1,
                        },
                        {"label": "Connectors", "href": "/connectors", "icon": "Zap", "order": 2},
                        {
                            "label": "Marketplace",
                            "href": "/marketplace",
                            "icon": "Package",
                            "order": 3,
                        },
                        {"label": "API Keys", "href": "/api-keys", "icon": "Key", "order": 4},
                        {"label": "Webhooks", "href": "/webhooks", "icon": "Webhook", "order": 5},
                        {
                            "label": "Subscriptions",
                            "href": "/admin-portal/subscriptions",
                            "icon": "CreditCard",
                            "order": 6,
                        },
                        {"label": "Billing", "href": "/billing", "icon": "CreditCard", "order": 7},
                    ],
                },
                {
                    "label": "System",
                    "order": 3,
                    "items": [
                        {
                            "label": "Notifications",
                            "href": "/notifications",
                            "icon": "Bell",
                            "order": 0,
                        },
                        {"label": "Settings", "href": "/settings", "icon": "Settings", "order": 1},
                    ],
                },
            ],
        },
        "org_owner": {
            "purpose": "Own and operate their organization",
            "groups": [
                {
                    "label": "Overview",
                    "order": 0,
                    "items": [
                        {
                            "label": "Dashboard",
                            "href": "/dashboard",
                            "icon": "LayoutDashboard",
                            "order": 0,
                        },
                        {
                            "label": "Dashboards",
                            "href": "/dashboard",
                            "icon": "LayoutDashboard",
                            "permission": "dashboard.view",
                            "order": 1,
                        },
                        {"label": "Studios", "href": "/studios", "icon": "Sparkles", "order": 2},
                        {
                            "label": "Templates",
                            "href": "/templates",
                            "icon": "LayoutTemplate",
                            "order": 3,
                        },
                    ],
                },
                {
                    "label": "Data",
                    "order": 1,
                    "items": [
                        {
                            "label": "Smart Data Capture",
                            "href": "/capture",
                            "icon": "ScanLine",
                            "order": 0,
                        },
                        {
                            "label": "Datasets",
                            "href": "/datasets",
                            "icon": "Database",
                            "permission": "datasets.view",
                            "order": 1,
                        },
                        {
                            "label": "Analytics",
                            "href": "/analytics",
                            "icon": "BarChart3",
                            "permission": "analytics.view",
                            "order": 2,
                        },
                        {
                            "label": "Reports",
                            "href": "/reports",
                            "icon": "FileText",
                            "permission": "reports.view",
                            "order": 3,
                        },
                    ],
                },
                {
                    "label": "Intelligence",
                    "order": 2,
                    "items": [
                        {
                            "label": "Analytics Assistant",
                            "href": "/ai",
                            "icon": "Bot",
                            "permission": "ai.use",
                            "order": 0,
                        },
                        {
                            "label": "Scheduler",
                            "href": "/scheduler",
                            "icon": "CalendarClock",
                            "order": 1,
                        },
                    ],
                },
                {
                    "label": "Administration",
                    "order": 3,
                    "items": [
                        {
                            "label": "Notifications",
                            "href": "/notifications",
                            "icon": "Bell",
                            "order": 0,
                        },
                        {
                            "label": "Members",
                            "href": "/admin",
                            "icon": "Users",
                            "permission": "users.read",
                            "order": 1,
                        },
                        {
                            "label": "Departments",
                            "href": "/admin/departments",
                            "icon": "Building2",
                            "permission": "departments.manage",
                            "order": 2,
                        },
                        {
                            "label": "Audit Logs",
                            "href": "/audit",
                            "icon": "ScrollText",
                            "permission": "audit.view",
                            "order": 3,
                        },
                        {
                            "label": "Organization Settings",
                            "href": "/settings",
                            "icon": "Settings",
                            "permission": "settings.manage",
                            "order": 4,
                        },
                    ],
                },
                {
                    "label": "Platform",
                    "order": 4,
                    "items": [
                        {"label": "Connectors", "href": "/connectors", "icon": "Zap", "order": 0},
                    ],
                },
            ],
        },
        "org_admin": {
            "purpose": "Operate their organization",
            "groups": [
                {
                    "label": "Overview",
                    "order": 0,
                    "items": [
                        {
                            "label": "Dashboard",
                            "href": "/dashboard",
                            "icon": "LayoutDashboard",
                            "order": 0,
                        },
                        {
                            "label": "Dashboards",
                            "href": "/dashboard",
                            "icon": "LayoutDashboard",
                            "permission": "dashboard.view",
                            "order": 1,
                        },
                        {"label": "Studios", "href": "/studios", "icon": "Sparkles", "order": 2},
                        {
                            "label": "Templates",
                            "href": "/templates",
                            "icon": "LayoutTemplate",
                            "order": 3,
                        },
                    ],
                },
                {
                    "label": "Data",
                    "order": 1,
                    "items": [
                        {
                            "label": "Smart Data Capture",
                            "href": "/capture",
                            "icon": "ScanLine",
                            "order": 0,
                        },
                        {
                            "label": "Datasets",
                            "href": "/datasets",
                            "icon": "Database",
                            "permission": "datasets.view",
                            "order": 1,
                        },
                        {
                            "label": "Analytics",
                            "href": "/analytics",
                            "icon": "BarChart3",
                            "permission": "analytics.view",
                            "order": 2,
                        },
                        {
                            "label": "Reports",
                            "href": "/reports",
                            "icon": "FileText",
                            "permission": "reports.view",
                            "order": 3,
                        },
                    ],
                },
                {
                    "label": "Intelligence",
                    "order": 2,
                    "items": [
                        {
                            "label": "Analytics Assistant",
                            "href": "/ai",
                            "icon": "Bot",
                            "permission": "ai.use",
                            "order": 0,
                        },
                        {
                            "label": "Scheduler",
                            "href": "/scheduler",
                            "icon": "CalendarClock",
                            "order": 1,
                        },
                    ],
                },
                {
                    "label": "Administration",
                    "order": 3,
                    "items": [
                        {
                            "label": "Notifications",
                            "href": "/notifications",
                            "icon": "Bell",
                            "order": 0,
                        },
                        {
                            "label": "Members",
                            "href": "/admin",
                            "icon": "Users",
                            "permission": "users.read",
                            "order": 1,
                        },
                        {
                            "label": "Departments",
                            "href": "/admin/departments",
                            "icon": "Building2",
                            "permission": "departments.manage",
                            "order": 2,
                        },
                        {
                            "label": "Audit Logs",
                            "href": "/audit",
                            "icon": "ScrollText",
                            "permission": "audit.view",
                            "order": 3,
                        },
                        {
                            "label": "Organization Settings",
                            "href": "/settings",
                            "icon": "Settings",
                            "permission": "settings.manage",
                            "order": 4,
                        },
                    ],
                },
                {
                    "label": "Platform",
                    "order": 4,
                    "items": [
                        {"label": "Connectors", "href": "/connectors", "icon": "Zap", "order": 0},
                    ],
                },
            ],
        },
        "data_analyst": {
            "purpose": "Prepare and analyze data",
            "groups": [
                {
                    "label": "Overview",
                    "order": 0,
                    "items": [
                        {
                            "label": "Dashboard",
                            "href": "/dashboard",
                            "icon": "LayoutDashboard",
                            "order": 0,
                        },
                        {
                            "label": "Dashboards",
                            "href": "/dashboard",
                            "icon": "LayoutDashboard",
                            "permission": "dashboard.view",
                            "order": 1,
                        },
                        {
                            "label": "Templates",
                            "href": "/templates",
                            "icon": "LayoutTemplate",
                            "order": 2,
                        },
                    ],
                },
                {
                    "label": "Analytics Studio",
                    "order": 1,
                    "items": [
                        {
                            "label": "Datasets",
                            "href": "/datasets",
                            "icon": "Database",
                            "permission": "datasets.view",
                            "order": 0,
                        },
                        {
                            "label": "Analytics",
                            "href": "/analytics",
                            "icon": "BarChart3",
                            "permission": "analytics.view",
                            "order": 1,
                        },
                        {
                            "label": "Reports",
                            "href": "/reports",
                            "icon": "FileText",
                            "permission": "reports.view",
                            "order": 2,
                        },
                    ],
                },
                {
                    "label": "Intelligence",
                    "order": 2,
                    "items": [
                        {
                            "label": "Analytics Assistant",
                            "href": "/ai",
                            "icon": "Bot",
                            "permission": "ai.use",
                            "order": 0,
                        },
                        {
                            "label": "Scheduler",
                            "href": "/scheduler",
                            "icon": "CalendarClock",
                            "order": 1,
                        },
                    ],
                },
                {
                    "label": "Personal",
                    "order": 3,
                    "items": [
                        {
                            "label": "Notifications",
                            "href": "/notifications",
                            "icon": "Bell",
                            "order": 0,
                        },
                        {"label": "Profile", "href": "/settings", "icon": "Settings", "order": 99},
                    ],
                },
            ],
        },
        "researcher": {
            "purpose": "Research and statistical analysis",
            "groups": [
                {
                    "label": "Overview",
                    "order": 0,
                    "items": [
                        {
                            "label": "Dashboard",
                            "href": "/dashboard",
                            "icon": "LayoutDashboard",
                            "order": 0,
                        },
                        {
                            "label": "Templates",
                            "href": "/templates",
                            "icon": "LayoutTemplate",
                            "order": 1,
                        },
                    ],
                },
                {
                    "label": "Research",
                    "order": 1,
                    "items": [
                        {
                            "label": "Research Studio",
                            "href": "/studios/research",
                            "icon": "FlaskConical",
                            "order": 0,
                        },
                        {
                            "label": "Statistics",
                            "href": "/studios/statistics",
                            "icon": "BarChart3",
                            "order": 1,
                        },
                        {
                            "label": "Publications",
                            "href": "/studios/publications",
                            "icon": "Newspaper",
                            "order": 2,
                        },
                        {
                            "label": "Reports",
                            "href": "/reports",
                            "icon": "FileText",
                            "permission": "reports.view",
                            "order": 3,
                        },
                        {
                            "label": "Datasets",
                            "href": "/datasets",
                            "icon": "Database",
                            "permission": "datasets.view",
                            "order": 4,
                        },
                    ],
                },
                {
                    "label": "Intelligence",
                    "order": 2,
                    "items": [
                        {
                            "label": "Analytics Assistant",
                            "href": "/ai",
                            "icon": "Bot",
                            "permission": "ai.use",
                            "order": 0,
                        },
                        {
                            "label": "Scheduler",
                            "href": "/scheduler",
                            "icon": "CalendarClock",
                            "order": 1,
                        },
                    ],
                },
                {
                    "label": "Personal",
                    "order": 3,
                    "items": [
                        {
                            "label": "Notifications",
                            "href": "/notifications",
                            "icon": "Bell",
                            "order": 0,
                        },
                        {"label": "Profile", "href": "/settings", "icon": "Settings", "order": 99},
                    ],
                },
            ],
        },
        "data_entry_officer": {
            "purpose": "Capture and validate data",
            "groups": [
                {
                    "label": "Capture",
                    "order": 0,
                    "items": [
                        {
                            "label": "Smart Data Capture",
                            "href": "/capture",
                            "icon": "ScanLine",
                            "order": 0,
                        },
                        {
                            "label": "Capture Queue",
                            "href": "/capture/queue",
                            "icon": "ClipboardList",
                            "order": 1,
                        },
                        {
                            "label": "Assigned Tasks",
                            "href": "/capture/tasks",
                            "icon": "CheckSquare",
                            "order": 2,
                        },
                        {
                            "label": "Validation",
                            "href": "/capture/review",
                            "icon": "CheckSquare",
                            "order": 3,
                        },
                    ],
                },
                {
                    "label": "Personal",
                    "order": 1,
                    "items": [
                        {
                            "label": "Notifications",
                            "href": "/notifications",
                            "icon": "Bell",
                            "order": 0,
                        },
                        {"label": "Profile", "href": "/settings", "icon": "Settings", "order": 99},
                    ],
                },
            ],
        },
        "viewer": {
            "purpose": "Consume information",
            "groups": [
                {
                    "label": "View",
                    "order": 0,
                    "items": [
                        {
                            "label": "Dashboards",
                            "href": "/dashboard",
                            "icon": "LayoutDashboard",
                            "permission": "dashboard.view",
                            "order": 0,
                        },
                        {
                            "label": "Reports",
                            "href": "/reports",
                            "icon": "FileText",
                            "permission": "reports.view",
                            "order": 1,
                        },
                    ],
                },
                {
                    "label": "Personal",
                    "order": 1,
                    "items": [
                        {
                            "label": "Notifications",
                            "href": "/notifications",
                            "icon": "Bell",
                            "order": 0,
                        },
                        {"label": "Profile", "href": "/settings", "icon": "Settings", "order": 99},
                    ],
                },
            ],
        },
    }

    DEFAULT_NAV = {
        "purpose": "Access the platform",
        "groups": [
            {
                "label": "Overview",
                "order": 0,
                "items": [
                    {
                        "label": "Dashboard",
                        "href": "/dashboard",
                        "icon": "LayoutDashboard",
                        "order": 0,
                    },
                ],
            },
            {
                "label": "Personal",
                "order": 1,
                "items": [
                    {
                        "label": "Notifications",
                        "href": "/notifications",
                        "icon": "Bell",
                        "order": 0,
                    },
                    {"label": "Profile", "href": "/settings", "icon": "Settings", "order": 99},
                ],
            },
        ],
    }

    ROLE_PRIORITY = [
        "super_admin",
        "org_owner",
        "org_admin",
        "dept_manager",
        "auditor",
        "data_engineer",
        "data_analyst",
        "researcher",
        "business_analyst",
        "executive",
        "dept_officer",
        "data_entry_officer",
        "viewer",
    ]

    primary_role = next((r for r in ROLE_PRIORITY if r in roles), roles[0] if roles else "viewer")
    nav_config = ROLE_NAVIGATION.get(primary_role, DEFAULT_NAV)

    def _has_perm(perm: str | None) -> bool:
        if not perm:
            return True
        if is_super_admin:
            return True
        return perm in permissions

    filtered_groups = []
    for grp in nav_config["groups"]:
        filtered_items = [item for item in grp["items"] if _has_perm(item.get("permission"))]
        filtered_items.sort(key=lambda x: x.get("order", 99))
        if filtered_items:
            filtered_groups.append(
                {
                    "label": grp["label"],
                    "order": grp.get("order", 0),
                    "items": filtered_items,
                }
            )

    if industry in ("healthcare", "education"):
        industry_item = {
            "healthcare": {
                "label": "Healthcare Studio",
                "href": "/studios/healthcare",
                "icon": "Stethoscope",
                "order": 10,
            },
            "education": {
                "label": "Education Studio",
                "href": "/studios/education",
                "icon": "GraduationCap",
                "order": 10,
            },
        }[industry]
        for grp in filtered_groups:
            if grp["label"] in ("Overview", "Platform Tools"):
                grp["items"].append(industry_item)
                grp["items"].sort(key=lambda x: x.get("order", 99))

    workspace_type = "organization" if org_id else "personal"
    if workspace_type == "personal":
        filtered_groups = [
            {**g, "items": [i for i in g["items"] if not i.get("role")]}
            for g in filtered_groups
            if g["label"] not in ("Administration", "Platform", "Platform Tools")
        ]
        filtered_groups = [g for g in filtered_groups if g["items"]]

    return success_response(
        {
            "purpose": nav_config["purpose"],
            "primary_role": primary_role,
            "groups": filtered_groups,
            "context": {
                "roles": roles,
                "permissions": permissions,
                "organization_type": org_type,
                "industry": industry,
                "workspace_type": workspace_type,
                "department_id": dept_id,
            },
        }
    )


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
            raise HTTPException(
                status_code=403, detail="Cannot create users outside your organization"
            )
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
    current_user: dict = Depends(require_permissions("role.assign")),
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
    log_audit_event(
        db=db,
        action="user.roles.assign",
        user_id=current_user["id"],
        organization_id=user_model.organization_id,
        resource_type="user",
        resource_id=user_id,
        metadata={"roles": role_names, "target_user": user_model.email},
    )
    db.commit()
    return success_response(None, "Roles assigned")


# --- Role management endpoints ---------------------------------------------

roles_router = APIRouter(prefix="/api/roles", tags=["Role Management"])


@roles_router.get("")
async def list_roles(
    current_user: dict = Depends(require_permissions("role.read")),
    db: DbSession = Depends(get_db),
):
    """List all roles with their permissions."""
    service = RoleService(db)
    roles = service.list_roles()
    return success_response(roles)


@roles_router.post("")
async def create_role(
    request: RoleCreate,
    current_user: dict = Depends(require_permissions("role.manage")),
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
    current_user: dict = Depends(require_permissions("role.manage")),
    db: DbSession = Depends(get_db),
):
    """Update a role."""
    service = RoleService(db)
    role = service.update_role(role_id, request)
    log_audit_event(
        db=db,
        action="role.update",
        user_id=current_user["id"],
        organization_id=current_user.get("organization_id"),
        resource_type="role",
        resource_id=role_id,
        new_values=role,
    )
    db.commit()
    return success_response(role, "Role updated")


@roles_router.delete("/{role_id}")
async def delete_role(
    role_id: int,
    current_user: dict = Depends(require_permissions("role.manage")),
    db: DbSession = Depends(get_db),
):
    """Delete a role (system roles cannot be deleted)."""
    service = RoleService(db)
    service.delete_role(role_id)
    log_audit_event(
        db=db,
        action="role.delete",
        user_id=current_user["id"],
        organization_id=current_user.get("organization_id"),
        resource_type="role",
        resource_id=role_id,
    )
    db.commit()
    return success_response(None, "Role deleted")


@roles_router.get("/permissions")
async def list_permissions(
    current_user: dict = Depends(require_permissions("role.read")),
    db: DbSession = Depends(get_db),
):
    """List all available permissions."""
    service = RoleService(db)
    perms = service.list_permissions()
    return success_response(perms)


# ─── Enterprise RBAC Routes ──────────────────────────────────────────


@roles_router.get("/level/{level}")
async def list_roles_by_level(
    level: str,
    current_user: dict = Depends(require_permissions("role.read")),
    db: DbSession = Depends(get_db),
):
    """List all roles at a specific level (platform, organization, department, personal)."""
    service = RoleService(db)
    roles = service.list_roles_by_level(level)
    return success_response(roles)


@roles_router.get("/assignable")
async def list_assignable_roles(
    current_user: dict = Depends(require_permissions("role.read")),
    db: DbSession = Depends(get_db),
):
    """List all roles that can be assigned to users."""
    service = RoleService(db)
    roles = service.list_assignable_roles()
    return success_response(roles)


@roles_router.post("/assign-scoped")
async def assign_scoped_role(
    request: ScopedRoleAssign,
    current_user: dict = Depends(require_permissions("role.assign")),
    db: DbSession = Depends(get_db),
):
    """Assign a role to a user with optional scope (organization, department, resource)."""
    service = RoleService(db)
    result = service.assign_scoped_role(request, assigned_by=current_user["id"])
    return success_response(result, "Scoped role assigned")


@users_router.get("/{user_id}/permissions")
async def get_user_permissions(
    user_id: int,
    current_user: dict = Depends(require_permissions("role.read")),
    db: DbSession = Depends(get_db),
):
    """Get a user's roles, permissions, and scoped role assignments."""
    service = RoleService(db)
    result = service.get_user_permissions(user_id)
    return success_response(result)


@users_router.post("/{user_id}/check-permission")
async def check_user_permission(
    user_id: int,
    request: PermissionCheckRequest,
    current_user: dict = Depends(require_permissions("role.read")),
    db: DbSession = Depends(get_db),
):
    """Check if a user has a specific permission."""
    service = RoleService(db)
    result = service.check_permission(
        user_id=user_id,
        permission=request.permission,
        scope_type=request.scope_type,
        scope_id=request.scope_id,
        resource_type=request.resource_type,
        resource_id=request.resource_id,
    )
    return success_response(result)
