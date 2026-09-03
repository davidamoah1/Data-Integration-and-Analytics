"""FastAPI routes for ZIP package ETL ingestion.

Endpoints:
  POST /api/etl/packages                  — Upload a ZIP package
  GET  /api/etl/packages                  — List packages
  GET  /api/etl/packages/{package_id}     — Get package details
  GET  /api/etl/packages/{package_id}/files — Get package files
  GET  /api/etl/packages/{package_id}/progress — Get progress
  GET  /api/etl/packages/{package_id}/errors   — Get errors
  GET  /api/etl/packages/{package_id}/quality  — Get quality report
  POST /api/etl/packages/{package_id}/retry-failed — Retry failed files
  POST /api/etl/packages/{package_id}/cancel     — Cancel processing
"""

from __future__ import annotations

import hashlib
import logging
import os
import tempfile

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from sqlalchemy.orm import Session as DbSession

from audit.service import log_audit_event
from etl.package_service import ETLPackageService
from etl.zip_extractor import validate_zip
from shared.database import get_db
from shared.tenant import get_tenant_context

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/etl/packages", tags=["ETL Packages"])

# Configurable limits
MAX_ZIP_SIZE = int(os.getenv("ETL_MAX_ZIP_SIZE_MB", "2048")) * 1024 * 1024


def _get_service(db: DbSession) -> ETLPackageService:
    return ETLPackageService(db)


@router.post("", response_model=dict)
async def upload_package(
    file: UploadFile = File(...),
    db: DbSession = Depends(get_db),
    tenant: dict = Depends(get_tenant_context),
):
    """Upload a ZIP package for ETL processing.

    Validates the ZIP, stores it, creates a package record, and enqueues
    a background job. Returns immediately with a package ID.
    """
    current_user = tenant["user"]
    org_id = tenant["organization_id"]

    # Validate filename
    if not file.filename or not file.filename.lower().endswith(".zip"):
        raise HTTPException(status_code=400, detail="File must be a ZIP archive (.zip)")

    # Read file content
    content = await file.read()
    file_size = len(content)

    if file_size == 0:
        raise HTTPException(status_code=400, detail="ZIP file is empty")

    if file_size > MAX_ZIP_SIZE:
        raise HTTPException(
            status_code=413,
            detail=f"ZIP file size {file_size / 1024 / 1024:.1f}MB exceeds maximum "
            f"{MAX_ZIP_SIZE / 1024 / 1024:.0f}MB",
        )

    # Compute checksum
    checksum = hashlib.sha256(content).hexdigest()

    # Save to temp file for validation
    with tempfile.NamedTemporaryFile(delete=False, suffix=".zip") as tmp:
        tmp.write(content)
        tmp_path = tmp.name

    try:
        # Validate ZIP structure
        validation = validate_zip(tmp_path)
        if not validation["valid"]:
            raise HTTPException(
                status_code=400,
                detail=f"ZIP validation failed: {'; '.join(validation['errors'])}",
            )
    finally:
        # Keep the temp file for background processing
        pass

    # Store the ZIP using storage backend
    from storage.storage import get_storage_backend

    storage = get_storage_backend()
    storage_key = f"etl/packages/org_{org_id}/{checksum[:16]}/{file.filename}"
    upload_result = storage.upload(storage_key, content, content_type="application/zip")

    # Create package record
    svc = _get_service(db)
    package = svc.create_package(
        organization_id=org_id,
        uploaded_by=current_user["id"] if current_user else None,
        filename=file.filename,
        storage_key=upload_result.key,
        storage_backend=storage.name,
        checksum=checksum,
        file_size=file_size,
    )

    # Enqueue background job
    from jobs.service import JobService

    job_svc = JobService(db)
    job = await job_svc.create_job(
        organization_id=org_id,
        user_id=current_user["id"] if current_user else None,
        job_type="etl_package",
        name=f"ETL Package: {file.filename}",
        payload={
            "package_id": package.id,
            "zip_path": tmp_path,
            "organization_id": org_id,
        },
    )

    # Link job to package
    package.job_id = job.id
    db.commit()

    # Audit log
    log_audit_event(
        db=db,
        action="etl.package.upload",
        user_id=current_user["id"] if current_user else None,
        organization_id=org_id,
        resource_type="etl_package",
        resource_id=str(package.id),
        metadata={
            "filename": file.filename,
            "size": file_size,
            "checksum": checksum[:16],
            "file_count": validation["file_count"],
            "job_id": job.id,
        },
    )
    db.commit()

    logger.info(
        "PACKAGE_UPLOAD package_id=%d job_id=%d filename=%s size=%d files=%d",
        package.id, job.id, file.filename, file_size, validation["file_count"],
    )

    return {
        "package_id": package.id,
        "job_id": job.id,
        "filename": file.filename,
        "status": "uploaded",
        "file_count": validation["file_count"],
        "checksum": checksum,
        "message": "Package uploaded. Processing will begin in the background.",
    }


