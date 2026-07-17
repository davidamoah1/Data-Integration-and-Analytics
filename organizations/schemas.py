"""Pydantic schemas for organization endpoints."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class OrganizationCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    slug: str = Field(..., min_length=1, max_length=100)
    description: str | None = None
    logo_url: str | None = None
    contact_email: str | None = None
    contact_phone: str | None = None
    address: str | None = None


class OrganizationUpdate(BaseModel):
    name: str | None = Field(None, max_length=255)
    description: str | None = None
    logo_url: str | None = None
    contact_email: str | None = None
    contact_phone: str | None = None
    address: str | None = None
    is_active: bool | None = None


class OrganizationResponse(BaseModel):
    id: int
    name: str
    slug: str
    description: str | None = None
    logo_url: str | None = None
    contact_email: str | None = None
    contact_phone: str | None = None
    address: str | None = None
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DepartmentCreate(BaseModel):
    organization_id: int
    branch_id: int | None = None
    name: str = Field(..., min_length=1, max_length=255)
    code: str | None = None
    description: str | None = None
    head_user_id: int | None = None
    parent_id: int | None = None


class DepartmentUpdate(BaseModel):
    name: str | None = Field(None, max_length=255)
    code: str | None = None
    description: str | None = None
    head_user_id: int | None = None
    parent_id: int | None = None
    is_active: bool | None = None


class DepartmentResponse(BaseModel):
    id: int
    organization_id: int
    branch_id: int | None = None
    name: str
    code: str | None = None
    description: str | None = None
    head_user_id: int | None = None
    parent_id: int | None = None
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class BranchCreate(BaseModel):
    organization_id: int
    name: str = Field(..., min_length=1, max_length=255)
    code: str | None = None
    address: str | None = None
    contact_email: str | None = None
    contact_phone: str | None = None


class BranchResponse(BaseModel):
    id: int
    organization_id: int
    name: str
    code: str | None = None
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
