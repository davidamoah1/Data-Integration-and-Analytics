"""SQLAlchemy ORM models for Phase 5 â€” ETL Engine.

Tables: etl_pipelines, etl_pipeline_versions, etl_pipeline_steps,
etl_jobs, etl_import_templates, etl_data_profiles, etl_quality_reports,
etl_data_lineage, etl_schedules, etl_transformations.
"""

from sqlalchemy import (
    JSON,
    TIMESTAMP,
    BigInteger,
    Column,
    Index,
    Integer,
    String,
    Text,
    func,
)

from shared.database import Base, BigInt


class ETLPipeline(Base):
    """A reusable ETL pipeline definition."""

    __tablename__ = "etl_pipelines"

    id = Column(BigInt, primary_key=True, autoincrement=True)
    organization_id = Column(BigInteger, nullable=False, index=True)
    name = Column(String(200), nullable=False, index=True)
    description = Column(Text, nullable=True)
    status = Column(String(20), nullable=False, default="active")  # active, inactive, archived
    current_version = Column(Integer, nullable=False, default=1)
    created_by = Column(BigInteger, nullable=True)
    created_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now(), nullable=False)


class ETLPipelineVersion(Base):
    """A specific version of a pipeline with its step configuration."""

    __tablename__ = "etl_pipeline_versions"

    id = Column(BigInt, primary_key=True, autoincrement=True)
    pipeline_id = Column(BigInteger, nullable=False, index=True)
    version_number = Column(Integer, nullable=False)
    step_config = Column(JSON, nullable=False)  # list of step definitions
    created_by = Column(BigInteger, nullable=True)
    created_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)
    is_active = Column(Integer, nullable=False, default=1)


class ETLPipelineStep(Base):
    """Execution record for a single step within a pipeline run."""

    __tablename__ = "etl_pipeline_steps"

    id = Column(BigInt, primary_key=True, autoincrement=True)
    job_id = Column(BigInteger, nullable=False, index=True)
    step_name = Column(String(100), nullable=False)
    step_type = Column(
        String(50), nullable=False
    )  # extract, validate, clean, transform, load, report, notify
    status = Column(
        String(20), nullable=False, default="pending"
    )  # pending, running, completed, failed, skipped
    config = Column(JSON, nullable=True)
    started_at = Column(TIMESTAMP, nullable=True)
    completed_at = Column(TIMESTAMP, nullable=True)
    duration_seconds = Column(Integer, nullable=True)
    retry_count = Column(Integer, nullable=False, default=0)
    rows_processed = Column(Integer, nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)


class ETLJob(Base):
    """A single execution of a pipeline (a job/run)."""

    __tablename__ = "etl_jobs"

    id = Column(BigInt, primary_key=True, autoincrement=True)
    organization_id = Column(BigInteger, nullable=False, index=True)
    pipeline_id = Column(BigInteger, nullable=True, index=True)
    job_type = Column(String(50), nullable=False)  # pipeline, import, export, profile, quality
    status = Column(
        String(20), nullable=False, default="queued"
    )  # queued, running, completed, failed, cancelled
    trigger_type = Column(
        String(30), nullable=False, default="manual"
    )  # manual, scheduled, api, retry
    rows_extracted = Column(Integer, nullable=False, default=0)
    rows_transformed = Column(Integer, nullable=False, default=0)
    rows_loaded = Column(Integer, nullable=False, default=0)
    rows_rejected = Column(Integer, nullable=False, default=0)
    error_message = Column(Text, nullable=True)
    extra_data = Column(JSON, nullable=True)  # was 'metadata' â€” reserved by SQLAlchemy
    started_at = Column(TIMESTAMP, nullable=True)
    completed_at = Column(TIMESTAMP, nullable=True)
    duration_seconds = Column(Integer, nullable=True)
    created_by = Column(BigInteger, nullable=True)
    created_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)

    __table_args__ = (
        Index("idx_job_status_created", "status", "created_at"),
        Index("idx_job_pipeline_status", "pipeline_id", "status"),
    )


