"""FastAPI routes for the Smart Data Capture platform."""

from __future__ import annotations

import logging
import zipfile

from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    Query,
    UploadFile,
    status,
)
from sqlalchemy.orm import Session as DbSession

from capture.document_types import ALL_DOCUMENT_TYPES, INDUSTRIES
from capture.ocr_engine import is_ocr_available
from capture.repositories import CaptureAuditLogRepository
from capture.service import CaptureError, CaptureService
from shared.database import get_db
from shared.dependencies import get_current_user
from shared.tenant import get_current_organization_id

router = APIRouter(prefix="/api/capture", tags=["smart-data-capture"])

logger = logging.getLogger(__name__)


# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# Metadata
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•


@router.get("/status")
async def capture_engine_status():
    return {
        "ocr_available": is_ocr_available(),
        "supported_industries": INDUSTRIES,
    }


@router.get("/document-types")
async def list_document_types_route(industry: str | None = Query(None)):
    types = (
        ALL_DOCUMENT_TYPES
        if not industry
        else [d for d in ALL_DOCUMENT_TYPES if d.industry == industry]
    )
    return {
        "document_types": [
            {
                "key": d.key,
                "label": d.label,
                "industry": d.industry,
                "fields": [
                    {
                        "name": f.name,
                        "label": f.label,
                        "data_type": f.data_type,
                        "required": f.required,
                    }
                    for f in d.fields
                ],
            }
            for d in types
        ]
    }


# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# Upload
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•


def _serialize_document(doc) -> dict:
    return {
        "id": doc.id,
        "batch_id": doc.batch_id,
        "filename": doc.filename,
        "file_type": doc.file_type,
        "page_count": doc.page_count,
        "status": doc.status,
        "error_message": doc.error_message,
        "industry": doc.industry,
        "document_type": doc.document_type,
        "document_type_label": doc.document_type_label,
        "classification_confidence": doc.classification_confidence,
        "needs_type_confirmation": doc.needs_type_confirmation,
        "overall_confidence": doc.overall_confidence,
        "duplicate_of_id": doc.duplicate_of_id,
        "extracted_tables": doc.extracted_tables,
        "created_at": doc.created_at.isoformat() if doc.created_at else None,
        "processed_at": doc.processed_at.isoformat() if doc.processed_at else None,
        "reviewed_at": doc.reviewed_at.isoformat() if doc.reviewed_at else None,
        "approved_at": doc.approved_at.isoformat() if doc.approved_at else None,
    }


def _serialize_field(field) -> dict:
    return {
        "id": field.id,
        "field_name": field.field_name,
        "field_label": field.field_label,
        "data_type": field.data_type,
        "value": field.value,
        "raw_value": field.raw_value,
        "confidence_score": field.confidence_score,
        "is_low_confidence": field.is_low_confidence,
        "was_corrected": field.was_corrected,
        "is_valid": field.is_valid,
        "validation_message": field.validation_message,
        "page_number": field.page_number,
    }


