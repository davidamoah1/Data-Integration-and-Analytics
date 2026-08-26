"""Pydantic schemas for the workflow API."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class WorkflowNodeDefinition(BaseModel):
    id: str = Field(..., min_length=1)
    type: str = Field(..., min_length=1)
    label: str | None = None
    config: dict[str, Any] = Field(default_factory=dict)
    inputs: dict[str, Any] = Field(default_factory=dict)
    position: dict[str, float] = Field(default_factory=dict)
    retry_policy: dict[str, Any] | None = None


class WorkflowEdgeDefinition(BaseModel):
    source: str = Field(..., min_length=1)
    target: str = Field(..., min_length=1)
    condition: str | None = None


class WorkflowDefinitionCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    category: str | None = None
    nodes: list[WorkflowNodeDefinition] = Field(default_factory=list)
    edges: list[WorkflowEdgeDefinition] = Field(default_factory=list)
    config: dict[str, Any] = Field(default_factory=dict)


class WorkflowDefinitionUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = None
    category: str | None = None
    is_active: bool | None = None


class WorkflowVersionCreate(BaseModel):
    nodes: list[WorkflowNodeDefinition] = Field(default_factory=list)
    edges: list[WorkflowEdgeDefinition] = Field(default_factory=list)
    config: dict[str, Any] = Field(default_factory=dict)


class WorkflowVersionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    workflow_id: int
    version_number: int
    status: str
    nodes: list[dict[str, Any]]
    edges: list[dict[str, Any]]
    config: dict[str, Any]
    created_by: int | None
    created_at: datetime


class WorkflowDefinitionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    organization_id: int | None
    created_by: int | None
    name: str
    description: str | None
    category: str | None
    is_active: bool
    published_version_id: int | None
    created_at: datetime
    updated_at: datetime


class WorkflowExecutionCreate(BaseModel):
    version_id: int | None = None
    trigger_type: str = "manual"
    inputs: dict[str, Any] = Field(default_factory=dict)


class WorkflowExecutionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    execution_id: str
    workflow_id: int | None
    version_id: int | None
    organization_id: int | None
    triggered_by: int | None
    trigger_type: str
    status: str
    started_at: datetime | None
    completed_at: datetime | None
    duration_seconds: int | None
    node_results: dict[str, Any]
    context: dict[str, Any]
    metrics: dict[str, Any]
    errors: list[str]
    warnings: list[str]
    ai_summary: str | None
    created_at: datetime
    updated_at: datetime


class WorkflowHistoryQuery(BaseModel):
    workflow_id: int | None = None
    status: str | None = None
    trigger_type: str | None = None
    limit: int = Field(50, ge=1, le=200)
    offset: int = Field(0, ge=0)


class WorkflowLineageResponse(BaseModel):
    id: int
    execution_id: str
    source_type: str
    source_id: str | None
    target_type: str
    target_id: str | None
    transformation: str | None
    metadata: dict[str, Any]
    created_at: datetime


class WorkflowTemplateCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    category: str | None = None
    nodes: list[WorkflowNodeDefinition] = Field(default_factory=list)
    edges: list[WorkflowEdgeDefinition] = Field(default_factory=list)
    config: dict[str, Any] = Field(default_factory=dict)
    is_public: bool = False


class WorkflowTemplateResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_by: int | None
    name: str
    description: str | None
    category: str | None
    is_public: bool
    created_at: datetime
