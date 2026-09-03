"""ORM models for ZIP package ETL ingestion.

Tables: etl_packages, etl_package_files.
Tracks packages containing thousands of files through the full
extract → discover → profile → transform → validate → load pipeline.
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


class ETLPackage(Base):
    """A ZIP package uploaded for bulk ETL processing."""

    __tablename__ = "etl_packages"

    id = Column(BigInt, primary_key=True, autoincrement=True)
    organization_id = Column(BigInteger, nullable=False, index=True)
    uploaded_by = Column(BigInteger, nullable=True, index=True)

    filename = Column(String(500), nullable=False)
    storage_key = Column(String(1000), nullable=False)
    storage_backend = Column(String(50), nullable=False, default="local")
    checksum = Column(String(64), nullable=False, index=True)
    file_size_bytes = Column(BigInteger, nullable=False)

    # Package-level status: uploaded, extracting, discovering, processing,
    # completed, completed_with_errors, failed, cancelled
    status = Column(String(30), nullable=False, default="uploaded", index=True)

    # Current pipeline stage: extraction, discovery, profiling,
    # transformation, validation, loading, reporting
    current_stage = Column(String(50), nullable=True)

    # Aggregate file counts (updated as processing progresses)
    total_files = Column(Integer, nullable=False, default=0)
    discovered_files = Column(Integer, nullable=False, default=0)
    queued_files = Column(Integer, nullable=False, default=0)
    processing_files = Column(Integer, nullable=False, default=0)
    completed_files = Column(Integer, nullable=False, default=0)
    failed_files = Column(Integer, nullable=False, default=0)
    skipped_files = Column(Integer, nullable=False, default=0)
    duplicate_files = Column(Integer, nullable=False, default=0)
    unsupported_files = Column(Integer, nullable=False, default=0)

    # Aggregate row counts
    total_rows_extracted = Column(BigInteger, nullable=False, default=0)
    total_rows_loaded = Column(BigInteger, nullable=False, default=0)
    total_rows_rejected = Column(BigInteger, nullable=False, default=0)

    # Quality summary
    overall_quality_score = Column(Integer, nullable=True)

    # Error tracking
    error_message = Column(Text, nullable=True)
    error_report_path = Column(String(1000), nullable=True)

    # Job linkage
    job_id = Column(BigInteger, nullable=True, index=True)

    # Timestamps
    started_at = Column(TIMESTAMP, nullable=True)
    completed_at = Column(TIMESTAMP, nullable=True)
    created_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now(), nullable=False)

    __table_args__ = (
        Index("ix_etl_packages_org_status", "organization_id", "status"),
    )


class ETLPackageFile(Base):
    """An individual file discovered inside a ZIP package."""

    __tablename__ = "etl_package_files"

    id = Column(BigInt, primary_key=True, autoincrement=True)
    package_id = Column(BigInteger, nullable=False, index=True)
    organization_id = Column(BigInteger, nullable=False, index=True)

    # File metadata
    original_path = Column(String(1000), nullable=False)
    sanitized_filename = Column(String(500), nullable=False)
    file_extension = Column(String(20), nullable=True)
    mime_type = Column(String(100), nullable=True)
    file_size_bytes = Column(BigInteger, nullable=True)
    checksum = Column(String(64), nullable=True, index=True)

    # Processing status: discovered, queued, processing, completed,
    # failed, skipped, duplicate, unsupported
    status = Column(String(20), nullable=False, default="discovered", index=True)

    # Processing stage: profiling, transformation, validation, loading
    stage = Column(String(50), nullable=True)

    # Results
    row_count = Column(Integer, nullable=True)
    column_count = Column(Integer, nullable=True)
    quality_score = Column(Integer, nullable=True)
    profile_data = Column(JSON, nullable=True)
    error_message = Column(Text, nullable=True)
    error_stage = Column(String(50), nullable=True)

    # Duplicate tracking
    duplicate_of_id = Column(BigInteger, nullable=True)

    # Dataset/table linkage
    target_table = Column(String(200), nullable=True)
    rows_loaded = Column(Integer, nullable=True)

    # Retry tracking
    retry_count = Column(Integer, nullable=False, default=0)
    last_retry_at = Column(TIMESTAMP, nullable=True)

    # Job linkage
    job_id = Column(BigInteger, nullable=True, index=True)

    # Timestamps
    discovered_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)
    processing_started_at = Column(TIMESTAMP, nullable=True)
    completed_at = Column(TIMESTAMP, nullable=True)
    created_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now(), nullable=False)

    __table_args__ = (
        Index("ix_etl_pkg_files_pkg_status", "package_id", "status"),
        Index("ix_etl_pkg_files_org_ext", "organization_id", "file_extension"),
    )