@router.post("/documents/upload", status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(...),
    db: DbSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    try:
        org_id = get_current_organization_id(current_user, db)
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Failed to resolve organization for user_id=%s", current_user["id"])
        raise HTTPException(status_code=500, detail=f"Organization lookup failed: {e}") from e

    svc = CaptureService(db)
    content = await file.read()

    try:
        doc = svc.upload_document(org_id, current_user["id"], file.filename or "upload", content)
    except CaptureError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        logger.exception("Failed to upload document: org_id=%s filename=%s", org_id, file.filename)
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Upload failed: {e}") from e

    # Try to create a background job for processing
    job_id = None
    try:
        from jobs.handlers import register_builtin_handlers
        from jobs.service import JobService, get_registered_types

        # Ensure handlers are registered (idempotent)
        if "ocr_document" not in get_registered_types():
            register_builtin_handlers()

        job_svc = JobService(db)
        job = job_svc.create_job(
            organization_id=org_id,
            user_id=current_user["id"],
            job_type="ocr_document",
            name=f"OCR: {doc.filename}",
            description=f"Processing document '{doc.filename}'",
            payload={"document_id": doc.id, "organization_id": org_id},
        )
        job_id = job.id
        db.commit()
    except Exception as e:
        logger.warning("Job system unavailable, using thread for processing: %s", e)
        import threading

        threading.Thread(target=_process_document_task, args=(doc.id,), daemon=True).start()

    # Re-fetch the doc to get fresh state
    db.refresh(doc)
    result = _serialize_document(doc)
    result["job_id"] = job_id
    return result


@router.post("/batches/upload-zip", status_code=status.HTTP_201_CREATED)
async def upload_zip_batch(
    file: UploadFile = File(...),
    batch_name: str | None = None,
    industry: str | None = None,
    db: DbSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    org_id = get_current_organization_id(current_user, db)
    svc = CaptureService(db)
    content = await file.read()

    try:
        batch, docs = svc.upload_zip_batch(
            org_id, current_user["id"], file.filename or "batch.zip", content, batch_name, industry
        )
    except CaptureError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except zipfile.BadZipFile as e:
        raise HTTPException(status_code=400, detail="Invalid or corrupted ZIP file.") from e

    # Create a background job for OCR processing
    job = None
    try:
        from jobs.service import JobService

        job_svc = JobService(db)
        job = job_svc.create_job(
            organization_id=org_id,
            user_id=current_user["id"],
            job_type="ocr_batch",
            name=f"OCR Batch: {batch.name}",
            description=f"Processing {batch.total_documents} documents from batch '{batch.name}'",
            payload={"batch_id": batch.id, "organization_id": org_id},
        )
    except Exception as e:
        logger.warning("Job system unavailable for batch, using thread: %s", e)
        import threading

        threading.Thread(target=_process_batch_task, args=(batch.id,), daemon=True).start()

    return {
        "batch_id": batch.id,
        "name": batch.name,
        "total_documents": batch.total_documents,
        "status": batch.status,
        "documents": [_serialize_document(d) for d in docs],
        "job_id": job.id if job else None,
    }


def _process_batch_task(batch_id: int) -> None:
    from shared.database import get_engine, get_session_factory

    engine = get_engine()
    factory = get_session_factory(engine)
    db = factory()
    try:
        CaptureService(db).process_batch(batch_id)
    finally:
        db.close()


def _process_document_task(document_id: int) -> None:
    from shared.database import get_engine, get_session_factory

    engine = get_engine()
    factory = get_session_factory(engine)
    db = factory()
    try:
        CaptureService(db).process_document(document_id)
    finally:
        db.close()


@router.get("/batches")
async def list_batches(
    limit: int = Query(50, le=200),
    offset: int = Query(0, ge=0),
    db: DbSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    org_id = get_current_organization_id(current_user, db)
    svc = CaptureService(db)
    batches = svc.list_batches(org_id, limit, offset)
    return {
        "batches": [
            {
                "id": b.id,
                "name": b.name,
                "industry": b.industry,
                "total_documents": b.total_documents,
                "processed_documents": b.processed_documents,
                "failed_documents": b.failed_documents,
                "status": b.status,
                "created_at": b.created_at.isoformat() if b.created_at else None,
            }
            for b in batches
        ]
    }


@router.get("/batches/{batch_id}")
async def get_batch(
    batch_id: int,
    db: DbSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    org_id = get_current_organization_id(current_user, db)
    svc = CaptureService(db)
    batch = svc.get_batch(batch_id, org_id)
    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")

    documents = svc.list_documents(org_id, batch_id=batch_id, limit=500)
    return {
        "id": batch.id,
        "name": batch.name,
        "status": batch.status,
        "total_documents": batch.total_documents,
        "processed_documents": batch.processed_documents,
        "failed_documents": batch.failed_documents,
        "documents": [_serialize_document(d) for d in documents],
    }


# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# Documents / review
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•


@router.get("/documents")
async def list_documents(
    status_filter: str | None = Query(None, alias="status"),
    document_type: str | None = Query(None),
    batch_id: int | None = Query(None),
    limit: int = Query(50, le=200),
    offset: int = Query(0, ge=0),
    db: DbSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    org_id = get_current_organization_id(current_user, db)
    svc = CaptureService(db)
    docs = svc.list_documents(org_id, status_filter, document_type, batch_id, limit, offset)
    return {"documents": [_serialize_document(d) for d in docs]}


@router.get("/documents/{document_id}")
async def get_document(
    document_id: int,
    db: DbSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    org_id = get_current_organization_id(current_user, db)
    svc = CaptureService(db)
    doc = svc.get_document(document_id, org_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    fields = svc.get_fields(document_id)
    payload = _serialize_document(doc)
    payload["fields"] = [_serialize_field(f) for f in fields]
    payload["raw_ocr_text"] = doc.raw_ocr_text
    return payload


@router.patch("/documents/{document_id}/fields/{field_id}")
async def update_field(
    document_id: int,
    field_id: int,
    payload: dict,
    db: DbSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    org_id = get_current_organization_id(current_user, db)
    svc = CaptureService(db)
    try:
        field = svc.update_field(
            document_id, field_id, org_id, payload.get("value", ""), current_user["id"]
        )
    except CaptureError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    return _serialize_field(field)


@router.post("/documents/{document_id}/document-type")
async def set_document_type(
    document_id: int,
    payload: dict,
    db: DbSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    org_id = get_current_organization_id(current_user, db)
    svc = CaptureService(db)
    try:
        doc = svc.set_document_type(
            document_id, org_id, payload["document_type"], current_user["id"]
        )
    except CaptureError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    return _serialize_document(doc)


@router.post("/documents/{document_id}/approve")
async def approve_document(
    document_id: int,
    db: DbSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    org_id = get_current_organization_id(current_user, db)
    svc = CaptureService(db)
    try:
        doc = svc.approve_document(document_id, org_id, current_user["id"])
    except CaptureError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    return _serialize_document(doc)


@router.post("/documents/{document_id}/reject")
async def reject_document(
    document_id: int,
    payload: dict | None = None,
    db: DbSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    org_id = get_current_organization_id(current_user, db)
    svc = CaptureService(db)
    try:
        doc = svc.reject_document(
            document_id, org_id, current_user["id"], (payload or {}).get("reason")
        )
    except CaptureError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    return _serialize_document(doc)


@router.post("/documents/{document_id}/draft")
async def save_draft(
    document_id: int,
    db: DbSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    org_id = get_current_organization_id(current_user, db)
    svc = CaptureService(db)
    try:
        doc = svc.save_draft(document_id, org_id, current_user["id"])
    except CaptureError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    return _serialize_document(doc)


@router.post("/documents/{document_id}/retry")
async def retry_document(
    document_id: int,
    db: DbSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    org_id = get_current_organization_id(current_user, db)
    svc = CaptureService(db)
    doc = svc.get_document(document_id, org_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    # Reset status for reprocessing â€” the file is already stored, no re-upload needed
    doc.status = "uploaded"
    doc.error_message = None
    db.commit()

    # Try job system first, fall back to thread
    job_id = None
    try:
        from jobs.handlers import register_builtin_handlers
        from jobs.service import JobService, get_registered_types

        # Ensure handlers are registered (idempotent)
        if "ocr_document" not in get_registered_types():
            register_builtin_handlers()

        job_svc = JobService(db)
        job = job_svc.create_job(
            organization_id=org_id,
            user_id=current_user["id"],
            job_type="ocr_document",
            name=f"Retry OCR: {doc.filename}",
            description=f"Reprocessing document '{doc.filename}'",
            payload={"document_id": document_id, "organization_id": org_id, "retry": True},
        )
        job_id = job.id
        db.commit()
    except Exception as e:
        logger.warning("Job system unavailable, using thread for retry: %s", e)
        import threading

        threading.Thread(target=_process_document_task, args=(document_id,), daemon=True).start()

    db.refresh(doc)
    result = _serialize_document(doc)
    result["job_id"] = job_id
    return result


@router.delete("/documents/{document_id}")
async def delete_document(
    document_id: int,
    db: DbSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    org_id = get_current_organization_id(current_user, db)
    svc = CaptureService(db)
    try:
        svc.delete_document(document_id, org_id, current_user["id"])
    except CaptureError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    return {"success": True}


@router.get("/documents/{document_id}/audit-log")
async def get_audit_log(
    document_id: int,
    db: DbSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    org_id = get_current_organization_id(current_user, db)
    audit_repo = CaptureAuditLogRepository(db)
    logs = audit_repo.list_by_document(document_id, org_id)
    return {
        "logs": [
            {
                "action": log.action,
                "actor_id": log.actor_id,
                "details": log.details,
                "created_at": log.created_at.isoformat() if log.created_at else None,
            }
            for log in logs
        ]
    }


# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# Database Entry (export approved documents to dataset)
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•


@router.post("/documents/{document_id}/export")
async def export_document_to_dataset(
    document_id: int,
    payload: dict | None = None,
    db: DbSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Export an approved document's extracted fields to a dataset CSV (Database Entry step)."""
    org_id = get_current_organization_id(current_user, db)
    svc = CaptureService(db)
    try:
        result = svc.export_to_dataset(
            document_id,
            org_id,
            current_user["id"],
            dataset_name=(payload or {}).get("dataset_name"),
        )
    except CaptureError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    return result


@router.post("/documents/bulk-export")
async def bulk_export_approved_documents(
    payload: dict | None = None,
    db: DbSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Export all approved documents to a single dataset CSV."""
    org_id = get_current_organization_id(current_user, db)
    svc = CaptureService(db)
    try:
        result = svc.bulk_export_approved(
            org_id,
            current_user["id"],
            document_type=(payload or {}).get("document_type"),
            dataset_name=(payload or {}).get("dataset_name"),
        )
    except CaptureError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    return result


# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# Analytics (dashboard integration)
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•


@router.get("/analytics/summary")
async def analytics_summary(
    db: DbSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    org_id = get_current_organization_id(current_user, db)
    svc = CaptureService(db)
    return svc.get_analytics_summary(org_id)
