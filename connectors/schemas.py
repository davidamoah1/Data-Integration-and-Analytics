"""Pydantic schemas for the Connector Framework."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class ConnectorCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    connector_type: str
    category: str = "database"
    description: str | None = None
    configuration: dict[str, Any] | None = None
    auth_config: dict[str, Any] | None = None
    is_public: bool = False


class ConnectorUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    configuration: dict[str, Any] | None = None
    auth_config: dict[str, Any] | None = None
    is_public: bool | None = None


class ConnectorResponse(BaseModel):
    id: int
    organization_id: int
    name: str
    connector_type: str
    category: str
    description: str | None = None
    status: str
    last_tested_at: str | None = None
    is_public: bool
    created_at: str | None = None
    updated_at: str | None = None


class ConnectorTestResult(BaseModel):
    success: bool
    message: str
    details: dict[str, Any] | None = None


class ConnectorExecutionResponse(BaseModel):
    id: int
    connector_id: int
    status: str
    rows_extracted: int | None = None
    error_message: str | None = None
    started_at: str | None = None
    completed_at: str | None = None
