"""ML platform models.

Captures model registry, training runs, evaluations, forecasts, anomaly jobs,
and drift monitoring for enterprise MLOps.
"""

from __future__ import annotations

import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import JSON, Column, DateTime, Enum, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from shared.database import Base, BigInt


class ModelType(str, enum.Enum):
    CLASSIFICATION = "classification"
    REGRESSION = "regression"
    CLUSTERING = "clustering"
    ANOMALY_DETECTION = "anomaly_detection"
    FORECASTING = "forecasting"


class ModelStatus(str, enum.Enum):
    DRAFT = "draft"
    TRAINING = "training"
    READY = "ready"
    FAILED = "failed"
    DEPRECATED = "deprecated"
    ARCHIVED = "archived"


class MLModel(Base):
    """Registered ML model owned by an organization."""

    __tablename__ = "ml_models"

    id = Column(String(64), primary_key=True, default=lambda: f"mdl_{uuid.uuid4().hex[:16]}")
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    model_type = Column(Enum(ModelType), nullable=False)
    status = Column(Enum(ModelStatus), default=ModelStatus.DRAFT, nullable=False)
    target_column = Column(String(255), nullable=True)
    feature_columns = Column(JSON, default=list, nullable=False)
    algorithm = Column(String(100), nullable=True)
    hyperparameters = Column(JSON, default=dict, nullable=False)
    metrics = Column(JSON, default=dict, nullable=False)
    artifact_path = Column(String(500), nullable=True)
    dataset_source = Column(String(500), nullable=True)
    organization_id = Column(BigInt, ForeignKey("organizations.id"), nullable=False, index=True)
    created_by = Column(BigInt, ForeignKey("users.id"), nullable=False)
    parent_model_id = Column(String(64), ForeignKey("ml_models.id"), nullable=True)
    version = Column(Integer, default=1, nullable=False)
    deployment_status = Column(String(50), default="not_deployed", nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    organization = relationship("Organization", foreign_keys=[organization_id])
    creator = relationship("User", foreign_keys=[created_by])
    training_runs = relationship(
        "MLTrainingRun", back_populates="model", cascade="all, delete-orphan"
    )
    predictions = relationship("MLPrediction", back_populates="model", cascade="all, delete-orphan")


class MLTrainingRun(Base):
    """Record of a model training or retraining execution."""

    __tablename__ = "ml_training_runs"

    id = Column(String(64), primary_key=True, default=lambda: f"trn_{uuid.uuid4().hex[:16]}")
    model_id = Column(
        String(64), ForeignKey("ml_models.id", ondelete="CASCADE"), nullable=False, index=True
    )
    status = Column(String(50), default="pending", nullable=False)
    algorithm = Column(String(100), nullable=True)
    hyperparameters = Column(JSON, default=dict, nullable=False)
    feature_columns = Column(JSON, default=list, nullable=False)
    target_column = Column(String(255), nullable=True)
    train_metrics = Column(JSON, default=dict, nullable=False)
    test_metrics = Column(JSON, default=dict, nullable=False)
    comparison_metrics = Column(JSON, default=dict, nullable=False)
    artifact_path = Column(String(500), nullable=True)
    dataset_source = Column(String(500), nullable=True)
    error_message = Column(Text, nullable=True)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    created_by = Column(BigInt, ForeignKey("users.id"), nullable=False)
    organization_id = Column(BigInt, ForeignKey("organizations.id"), nullable=False, index=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    model = relationship("MLModel", back_populates="training_runs")


class MLPrediction(Base):
    """Individual batch or single predictions from a registered model."""

    __tablename__ = "ml_predictions"

    id = Column(String(64), primary_key=True, default=lambda: f"prd_{uuid.uuid4().hex[:16]}")
    model_id = Column(
        String(64), ForeignKey("ml_models.id", ondelete="CASCADE"), nullable=False, index=True
    )
    input_features = Column(JSON, default=dict, nullable=False)
    prediction = Column(JSON, default=dict, nullable=False)
    probability = Column(Float, nullable=True)
    confidence_interval = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    model = relationship("MLModel", back_populates="predictions")


class MLForecast(Base):
    """Forecast results for time-series models."""

    __tablename__ = "ml_forecasts"

    id = Column(String(64), primary_key=True, default=lambda: f"frc_{uuid.uuid4().hex[:16]}")
    model_id = Column(
        String(64), ForeignKey("ml_models.id", ondelete="CASCADE"), nullable=False, index=True
    )
    horizon = Column(Integer, nullable=False)
    frequency = Column(String(20), nullable=False)
    forecast_values = Column(JSON, default=list, nullable=False)
    confidence_intervals = Column(JSON, default=dict, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)


class MLAnomalyJob(Base):
    """Configuration and latest results for an anomaly-detection job."""

    __tablename__ = "ml_anomaly_jobs"

    id = Column(String(64), primary_key=True, default=lambda: f"anm_{uuid.uuid4().hex[:16]}")
    name = Column(String(255), nullable=False)
    dataset_source = Column(String(500), nullable=True)
    algorithm = Column(String(100), default="isolation_forest", nullable=False)
    config = Column(JSON, default=dict, nullable=False)
    latest_result = Column(JSON, default=dict, nullable=False)
    organization_id = Column(BigInt, ForeignKey("organizations.id"), nullable=False, index=True)
    created_by = Column(BigInt, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )


class MLDriftRecord(Base):
    """Drift monitoring record for deployed models."""

    __tablename__ = "ml_drift_records"

    id = Column(BigInt, primary_key=True, autoincrement=True)
    model_id = Column(
        String(64), ForeignKey("ml_models.id", ondelete="CASCADE"), nullable=False, index=True
    )
    drift_type = Column(String(50), nullable=False)  # data_drift, concept_drift, prediction_drift
    score = Column(Float, nullable=False)
    threshold = Column(Float, default=0.05, nullable=False)
    details = Column(JSON, default=dict, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
