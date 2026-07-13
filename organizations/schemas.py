"""Pydantic schemas for organization endpoints."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class OrganizationCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    slug: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    logo_url: Optional[str] = None
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    address: Optional[str] = None


class OrganizationUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    logo_url: Optional[str] = None
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    address: Optional[str] = None
    is_active: Optional[bool] = None


class OrganizationResponse(BaseModel):
    id: int
    name: str
    slug: str
    description: Optional[str] = None
    logo_url: Optional[str] = None
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    address: Optional[str] = None
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class DepartmentCreate(BaseModel):
    organization_id: int
    branch_id: Optional[int] = None
    name: str = Field(..., min_length=1, max_length=255)
    code: Optional[str] = None
    description: Optional[str] = None
    head_user_id: Optional[int] = None
    parent_id: Optional[int] = None


class DepartmentUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=255)
    code: Optional[str] = None
    description: Optional[str] = None
    head_user_id: Optional[int] = None
    parent_id: Optional[int] = None
    is_active: Optional[bool] = None


class DepartmentResponse(BaseModel):
    id: int
    organization_id: int
    branch_id: Optional[int] = None
    name: str
    code: Optional[str] = None
    description: Optional[str] = None
    head_user_id: Optional[int] = None
    parent_id: Optional[int] = None
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class BranchCreate(BaseModel):
    organization_id: int
    name: str = Field(..., min_length=1, max_length=255)
    code: Optional[str] = None
    address: Optional[str] = None
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None


class BranchResponse(BaseModel):
    id: int
    organization_id: int
    name: str
    code: Optional[str] = None
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True
