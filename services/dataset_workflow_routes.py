"""FastAPI routes for the Dataset Intelligence Workflow.

Endpoints:
  POST /dataset-workflow/run          — Start a full workflow on an uploaded file
  GET  /dataset-workflow/{id}/status  — Get workflow status and progress
  GET  /dataset-workflow/{id}/profile — Get dataset profile
  GET  /dataset-workflow/{id}/quality — Get quality report
  GET  /dataset-workflow/{id}/semantic — Get semantic analysis
  GET  /dataset-workflow/{id}/industry — Get industry detection
  GET  /dataset-workflow/{id}/insights — Get AI insights
  GET  /dataset-workflow/{id}/dashboard — Get dashboard recommendations
  POST /dataset-workflow/{id}/retry/{stage} — Retry a failed stage
  POST /dataset-workflow/{id}/confirm-industry — Confirm industry detection
"""

from __future__ import annotations

import io
import json
import logging
import os
import tempfile

import pandas as pd
from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session as DbSession

import shared.database as db_module
from audit.service import log_audit_event
from etl.file_security import FileValidator
from governance import classify_dataset
from services.dataset_workflow import (
    DatasetWorkflowOrchestrator,
    WorkflowStage,
)
from services.dataset_workflow_models import DatasetWorkflowRun
from shared.database import get_db
from shared.dependencies import get_current_user
from shared.tenant import get_current_organization_id

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/dataset-workflow", tags=["Dataset Workflow"])

# Global orchestrator instance. Live state lives in this in-process dict for
# the lifetime of the run, but every stage transition is also persisted to
# the dataset_workflow_runs table (see `_persist_workflow_state` below) so
# status/results survive a restart and are visible to other worker
# processes (C3). Retrying a stage still requires the original process
# (it needs the in-memory DataFrame) — see `retry_stage` below.
_orchestrator = DatasetWorkflowOrchestrator()
_validator = FileValidator()


def _persist_workflow_state(state) -> None:
    """Progress callback: persist workflow state to DB after every stage.

    Uses a short-lived session (same pattern as jobs.service.
    update_job_progress) so this works regardless of which request/thread
    triggered the stage transition. Persistence failures are logged and
    swallowed - the in-memory state, which is already correct, remains the
    source of truth for the response of the request currently running the
    workflow.
    """
    try:
        engine = db_module.get_engine()
        db_module.ensure_tables(engine)
        factory = db_module.get_session_factory(engine)
        db = factory()
    except Exception as e:
        logger.warning("Could not open DB session to persist workflow state: %s", e)
        return

    try:
        state_dict = state.to_dict()
        # Stage results can contain numpy scalar types (bool_, int64,
        # float64, ...) produced by pandas/numpy operations in stage
        # handlers, which the stdlib json encoder used by SQLAlchemy's JSON
        # column type cannot serialize directly. Round-trip through
        # json.dumps(..., default=str) - same fallback already used by
        # performance/cache.py's CacheManager - to coerce everything to
        # plain JSON-safe Python types before writing to the DB.
        stages_safe = json.loads(json.dumps(state_dict["stages"], default=str))

        existing = db.execute(
            select(DatasetWorkflowRun).where(
                DatasetWorkflowRun.workflow_id == state_dict["workflow_id"]
            )
        ).scalar_one_or_none()
        if existing:
            existing.dataset_name = state_dict["dataset_name"]
            existing.created_by = state_dict["created_by"]
            existing.organization_id = state_dict["organization_id"]
            existing.current_stage = state_dict["current_stage"]
            existing.stages = stages_safe
            existing.is_complete = state_dict["is_complete"]
            existing.has_errors = state_dict["has_errors"]
        else:
            db.add(
                DatasetWorkflowRun(
                    workflow_id=state_dict["workflow_id"],
                    dataset_name=state_dict["dataset_name"],
                    created_by=state_dict["created_by"],
                    organization_id=state_dict["organization_id"],
                    current_stage=state_dict["current_stage"],
                    stages=stages_safe,
                    is_complete=state_dict["is_complete"],
                    has_errors=state_dict["has_errors"],
                )
            )
        db.commit()
    except Exception as e:
        logger.warning("Failed to persist workflow state for %s: %s", state.workflow_id, e)
        db.rollback()
    finally:
        db.close()


_orchestrator.on_progress(_persist_workflow_state)


