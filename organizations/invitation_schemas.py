"""Pydantic schemas for invitation and workspace endpoints."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class InvitationCreate(BaseModel):
    email: EmailStr
    role_name: str = Field(..., description="Role to assign when invitation is accepted")
    department_id: int | None = None


class InvitationAccept(BaseModel):
    token: str
    email: EmailStr
    full_name: str = Field(..., min_length=1, max_length=255)
    password: str = Field(..., min_length=8)


class InvitationResponse(BaseModel):
    id: int
    organization_id: int
    email: str
    role_name: str | None = None
    department_id: int | None = None
    status: str
    expires_at: datetime
    accepted_at: datetime | None = None
    created_by: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class WorkspaceResponse(BaseModel):
    id: int
    organization_id: int | None = None
    user_id: int | None = None
    name: str
    type: str
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SignupV2Request(BaseModel):
    """Enhanced signup supporting three registration modes."""

    email: EmailStr
    password: str = Field(..., min_length=8)
    full_name: str = Field(..., min_length=1, max_length=255)
    registration_mode: str = Field(
        ..., description="One of: create_organization, join_organization, personal"
    )
    # For create_organization
    organization_name: str | None = Field(None, max_length=255)
    industry: str | None = Field(None, max_length=100)
    country: str | None = Field(None, max_length=100)
    organization_type: str | None = Field(None, max_length=100)
    # For join_organization
    invitation_token: str | None = None
