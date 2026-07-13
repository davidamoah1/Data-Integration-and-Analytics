"""Pydantic schemas for authentication endpoints."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field, field_validator


# --- Auth -------------------------------------------------------------------

class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=1)
    remember_me: bool = False


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class ChangePasswordRequest(BaseModel):
    current_password: str = Field(..., min_length=1)
    new_password: str = Field(..., min_length=8)


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str = Field(..., min_length=8)


class VerifyEmailRequest(BaseModel):
    token: str


# --- User -------------------------------------------------------------------

class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)
    full_name: str = Field(..., min_length=1, max_length=255)
    phone: Optional[str] = None
    organization_id: Optional[int] = None
    department_id: Optional[int] = None
    position: Optional[str] = None
    role_names: list[str] = Field(default_factory=list)


class UserUpdate(BaseModel):
    full_name: Optional[str] = Field(None, max_length=255)
    phone: Optional[str] = None
    avatar_url: Optional[str] = None
    organization_id: Optional[int] = None
    department_id: Optional[int] = None
    position: Optional[str] = None
    language: Optional[str] = None
    timezone: Optional[str] = None


class UserResponse(BaseModel):
    id: int
    email: str
    full_name: str
    avatar_url: Optional[str] = None
    phone: Optional[str] = None
    organization_id: Optional[int] = None
    department_id: Optional[int] = None
    position: Optional[str] = None
    language: Optional[str] = None
    timezone: Optional[str] = None
    is_active: bool
    email_verified: bool
    last_login_at: Optional[datetime] = None
    created_at: datetime
    roles: list[str] = Field(default_factory=list)

    class Config:
        from_attributes = True


class UserListResponse(BaseModel):
    users: list[UserResponse]
    total: int
    page: int
    page_size: int


# --- Role -------------------------------------------------------------------

class RoleCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=50)
    display_name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    permission_names: list[str] = Field(default_factory=list)


class RoleUpdate(BaseModel):
    display_name: Optional[str] = None
    description: Optional[str] = None
    permission_names: Optional[list[str]] = None


class RoleResponse(BaseModel):
    id: int
    name: str
    display_name: str
    description: Optional[str] = None
    is_system: bool
    permissions: list[str] = Field(default_factory=list)

    class Config:
        from_attributes = True


# --- Permission -------------------------------------------------------------

class PermissionResponse(BaseModel):
    id: int
    name: str
    display_name: str
    module: str
    description: Optional[str] = None

    class Config:
        from_attributes = True


# --- Session ----------------------------------------------------------------

class SessionResponse(BaseModel):
    id: int
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    device: Optional[str] = None
    is_active: bool
    last_activity_at: datetime
    created_at: datetime
    expires_at: datetime

    class Config:
        from_attributes = True


# --- Login History ----------------------------------------------------------

class LoginHistoryResponse(BaseModel):
    id: int
    email: str
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    success: bool
    failure_reason: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


# --- Profile ----------------------------------------------------------------

class ProfileUpdate(BaseModel):
    full_name: Optional[str] = Field(None, max_length=255)
    phone: Optional[str] = None
    avatar_url: Optional[str] = None
    position: Optional[str] = None
    language: Optional[str] = None
    timezone: Optional[str] = None


class NotificationPreferences(BaseModel):
    in_app_enabled: bool = True
    email_enabled: bool = False
    sms_enabled: bool = False
