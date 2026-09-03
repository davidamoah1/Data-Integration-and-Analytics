"""Built-in job handlers for ETL, OCR, Reports, and large imports.

Each handler receives (job_id, payload, db) and returns a result dict.
Handlers are registered at import time so the JobService can dispatch
to them.
"""

from __future__ import annotations

import logging

from sqlalchemy.orm import Session as DbSession

from jobs.service import register_handler, update_job_progress
from performance.queue import TaskPriority

logger = logging.getLogger(__name__)


# â”€â”€ ETL Pipeline Handler â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€


def _handle_etl_run(job_id: int, payload: dict, db: DbSession) -> dict:
    """Run an ETL pipeline as a background job."""
    from services.etl_service import ETLService

    pipeline_id = payload.get("pipeline_id")
    update_job_progress(job_id, 0.1, "Initializing ETL pipeline")

    svc = ETLService()
    update_job_progress(job_id, 0.2, "Running pipeline")

    metrics = svc.run_pipeline(pipeline_id=int(pipeline_id)) if pipeline_id else svc.run_pipeline()

    update_job_progress(job_id, 0.9, "Pipeline completed, collecting metrics")
    return {"metrics": metrics}


# â”€â”€ OCR / Capture Batch Handler â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€


def _handle_ocr_document(job_id: int, payload: dict, db: DbSession) -> dict:
    """Process a single capture document (OCR extraction) as a background job."""
    from capture.service import CaptureService

    document_id = payload.get("document_id")
    if not document_id:
        raise ValueError("document_id is required for ocr_document jobs")

    update_job_progress(job_id, 0.1, "Starting document processing")

    svc = CaptureService(db)
    doc = svc.get_document(document_id, payload.get("organization_id", 0))
    if not doc:
        raise ValueError(f"Document {document_id} not found")

    update_job_progress(job_id, 0.3, f"Processing document '{doc.filename}'")

    # Start a heartbeat thread so the watchdog doesn't kill long-running
    # OCR jobs. The thread updates the job's heartbeat every 60s while
    # process_document() is running. It stops when processing completes.
    import threading

    heartbeat_stop = threading.Event()

    def _heartbeat_loop():
        from jobs.service import update_heartbeat

        while not heartbeat_stop.wait(timeout=60):
            try:
                update_heartbeat(job_id)
            except Exception:  # nosec B110 — heartbeat must not crash the worker
                pass

    hb_thread = threading.Thread(target=_heartbeat_loop, daemon=True)
    hb_thread.start()

    try:
        doc = svc.process_document(document_id)
    finally:
        heartbeat_stop.set()

    update_job_progress(job_id, 1.0, f"Document processing complete: {doc.status}")

    return {
        "document_id": document_id,
        "status": doc.status,
        "error_message": doc.error_message,
    }


def _handle_ocr_batch(job_id: int, payload: dict, db: DbSession) -> dict:
    """Process a capture batch (OCR extraction) as a background job."""
    from capture.service import CaptureService

    batch_id = payload.get("batch_id")
    if not batch_id:
        raise ValueError("batch_id is required for ocr_batch jobs")

    update_job_progress(job_id, 0.1, "Starting OCR batch processing")

    svc = CaptureService(db)
    batch = svc.get_batch(batch_id, payload.get("organization_id", 0))
    if not batch:
        raise ValueError(f"Batch {batch_id} not found")

    update_job_progress(job_id, 0.2, f"Processing batch '{batch.name}'")

    # Heartbeat thread for long-running batch processing
    import threading

    heartbeat_stop = threading.Event()

    def _heartbeat_loop():
        from jobs.service import update_heartbeat

        while not heartbeat_stop.wait(timeout=60):
            try:
                update_heartbeat(job_id)
            except Exception:  # nosec B110 — heartbeat must not crash the worker
                pass

    hb_thread = threading.Thread(target=_heartbeat_loop, daemon=True)
    hb_thread.start()

    try:
        svc.process_batch(batch_id)
    finally:
        heartbeat_stop.set()

    # Refresh to get final counts
    db.refresh(batch)
    update_job_progress(
        job_id,
        1.0,
        f"Batch complete: {batch.processed_documents} processed, {batch.failed_documents} failed",
    )

    return {
        "batch_id": batch_id,
        "processed": batch.processed_documents,
        "failed": batch.failed_documents,
        "status": batch.status,
    }


# â”€â”€ Report Generation Handler â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€


