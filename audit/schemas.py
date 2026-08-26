"""Pydantic schemas for audit endpoints."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class AuditLogResponse(BaseModel):
    id: int
    user_id: int | None = None
    action: str
    resource_type: str | None = None
    resource_id: int | None = None
    ip_address: str | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SecurityLogResponse(BaseModel):
    id: int
    user_id: int | None = None
    event_type: str
    ip_address: str | None = None
    severity: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SystemLogResponse(BaseModel):
    id: int
    log_level: str
    message: str
    module: str | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