class ConfirmIndustryRequest(BaseModel):
    industry: str | None = None
    overrides: dict | None = None


class ApplyTransformationRequest(BaseModel):
    """Request to apply a cleaning transformation to a workflow dataset."""
    check_name: str
    column: str | None = None
    action: str  # fill_missing, normalize_countries, normalize_categories, convert_type, parse_dates, flag_outliers, remove_duplicates
    method: str | None = None  # mean, mode, median, etc.
    value: str | None = None  # fill value for fill_missing


class UndoTransformationRequest(BaseModel):
    """Request to undo a previously applied transformation."""
    transformation_id: str


class AnalyzeRequest(BaseModel):
    """Request to run analysis on a workflow dataset."""
    mode: str = "easy"  # easy or pro
    analysis_type: str | None = None  # descriptive, correlation, ttest, anova, chi_square, regression, normality, mann_whitney, kruskal_wallis
    columns: list[str] | None = None
    group_column: str | None = None
    target_column: str | None = None
    question: str | None = None  # natural language question for easy mode


class GeneratePresentationRequest(BaseModel):
    """Request to generate a PPTX presentation from workflow results."""
    template: str = "executive"  # executive, analytical, research, pitch
    title: str | None = None


def _parse_upload_bytes(content: bytes, filename: str) -> pd.DataFrame:
    """Parse raw upload bytes into a DataFrame based on filename extension.

    Shared by the synchronous request path (`_read_upload`) and the async
    job handler (`jobs/handlers.py::_handle_dataset_workflow`), which
    re-downloads the same bytes from storage in a (possibly different)
    worker process.
    """
    if filename and filename.endswith(".csv"):
        try:
            return pd.read_csv(io.BytesIO(content), encoding="utf-8")
        except UnicodeDecodeError:
            return pd.read_csv(io.BytesIO(content), encoding="latin-1")
    elif filename and filename.endswith((".xlsx", ".xls")):
        return pd.read_excel(io.BytesIO(content))
    else:
        # Try CSV as default
        try:
            return pd.read_csv(io.BytesIO(content), encoding="utf-8")
        except Exception:
            return pd.read_csv(io.BytesIO(content), encoding="latin-1")


def _read_upload(file: UploadFile) -> pd.DataFrame:
    """Read an uploaded file into a DataFrame."""
    content = file.file.read()
    file.file.seek(0)
    return _parse_upload_bytes(content, file.filename or "")


def _validate_uploaded_file(file: UploadFile) -> bytes:
    """Save upload to a temp file, validate it, and return its bytes."""
    suffix = os.path.splitext(file.filename or "")[1]
    content = file.file.read()
    file.file.seek(0)

    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(content)
        tmp_path = tmp.name

    try:
        ext = suffix.lstrip(".").lower()
        validation = _validator.validate(
            tmp_path, expected_type=ext if ext in ("csv", "xlsx", "xls", "json", "xml") else None
        )
        if not validation["valid"]:
            raise HTTPException(status_code=422, detail=validation["errors"])
    finally:
        os.unlink(tmp_path)

    return content


def _get_workflow_state_dict(
    workflow_id: str,
    current_user: dict,
    db: DbSession,
) -> dict:
    """Return workflow state as a dict, checking memory then DB, with access control.

    Checks the in-process orchestrator first (fast path, always up to date
    for the process that ran the workflow), then falls back to the durable
    `dataset_workflow_runs` snapshot so status/results are still readable
    after a restart or from a different worker process (C3). Raises 404 if
    not found anywhere, 403 if found but not owned by the caller's org.
    """
    state = _orchestrator.get_state(workflow_id)
    if state is not None:
        state_dict = state.to_dict()
    else:
        row = db.execute(
            select(DatasetWorkflowRun).where(DatasetWorkflowRun.workflow_id == workflow_id)
        ).scalar_one_or_none()
        if row is None:
            raise HTTPException(status_code=404, detail="Workflow not found")
        state_dict = row.to_state_dict()

    if "super_admin" not in current_user.get("roles", []):
        user_org = get_current_organization_id(current_user, db)
        if state_dict["organization_id"] is not None and state_dict["organization_id"] != user_org:
            raise HTTPException(status_code=403, detail="Access to this workflow is not permitted")

    return state_dict


