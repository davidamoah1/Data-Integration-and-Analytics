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
    classify_file_type,
    cleanup_extraction,
    extract_zip,
    verify_magic_bytes,
)

logger = logging.getLogger(__name__)

# Supported structured data extensions that can be profiled/loaded
STRUCTURED_EXTENSIONS = {"csv", "tsv", "xlsx", "xls", "json", "xml", "ods"}

# Document/image extensions routed to the capture pipeline
DOCUMENT_EXTENSIONS = {"pdf", "txt"}
IMAGE_EXTENSIONS = {"jpg", "jpeg", "png", "tiff", "tif", "bmp"}

# Batch size for file processing to avoid overwhelming resources
FILE_PROCESSING_BATCH_SIZE = 50


def _cert_doc_type_keys() -> set[str]:
    """Return the set of certificate document type keys from the capture registry."""
    from certificates.routes import CERTIFICATE_DOC_TYPES

    return CERTIFICATE_DOC_TYPES


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
        """Create a new ETL package record after ZIP upload.

        Idempotency: if a package with the same checksum already exists
        for this organization, return the existing package instead of
        creating a duplicate.
        """
        existing = (
            self.db.query(ETLPackage)
            .filter(
                ETLPackage.organization_id == organization_id,
                ETLPackage.checksum == checksum,
            )
            .first()
        )
        if existing:
            logger.info(
                "PACKAGE_DUPLICATE_SKIP package_id=%d checksum=%s — returning existing",
                existing.id,
                checksum[:16],
            )
            return existing

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

    def find_by_checksum(self, organization_id: int, checksum: str) -> ETLPackage | None:
        """Find a package by checksum for idempotency check."""
        return (
            self.db.query(ETLPackage)
            .filter(
                ETLPackage.organization_id == organization_id,
                ETLPackage.checksum == checksum,
            )
            .first()
        )

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
        self,
        organization_id: int,
        limit: int = 50,
        offset: int = 0,
        status: str | None = None,
        search: str | None = None,
    ) -> list[ETLPackage]:
        """List packages for an organization with optional filters."""
        query = self.db.query(ETLPackage).filter(ETLPackage.organization_id == organization_id)
        if status:
            query = query.filter(ETLPackage.status == status)
        if search:
            query = query.filter(ETLPackage.filename.ilike(f"%{search}%"))
        return query.order_by(ETLPackage.created_at.desc()).limit(limit).offset(offset).all()

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
        import time as _time

        t0 = _time.monotonic()

        def _log(stage: str, status: str, **extra) -> None:
            elapsed_ms = int((_time.monotonic() - t0) * 1000)
            logger.info(
                "PACKAGE_PROCESS package_id=%d organization_id=%d filename=%s size=%d "
                "stage=%s status=%s elapsed_ms=%d%s",
                package_id,
                organization_id,
                pkg.filename if pkg else "?",
                pkg.file_size_bytes if pkg else 0,
                stage,
                status,
                elapsed_ms,
                "".join(f" {k}={v}" for k, v in extra.items()),
            )

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

        _log("extraction", "started")

        extract_base = tempfile.gettempdir()
        extraction = extract_zip(zip_path, extract_base, organization_id)

        if not extraction.success:
            pkg.status = "failed"
            pkg.error_message = extraction.error
            pkg.completed_at = _utcnow()
            self.db.commit()
            result["status"] = "failed"
            result["error"] = extraction.error
            _log("extraction", "failed", error=extraction.error)
            return result

        _log("extraction", "completed", files=extraction.total_files)

        # ── Stage 2: Discovery ────────────────────────────────────────────
        pkg.status = "discovering"
        pkg.current_stage = "discovery"
        pkg.total_files = extraction.total_files
        self.db.commit()

        _log("discovery", "started")

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

        _log(
            "discovery",
            "completed",
            discovered=len(file_records),
            duplicates=extraction.duplicate_files,
            unsupported=extraction.unsupported_files,
        )

        # ── Stage 3: Processing (profile + load) ──────────────────────────
        pkg.status = "processing"
        pkg.current_stage = "profiling"
        self.db.commit()

        _log("processing", "started")

        quality_scores = []
        total_rows_loaded = 0
        total_rows_extracted = 0
        total_rows_rejected = 0
        document_statuses = {
            "document_processed",
            "certificate_detected",
            "document_extraction_pending",
            "document_extraction_failed",
        }

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

                # Only collect quality scores for structured data (not documents)
                if record.status not in document_statuses and record.quality_score:
                    quality_scores.append(record.quality_score)
                if record.status == "failed":
                    result["failed"] += 1
                else:
                    result["completed"] += 1
                total_rows_loaded += record.rows_loaded or 0
                total_rows_extracted += record.row_count or 0
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

        _log(
            "processing",
            "completed",
            completed=result["completed"],
            failed=result["failed"],
            rows_loaded=total_rows_loaded,
        )

        # Cleanup extraction directory
        cleanup_extraction(extraction.extract_dir)

        result["total_files"] = extraction.total_files
        result["duplicates"] = extraction.duplicate_files
        result["unsupported"] = extraction.unsupported_files
        result["rows_loaded"] = total_rows_loaded
        result["quality_score"] = pkg.overall_quality_score
        result["status"] = pkg.status

        _log(
            "package",
            pkg.status,
            completed=result["completed"],
            failed=result["failed"],
            quality=pkg.overall_quality_score,
        )

        return result

    def _process_single_file(
        self, record: ETLPackageFile, package_id: int, organization_id: int, file_path: str
    ) -> None:
        """Process a single file based on its classification.

        STRUCTURED_DATA → ETL connector pipeline (profile + quality + load)
        DOCUMENT/IMAGE  → Capture pipeline (PDF text extraction / OCR)
        """
        import time as _time

        t0 = _time.monotonic()
        record.status = "processing"
        record.processing_started_at = _utcnow()
        self.db.commit()

        ext = record.file_extension
        filename = record.sanitized_filename

        if not file_path or not os.path.exists(file_path):
            raise FileNotFoundError(f"Extracted file not found: {filename}")

        # ── Classify the file ───────────────────────────────────────────
        file_category = classify_file_type(filename, file_path)

        # Verify magic bytes for documents and images (security)
        if file_category in ("DOCUMENT", "IMAGE"):
            if not verify_magic_bytes(filename, file_path):
                record.status = "failed"
                record.error_stage = "validation"
                record.error_message = (
                    f"File '{filename}' content does not match its extension "
                    f"'.{ext}' — magic byte verification failed"
                )
                self.db.commit()
                logger.warning(
                    "FILE_FAILED package_id=%d file=%s stage=validation "
                    "error_code=MAGIC_BYTE_MISMATCH elapsed_ms=%d",
                    package_id,
                    filename,
                    int((_time.monotonic() - t0) * 1000),
                )
                return

        # ── Route based on classification ───────────────────────────────
        if file_category == "STRUCTURED_DATA":
            self._process_structured_file(record, package_id, organization_id, file_path)
        elif file_category in ("DOCUMENT", "IMAGE"):
            self._process_document_file(
                record, package_id, organization_id, file_path, file_category
            )
        else:
            record.status = "unsupported"
            record.error_message = f"Unsupported file type: .{ext}"
            record.error_stage = "classification"
            self.db.commit()
            logger.info(
                "FILE_SKIPPED package_id=%d file=%s reason=unsupported_type ext=%s",
                package_id,
                filename,
                ext,
            )

    def _process_structured_file(
        self, record: ETLPackageFile, package_id: int, organization_id: int, file_path: str
    ) -> None:
        """Profile and load a structured data file (CSV, XLSX, JSON, etc.)."""
        from etl.connectors.connectors import get_connector

        ext = record.file_extension
        record.stage = "profiling"
        self.db.commit()

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

    def _process_document_file(
        self,
        record: ETLPackageFile,
        package_id: int,
        organization_id: int,
        file_path: str,
        file_category: str,
    ) -> None:
        """Route a document/image file to the capture pipeline.

        PDFs and images are binary files that must NOT be decoded as UTF-8.
        They are processed through the existing Smart Data Capture pipeline
        which uses PyMuPDF for PDF text extraction and Tesseract for OCR.

        The file is uploaded to the capture service, then processed through
        the document intelligence pipeline (OCR → classify → extract fields).
        """
        import time as _time

        t0 = _time.monotonic()
        filename = record.sanitized_filename

        logger.info(
            "FILE_PROCESSING package_id=%d file=%s detected_type=%s "
            "mime_type=%s size=%d stage=document_extraction",
            package_id,
            filename,
            file_category,
            record.mime_type,
            record.file_size_bytes or 0,
        )

        record.stage = "document_extraction"
        self.db.commit()

        try:
            # Read file as binary — never decode as text
            with open(file_path, "rb") as f:
                file_content = f.read()

            # Use existing capture service to upload and process
            from capture.service import CaptureService

            capture_svc = CaptureService(self.db)

            # Upload to capture pipeline
            doc = capture_svc.upload_document(
                organization_id=organization_id,
                user_id=record.package_id,  # use package_id as actor
                filename=filename,
                file_content=file_content,
                source="etl_package",
            )

            logger.info(
                "FILE_DOCUMENT_DETECTED package_id=%d file=%s "
                "capture_document_id=%d detected_type=%s",
                package_id,
                filename,
                doc.id,
                file_category,
            )

            # Attempt to process the document through the capture pipeline
            try:
                processed_doc = capture_svc.process_document(doc.id)
                capture_status = processed_doc.status
                doc_type = processed_doc.document_type or "unknown"
                doc_type_label = processed_doc.document_type_label or "Unknown"

                logger.info(
                    "FILE_DOCUMENT_PROCESSED package_id=%d file=%s "
                    "capture_document_id=%d status=%s document_type=%s "
                    "elapsed_ms=%d",
                    package_id,
                    filename,
                    doc.id,
                    capture_status,
                    doc_type,
                    int((_time.monotonic() - t0) * 1000),
                )

                # Determine the appropriate ETL status
                if capture_status == "ready_for_review":
                    if doc_type in _cert_doc_type_keys():
                        etl_status = "certificate_detected"
                    else:
                        etl_status = "document_processed"
                elif capture_status == "failed":
                    etl_status = "document_extraction_failed"
                else:
                    etl_status = "document_processed"

                record.status = etl_status
                record.error_message = None
                record.error_stage = None

                # Store document metadata
                record.profile_data = {
                    "capture_document_id": doc.id,
                    "document_type": doc_type,
                    "document_type_label": doc_type_label,
                    "classification_confidence": processed_doc.classification_confidence,
                    "processing_status": capture_status,
                    "file_category": file_category,
                    "extraction_method": getattr(processed_doc, "extraction_method", "pdf_text"),
                }

                # For documents, row_count represents extracted fields/records
                # not tabular rows
                if hasattr(processed_doc, "fields") and processed_doc.fields:
                    record.row_count = len(processed_doc.fields)
                else:
                    # Count fields from DB
                    from capture.models import CaptureField

                    field_count = (
                        self.db.query(CaptureField)
                        .filter(CaptureField.document_id == doc.id)
                        .count()
                    )
                    record.row_count = field_count

                record.column_count = 0  # Not applicable for documents
                record.quality_score = None  # Quality scoring only for structured data

            except Exception as proc_err:
                logger.warning(
                    "FILE_DOCUMENT_EXTRACTION_FAILED package_id=%d file=%s "
                    "capture_document_id=%d error=%s elapsed_ms=%d",
                    package_id,
                    filename,
                    doc.id,
                    proc_err,
                    int((_time.monotonic() - t0) * 1000),
                )
                record.status = "document_extraction_pending"
                record.error_message = str(proc_err)
                record.error_stage = "document_extraction"
                record.profile_data = {
                    "capture_document_id": doc.id,
                    "file_category": file_category,
                    "processing_status": "pending",
                }

        except Exception as e:
            logger.error(
                "FILE_FAILED package_id=%d file=%s stage=document_upload "
                "error_code=DOCUMENT_UPLOAD_ERROR error_message=%s elapsed_ms=%d",
                package_id,
                filename,
                e,
                int((_time.monotonic() - t0) * 1000),
            )
            record.status = "failed"
            record.error_message = str(e)
            record.error_stage = "document_upload"

        record.completed_at = _utcnow()
        self.db.commit()

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

    def download_package(
        self, package_id: int, organization_id: int
    ) -> tuple[bytes, str, str] | None:
        """Download the original ZIP file for a package.

        Returns (content, filename, content_type) or None if not found.
        """
        pkg = self.get_package(package_id, organization_id)
        if not pkg:
            return None

        from storage.storage import get_storage_backend

        storage = get_storage_backend()
        content = storage.download(pkg.storage_key)
        return content, pkg.filename, "application/zip"

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
