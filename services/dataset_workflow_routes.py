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
import logging
import os
import tempfile

import pandas as pd
from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile
from pydantic import BaseModel
from sqlalchemy.orm import Session as DbSession

from audit.service import log_audit_event
from etl.file_security import FileValidator
from governance import classify_dataset
from shared.database import get_db
from shared.dependencies import get_current_user
from shared.tenant import get_current_organization_id

from services.dataset_workflow import (
    DatasetWorkflowOrchestrator,
    WorkflowStage,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/dataset-workflow", tags=["Dataset Workflow"])

# Global orchestrator instance (in production, use Redis/DB for state)
_orchestrator = DatasetWorkflowOrchestrator()
_validator = FileValidator()


class ConfirmIndustryRequest(BaseModel):
    industry: str | None = None
    overrides: dict | None = None


def _read_upload(file: UploadFile) -> pd.DataFrame:
    """Read an uploaded file into a DataFrame."""
    content = file.file.read()
    file.file.seek(0)

    if file.filename and file.filename.endswith(".csv"):
        try:
            return pd.read_csv(io.BytesIO(content), encoding="utf-8")
        except UnicodeDecodeError:
            return pd.read_csv(io.BytesIO(content), encoding="latin-1")
    elif file.filename and file.filename.endswith((".xlsx", ".xls")):
        return pd.read_excel(io.BytesIO(content))
    else:
        # Try CSV as default
        try:
            return pd.read_csv(io.BytesIO(content), encoding="utf-8")
        except Exception:
            return pd.read_csv(io.BytesIO(content), encoding="latin-1")


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


def _ensure_workflow_access(
    workflow_id: str,
    current_user: dict,
    db: DbSession | None = None,
) -> None:
    """Raise 404/403 if the workflow is not visible to the current user."""
    state = _orchestrator.get_state(workflow_id)
    if not state:
        raise HTTPException(status_code=404, detail="Workflow not found")
    if "super_admin" not in current_user.get("roles", []):
        user_org = get_current_organization_id(current_user, db)
        if state.organization_id is not None and state.organization_id != user_org:
            raise HTTPException(status_code=403, detail="Access to this workflow is not permitted")


@router.post("/run")
async def run_workflow(
    request: Request,
    file: UploadFile = File(...),
    admin_confirmed: bool = False,
    current_user: dict = Depends(get_current_user),
    db: DbSession = Depends(get_db),
):
    """Upload a dataset and run the full intelligence workflow.

    Returns the complete workflow state with all stage results.
    """
    content = _validate_uploaded_file(file)

    try:
        df = _read_upload(file)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to read file: {e}")

    if df.empty:
        raise HTTPException(status_code=400, detail="Uploaded file is empty")

    org_id = get_current_organization_id(current_user, db)

    # Run a governance review before processing.
    governance = classify_dataset(df)

    state = _orchestrator.start(
        df,
        dataset_name=file.filename or "uploaded_dataset",
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
):
    """Get the current status of a workflow."""
    _ensure_workflow_access(workflow_id, current_user)
    state = _orchestrator.get_state(workflow_id)
    return {"success": True, "data": state.to_dict()}


@router.get("/{workflow_id}/profile")
async def get_profile(
    workflow_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Get the dataset profile from a workflow."""
    _ensure_workflow_access(workflow_id, current_user)
    state = _orchestrator.get_state(workflow_id)
    profile = state.context.get("profile")
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not available")
    return {"success": True, "data": profile}


@router.get("/{workflow_id}/quality")
async def get_quality(
    workflow_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Get the quality report from a workflow."""
    _ensure_workflow_access(workflow_id, current_user)
    state = _orchestrator.get_state(workflow_id)
    quality = state.context.get("quality_report")
    if not quality:
        raise HTTPException(status_code=404, detail="Quality report not available")
    return {"success": True, "data": quality}


@router.get("/{workflow_id}/semantic")
async def get_semantic(
    workflow_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Get the semantic analysis from a workflow."""
    _ensure_workflow_access(workflow_id, current_user)
    state = _orchestrator.get_state(workflow_id)
    semantic = state.context.get("semantic_result")
    if not semantic:
        raise HTTPException(status_code=404, detail="Semantic analysis not available")
    return {"success": True, "data": semantic}


@router.get("/{workflow_id}/industry")
async def get_industry(
    workflow_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Get the industry detection result from a workflow."""
    _ensure_workflow_access(workflow_id, current_user)
    state = _orchestrator.get_state(workflow_id)
    industry = state.context.get("industry_result")
    if not industry:
        raise HTTPException(status_code=404, detail="Industry detection not available")
    return {"success": True, "data": industry}


@router.get("/{workflow_id}/metadata")
async def get_metadata(
    workflow_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Get the generated metadata from a workflow."""
    _ensure_workflow_access(workflow_id, current_user)
    state = _orchestrator.get_state(workflow_id)
    metadata = state.context.get("metadata")
    if not metadata:
        raise HTTPException(status_code=404, detail="Metadata not available")
    return {"success": True, "data": metadata}


@router.get("/{workflow_id}/knowledge")
async def get_knowledge(
    workflow_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Get the extracted business knowledge from a workflow."""
    _ensure_workflow_access(workflow_id, current_user)
    state = _orchestrator.get_state(workflow_id)
    knowledge = state.context.get("business_knowledge")
    if not knowledge:
        raise HTTPException(status_code=404, detail="Business knowledge not available")
    return {"success": True, "data": knowledge}


@router.get("/{workflow_id}/insights")
async def get_insights(
    workflow_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Get the AI insights from a workflow."""
    _ensure_workflow_access(workflow_id, current_user)
    state = _orchestrator.get_state(workflow_id)
    insights = state.context.get("insights")
    if not insights:
        raise HTTPException(status_code=404, detail="Insights not available")
    return {"success": True, "data": insights}


@router.get("/{workflow_id}/dashboard")
async def get_dashboard(
    workflow_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Get the dashboard recommendations from a workflow."""
    _ensure_workflow_access(workflow_id, current_user)
    state = _orchestrator.get_state(workflow_id)
    dashboard = state.context.get("dashboard_recommendations")
    if not dashboard:
        raise HTTPException(status_code=404, detail="Dashboard recommendations not available")
    return {"success": True, "data": dashboard}


@router.get("/{workflow_id}/summary")
async def get_summary(
    workflow_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Get the final analysis summary from a workflow."""
    _ensure_workflow_access(workflow_id, current_user)
    state = _orchestrator.get_state(workflow_id)

    # Get the final stage result
    final_stage = state.stages.get(WorkflowStage.ANALYSIS_COMPLETE)
    if not final_stage or final_stage.status != "completed":
        raise HTTPException(status_code=404, detail="Analysis not complete")

    return {"success": True, "data": final_stage.result}


@router.post("/{workflow_id}/retry/{stage}")
async def retry_stage(
    workflow_id: str,
    stage: str,
    current_user: dict = Depends(get_current_user),
):
    """Retry a failed workflow stage."""
    _ensure_workflow_access(workflow_id, current_user)
    try:
        stage_enum = WorkflowStage(stage)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid stage: {stage}")

    state = _orchestrator.retry_stage(workflow_id, stage_enum)
    if not state:
        raise HTTPException(status_code=404, detail="Workflow not found")

    return {
        "success": True,
        "data": state.to_dict(),
        "message": "Stage retried successfully" if not state.has_errors else "Stage retry failed",
    }