def _stage_result(state_dict: dict, stage: WorkflowStage) -> dict | None:
    """Read a stage's result from a workflow state dict, or None if absent."""
    return state_dict["stages"].get(stage.value, {}).get("result")


def _async_workflow_execution_available() -> bool:
    """Whether a background worker exists to process a queued workflow job.

    Mirrors `api.main._is_serverless()` without importing `api.main` (which
    itself imports this module at startup - importing it back here would be
    circular). Async execution requires:
      1. `REDIS_URL` configured, so the job queue is the shared Redis-backed
         queue rather than an in-process-only in-memory one.
      2. Not running serverless (Vercel), since no persistent worker process
         exists there to consume the queue - only `docker-compose.prod.yml`'s
         dedicated `worker` service (`python -m performance.worker_entry`)
         does. Enqueuing on Vercel would leave the job stuck "pending"
         forever with nothing to run it.
    """
    import config

    is_serverless = os.getenv("VERCEL", "").lower() in ("1", "true", "yes") or os.getenv(
        "DISABLE_STARTUP_TASKS", ""
    ).lower() in ("1", "true", "yes")
    return bool(getattr(config, "REDIS_URL", "")) and not is_serverless


@router.post("/run")
async def run_workflow(
    request: Request,
    file: UploadFile = File(...),
    admin_confirmed: bool = False,
    current_user: dict = Depends(get_current_user),
    db: DbSession = Depends(get_db),
):
    """Upload a dataset and run the full intelligence workflow.

    When a background worker is available (`REDIS_URL` configured and not
    serverless - see `_async_workflow_execution_available`), this enqueues
    the pipeline as a background job via `jobs.service.JobService` and
    returns `202` with a `job_id` to poll (via `GET /api/jobs/{job_id}` or
    `GET /dataset-workflow/{workflow_id}/status` once the job assigns a
    workflow_id), instead of blocking the request for the full pipeline
    duration (C4 - avoids Vercel's 30s `maxDuration` timeout on large
    files). Otherwise, falls back to the original synchronous behavior and
    returns the complete result directly in the response.
    """
    _validate_uploaded_file(file)
    content = file.file.read()
    file.file.seek(0)
    filename = file.filename or "uploaded_dataset"
    org_id = get_current_organization_id(current_user, db)

    if _async_workflow_execution_available():
        from jobs.service import JobService
        from storage.service import FileService

        file_service = FileService(db)
        record = file_service.upload(
            organization_id=org_id,
            filename=filename,
            data=content,
            uploaded_by=current_user["id"],
            key_prefix=f"dataset-workflow/org_{org_id}/",
        )

        try:
            job = JobService(db).create_job(
                organization_id=org_id,
                user_id=current_user["id"],
                job_type="dataset_workflow",
                name=f"Dataset workflow: {filename}",
                payload={
                    "file_id": record.file_id,
                    "filename": filename,
                    "admin_confirmed": admin_confirmed,
                    "organization_id": org_id,
                    "created_by": current_user["id"],
                },
            )
        except ValueError as e:
            # No handler registered for "dataset_workflow" in this process
            # (e.g. jobs.handlers.register_builtin_handlers() hasn't run
            # yet). Fail safe to synchronous execution below rather than
            # erroring out the request.
            logger.warning(
                "dataset_workflow job handler unavailable (%s); running synchronously", e
            )
        else:
            return JSONResponse(
                status_code=202,
                content={
                    "success": True,
                    "data": {
                        "job_id": job.id,
                        "status": job.status,
                        "status_url": f"/api/jobs/{job.id}",
                    },
                    "message": (
                        "Workflow queued for background processing. "
                        "Poll status_url for progress and results."
                    ),
                },
            )

    # Synchronous fallback (serverless, or no Redis-backed queue available).
    try:
        df = _parse_upload_bytes(content, filename)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to read file: {e}") from None

    if df.empty:
        raise HTTPException(status_code=400, detail="Uploaded file is empty")

    # Run a governance review before processing.
    governance = classify_dataset(df)

    state = _orchestrator.start(
        df,
        dataset_name=filename,
        admin_confirmed=admin_confirmed,
        created_by=current_user["id"],
        organization_id=org_id,
    )

    log_audit_event(
        db=db,
        action="dataset_workflow.run",
        user_id=current_user["id"],
        organization_id=org_id,
        resource_type="workflow",
        resource_id=state.workflow_id,
        new_values={
            "dataset_name": state.dataset_name,
            "governance": governance.to_dict(),
            "admin_confirmed": admin_confirmed,
        },
        request=request,
    )
    db.commit()

    return {
        "success": True,
        "data": {
            **state.to_dict(),
            "governance": governance.to_dict(),
        },
        "message": "Workflow completed" if state.is_complete else "Workflow completed with errors",
    }


