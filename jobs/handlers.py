"""Built-in job handlers for ETL, OCR, Reports, and large imports.

Each handler receives (job_id, payload, db) and returns a result dict.
Handlers are registered at import time so the JobService can dispatch
to them.
"""

from __future__ import annotations

import logging
from typing import Any

from sqlalchemy.orm import Session as DbSession

from jobs.service import register_handler, update_job_progress
from performance.queue import TaskPriority

logger = logging.getLogger(__name__)


# ── ETL Pipeline Handler ──────────────────────────────────────────────────


def _handle_etl_run(job_id: int, payload: dict, db: DbSession) -> dict:
    """Run an ETL pipeline as a background job."""
    from services.etl_service import ETLService

    pipeline_id = payload.get("pipeline_id")
    update_job_progress(job_id, 0.1, "Initializing ETL pipeline")

    svc = ETLService()
    update_job_progress(job_id, 0.2, "Running pipeline")

    if pipeline_id:
        metrics = svc.run_pipeline(pipeline_id=int(pipeline_id))
    else:
        metrics = svc.run_pipeline()

    update_job_progress(job_id, 0.9, "Pipeline completed, collecting metrics")
    return {"metrics": metrics}


# ── OCR / Capture Batch Handler ───────────────────────────────────────────


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
    svc.process_batch(batch_id)

    # Refresh to get final counts
    db.refresh(batch)
    update_job_progress(job_id, 1.0, f"Batch complete: {batch.processed_documents} processed, {batch.failed_documents} failed")

    return {
        "batch_id": batch_id,
        "processed": batch.processed_documents,
        "failed": batch.failed_documents,
        "status": batch.status,
    }


# ── Report Generation Handler ─────────────────────────────────────────────


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


# ── Large Data Import Handler ─────────────────────────────────────────────


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

    import pandas as pd
    import os

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


# ── Export Handler ────────────────────────────────────────────────────────


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


# ── Register all handlers ─────────────────────────────────────────────────


def register_builtin_handlers() -> None:
    """Register all built-in job handlers."""
    register_handler("etl_run", _handle_etl_run, TaskPriority.ETL)
    register_handler("ocr_batch", _handle_ocr_batch, TaskPriority.NORMAL)
    register_handler("report_gen", _handle_report_gen, TaskPriority.REPORTS)
    register_handler("data_import", _handle_data_import, TaskPriority.NORMAL)
    register_handler("export", _handle_export, TaskPriority.LOW)
    logger.info("Registered %d built-in job handlers", 5)