def _handle_report_gen(job_id: int, payload: dict, db: DbSession) -> dict:
    """Generate an AI report as a background job."""
    from ai.engines.report_writer import AIReportWriter

    report_type = payload.get("report_type", "executive_summary")
    title = payload.get("title", "Generated Report")
    user_id = payload.get("user_id")
    parameters = payload.get("parameters", {})

    update_job_progress(job_id, 0.1, "Initializing report writer")

    writer = AIReportWriter(db)
    update_job_progress(job_id, 0.3, "Generating report content")

    result = writer.generate_report(
        report_type=report_type,
        title=title,
        user_id=user_id,
        **parameters,
    )

    update_job_progress(job_id, 0.9, "Finalizing report")
    return {"report": result}


# â”€â”€ Large Data Import Handler â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€


def _handle_data_import(job_id: int, payload: dict, db: DbSession) -> dict:
    """Import a large dataset as a background job."""
    from dataset_library import get_dataset_library

    file_path = payload.get("file_path")
    dataset_name = payload.get("dataset_name", "Imported Dataset")
    industry = payload.get("industry", "business")
    description = payload.get("description", "")

    if not file_path:
        raise ValueError("file_path is required for data_import jobs")

    update_job_progress(job_id, 0.1, f"Loading file: {file_path}")

    import os

    import pandas as pd

    ext = os.path.splitext(file_path)[1].lower()
    if ext == ".csv":
        df = pd.read_csv(file_path)
    elif ext in (".xlsx", ".xls"):
        df = pd.read_excel(file_path)
    elif ext == ".json":
        df = pd.read_json(file_path)
    elif ext == ".parquet":
        df = pd.read_parquet(file_path)
    else:
        raise ValueError(f"Unsupported file type: {ext}")

    update_job_progress(job_id, 0.4, f"Loaded {len(df)} rows, {len(df.columns)} columns")

    # Register in dataset library
    lib = get_dataset_library()
    from dataset_library import DatasetEntry, DataTier

    ds_id = f"import_{job_id}_{dataset_name.replace(' ', '_').lower()}"

    update_job_progress(job_id, 0.7, "Registering dataset")
    entry = DatasetEntry(
        id=ds_id,
        name=dataset_name,
        tier=DataTier.RAW,
        file_path=file_path,
        metadata={
            "source": "background_import",
            "industry": industry,
            "description": description,
            "rows": len(df),
            "columns": len(df.columns),
        },
    )
    lib.register(entry)

    update_job_progress(job_id, 1.0, f"Imported {len(df)} rows")
    return {
        "dataset_id": ds_id,
        "rows": len(df),
        "columns": len(df.columns),
    }


# â”€â”€ Dataset Workflow Handler â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€


def _handle_dataset_workflow(job_id: int, payload: dict, db: DbSession) -> dict:
    """Run the full dataset intelligence workflow as a background job (C4).

    Mirrors the synchronous fallback path in
    services.dataset_workflow_routes.run_workflow: downloads the uploaded
    file from storage (uploaded there by the route before enqueuing, since
    a DataFrame itself isn't JSON-serializable for the job payload), parses
    it, runs governance classification, runs the orchestrator, and writes
    the same audit log entry the synchronous path would have written.
    """
    from audit.service import log_audit_event
    from governance import classify_dataset
    from services.dataset_workflow_routes import _orchestrator, _parse_upload_bytes
    from storage.service import FileService

    file_id = payload.get("file_id")
    if not file_id:
        raise ValueError("file_id is required for dataset_workflow jobs")
    filename = payload.get("filename") or "uploaded_dataset"
    admin_confirmed = payload.get("admin_confirmed", False)
    organization_id = payload.get("organization_id")
    created_by = payload.get("created_by")

    logger.info(
        "DATASET_WORKFLOW_START job_id=%d file_id=%s filename='%s' org_id=%s",
        job_id,
        file_id,
        filename,
        organization_id,
    )

    update_job_progress(job_id, 0.05, "Loading uploaded file")
    content, _record = FileService(db).download(file_id, organization_id)
    logger.info("DATASET_WORKFLOW_FILE_LOADED job_id=%d bytes=%d", job_id, len(content))

    update_job_progress(job_id, 0.10, "Validating uploaded file")
    df = _parse_upload_bytes(content, filename)
    if df.empty:
        raise ValueError("Uploaded file is empty")
    logger.info(
        "DATASET_WORKFLOW_PARSED job_id=%d rows=%d cols=%d",
        job_id,
        len(df),
        len(df.columns),
    )

    update_job_progress(job_id, 0.15, "Running governance classification")
    governance = classify_dataset(df)
    logger.info("DATASET_WORKFLOW_GOVERNANCE_DONE job_id=%d", job_id)

    update_job_progress(job_id, 0.20, "Profiling dataset")
    state = _orchestrator.start(
        df,
        dataset_name=filename,
        admin_confirmed=admin_confirmed,
        created_by=created_by,
        organization_id=organization_id,
    )
    logger.info(
        "DATASET_WORKFLOW_ORCHESTRATOR_DONE job_id=%d workflow_id=%s",
        job_id,
        state.workflow_id,
    )

    update_job_progress(job_id, 0.50, "Detecting patterns and running analysis")

    update_job_progress(job_id, 0.80, "Generating insights")

    update_job_progress(job_id, 0.90, "Preparing visualizations and report")

    log_audit_event(
        db=db,
        action="dataset_workflow.run",
        user_id=created_by,
        organization_id=organization_id,
        resource_type="workflow",
        resource_id=state.workflow_id,
        new_values={
            "dataset_name": state.dataset_name,
            "governance": governance.to_dict(),
            "admin_confirmed": admin_confirmed,
        },
        request=None,
    )
    db.commit()

    update_job_progress(job_id, 1.0, "Processing complete")
    logger.info(
        "DATASET_WORKFLOW_COMPLETE job_id=%d workflow_id=%s",
        job_id,
        state.workflow_id,
    )
    return {
        **state.to_dict(),
        "governance": governance.to_dict(),
    }