@router.get("/{workflow_id}/status")
async def get_status(
    workflow_id: str,
    current_user: dict = Depends(get_current_user),
    db: DbSession = Depends(get_db),
):
    """Get the current status of a workflow."""
    state_dict = _get_workflow_state_dict(workflow_id, current_user, db)
    return {"success": True, "data": state_dict}


@router.get("/{workflow_id}/profile")
async def get_profile(
    workflow_id: str,
    current_user: dict = Depends(get_current_user),
    db: DbSession = Depends(get_db),
):
    """Get the dataset profile from a workflow."""
    state_dict = _get_workflow_state_dict(workflow_id, current_user, db)
    profile = _stage_result(state_dict, WorkflowStage.PROFILED)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not available")
    return {"success": True, "data": profile}


@router.get("/{workflow_id}/quality")
async def get_quality(
    workflow_id: str,
    current_user: dict = Depends(get_current_user),
    db: DbSession = Depends(get_db),
):
    """Get the quality report from a workflow."""
    state_dict = _get_workflow_state_dict(workflow_id, current_user, db)
    quality = _stage_result(state_dict, WorkflowStage.QUALITY_CHECKED)
    if not quality:
        raise HTTPException(status_code=404, detail="Quality report not available")
    return {"success": True, "data": quality}


@router.get("/{workflow_id}/semantic")
async def get_semantic(
    workflow_id: str,
    current_user: dict = Depends(get_current_user),
    db: DbSession = Depends(get_db),
):
    """Get the semantic analysis from a workflow."""
    state_dict = _get_workflow_state_dict(workflow_id, current_user, db)
    semantic = _stage_result(state_dict, WorkflowStage.SEMANTICALLY_ANALYZED)
    if not semantic:
        raise HTTPException(status_code=404, detail="Semantic analysis not available")
    return {"success": True, "data": semantic}


@router.get("/{workflow_id}/industry")
async def get_industry(
    workflow_id: str,
    current_user: dict = Depends(get_current_user),
    db: DbSession = Depends(get_db),
):
    """Get the industry detection result from a workflow."""
    state_dict = _get_workflow_state_dict(workflow_id, current_user, db)
    industry = _stage_result(state_dict, WorkflowStage.INDUSTRY_IDENTIFIED)
    if not industry:
        raise HTTPException(status_code=404, detail="Industry detection not available")
    return {"success": True, "data": industry}


@router.get("/{workflow_id}/metadata")
async def get_metadata(
    workflow_id: str,
    current_user: dict = Depends(get_current_user),
    db: DbSession = Depends(get_db),
):
    """Get the generated metadata from a workflow."""
    state_dict = _get_workflow_state_dict(workflow_id, current_user, db)
    metadata = _stage_result(state_dict, WorkflowStage.METADATA_GENERATED)
    if not metadata:
        raise HTTPException(status_code=404, detail="Metadata not available")
    return {"success": True, "data": metadata}


@router.get("/{workflow_id}/knowledge")
async def get_knowledge(
    workflow_id: str,
    current_user: dict = Depends(get_current_user),
    db: DbSession = Depends(get_db),
):
    """Get the extracted business knowledge from a workflow."""
    state_dict = _get_workflow_state_dict(workflow_id, current_user, db)
    knowledge = _stage_result(state_dict, WorkflowStage.KNOWLEDGE_EXTRACTED)
    if not knowledge:
        raise HTTPException(status_code=404, detail="Business knowledge not available")
    return {"success": True, "data": knowledge}


@router.get("/{workflow_id}/insights")
async def get_insights(
    workflow_id: str,
    current_user: dict = Depends(get_current_user),
    db: DbSession = Depends(get_db),
):
    """Get the AI insights from a workflow."""
    state_dict = _get_workflow_state_dict(workflow_id, current_user, db)
    insights = _stage_result(state_dict, WorkflowStage.INSIGHTS_GENERATED)
    if not insights:
        raise HTTPException(status_code=404, detail="Insights not available")
    return {"success": True, "data": insights}


