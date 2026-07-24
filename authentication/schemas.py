"""Pydantic schemas for authentication endpoints."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field

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


class SignupRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)
    full_name: str = Field(..., min_length=1, max_length=255)
    organization_name: str | None = Field(
        None, max_length=200, description="Optional — creates a new org for this user"
    )


# --- User -------------------------------------------------------------------


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)
    full_name: str = Field(..., min_length=1, max_length=255)
    phone: str | None = None
    organization_id: int | None = None
    department_id: int | None = None
    position: str | None = None
    role_names: list[str] = Field(default_factory=list)


class UserUpdate(BaseModel):
    full_name: str | None = Field(None, max_length=255)
    phone: str | None = None
    avatar_url: str | None = None
    organization_id: int | None = None
    department_id: int | None = None
    position: str | None = None
    language: str | None = None
    timezone: str | None = None


class UserResponse(BaseModel):
    id: int
    email: str
    full_name: str
    avatar_url: str | None = None
    phone: str | None = None
    organization_id: int | None = None
    department_id: int | None = None
    position: str | None = None
    language: str | None = None
    timezone: str | None = None
    is_active: bool
    email_verified: bool
    last_login_at: datetime | None = None
    created_at: datetime
    roles: list[str] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class UserListResponse(BaseModel):
    users: list[UserResponse]
    total: int
    page: int
    page_size: int


# --- Role -------------------------------------------------------------------


class RoleCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=50)
    display_name: str = Field(..., min_length=1, max_length=100)
    description: str | None = None
    permission_names: list[str] = Field(default_factory=list)


class RoleUpdate(BaseModel):
    display_name: str | None = None
    description: str | None = None
    permission_names: list[str] | None = None


class RoleResponse(BaseModel):
    id: int
    name: str
    display_name: str
    description: str | None = None
    is_system: bool
    permissions: list[str] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


# --- Permission -------------------------------------------------------------


class PermissionResponse(BaseModel):
    id: int
    name: str
    display_name: str
    module: str
    description: str | None = None

    model_config = ConfigDict(from_attributes=True)


# --- Session ----------------------------------------------------------------


class SessionResponse(BaseModel):
    id: int
    ip_address: str | None = None
    user_agent: str | None = None
    device: str | None = None
    is_active: bool
    last_activity_at: datetime
    created_at: datetime
    expires_at: datetime

    model_config = ConfigDict(from_attributes=True)


# --- Login History ----------------------------------------------------------


class LoginHistoryResponse(BaseModel):
    id: int
    email: str
    ip_address: str | None = None
    user_agent: str | None = None
    success: bool
    failure_reason: str | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# --- Profile ----------------------------------------------------------------


class ProfileUpdate(BaseModel):
    full_name: str | None = Field(None, max_length=255)
    phone: str | None = None
    avatar_url: str | None = None
    position: str | None = None
    language: str | None = None
    timezone: str | None = None


class NotificationPreferences(BaseModel):
    in_app_enabled: bool = True
    email_enabled: bool = False
    sms_enabled: bool = False
