"""Services and routes for organization management."""

from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, update, func
from sqlalchemy.orm import Session as DbSession

from shared.database import get_db
from shared.dependencies import get_current_user, require_permissions
from shared.response import success_response
from shared.exceptions import NotFoundError, ConflictError
from organizations.models import Organization, Branch, Department, Team
from organizations.schemas import (
    OrganizationCreate, OrganizationUpdate, OrganizationResponse,
    DepartmentCreate, DepartmentUpdate, DepartmentResponse,
    BranchCreate, BranchResponse,
)


class OrganizationService:
    def __init__(self, db: DbSession):
        self.db = db

    def create_org(self, request: OrganizationCreate) -> dict:
        existing = self.db.execute(
            select(Organization).where(Organization.slug == request.slug)
        ).scalar_one_or_none()
        if existing:
            raise ConflictError("Organization with this slug already exists")
        org = Organization(**request.model_dump())
        self.db.add(org)
        self.db.flush()
        self.db.commit()
        return self._org_to_dict(org)

    def update_org(self, org_id: int, request: OrganizationUpdate) -> dict:
        org = self._get_org(org_id)
        if not org:
            raise NotFoundError("Organization not found")
        kwargs = {k: v for k, v in request.model_dump().items() if v is not None}
        if kwargs:
            self.db.execute(
                update(Organization).where(Organization.id == org_id).values(**kwargs)
            )
            self.db.flush()
        self.db.commit()
        return self._org_to_dict(self._get_org(org_id))

    def delete_org(self, org_id: int):
        org = self._get_org(org_id)
        if not org:
            raise NotFoundError("Organization not found")
        self.db.execute(
            update(Organization).where(Organization.id == org_id).values(
                is_deleted=1, deleted_at=datetime.now(timezone.utc), is_active=0
            )
        )
        self.db.commit()

    def list_orgs(self) -> list[dict]:
        orgs = self.db.execute(
            select(Organization).where(Organization.is_deleted == 0).order_by(Organization.id)
        ).scalars().all()
        return [self._org_to_dict(o) for o in orgs]

    def get_org(self, org_id: int) -> dict:
        org = self._get_org(org_id)
        if not org:
            raise NotFoundError("Organization not found")
        return self._org_to_dict(org)

    def _get_org(self, org_id: int) -> Optional[Organization]:
        return self.db.execute(
            select(Organization).where(
                Organization.id == org_id, Organization.is_deleted == 0
            )
        ).scalar_one_or_none()

    def _org_to_dict(self, org: Organization) -> dict:
        return {
            "id": org.id, "name": org.name, "slug": org.slug,
            "description": org.description, "logo_url": org.logo_url,
            "contact_email": org.contact_email, "contact_phone": org.contact_phone,
            "address": org.address, "is_active": bool(org.is_active),
            "created_at": org.created_at,
        }


class DepartmentService:
    def __init__(self, db: DbSession):
        self.db = db

    def create_dept(self, request: DepartmentCreate) -> dict:
        dept = Department(**request.model_dump())
        self.db.add(dept)
        self.db.flush()
        self.db.commit()
        return self._dept_to_dict(dept)

    def update_dept(self, dept_id: int, request: DepartmentUpdate) -> dict:
        dept = self._get_dept(dept_id)
        if not dept:
            raise NotFoundError("Department not found")
        kwargs = {k: v for k, v in request.model_dump().items() if v is not None}
        if kwargs:
            self.db.execute(
                update(Department).where(Department.id == dept_id).values(**kwargs)
            )
            self.db.flush()
        self.db.commit()
        return self._dept_to_dict(self._get_dept(dept_id))

    def delete_dept(self, dept_id: int):
        self.db.execute(
            update(Department).where(Department.id == dept_id).values(
                is_deleted=1, deleted_at=datetime.now(timezone.utc), is_active=0
            )
        )
        self.db.commit()

    def list_depts(self, org_id: int = None) -> list[dict]:
        query = select(Department).where(Department.is_deleted == 0)
        if org_id:
            query = query.where(Department.organization_id == org_id)
        depts = self.db.execute(query.order_by(Department.id)).scalars().all()
        return [self._dept_to_dict(d) for d in depts]

    def get_dept(self, dept_id: int) -> dict:
        dept = self._get_dept(dept_id)
        if not dept:
            raise NotFoundError("Department not found")
        return self._dept_to_dict(dept)

    def _get_dept(self, dept_id: int) -> Optional[Department]:
        return self.db.execute(
            select(Department).where(
                Department.id == dept_id, Department.is_deleted == 0
            )
        ).scalar_one_or_none()

    def _dept_to_dict(self, dept: Department) -> dict:
        return {
            "id": dept.id, "organization_id": dept.organization_id,
            "branch_id": dept.branch_id, "name": dept.name,
            "code": dept.code, "description": dept.description,
            "head_user_id": dept.head_user_id, "parent_id": dept.parent_id,
            "is_active": bool(dept.is_active), "created_at": dept.created_at,
        }