@router.get("/{workflow_id}/dashboard")
async def get_dashboard(
    workflow_id: str,
    current_user: dict = Depends(get_current_user),
    db: DbSession = Depends(get_db),
):
    """Get the dashboard recommendations from a workflow."""
    state_dict = _get_workflow_state_dict(workflow_id, current_user, db)
    dashboard = _stage_result(state_dict, WorkflowStage.DASHBOARD_READY)
    if not dashboard:
        raise HTTPException(status_code=404, detail="Dashboard recommendations not available")
    return {"success": True, "data": dashboard}


@router.get("/{workflow_id}/summary")
async def get_summary(
    workflow_id: str,
    current_user: dict = Depends(get_current_user),
    db: DbSession = Depends(get_db),
):
    """Get the final analysis summary from a workflow."""
    state_dict = _get_workflow_state_dict(workflow_id, current_user, db)

    final_stage = state_dict["stages"].get(WorkflowStage.ANALYSIS_COMPLETE.value)
    if not final_stage or final_stage.get("status") != "completed":
        raise HTTPException(status_code=404, detail="Analysis not complete")

    return {"success": True, "data": final_stage["result"]}


@router.post("/{workflow_id}/retry/{stage}")
async def retry_stage(
    workflow_id: str,
    stage: str,
    current_user: dict = Depends(get_current_user),
    db: DbSession = Depends(get_db),
):
    """Retry a failed workflow stage.

    Requires the workflow to still be live in this process's in-memory
    orchestrator, since retrying re-runs stage handlers against the
    original uploaded DataFrame, which is not persisted (only stage
    *results* are, via `_persist_workflow_state`). If the workflow was run
    by a different worker process, or this process has restarted since,
    retry is not possible and the caller must re-run the workflow instead.
    """
    # Access check first (memory or DB-backed), consistent with all other reads.
    _get_workflow_state_dict(workflow_id, current_user, db)

    try:
        stage_enum = WorkflowStage(stage)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid stage: {stage}") from None

    if _orchestrator.get_state(workflow_id) is None:
        raise HTTPException(
            status_code=409,
            detail=(
                "This workflow is not available for retry in this worker process "
                "(it may have completed in a different process or this process "
                "restarted). Re-run the workflow instead."
            ),
        )

    state = _orchestrator.retry_stage(workflow_id, stage_enum)
    if not state:
        raise HTTPException(status_code=404, detail="Workflow not found")

    return {
        "success": True,
        "data": state.to_dict(),
        "message": "Stage retried successfully" if not state.has_errors else "Stage retry failed",
    }


