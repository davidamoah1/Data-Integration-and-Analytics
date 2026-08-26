"""Pydantic schemas for the ML platform API."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class MLReadinessRequest(BaseModel):
    dataset_source: str = Field(..., description="Dataset identifier, uploaded file key, or path")
    target_column: str | None = None
    sample_limit: int = Field(10000, ge=1)


class MLReadinessResponse(BaseModel):
    ready: bool
    quality_score: float
    row_count: int
    column_count: int
    missing_values: dict[str, Any]
    outliers: dict[str, Any]
    class_imbalance: dict[str, Any]
    feature_completeness: dict[str, Any]
    forecast_suitable: bool
    suggested_algorithms: list[dict[str, Any]]
    recommended_targets: list[str]
    warnings: list[str]
    recommendations: list[str]


class FeatureEngineeringRequest(BaseModel):
    dataset_source: str
    target_column: str | None = None
    scaling: Literal["standard", "minmax", "none"] = "standard"
    polynomial_degree: int = Field(0, ge=0, le=3)
    interaction_only: bool = False
    k_best: int = Field(0, ge=0)
    rolling_column: str | None = None
    rolling_windows: list[int] = [7, 14, 30]
    lag_column: str | None = None
    lag_periods: list[int] = [1, 2, 3, 7]


class FeatureEngineeringResponse(BaseModel):
    original_shape: list[int]
    transformed_shape: list[int]
    output_columns: list[str]
    log: list[dict[str, Any]]


class ModelCreateRequest(BaseModel):
    name: str
    description: str = ""
    model_type: Literal[
        "classification", "regression", "clustering", "anomaly_detection", "forecasting"
    ]
    dataset_source: str
    target_column: str | None = None
    feature_columns: list[str] = []
    algorithm: str | None = None
    hyperparameters: dict[str, Any] = {}
    test_size: float = 0.2
    include_all: bool = False
    feature_config: dict[str, Any] = {}


class ModelResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    description: str
    model_type: str
    status: str
    algorithm: str | None
    target_column: str | None
    feature_columns: list[str]
    metrics: dict[str, Any]
    dataset_source: str | None
    version: int
    deployment_status: str
    created_at: str
    updated_at: str


class TrainingRunResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    model_id: str
    status: str
    algorithm: str | None
    train_metrics: dict[str, Any]
    test_metrics: dict[str, Any]
    comparison_metrics: dict[str, Any]
    error_message: str | None
    started_at: str | None
    completed_at: str | None


class PredictRequest(BaseModel):
    features: list[dict[str, Any]]


class PredictResponse(BaseModel):
    model_id: str
    predictions: list[Any]


class ForecastRequest(BaseModel):
    dataset_source: str
    date_column: str
    target_column: str
    horizon: int = Field(30, ge=1, le=365)
    frequency: Literal["D", "W", "M", "H"] = "D"
    algorithm: Literal["auto", "ARIMA", "ExponentialSmoothing", "Prophet"] = "auto"


class ForecastResponse(BaseModel):
    model_id: str
    algorithm: str
    horizon: int
    forecast: list[float]
    lower: list[float] | None = None
    upper: list[float] | None = None


class AnomalyRequest(BaseModel):
    dataset_source: str
    algorithm: Literal["isolation_forest", "local_outlier_factor"] = "isolation_forest"
    threshold: float = 3.0
    column: str | None = None
    config: dict[str, Any] = {}


class AnomalyResponse(BaseModel):
    total: int
    anomalies: int
    anomaly_rate: float
    anomaly_indices: list[Any]
    algorithm: str


class DecisionRecommendationRequest(BaseModel):
    dataset_source: str
    metric_column: str
    segment_column: str | None = None
    include_forecast: bool = False
    forecast_horizon: int = 30


class DecisionRecommendationResponse(BaseModel):
    recommendation: str
    facts: list[str]
    reasoning: str
    confidence: float
    metric_change_pct: float


class WhatIfRequest(BaseModel):
    dataset_source: str
    metric_column: str
    driver_column: str | None = None
    scenarios: list[dict[str, Any]] | None = None


class WhatIfResponse(BaseModel):
    scenarios: list[dict[str, Any]]


class DriftRequest(BaseModel):
    model_id: str
    current_dataset_source: str
    threshold: float = 0.05


class DriftResponse(BaseModel):
    drift_detected: bool
    drifted_features: int
    total_features: int
    features: list[dict[str, Any]]


class ModelCompareRequest(BaseModel):
    model_ids: list[str]