# --- Routers ----------------------------------------------------------------

org_router = APIRouter(prefix="/organizations", tags=["Organizations"])


@org_router.get("")
async def list_organizations(
    current_user: dict = Depends(get_current_user),
    db: DbSession = Depends(get_db),
):
    service = OrganizationService(db)
    return success_response(service.list_orgs())


@org_router.post("")
async def create_organization(
    request: OrganizationCreate,
    current_user: dict = Depends(require_permissions("organizations.manage")),
    db: DbSession = Depends(get_db),
):
    service = OrganizationService(db)
    org = service.create_org(request)
    return success_response(org, "Organization created")


@org_router.get("/{org_id}")
async def get_organization(
    org_id: int,
    current_user: dict = Depends(get_current_user),
    db: DbSession = Depends(get_db),
):
    service = OrganizationService(db)
    return success_response(service.get_org(org_id))


@org_router.put("/{org_id}")
async def update_organization(
    org_id: int,
    request: OrganizationUpdate,
    current_user: dict = Depends(require_permissions("organizations.manage")),
    db: DbSession = Depends(get_db),
):
    service = OrganizationService(db)
    org = service.update_org(org_id, request)
    return success_response(org, "Organization updated")


@org_router.delete("/{org_id}")
async def delete_organization(
    org_id: int,
    current_user: dict = Depends(require_permissions("organizations.manage")),
    db: DbSession = Depends(get_db),
):
    service = OrganizationService(db)
    service.delete_org(org_id)
    return success_response(None, "Organization deleted")


dept_router = APIRouter(prefix="/departments", tags=["Departments"])


@dept_router.get("")
async def list_departments(
    organization_id: int = None,
    current_user: dict = Depends(get_current_user),
    db: DbSession = Depends(get_db),
):
    service = DepartmentService(db)
    return success_response(service.list_depts(organization_id))


@dept_router.post("")
async def create_department(
    request: DepartmentCreate,
    current_user: dict = Depends(require_permissions("departments.manage")),
    db: DbSession = Depends(get_db),
):
    service = DepartmentService(db)
    dept = service.create_dept(request)
    return success_response(dept, "Department created")


@dept_router.get("/{dept_id}")
async def get_department(
    dept_id: int,
    current_user: dict = Depends(get_current_user),
    db: DbSession = Depends(get_db),
):
    service = DepartmentService(db)
    return success_response(service.get_dept(dept_id))


@dept_router.put("/{dept_id}")
async def update_department(
    dept_id: int,
    request: DepartmentUpdate,
    current_user: dict = Depends(require_permissions("departments.manage")),
    db: DbSession = Depends(get_db),
):
    service = DepartmentService(db)
    dept = service.update_dept(dept_id, request)
    return success_response(dept, "Department updated")


@dept_router.delete("/{dept_id}")
async def delete_department(
    dept_id: int,
    current_user: dict = Depends(require_permissions("departments.manage")),
    db: DbSession = Depends(get_db),
):
    service = DepartmentService(db)
    service.delete_dept(dept_id)
    return success_response(None, "Department deleted")
