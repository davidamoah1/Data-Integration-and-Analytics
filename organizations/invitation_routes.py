"""FastAPI routes for invitation and registration v2 endpoints."""

# ruff: noqa: B008  # FastAPI Depends() calls in default arguments are intentional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session as DbSession

from organizations.invitation_schemas import (
    InvitationAccept,
    InvitationCreate,
    SignupV2Request,
)
from organizations.invitation_service import InvitationService, RegistrationService
from shared.database import get_db
from shared.dependencies import require_permissions
from shared.response import success_response
from shared.tenant import get_current_organization_id

invitation_router = APIRouter(prefix="/api/invitations", tags=["Invitations"])
registration_router = APIRouter(prefix="/api/auth", tags=["Authentication"])


# --- Registration v2 --------------------------------------------------------


@registration_router.post("/signup-v2")
async def signup_v2(request: SignupV2Request, db: DbSession = Depends(get_db)):
    """Enhanced signup supporting three registration modes.

    Modes:
      - create_organization: First user creates an org and becomes org_admin
      - join_organization: User accepts an invitation token
      - personal: User creates a personal workspace with viewer role
    """
    service = RegistrationService(db)
    result = service.register(request)
    return success_response(result, "Account created successfully")


# --- Invitation endpoints ---------------------------------------------------


@invitation_router.get("/info/{token}")
async def get_invitation_info(token: str, db: DbSession = Depends(get_db)):
    """Get invitation details by token (public — used by invitation landing page)."""
    service = InvitationService(db)
    info = service.get_invitation_by_token(token)
    return success_response(info)


@invitation_router.post("/accept")
async def accept_invitation(
    request: InvitationAccept,
    db: DbSession = Depends(get_db),
):
    """Accept an invitation and create a new user account."""
    service = InvitationService(db)
    result = service.accept_invitation(request)
    return success_response(result, "Invitation accepted successfully")


@invitation_router.get("")
async def list_invitations(
    current_user: dict = Depends(require_permissions("users.read")),
    db: DbSession = Depends(get_db),
):
    """List all invitations for the current user's organization."""
    org_id = get_current_organization_id(current_user, db)
    if not org_id:
        raise HTTPException(status_code=400, detail="No organization associated with your account")
    service = InvitationService(db)
    invitations = service.list_invitations(org_id)
    return success_response(invitations)


@invitation_router.post("")
async def create_invitation(
    request: InvitationCreate,
    current_user: dict = Depends(require_permissions("users.manage")),
    db: DbSession = Depends(get_db),
):
    """Send an invitation to join the current user's organization."""
    org_id = get_current_organization_id(current_user, db)
    if not org_id:
        raise HTTPException(status_code=400, detail="No organization associated with your account")
    service = InvitationService(db)
    invitation = service.create_invitation(org_id, request, created_by=current_user["id"])
    return success_response(invitation, "Invitation sent")


@invitation_router.delete("/{invitation_id}")
async def revoke_invitation(
    invitation_id: int,
    current_user: dict = Depends(require_permissions("users.manage")),
    db: DbSession = Depends(get_db),
):
    """Revoke a pending invitation."""
    org_id = get_current_organization_id(current_user, db)
    if not org_id:
        raise HTTPException(status_code=400, detail="No organization associated with your account")
    service = InvitationService(db)
    service.revoke_invitation(invitation_id, org_id)
    return success_response(None, "Invitation revoked")