@router.post("/{workflow_id}/clean/apply")
async def apply_cleaning_transformation(
    workflow_id: str,
    payload: ApplyTransformationRequest,
    request: Request,
    current_user: dict = Depends(get_current_user),
    db: DbSession = Depends(get_db),
):
    """Apply a single cleaning transformation to the workflow dataset.

    Tracks the transformation in the workflow state for auditability
    and supports undo via the transformation_id returned.
    """
    state_dict = _get_workflow_state_dict(workflow_id, current_user, db)
    org_id = get_current_organization_id(current_user, db)

    # The in-memory orchestrator must still hold the DataFrame
    state = _orchestrator.get_state(workflow_id)
    if state is None or not hasattr(state, "df") or state.df is None:
        raise HTTPException(
            status_code=409,
            detail="Workflow data is not available for cleaning in this process.",
        )

    import uuid
    from datetime import datetime, timezone

    transformation_id = str(uuid.uuid4())
    df = state.df
    affected_rows = 0
    description = ""

    col = payload.column

    if payload.action == "fill_missing" and col:
        before_missing = int(df[col].isna().sum())
        if payload.method == "mean" and df[col].dtype in ("int64", "float64"):
            fill_val = df[col].mean()
            df[col] = df[col].fillna(fill_val)
            description = f"Filled {before_missing} missing values in '{col}' with mean ({fill_val:.2f})"
        elif payload.method == "median" and df[col].dtype in ("int64", "float64"):
            fill_val = df[col].median()
            df[col] = df[col].fillna(fill_val)
            description = f"Filled {before_missing} missing values in '{col}' with median ({fill_val:.2f})"
        elif payload.method == "mode":
            mode_val = df[col].mode().iloc[0] if not df[col].mode().empty else "Unknown"
            df[col] = df[col].fillna(mode_val)
            description = f"Filled {before_missing} missing values in '{col}' with mode ('{mode_val}')"
        elif payload.value is not None:
            df[col] = df[col].fillna(payload.value)
            description = f"Filled {before_missing} missing values in '{col}' with '{payload.value}'"
        else:
            raise HTTPException(status_code=400, detail="fill_missing requires method or value")
        affected_rows = before_missing

    elif payload.action == "remove_duplicates":
        before_count = len(df)
        df = df.drop_duplicates()
        state.df = df
        affected_rows = before_count - len(df)
        description = f"Removed {affected_rows} duplicate rows"

    elif payload.action == "normalize_categories" and col:
        from studios.cleaning_service import CATEGORY_NORMALIZATION
        mapping = {k.lower().strip(): v for k, v in CATEGORY_NORMALIZATION.items()}
        before = df[col].copy()
        df[col] = df[col].apply(
            lambda x, m=mapping: m.get(str(x).lower().strip(), x) if pd.notna(x) else x
        )
        affected_rows = int((before != df[col]).sum())
        description = f"Normalized {affected_rows} category values in '{col}'"

    elif payload.action == "normalize_countries" and col:
        from studios.cleaning_service import COUNTRY_NORMALIZATION
        mapping = {k.lower().strip(): v for k, v in COUNTRY_NORMALIZATION.items()}
        before = df[col].copy()
        df[col] = df[col].apply(
            lambda x, m=mapping: m.get(str(x).lower().strip(), x) if pd.notna(x) else x
        )
        affected_rows = int((before != df[col]).sum())
        description = f"Normalized {affected_rows} country names in '{col}'"

    elif payload.action == "convert_type" and col:
        df[col] = pd.to_numeric(df[col], errors="coerce")
        affected_rows = int(df[col].notna().sum())
        description = f"Converted '{col}' to numeric type"

    elif payload.action == "parse_dates" and col:
        df[col] = pd.to_datetime(df[col], errors="coerce")
        affected_rows = int(df[col].notna().sum())
        description = f"Parsed '{col}' as datetime"

    elif payload.action == "flag_outliers" and col:
        q1 = df[col].quantile(0.25)
        q3 = df[col].quantile(0.75)
        iqr = q3 - q1
        lower = q1 - 1.5 * iqr
        upper = q3 + 1.5 * iqr
        outlier_col = f"{col}_is_outlier"
        df[outlier_col] = (df[col] < lower) | (df[col] > upper)
        affected_rows = int(df[outlier_col].sum())
        description = f"Flagged {affected_rows} outliers in '{col}'"

    else:
        raise HTTPException(status_code=400, detail=f"Unsupported action: {payload.action}")

    # Record transformation
    transformation_record = {
        "id": transformation_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "action": payload.action,
        "check_name": payload.check_name,
        "column": col,
        "description": description,
        "affected_rows": affected_rows,
        "undone": False,
        "applied_by": current_user["id"],
    }

    # Store in workflow state
    if not hasattr(state, "transformations"):
        state.transformations = []
    state.transformations.append(transformation_record)

    log_audit_event(
        db=db,
        action="dataset_workflow.clean.apply",
        user_id=current_user["id"],
        organization_id=org_id,
        resource_type="workflow",
        resource_id=workflow_id,
        new_values=transformation_record,
        request=request,
    )
    db.commit()

    return {
        "success": True,
        "data": transformation_record,
        "message": description,
    }


@router.get("/{workflow_id}/clean/history")
async def get_cleaning_history(
    workflow_id: str,
    current_user: dict = Depends(get_current_user),
    db: DbSession = Depends(get_db),
):
    """Get the transformation history for a workflow."""
    _get_workflow_state_dict(workflow_id, current_user, db)

    state = _orchestrator.get_state(workflow_id)
    transformations = getattr(state, "transformations", []) if state else []

    return {
        "success": True,
        "data": {
            "transformations": transformations,
            "total": len(transformations),
            "active": sum(1 for t in transformations if not t.get("undone")),
        },
    }