@router.get("", response_model=dict)
async def list_packages(
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: DbSession = Depends(get_db),
    tenant: dict = Depends(get_tenant_context),
):
    """List ETL packages for the current organization."""
    org_id = tenant["organization_id"]
    svc = _get_service(db)
    packages = svc.list_packages(org_id, limit=limit, offset=offset)

    return {
        "packages": [
            {
                "id": p.id,
                "filename": p.filename,
                "status": p.status,
                "current_stage": p.current_stage,
                "total_files": p.total_files,
                "completed_files": p.completed_files,
                "failed_files": p.failed_files,
                "file_size_bytes": p.file_size_bytes,
                "overall_quality_score": p.overall_quality_score,
                "created_at": p.created_at.isoformat() if p.created_at else None,
                "completed_at": p.completed_at.isoformat() if p.completed_at else None,
            }
            for p in packages
        ],
        "count": len(packages),
    }


@router.get("/{package_id}", response_model=dict)
async def get_package(
    package_id: int,
    db: DbSession = Depends(get_db),
    tenant: dict = Depends(get_tenant_context),
):
    """Get package details."""
    org_id = tenant["organization_id"]
    svc = _get_service(db)
    pkg = svc.get_package(package_id, org_id)
    if not pkg:
        raise HTTPException(status_code=404, detail="Package not found")

    return {
        "id": pkg.id,
        "filename": pkg.filename,
        "status": pkg.status,
        "current_stage": pkg.current_stage,
        "total_files": pkg.total_files,
        "discovered_files": pkg.discovered_files,
        "completed_files": pkg.completed_files,
        "failed_files": pkg.failed_files,
        "duplicate_files": pkg.duplicate_files,
        "unsupported_files": pkg.unsupported_files,
        "processing_files": pkg.processing_files,
        "queued_files": pkg.queued_files,
        "total_rows_extracted": pkg.total_rows_extracted,
        "total_rows_loaded": pkg.total_rows_loaded,
        "overall_quality_score": pkg.overall_quality_score,
        "file_size_bytes": pkg.file_size_bytes,
        "checksum": pkg.checksum,
        "job_id": pkg.job_id,
        "error_message": pkg.error_message,
        "started_at": pkg.started_at.isoformat() if pkg.started_at else None,
        "completed_at": pkg.completed_at.isoformat() if pkg.completed_at else None,
        "created_at": pkg.created_at.isoformat() if pkg.created_at else None,
    }


@router.get("/{package_id}/progress", response_model=dict)
async def get_progress(
    package_id: int,
    db: DbSession = Depends(get_db),
    tenant: dict = Depends(get_tenant_context),
):
    """Get real-time progress for a package."""
    org_id = tenant["organization_id"]
    svc = _get_service(db)
    progress = svc.get_progress(package_id, org_id)
    if not progress:
        raise HTTPException(status_code=404, detail="Package not found")
    return progress


@router.get("/{package_id}/files", response_model=dict)
async def get_files(
    package_id: int,
    status: str | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
    db: DbSession = Depends(get_db),
    tenant: dict = Depends(get_tenant_context),
):
    """Get files in a package."""
    org_id = tenant["organization_id"]
    svc = _get_service(db)
    files = svc.get_package_files(package_id, org_id, status=status, limit=limit, offset=offset)

    return {
        "files": [
            {
                "id": f.id,
                "filename": f.sanitized_filename,
                "original_path": f.original_path,
                "extension": f.file_extension,
                "size": f.file_size_bytes,
                "status": f.status,
                "stage": f.stage,
                "row_count": f.row_count,
                "column_count": f.column_count,
                "quality_score": f.quality_score,
                "error_message": f.error_message,
                "error_stage": f.error_stage,
                "retry_count": f.retry_count,
                "target_table": f.target_table,
                "rows_loaded": f.rows_loaded,
                "completed_at": f.completed_at.isoformat() if f.completed_at else None,
            }
            for f in files
        ],
        "count": len(files),
    }


@router.get("/{package_id}/errors", response_model=dict)
async def get_errors(
    package_id: int,
    db: DbSession = Depends(get_db),
    tenant: dict = Depends(get_tenant_context),
):
    """Get all errors for a package."""
    org_id = tenant["organization_id"]
    svc = _get_service(db)
    errors = svc.get_errors(package_id, org_id)
    return {"package_id": package_id, "errors": errors, "count": len(errors)}


@router.get("/{package_id}/quality", response_model=dict)
async def get_quality_report(
    package_id: int,
    db: DbSession = Depends(get_db),
    tenant: dict = Depends(get_tenant_context),
):
    """Get quality report for a package."""
    org_id = tenant["organization_id"]
    svc = _get_service(db)
    report = svc.get_quality_report(package_id, org_id)
    if not report:
        raise HTTPException(status_code=404, detail="Package not found")
    return report


@router.post("/{package_id}/retry-failed", response_model=dict)
async def retry_failed(
    package_id: int,
    db: DbSession = Depends(get_db),
    tenant: dict = Depends(get_tenant_context),
):
    """Retry all failed files in a package."""
    org_id = tenant["organization_id"]
    svc = _get_service(db)
    result = svc.retry_failed(package_id, org_id)
    return result


@router.post("/{package_id}/cancel", response_model=dict)
async def cancel_package(
    package_id: int,
    db: DbSession = Depends(get_db),
    tenant: dict = Depends(get_tenant_context),
):
    """Cancel package processing."""
    org_id = tenant["organization_id"]
    svc = _get_service(db)
    result = svc.cancel_package(package_id, org_id)
    if not result.get("cancelled"):
        raise HTTPException(status_code=400, detail=result.get("error", "Cannot cancel"))
    return result