# ── ETL Package Handler ────────────────────────────────────────────────────


def _handle_etl_package(job_id: int, payload: dict, db: DbSession) -> dict:
    """Process a ZIP package as a background job.

    Payload:
        package_id: int
        zip_path: str — temp path to the uploaded ZIP file
        organization_id: int
    """
    import os

    package_id = payload.get("package_id")
    zip_path = payload.get("zip_path", "")
    organization_id = payload.get("organization_id")

    if not package_id or not zip_path or not organization_id:
        raise ValueError("Missing required payload: package_id, zip_path, organization_id")

    update_job_progress(job_id, 0.05, "Starting ZIP extraction")

    from etl.package_service import ETLPackageService

    svc = ETLPackageService(db)
    update_job_progress(job_id, 0.10, "Extracting ZIP contents")

    result = svc.process_package(
        package_id=int(package_id),
        zip_path=zip_path,
        organization_id=int(organization_id),
    )

    # Cleanup temp ZIP file
    try:
        if os.path.exists(zip_path):
            os.unlink(zip_path)
    except OSError:
        pass

    status = result.get("status", "completed")
    if status == "failed":
        update_job_progress(job_id, 1.0, f"Failed: {result.get('error', 'unknown')}")
    elif status == "completed_with_errors":
        update_job_progress(
            job_id,
            1.0,
            f"Completed with {result.get('failed', 0)} errors out of {result.get('total_files', 0)} files",
        )
    else:
        update_job_progress(
            job_id,
            1.0,
            f"Completed: {result.get('completed', 0)}/{result.get('total_files', 0)} files",
        )

    return result


# ── Export Handler ──────────────────────────────────────────────────────────


def _handle_export(job_id: int, payload: dict, db: DbSession) -> dict:
    """Export data as a background job."""
    export_type = payload.get("export_type", "csv")
    organization_id = payload.get("organization_id")
    dataset_name = payload.get("dataset_name")

    update_job_progress(job_id, 0.1, "Preparing export")

    if payload.get("capture_bulk_export"):
        from capture.service import CaptureService

        svc = CaptureService(db)
        update_job_progress(job_id, 0.3, "Exporting approved capture documents")
        result = svc.bulk_export_approved(
            organization_id=organization_id,
            user_id=payload.get("user_id", 0),
            document_type=payload.get("document_type"),
            dataset_name=dataset_name,
        )
        update_job_progress(job_id, 1.0, f"Exported {result['row_count']} rows")
        return result

    raise ValueError(f"Unknown export type: {export_type}")


# â”€â”€ Register all handlers â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€


def register_builtin_handlers() -> None:
    """Register all built-in job handlers."""
    register_handler("etl_run", _handle_etl_run, TaskPriority.ETL)
    register_handler("ocr_document", _handle_ocr_document, TaskPriority.NORMAL)
    register_handler("ocr_batch", _handle_ocr_batch, TaskPriority.NORMAL)
    register_handler("report_gen", _handle_report_gen, TaskPriority.REPORTS)
    register_handler("data_import", _handle_data_import, TaskPriority.NORMAL)
    register_handler("export", _handle_export, TaskPriority.LOW)
    register_handler("dataset_workflow", _handle_dataset_workflow, TaskPriority.ETL)
    register_handler("etl_package", _handle_etl_package, TaskPriority.ETL)
    logger.info("Registered %d built-in job handlers", 8)
