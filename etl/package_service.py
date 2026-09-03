"""ETL Package Service — orchestrates ZIP package ingestion.

Pipeline:
  Upload → Extract → Discover → Profile → Transform → Validate → Load → Report

Reuses existing ETL infrastructure:
  - etl.connectors.connectors.get_connector for file reading
  - etl.profiling.DataProfiler for dataset profiling
  - etl.quality.DataQualityEngine for quality checks
  - etl.transformations.TransformationEngine for transformations
  - etl.load_engine.LoadEngine for database loading
  - etl.lineage.LineageTracker for lineage tracking
  - jobs.service for background job management
"""

from __future__ import annotations

import logging
import os
import tempfile
from datetime import datetime, timezone

from sqlalchemy.orm import Session as DbSession

from etl.lineage import LineageTracker
from etl.load_engine import LoadEngine, LoadMode
from etl.models import ETLDataProfile, ETLQualityReport
from etl.package_models import ETLPackage, ETLPackageFile
from etl.profiling import DataProfiler
from etl.quality import DataQualityEngine
from etl.transformations import TransformationEngine
from etl.zip_extractor import (
    cleanup_extraction,
    extract_zip,
)

logger = logging.getLogger(__name__)

# Supported structured data extensions that can be profiled/loaded
STRUCTURED_EXTENSIONS = {"csv", "tsv", "xlsx", "xls", "json", "xml", "ods"}

# Batch size for file processing to avoid overwhelming resources
FILE_PROCESSING_BATCH_SIZE = 50


def _utcnow():
    return datetime.now(timezone.utc).replace(tzinfo=None)


