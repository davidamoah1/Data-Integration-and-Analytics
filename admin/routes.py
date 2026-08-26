"""Enterprise admin panel API routes.

Provides organization management, user management, and system monitoring
endpoints for platform and organization administrators.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session as DbSession

from admin.service import AdminService
from audit.service import log_audit_event
from shared.database import get_db
from shared.dependencies import require_permissions
from shared.response import success_response

router = APIRouter(prefix="/api/admin", tags=["Admin Panel"])


class AssignRolesRequest(BaseModel):
    role_names: list[str]


class InviteUserRequest(BaseModel):
    email: str
    full_name: str
    organization_id: int | None = None
    role_names: list[str] = []


# --- Organization management -------------------------------------------------


@router.get("/organizations")
async def list_organizations(
    current_user: dict = Depends(require_permissions("admin.organizations.read")),
    db: DbSession = Depends(get_db),
):
    service = AdminService(db, current_user)
    return success_response(service.list_organizations())


@router.post("/organizations/{org_id}/suspend")
async def suspend_organization(
    org_id: int,
    current_user: dict = Depends(require_permissions("admin.organizations.manage")),
    db: DbSession = Depends(get_db),
):
    service = AdminService(db, current_user)
    result = service.suspend_organization(org_id)
    log_audit_event(
        db=db,
        action="admin.organization.suspend",
        user_id=current_user["id"],
        organization_id=org_id,
        resource_type="organization",
        resource_id=org_id,
    )
    db.commit()
    return success_response(result, "Organization suspended")


@router.post("/organizations/{org_id}/activate")
async def activate_organization(
    org_id: int,
    current_user: dict = Depends(require_permissions("admin.organizations.manage")),
    db: DbSession = Depends(get_db),
):
    service = AdminService(db, current_user)
    result = service.activate_organization(org_id)
    log_audit_event(
        db=db,
        action="admin.organization.activate",
        user_id=current_user["id"],
        organization_id=org_id,
        resource_type="organization",
        resource_id=org_id,
    )
    db.commit()
    return success_response(result, "Organization activated")


@router.get("/organizations/{org_id}/usage")
async def organization_usage(
    org_id: int,
    current_user: dict = Depends(require_permissions("admin.organizations.read")),
    db: DbSession = Depends(get_db),
):
    service = AdminService(db, current_user)
    return success_response(service.get_organization_usage(org_id))


# --- User management --------------------------------------------------------


@router.get("/users")
async def list_users(
    organization_id: int | None = None,
    current_user: dict = Depends(require_permissions("admin.users.read")),
    db: DbSession = Depends(get_db),
):
    service = AdminService(db, current_user)
    return success_response(service.list_users(organization_id))


@router.post("/users/{user_id}/disable")
async def disable_user(
    user_id: int,
    current_user: dict = Depends(require_permissions("admin.users.manage")),
    db: DbSession = Depends(get_db),
):
    service = AdminService(db, current_user)
    result = service.disable_user(user_id)
    log_audit_event(
        db=db,
        action="admin.user.disable",
        user_id=current_user["id"],
        organization_id=result.get("organization_id"),
        resource_type="user",
        resource_id=user_id,
    )
    db.commit()
    return success_response(result, "User disabled")


@router.post("/users/{user_id}/enable")
async def enable_user(
    user_id: int,
    current_user: dict = Depends(require_permissions("admin.users.manage")),
    db: DbSession = Depends(get_db),
):
    service = AdminService(db, current_user)
    result = service.enable_user(user_id)
    log_audit_event(
        db=db,
        action="admin.user.enable",
        user_id=current_user["id"],
        organization_id=result.get("organization_id"),
        resource_type="user",
        resource_id=user_id,
    )
    db.commit()
    return success_response(result, "User enabled")


@router.post("/users/{user_id}/roles")
async def assign_user_roles(
    user_id: int,
    request: AssignRolesRequest,
    current_user: dict = Depends(require_permissions("admin.users.manage")),
    db: DbSession = Depends(get_db),
):
    service = AdminService(db, current_user)
    result = service.assign_user_roles(user_id, request.role_names)
    log_audit_event(
        db=db,
        action="admin.user.roles.assign",
        user_id=current_user["id"],
        organization_id=result.get("organization_id"),
        resource_type="user",
        resource_id=user_id,
        new_values={"role_names": request.role_names},
    )
    db.commit()
    return success_response(result, "Roles assigned")


# --- System monitoring -------------------------------------------------------


@router.get("/metrics")
async def system_metrics(
    current_user: dict = Depends(require_permissions("admin.metrics.read")),
    db: DbSession = Depends(get_db),
):
    service = AdminService(db, current_user)
    return success_response(service.get_system_metrics())
