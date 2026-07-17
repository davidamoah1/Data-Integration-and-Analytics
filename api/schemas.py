"""Pydantic schemas for API request/response validation."""

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field


class KPIResponse(BaseModel):
    """Response schema for aggregate KPIs."""

    total_sales: float = Field(..., description="Total revenue")
    total_profit: float = Field(..., description="Total profit")
    total_orders: int = Field(..., description="Number of unique orders")
    avg_order_value: float = Field(..., description="Average order value")
    margin_pct: float = Field(..., description="Profit margin percentage")


class SalesRecordResponse(BaseModel):
    """Response schema for a single sales record."""

    order_id: str
    order_date: date | None = None
    ship_date: date | None = None
    customer_name: str | None = None
    segment: str | None = None
    region: str | None = None
    category: str | None = None
    sub_category: str | None = None
    product_name: str | None = None
    sales: float
    quantity: int
    discount: float
    profit: float

    model_config = ConfigDict(from_attributes=True)


class SalesListResponse(BaseModel):
    """Response schema for a paginated list of sales records."""

    records: list[SalesRecordResponse]
    total: int
    page: int
    page_size: int


class FilterOptionsResponse(BaseModel):
    """Response schema for available filter options."""

    regions: list[str]
    categories: list[str]
    date_range: dict


class PipelineRunResponse(BaseModel):
    """Response schema for pipeline run metadata."""

    run_id: str
    status: str
    started_at: datetime
    completed_at: datetime | None = None
    rows_extracted: int = 0
    rows_transformed: int = 0
    rows_loaded: int = 0
    duplicates_removed: int = 0
    error_message: str | None = None


class PipelineTriggerResponse(BaseModel):
    """Response schema for triggering a pipeline run."""

    run_id: str
    status: str = "triggered"
    message: str = "Pipeline execution started"


class HealthResponse(BaseModel):
    """Response schema for health check endpoint."""

    status: str = "healthy"
    database_connected: bool
    record_count: int
    timestamp: datetime
