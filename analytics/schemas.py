from datetime import datetime

from pydantic import BaseModel, Field


class DashboardCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    description: str | None = None
    theme: str = "default"
    layout: list[dict] = Field(default_factory=list)
    is_public: bool = False


class DashboardUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = None
    theme: str | None = None
    layout: list[dict] | None = None
    is_public: bool | None = None


class WidgetCreate(BaseModel):
    widget_type: str = Field(min_length=1, max_length=50)
    title: str = Field(min_length=1, max_length=255)
    configuration: dict = Field(default_factory=dict)
    position: dict = Field(default_factory=dict)
    group_name: str | None = Field(None, max_length=100)


class KPICreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    formula: str = Field(min_length=1)
    description: str | None = None
    category: str | None = Field(None, max_length=100)
    target_value: float | None = None
    warning_threshold: float | None = None
    critical_threshold: float | None = None
    unit: str | None = Field(None, max_length=50)


class KPIRecord(BaseModel):
    value: float


class AlertCreate(BaseModel):
    alert_type: str = Field(min_length=1, max_length=50)
    severity: str = Field(default="warning", max_length=20)
    title: str = Field(min_length=1, max_length=255)
    message: str = Field(min_length=1)
    source_type: str | None = Field(None, max_length=50)
    source_id: int | None = None


class AlertResponse(BaseModel):
    id: int
    alert_type: str
    severity: str
    title: str
    message: str
    source_type: str | None
    source_id: int | None
    acknowledged_by: int | None
    acknowledged_at: datetime | None
    created_at: datetime