class ETLImportTemplate(Base):
    """Saved import configuration for recurring imports."""

    __tablename__ = "etl_import_templates"

    id = Column(BigInt, primary_key=True, autoincrement=True)
    organization_id = Column(BigInteger, nullable=False, index=True)
    name = Column(String(200), nullable=False)
    source_type = Column(String(50), nullable=False)  # csv, excel, json, xml, mysql, api
    source_config = Column(JSON, nullable=False)  # connector-specific config
    column_mapping = Column(JSON, nullable=True)  # source_col -> target_col
    transformations = Column(JSON, nullable=True)  # list of transformation configs
    validation_rules = Column(JSON, nullable=True)
    created_by = Column(BigInteger, nullable=True)
    created_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now(), nullable=False)


class ETLDataProfile(Base):
    """Saved data profiling results."""

    __tablename__ = "etl_data_profiles"

    id = Column(BigInt, primary_key=True, autoincrement=True)
    organization_id = Column(BigInteger, nullable=False, index=True)
    job_id = Column(BigInteger, nullable=True, index=True)
    source_name = Column(String(255), nullable=False)
    source_type = Column(String(50), nullable=False)
    row_count = Column(Integer, nullable=False, default=0)
    column_count = Column(Integer, nullable=False, default=0)
    profile_data = Column(JSON, nullable=False)  # full profiling results
    quality_score = Column(Integer, nullable=True)  # 0-100
    created_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)


class ETLQualityReport(Base):
    """Saved data quality assessment results."""

    __tablename__ = "etl_quality_reports"

    id = Column(BigInt, primary_key=True, autoincrement=True)
    organization_id = Column(BigInteger, nullable=False, index=True)
    job_id = Column(BigInteger, nullable=True, index=True)
    source_name = Column(String(255), nullable=False)
    overall_score = Column(Integer, nullable=False, default=0)  # 0-100
    checks_passed = Column(Integer, nullable=False, default=0)
    checks_failed = Column(Integer, nullable=False, default=0)
    checks_warning = Column(Integer, nullable=False, default=0)
    report_data = Column(JSON, nullable=False)  # full quality report
    recommendations = Column(JSON, nullable=True)  # list of recommendation strings
    created_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)


class ETLDataLineage(Base):
    """Tracks data flow from source through transformations to destination."""

    __tablename__ = "etl_data_lineage"

    id = Column(BigInt, primary_key=True, autoincrement=True)
    organization_id = Column(BigInteger, nullable=False, index=True)
    job_id = Column(BigInteger, nullable=True, index=True)
    pipeline_id = Column(BigInteger, nullable=True, index=True)
    source_name = Column(String(255), nullable=False)
    source_type = Column(String(50), nullable=False)
    transformation = Column(Text, nullable=True)  # description of transformation applied
    destination_name = Column(String(255), nullable=True)
    destination_type = Column(String(50), nullable=True)
    user_id = Column(BigInteger, nullable=True)
    extra_data = Column(JSON, nullable=True)
    created_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)


class ETLSchedule(Base):
    """Pipeline execution schedules."""

    __tablename__ = "etl_schedules"

    id = Column(BigInt, primary_key=True, autoincrement=True)
    organization_id = Column(BigInteger, nullable=False, index=True)
    pipeline_id = Column(BigInteger, nullable=False, index=True)
    schedule_type = Column(String(30), nullable=False)  # once, hourly, daily, weekly, monthly, cron
    cron_expr = Column(String(100), nullable=True)  # for custom cron
    is_active = Column(Integer, nullable=False, default=1)
    last_run_at = Column(TIMESTAMP, nullable=True)
    next_run_at = Column(TIMESTAMP, nullable=True)
    created_by = Column(BigInteger, nullable=True)
    created_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now(), nullable=False)


class ETLTransformation(Base):
    """Reusable transformation templates."""

    __tablename__ = "etl_transformations"

    id = Column(BigInt, primary_key=True, autoincrement=True)
    organization_id = Column(BigInteger, nullable=False, index=True)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    transformation_type = Column(
        String(50), nullable=False
    )  # rename, drop, filter, fill, convert, calculate, join, split, merge, sort, deduplicate, standardize
    config = Column(JSON, nullable=False)  # transformation-specific config
    is_builtin = Column(Integer, nullable=False, default=0)
    created_by = Column(BigInteger, nullable=True)
    created_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now(), nullable=False)