class ETLPackageService:
    """Service for managing ZIP package ETL ingestion."""

    def __init__(self, db: DbSession):
        self.db = db
        self.profiler = DataProfiler()
        self.quality_engine = DataQualityEngine()
        self.transform_engine = TransformationEngine()
        self.load_engine = LoadEngine()
        self.lineage = LineageTracker(db)

    def create_package(
        self,
        organization_id: int,
        uploaded_by: int,
        filename: str,
        storage_key: str,
        storage_backend: str,
        checksum: str,
        file_size: int,
    ) -> ETLPackage:
        """Create a new ETL package record after ZIP upload."""
        package = ETLPackage(
            organization_id=organization_id,
            uploaded_by=uploaded_by,
            filename=filename,
            storage_key=storage_key,
            storage_backend=storage_backend,
            checksum=checksum,
            file_size_bytes=file_size,
            status="uploaded",
            total_files=0,
        )
        self.db.add(package)
        self.db.commit()
        self.db.refresh(package)

        logger.info(
            "PACKAGE_CREATED package_id=%d org_id=%d filename=%s size=%d checksum=%s",
            package.id,
            organization_id,
            filename,
            file_size,
            checksum[:16],
        )
        return package

    def get_package(self, package_id: int, organization_id: int) -> ETLPackage | None:
        """Get a package by ID, enforcing tenant isolation."""
        return (
            self.db.query(ETLPackage)
            .filter(
                ETLPackage.id == package_id,
                ETLPackage.organization_id == organization_id,
            )
            .first()
        )

    def list_packages(
        self, organization_id: int, limit: int = 50, offset: int = 0
    ) -> list[ETLPackage]:
        """List packages for an organization."""
        return (
            self.db.query(ETLPackage)
            .filter(ETLPackage.organization_id == organization_id)
            .order_by(ETLPackage.created_at.desc())
            .limit(limit)
            .offset(offset)
            .all()
        )

    def get_package_files(
        self,
        package_id: int,
        organization_id: int,
        status: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[ETLPackageFile]:
        """Get files for a package, optionally filtered by status."""
        query = self.db.query(ETLPackageFile).filter(
            ETLPackageFile.package_id == package_id,
            ETLPackageFile.organization_id == organization_id,
        )
        if status:
            query = query.filter(ETLPackageFile.status == status)
        return query.order_by(ETLPackageFile.original_path).limit(limit).offset(offset).all()

    def get_progress(self, package_id: int, organization_id: int) -> dict | None:
        """Get progress summary for a package."""
        pkg = self.get_package(package_id, organization_id)
        if not pkg:
            return None

        total = pkg.total_files or 0
        completed = pkg.completed_files
        failed = pkg.failed_files
        processing = pkg.processing_files
        queued = pkg.queued_files
        duplicate = pkg.duplicate_files
        skipped = pkg.skipped_files
        unsupported = pkg.unsupported_files

        processed = completed + failed + duplicate + skipped + unsupported
        percentage = round((processed / total * 100), 1) if total > 0 else 0.0

        return {
            "package_id": pkg.id,
            "filename": pkg.filename,
            "status": pkg.status,
            "current_stage": pkg.current_stage,
            "total_files": total,
            "discovered_files": pkg.discovered_files,
            "queued_files": queued,
            "processing_files": processing,
            "completed_files": completed,
            "failed_files": failed,
            "duplicate_files": duplicate,
            "skipped_files": skipped,
            "unsupported_files": unsupported,
            "percentage": percentage,
            "total_rows_extracted": pkg.total_rows_extracted,
            "total_rows_loaded": pkg.total_rows_loaded,
            "total_rows_rejected": pkg.total_rows_rejected,
            "overall_quality_score": pkg.overall_quality_score,
            "started_at": pkg.started_at.isoformat() if pkg.started_at else None,
            "completed_at": pkg.completed_at.isoformat() if pkg.completed_at else None,
            "error_message": pkg.error_message,
        }

    def get_errors(self, package_id: int, organization_id: int) -> list[dict]:
        """Get all failed file errors for a package."""
        files = self.get_package_files(package_id, organization_id, status="failed")
        return [
            {
                "file_id": f.id,
                "filename": f.sanitized_filename,
                "original_path": f.original_path,
                "error_message": f.error_message,
                "error_stage": f.error_stage,
                "retry_count": f.retry_count,
            }
            for f in files
        ]

    def process_package(self, package_id: int, zip_path: str, organization_id: int) -> dict:
        """Full pipeline: extract → discover → profile → load.

        This is the main background job handler.
        """
        pkg = self.get_package(package_id, organization_id)
        if not pkg:
            raise ValueError(f"Package {package_id} not found")

        result = {
            "package_id": package_id,
            "total_files": 0,
            "completed": 0,
            "failed": 0,
            "duplicates": 0,
            "unsupported": 0,
            "rows_loaded": 0,
            "quality_score": None,
            "status": "processing",
        }

        # ── Stage 1: Extraction ──────────────────────────────────────────
        pkg.status = "extracting"
        pkg.current_stage = "extraction"
        pkg.started_at = _utcnow()
        self.db.commit()

        logger.info("EXTRACTION_STARTED package_id=%d", package_id)

        extract_base = tempfile.gettempdir()
        extraction = extract_zip(zip_path, extract_base, organization_id)

        if not extraction.success:
            pkg.status = "failed"
            pkg.error_message = extraction.error
            pkg.completed_at = _utcnow()
            self.db.commit()
            result["status"] = "failed"
            result["error"] = extraction.error
            logger.error("EXTRACTION_FAILED package_id=%d error=%s", package_id, extraction.error)
            return result

        logger.info(
            "EXTRACTION_COMPLETED package_id=%d files=%d", package_id, extraction.total_files
        )

        # ── Stage 2: Discovery ────────────────────────────────────────────
        pkg.status = "discovering"
        pkg.current_stage = "discovery"
        pkg.total_files = extraction.total_files
        self.db.commit()

        logger.info(
            "FILE_DISCOVERY_STARTED package_id=%d files=%d", package_id, extraction.total_files
        )

        # Create file records and map to extracted paths
        file_records: list[ETLPackageFile] = []
        extracted_paths: dict[int, str] = {}  # file_rec index -> extracted path
        for idx, ef in enumerate(extraction.files):
            if ef.is_duplicate:
                status = "duplicate"
            elif not ef.is_supported:
                status = "unsupported"
            else:
                status = "discovered"

            file_rec = ETLPackageFile(
                package_id=package_id,
                organization_id=organization_id,
                original_path=ef.original_path,
                sanitized_filename=ef.sanitized_filename,
                file_extension=ef.file_extension,
                mime_type=ef.mime_type,
                file_size_bytes=ef.file_size,
                checksum=ef.checksum,
                status=status,
            )
            self.db.add(file_rec)
            file_records.append(file_rec)
            extracted_paths[idx] = ef.extracted_path

        pkg.discovered_files = len(file_records)
        pkg.duplicate_files = extraction.duplicate_files
        pkg.unsupported_files = extraction.unsupported_files
        self.db.commit()

        logger.info(
            "FILE_DISCOVERY_COMPLETED package_id=%d discovered=%d duplicates=%d unsupported=%d",
            package_id,
            len(file_records),
            extraction.duplicate_files,
            extraction.unsupported_files,
        )

        # ── Stage 3: Processing (profile + load) ──────────────────────────
        pkg.status = "processing"
        pkg.current_stage = "profiling"
        self.db.commit()

        quality_scores = []
        total_rows_loaded = 0
        total_rows_extracted = 0
        total_rows_rejected = 0

        for idx, record in enumerate(file_records):
            if record.status in ("duplicate", "unsupported"):
                continue

            file_path = extracted_paths.get(idx)
            if not file_path:
                record.status = "failed"
                record.error_message = "Extracted file path not found"
                record.error_stage = "discovery"
                self.db.commit()
                result["failed"] += 1
                continue

            try:
                self._process_single_file(record, package_id, organization_id, file_path)
                quality_scores.append(record.quality_score or 0)
                total_rows_loaded += record.rows_loaded or 0
                total_rows_extracted += record.row_count or 0
                result["completed"] += 1
            except Exception as e:
                logger.error(
                    "FILE_FAILED package_id=%d file=%s error=%s",
                    package_id,
                    record.sanitized_filename,
                    e,
                )
                record.status = "failed"
                record.error_message = str(e)
                record.error_stage = "processing"
                self.db.commit()
                result["failed"] += 1

        # Update package aggregates
        pkg.completed_files = result["completed"]
        pkg.failed_files = result["failed"]
        pkg.total_rows_extracted = total_rows_extracted
        pkg.total_rows_loaded = total_rows_loaded
        pkg.total_rows_rejected = total_rows_rejected
        pkg.overall_quality_score = (
            round(sum(quality_scores) / len(quality_scores)) if quality_scores else None
        )

        # Determine final status
        if result["failed"] > 0:
            pkg.status = "completed_with_errors"
        else:
            pkg.status = "completed"

        pkg.current_stage = "completed"
        pkg.completed_at = _utcnow()
        self.db.commit()

        # Cleanup extraction directory
        cleanup_extraction(extraction.extract_dir)

        result["total_files"] = extraction.total_files
        result["duplicates"] = extraction.duplicate_files
        result["unsupported"] = extraction.unsupported_files
        result["rows_loaded"] = total_rows_loaded
        result["quality_score"] = pkg.overall_quality_score
        result["status"] = pkg.status

        logger.info(
            "PACKAGE_COMPLETED package_id=%d status=%s completed=%d failed=%d duplicates=%d quality=%s",
            package_id,
            pkg.status,
            result["completed"],
            result["failed"],
            result["duplicates"],
            pkg.overall_quality_score,
        )

        return result

    def _process_single_file(
        self, record: ETLPackageFile, package_id: int, organization_id: int, file_path: str
    ) -> None:
        """Profile and load a single file."""
        from etl.connectors.connectors import get_connector

        record.status = "processing"
        record.processing_started_at = _utcnow()
        self.db.commit()

        ext = record.file_extension

        if not file_path or not os.path.exists(file_path):
            raise FileNotFoundError(f"Extracted file not found: {record.sanitized_filename}")

        # Read data using existing connectors
        source_type = self._ext_to_connector_type(ext)
        config = {"file_path": file_path}
        connector = get_connector(source_type, config)

        with connector:
            df = connector.extract()

        record.row_count = len(df)
        record.column_count = len(df.columns)

        # Profile
        profile = self.profiler.profile(df, source_name=record.sanitized_filename)
        record.profile_data = profile
        record.quality_score = profile.get("quality_score")

        # Quality check
        quality = self.quality_engine.run_checks(df, source_name=record.sanitized_filename)

        # Save profile and quality to DB
        profile_rec = ETLDataProfile(
            organization_id=organization_id,
            job_id=record.package_id,
            source_name=record.sanitized_filename,
            source_type=ext,
            row_count=profile["row_count"],
            column_count=profile["column_count"],
            profile_data=profile,
            quality_score=profile.get("quality_score"),
        )
        self.db.add(profile_rec)

        quality_rec = ETLQualityReport(
            organization_id=organization_id,
            job_id=record.package_id,
            source_name=record.sanitized_filename,
            overall_score=quality["overall_score"],
            checks_passed=quality["checks_passed"],
            checks_failed=quality["checks_failed"],
            checks_warning=quality["checks_warning"],
            report_data=quality,
            recommendations=quality.get("recommendations"),
        )
        self.db.add(quality_rec)

        # Record lineage
        self.lineage.record(
            source_name=record.sanitized_filename,
            source_type=f"zip:{ext}",
            transformation="profile+quality",
            destination_name=f"package_{package_id}",
            destination_type="dataset",
            organization_id=organization_id,
        )

        # Load into staging table
        table_name = f"stg_pkg_{package_id}_{record.id}"
        try:
            load_result = self.load_engine.load(df, table_name, LoadMode.INSERT)
            record.target_table = table_name
            record.rows_loaded = load_result.get("rows_inserted", 0)
        except Exception as e:
            logger.warning(
                "FILE_LOAD_FAILED package_id=%d file=%s error=%s — marking as completed without load",
                package_id,
                record.sanitized_filename,
                e,
            )
            record.rows_loaded = 0

        record.status = "completed"
        record.completed_at = _utcnow()
        self.db.commit()

        logger.info(
            "FILE_COMPLETED package_id=%d file=%s rows=%d cols=%d quality=%s",
            package_id,
            record.sanitized_filename,
            record.row_count,
            record.column_count,
            record.quality_score,
        )

    def _ext_to_connector_type(self, ext: str) -> str:
        """Map file extension to connector type."""
        mapping = {
            "csv": "csv",
            "tsv": "csv",  # TSV uses CSV connector with tab delimiter
            "xlsx": "excel",
            "xls": "excel",
            "json": "json",
            "xml": "xml",
            "ods": "excel",
        }
        return mapping.get(ext, "csv")

    def retry_failed(self, package_id: int, organization_id: int) -> dict:
        """Retry all failed files in a package."""
        files = self.get_package_files(package_id, organization_id, status="failed")
        retried = 0
        for f in files:
            f.retry_count += 1
            f.last_retry_at = _utcnow()
            f.status = "discovered"
            f.error_message = None
            f.error_stage = None
            retried += 1

        # Reset package status if it was completed_with_errors
        pkg = self.get_package(package_id, organization_id)
        if pkg and pkg.status in ("completed_with_errors", "failed"):
            pkg.status = "processing"
            pkg.current_stage = "profiling"

        self.db.commit()
        logger.info("RETRY_FAILED package_id=%d retried=%d", package_id, retried)
        return {"package_id": package_id, "retried": retried}

    def cancel_package(self, package_id: int, organization_id: int) -> dict:
        """Cancel a package processing."""
        pkg = self.get_package(package_id, organization_id)
        if not pkg:
            return {"package_id": package_id, "cancelled": False, "error": "Package not found"}

        if pkg.status in ("completed", "completed_with_errors", "failed", "cancelled"):
            return {
                "package_id": package_id,
                "cancelled": False,
                "error": f"Cannot cancel package in '{pkg.status}' state",
            }

        pkg.status = "cancelled"
        pkg.completed_at = _utcnow()
        self.db.commit()

        logger.info("PACKAGE_CANCELLED package_id=%d", package_id)
        return {"package_id": package_id, "cancelled": True}

    def get_quality_report(self, package_id: int, organization_id: int) -> dict | None:
        """Generate a quality report for a completed package."""
        pkg = self.get_package(package_id, organization_id)
        if not pkg:
            return None

        files = self.get_package_files(package_id, organization_id, limit=10000)
        completed_files = [f for f in files if f.status == "completed"]
        failed_files = [f for f in files if f.status == "failed"]
        duplicate_files = [f for f in files if f.status == "duplicate"]
        unsupported_files = [f for f in files if f.status == "unsupported"]

        total_rows = sum(f.row_count or 0 for f in completed_files)
        total_loaded = sum(f.rows_loaded or 0 for f in completed_files)

        # Collect all quality recommendations
        all_recommendations = []
        for f in completed_files:
            if f.profile_data and isinstance(f.profile_data, dict):
                recs = f.profile_data.get("recommendations", [])
                if isinstance(recs, list):
                    all_recommendations.extend(recs[:3])  # top 3 per file

        return {
            "package_id": package_id,
            "filename": pkg.filename,
            "total_files": pkg.total_files,
            "successful": len(completed_files),
            "failed": len(failed_files),
            "duplicates": len(duplicate_files),
            "unsupported": len(unsupported_files),
            "datasets_created": len(completed_files),
            "rows_processed": total_rows,
            "rows_loaded": total_loaded,
            "data_quality_score": pkg.overall_quality_score,
            "transformations_applied": "profile+quality+load",
            "warnings": all_recommendations[:20],
            "errors": [
                {"file": f.sanitized_filename, "error": f.error_message} for f in failed_files
            ][:50],
        }
