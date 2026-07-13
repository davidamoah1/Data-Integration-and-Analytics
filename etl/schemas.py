"""Pydantic schemas for Phase 5 ETL Engine API endpoints."""

from datetime import datetime
from typing import Optional, Any
from pydantic import BaseModel, Field


# --- Import -----------------------------------------------------------------

class ImportRequest(BaseModel):
    source_type: str = Field(..., description="csv, excel, json, xml, mysql, api")
    source_config: dict = Field(..., description="Connector-specific configuration")
    column_mapping: Optional[dict] = None
    transformations: Optional[list[dict]] = None
    validation_rules: Optional[dict] = None
    template_name: Optional[str] = None


class ImportPreviewResponse(BaseModel):
    columns: list[str]
    rows: list[dict]
    row_count: int
    column_count: int


class ImportResponse(BaseModel):
    job_id: int
    status: str
    rows_imported: int
    quality_score: Optional[int] = None
    errors: list[str] = []


# --- Profiling --------------------------------------------------------------

class ProfileResponse(BaseModel):
    source_name: str
    row_count: int
    column_count: int
    quality_score: int
    columns: dict
    duplicate_rows: int
    duplicate_percentage: float


# --- Quality ----------------------------------------------------------------

class QualityResponse(BaseModel):
    source_name: str
    overall_score: int
    checks_passed: int
    checks_failed: int
    checks_warning: int
    total_checks: int
    checks: list[dict]
    recommendations: list[str]


class ApplyFixRequest(BaseModel):
    check_names: Optional[list[str]] = None


# --- Transformations --------------------------------------------------------

class TransformRequest(BaseModel):
    source_type: str = Field(..., description="csv, excel, json, xml, mysql, api")
    source_config: dict = Field(..., description="Connector-specific configuration")
    transformations: list[dict] = Field(..., description="List of transformation configs")


class TransformResponse(BaseModel):
    rows_before: int
    rows_after: int
    rows_changed: int
    transformations_applied: int


class TransformationTemplateCreate(BaseModel):
    name: str
    description: Optional[str] = None
    transformation_type: str
    config: dict


# --- Pipeline ---------------------------------------------------------------

class PipelineCreate(BaseModel):
    name: str
    description: Optional[str] = None
    steps: list[dict] = Field(default_factory=list)


class PipelineUpdate(BaseModel):
    steps: list[dict]


class PipelineResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    status: str
    current_version: int
    steps: list[dict]
    created_at: Optional[str]


class PipelineExecuteResponse(BaseModel):
    job_id: int
    status: str
    rows_extracted: int
    rows_transformed: int
    rows_loaded: int
    duration_seconds: float


class VersionHistoryItem(BaseModel):
    id: int
    version_number: int
    is_active: bool
    created_at: Optional[str]


class RollbackRequest(BaseModel):
    version_number: int


# --- Jobs -------------------------------------------------------------------

class JobResponse(BaseModel):
    id: int
    pipeline_id: Optional[int]
    job_type: str
    status: str
    trigger_type: str
    rows_extracted: int
    rows_transformed: int
    rows_loaded: int
    rows_rejected: int
    error_message: Optional[str]
    duration_seconds: Optional[int]
    started_at: Optional[str]
    completed_at: Optional[str]
    created_at: Optional[str]


class JobStatsResponse(BaseModel):
    total_jobs: int
    running: int
    completed: int
    failed: int
    queued: int
    success_rate: float
    failure_rate: float
    average_duration_seconds: float


# --- Lineage ----------------------------------------------------------------

class LineageResponse(BaseModel):
    nodes: list[dict]
    edges: list[dict]


# --- Schedules --------------------------------------------------------------

class ScheduleCreate(BaseModel):
    pipeline_id: int
    schedule_type: str = Field(..., description="once, hourly, daily, weekly, monthly, cron")
    cron_expr: Optional[str] = None


class ScheduleResponse(BaseModel):
    id: int
    pipeline_id: int
    schedule_type: str
    cron_expr: Optional[str]
    is_active: bool
    last_run_at: Optional[str]
    next_run_at: Optional[str]


# --- Dashboard --------------------------------------------------------------

class DashboardResponse(BaseModel):
    total_jobs: int
    running_jobs: int
    completed_jobs: int
    failed_jobs: int
    success_rate: float
    average_quality_score: Optional[float]
    recent_activity: list[dict]
    active_pipelines: int


# --- Templates --------------------------------------------------------------

class ImportTemplateResponse(BaseModel):
    id: int
    name: str
    source_type: str
    source_config: dict
    column_mapping: Optional[dict]
    transformations: Optional[list[dict]]
    created_at: Optional[str]


# --- AI Hooks ---------------------------------------------------------------

class AIHooksResponse(BaseModel):
    hooks: list[dict]