@router.post("/{workflow_id}/analyze")
async def run_analysis(
    workflow_id: str,
    payload: AnalyzeRequest,
    current_user: dict = Depends(get_current_user),
    db: DbSession = Depends(get_db),
):
    """Run statistical analysis on the workflow dataset.

    Supports two modes:
      - easy: Auto-detects appropriate analysis, presents insights in plain language.
      - pro: Runs specific statistical tests (descriptive, correlation, ttest, anova, etc.)
    """
    _get_workflow_state_dict(workflow_id, current_user, db)

    state = _orchestrator.get_state(workflow_id)
    if state is None or not hasattr(state, "df") or state.df is None:
        raise HTTPException(
            status_code=409,
            detail="Workflow data is not available for analysis in this process.",
        )

    df = state.df

    if payload.mode == "easy":
        # Easy mode: auto-generate insights using InsightGenerator
        from ai_copilot.insight_generator import InsightGenerator

        col_mapping = {}
        # Use semantic mapping from earlier stage if available
        semantic_result = state.to_dict()["stages"].get("semantically_analyzed", {}).get("result")
        if semantic_result and isinstance(semantic_result, dict):
            col_mapping = semantic_result.get("column_mapping", {})

        generator = InsightGenerator()
        insights = generator.generate(df, col_mapping=col_mapping, max_insights=15)

        # Get industry-specific analytics if industry was detected
        industry_result = state.to_dict()["stages"].get("industry_identified", {}).get("result")
        industry_analytics = None
        if industry_result and isinstance(industry_result, dict):
            industry_name = industry_result.get("industry", "").lower()
            try:
                from industry_intelligence.base import IndustryAnalyticsRegistry
                industry_analytics = IndustryAnalyticsRegistry.analyze(
                    industry_name, df, col_mapping
                )
            except Exception:
                pass

        return {
            "success": True,
            "data": {
                "mode": "easy",
                "insights": [i.to_dict() for i in insights],
                "total_insights": len(insights),
                "industry_analytics": industry_analytics.to_dict() if industry_analytics else None,
                "question": payload.question,
            },
        }

    elif payload.mode == "pro":
        # Pro mode: run specific statistical tests
        from studios.statistics_service import StatisticsService

        svc = StatisticsService(db)
        analysis_type = payload.analysis_type or "descriptive"
        columns = payload.columns

        try:
            if analysis_type == "descriptive":
                result = svc.descriptive(df, columns)
            elif analysis_type == "correlation":
                result = svc.correlation(df, columns, method="pearson")
            elif analysis_type == "ttest":
                if not columns or len(columns) < 1 or not payload.group_column:
                    raise HTTPException(
                        status_code=400,
                        detail="T-test requires at least one numeric column and a group_column",
                    )
                result = svc.ttest(df, columns[0], payload.group_column)
            elif analysis_type == "anova":
                if not columns or len(columns) < 1 or not payload.group_column:
                    raise HTTPException(
                        status_code=400,
                        detail="ANOVA requires a numeric column and a group_column",
                    )
                result = svc.anova(df, columns[0], payload.group_column)
            elif analysis_type == "chi_square":
                if not columns or len(columns) < 2:
                    raise HTTPException(
                        status_code=400,
                        detail="Chi-square requires two categorical columns",
                    )
                result = svc.chi_square(df, columns[0], columns[1])
            elif analysis_type == "regression":
                if not columns or not payload.target_column:
                    raise HTTPException(
                        status_code=400,
                        detail="Regression requires feature columns and a target_column",
                    )
                result = svc.regression(df, columns, payload.target_column)
            elif analysis_type == "normality":
                if not columns or len(columns) < 1:
                    raise HTTPException(status_code=400, detail="Normality test requires a column")
                result = svc.normality_test(df, columns[0])
            elif analysis_type == "mann_whitney":
                if not columns or len(columns) < 1 or not payload.group_column:
                    raise HTTPException(
                        status_code=400,
                        detail="Mann-Whitney requires a numeric column and group_column",
                    )
                result = svc.mann_whitney(df, columns[0], payload.group_column)
            elif analysis_type == "kruskal_wallis":
                if not columns or len(columns) < 1 or not payload.group_column:
                    raise HTTPException(
                        status_code=400,
                        detail="Kruskal-Wallis requires a numeric column and group_column",
                    )
                result = svc.kruskal_wallis(df, columns[0], payload.group_column)
            else:
                raise HTTPException(status_code=400, detail=f"Unknown analysis type: {analysis_type}")

            return {
                "success": True,
                "data": {
                    "mode": "pro",
                    "analysis_type": analysis_type,
                    "result": result,
                },
            }
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}") from None

    else:
        raise HTTPException(status_code=400, detail=f"Invalid mode: {payload.mode}")


