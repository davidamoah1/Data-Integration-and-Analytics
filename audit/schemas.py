"""Pydantic schemas for audit endpoints."""

from datetime import datetime
from typing import Optional, Any

from pydantic import BaseModel


class AuditLogResponse(BaseModel):
    id: int
    user_id: Optional[int] = None
    action: str
    resource_type: Optional[str] = None
    resource_id: Optional[int] = None
    ip_address: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class SecurityLogResponse(BaseModel):
    id: int
    user_id: Optional[int] = None
    event_type: str
    ip_address: Optional[str] = None
    severity: str
    created_at: datetime

    class Config:
        from_attributes = True


class SystemLogResponse(BaseModel):
    id: int
    log_level: str
    message: str
    module: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True