@router.post("/{workflow_id}/presentation")
async def generate_presentation(
    workflow_id: str,
    payload: GeneratePresentationRequest,
    request: Request,
    current_user: dict = Depends(get_current_user),
    db: DbSession = Depends(get_db),
):
    """Generate a PPTX presentation from the workflow results.

    Uses the analysis summary, insights, quality score, and dashboard
    recommendations to build a professional presentation file.
    Returns the file as a downloadable response.
    """
    from fastapi.responses import StreamingResponse
    from pptx import Presentation as PptxPresentation
    from pptx.util import Inches, Pt
    from studios.presentation_service import PresentationStudioService

    state_dict = _get_workflow_state_dict(workflow_id, current_user, db)
    org_id = get_current_organization_id(current_user, db)

    # Gather data from workflow stages
    profile = _stage_result(state_dict, WorkflowStage.PROFILED) or {}
    quality = _stage_result(state_dict, WorkflowStage.QUALITY_CHECKED) or {}
    industry = _stage_result(state_dict, WorkflowStage.INDUSTRY_IDENTIFIED) or {}
    insights_data = _stage_result(state_dict, WorkflowStage.INSIGHTS_GENERATED) or {}
    dashboard = _stage_result(state_dict, WorkflowStage.DASHBOARD_READY) or {}

    dataset_name = state_dict.get("dataset_name", "Dataset")
    title = payload.title or f"{dataset_name} — Analysis Presentation"

    # Build source data for slide generation
    source_data = {
        "title": title,
        "subtitle": f"Generated from {dataset_name}",
        "summary": quality.get("summary", insights_data.get("executive_summary", "")),
        "findings": "\n".join(
            f"• {i.get('title', '')}: {i.get('description', '')}"
            for i in insights_data.get("insights", [])[:5]
        ),
        "recommendations": "\n".join(quality.get("recommendations", [])[:5]),
        "data_overview": (
            f"Rows: {profile.get('row_count', 'N/A')}, "
            f"Columns: {profile.get('column_count', 'N/A')}, "
            f"Quality Score: {quality.get('score', {}).get('overall', 'N/A')}"
        ),
        "chart_config": dashboard.get("recommended_charts", [{}])[0] if dashboard.get("recommended_charts") else None,
        "next_steps": "Review findings and implement recommended actions.",
        "industry": industry.get("industry", "general"),
    }

    # Generate slides metadata
    slides = PresentationStudioService.generate_slides(
        source_type="workflow",
        source_data=source_data,
        template=payload.template,
    )

    # Create actual PPTX file
    prs = PptxPresentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)

    for slide_data in slides:
        layout = prs.slide_layouts[1]  # Title and Content layout
        if slide_data.get("layout") == "title":
            layout = prs.slide_layouts[0]  # Title Slide layout

        slide = prs.slides.add_slide(layout)

        # Set title
        if slide.shapes.title:
            slide.shapes.title.text = slide_data.get("title", "")

        # Set content
        content = slide_data.get("content", "")
        if content and len(slide.placeholders) > 1:
            body = slide.placeholders[1]
            tf = body.text_frame
            tf.text = content

        # Add speaker notes
        notes = slide_data.get("speaker_notes", "")
        if notes:
            notes_slide = slide.notes_slide
            notes_slide.notes_text_frame.text = notes

    # Save to BytesIO and return as download
    output = io.BytesIO()
    prs.save(output)
    output.seek(0)

    # Record in audit
    log_audit_event(
        db=db,
        action="dataset_workflow.presentation.generate",
        user_id=current_user["id"],
        organization_id=org_id,
        resource_type="workflow",
        resource_id=workflow_id,
        new_values={"template": payload.template, "title": title, "slides": len(slides)},
        request=request,
    )
    db.commit()

    safe_filename = dataset_name.replace(" ", "_").replace("/", "_")
    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
        headers={
            "Content-Disposition": f'attachment; filename="{safe_filename}_presentation.pptx"',
        },
    )
