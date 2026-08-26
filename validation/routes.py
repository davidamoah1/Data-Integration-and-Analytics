"""REST API routes for the Hospital Data Validation Engine."""

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
from shared.database import get_db
from shared.dependencies import get_current_user, require_permissions
from shared.tenant import get_current_organization_id, is_super_admin
from validation.approval import ApprovalWorkflow
from validation.audit import ValidationAuditLogger
from validation.engine import ValidationEngine
from validation.report_generator import ValidationReportGenerator

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/validation", tags=["validation"])

# In-memory store for validation sessions (production would use DB)
_sessions: dict[int, dict] = {}
_next_id = 1


class ApprovalRequest(BaseModel):
    approver: str
    role: str = "administrator"
    comments: str = ""


class RuleToggleRequest(BaseModel):
    rule_name: str
    enabled: bool


def _get_next_id() -> int:
    global _next_id
    _next_id += 1
    return _next_id


def _detect_schema_type(filename: str) -> str:
    name_lower = filename.lower()
    if "patient" in name_lower and "admission" not in name_lower:
        return "patient_registry"
    if "admission" in name_lower or "visit" in name_lower:
        return "admission_records"
    if "lab" in name_lower or "laboratory" in name_lower:
        return "laboratory_results"
    if "medication" in name_lower or "prescription" in name_lower:
        return "medication_records"
    return "general"


def _can_access_session(session: dict, current_user: dict, db: DbSession | None = None) -> bool:
    """Return True if the current user can access a validation session."""
    if "super_admin" in current_user.get("roles", []):
        return True
    session_org = session.get("organization_id")
    user_org = get_current_organization_id(current_user, db)
    return session_org is None or session_org == user_org


@router.post("/run")
async def run_validation(
    request: Request,
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
    db: DbSession = Depends(get_db),
):
    """Run validation on an uploaded dataset."""
    global _next_id

    content = await file.read()
    filename = file.filename or "uploaded.csv"

    if filename.endswith(".csv"):
        try:
            df = pd.read_csv(io.BytesIO(content), encoding="utf-8")
        except UnicodeDecodeError:
            df = pd.read_csv(io.BytesIO(content), encoding="latin-1")
    elif filename.endswith((".xlsx", ".xls")):
        df = pd.read_excel(io.BytesIO(content))
    elif filename.endswith(".json"):
        df = pd.read_json(io.BytesIO(content))
    else:
        raise HTTPException(
            status_code=400, detail="Unsupported file format. Use CSV, Excel, or JSON."
        )

    schema_type = _detect_schema_type(filename)
    engine = ValidationEngine()
    result = engine.validate(df, dataset_name=filename, schema_type=schema_type)

    session_id = _get_next_id()
    org_id = (
        current_user.get("organization_id")
        if is_super_admin(current_user)
        else get_current_organization_id(current_user, db)
    )
    session = {
        "id": session_id,
        "result": result,
        "filename": filename,
        "schema_type": schema_type,
        "created_by": current_user["id"],
        "organization_id": org_id,
    }
    _sessions[session_id] = session

    ValidationAuditLogger.log_upload(filename)
    ValidationAuditLogger.log_validation(
        session_id,
        result.status.value,
        result.quality_score.overall if result.quality_score else None,
    )

    log_audit_event(
        db=db,
        action="validation.run",
        user_id=current_user["id"],
        organization_id=org_id,
        resource_type="validation_session",
        resource_id=session_id,
        new_values={"filename": filename, "schema_type": schema_type},
        request=request,
    )
    db.commit()

    return {
        "session_id": session_id,
        "status": result.status.value,
        "quality_score": result.quality_score.to_dict() if result.quality_score else None,
        "total_errors": result.total_errors,
        "total_warnings": result.total_warnings,
        "total_info": result.total_info,
        "can_proceed_to_etl": result.can_proceed_to_etl,
        "summary": ValidationReportGenerator.generate_summary(result),
    }


@router.get("/status/{session_id}")
async def get_validation_status(
    session_id: int,
    current_user: dict = Depends(get_current_user),
):
    """Get validation status for a session."""
    session = _sessions.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Validation session not found.")
    if not _can_access_session(session, current_user):
        raise HTTPException(status_code=403, detail="Access denied.")
    result = session["result"]
    return {
        "session_id": session_id,
        "status": result.status.value,
        "quality_score": result.quality_score.to_dict() if result.quality_score else None,
        "total_errors": result.total_errors,
        "total_warnings": result.total_warnings,
        "total_info": result.total_info,
        "can_proceed_to_etl": result.can_proceed_to_etl,
    }


@router.get("/report/{session_id}")
async def get_validation_report(
    session_id: int,
    current_user: dict = Depends(get_current_user),
):
    """Get full validation report for a session."""
    session = _sessions.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Validation session not found.")
    if not _can_access_session(session, current_user):
        raise HTTPException(status_code=403, detail="Access denied.")
    result = session["result"]
    return ValidationReportGenerator.generate_summary(result)


@router.get("/report/{session_id}/export")
async def export_validation_report(
    session_id: int,
    format: str = "csv",
    current_user: dict = Depends(get_current_user),
):
    """Export validation report in CSV, Excel, or PDF format."""
    session = _sessions.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Validation session not found.")
    if not _can_access_session(session, current_user):
        raise HTTPException(status_code=403, detail="Access denied.")
    result = session["result"]

    if format == "csv":
        content = ValidationReportGenerator.export_csv(result)
        from fastapi.responses import Response

        return Response(
            content=content,
            media_type="text/csv",
            headers={
                "Content-Disposition": f"attachment; filename=validation_report_{session_id}.csv"
            },
        )
    elif format == "excel":
        with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as tmp:
            ValidationReportGenerator.export_excel(result, tmp.name)
            with open(tmp.name, "rb") as f:
                content = f.read()
            os.unlink(tmp.name)
        from fastapi.responses import Response

        return Response(
            content=content,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={
                "Content-Disposition": f"attachment; filename=validation_report_{session_id}.xlsx"
            },
        )
    elif format == "pdf":
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            ValidationReportGenerator.export_pdf(result, tmp.name)
            with open(tmp.name, "rb") as f:
                content = f.read()
            os.unlink(tmp.name)
        from fastapi.responses import Response

        return Response(
            content=content,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename=validation_report_{session_id}.pdf"
            },
        )
    else:
        raise HTTPException(status_code=400, detail="Format must be csv, excel, or pdf.")


@router.post("/approve/{session_id}")
async def approve_validation(
    session_id: int,
    req: ApprovalRequest,
    current_user: dict = Depends(require_permissions("validation.approve")),
):
    """Approve a validation session, allowing ETL to proceed."""
    session = _sessions.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Validation session not found.")
    if not _can_access_session(session, current_user):
        raise HTTPException(status_code=403, detail="Access denied.")
    result = session["result"]
    if not ApprovalWorkflow.can_approve(result):
        raise HTTPException(
            status_code=400, detail=f"Cannot approve session with status '{result.status.value}'."
        )
    result, decision = ApprovalWorkflow.approve(result, req.approver, req.role, req.comments)
    ValidationAuditLogger.log_approval(session_id, req.approver, "approved", req.comments)
    return {
        "session_id": session_id,
        "status": result.status.value,
        "can_proceed_to_etl": result.can_proceed_to_etl,
        "decision": decision.to_dict(),
    }


@router.post("/reject/{session_id}")
async def reject_validation(
    session_id: int,
    req: ApprovalRequest,
    current_user: dict = Depends(require_permissions("validation.reject")),
):
    """Reject a validation session, blocking ETL."""
    session = _sessions.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Validation session not found.")
    if not _can_access_session(session, current_user):
        raise HTTPException(status_code=403, detail="Access denied.")
    result = session["result"]
    result, decision = ApprovalWorkflow.reject(result, req.approver, req.role, req.comments)
    ValidationAuditLogger.log_rejection(session_id, req.approver, req.comments)
    return {
        "session_id": session_id,
        "status": result.status.value,
        "can_proceed_to_etl": result.can_proceed_to_etl,
        "decision": decision.to_dict(),
    }


@router.get("/rules")
async def list_validation_rules(
    current_user: dict = Depends(get_current_user),
):
    """List all configured validation rules."""
    engine = ValidationEngine()
    return {"rules": engine.business_rules.list_rules()}


@router.post("/rules/toggle")
async def toggle_validation_rule(
    req: RuleToggleRequest,
    current_user: dict = Depends(require_permissions("validation.manage_rules")),
):
    """Enable or disable a validation rule."""
    engine = ValidationEngine()
    if req.enabled:
        engine.business_rules.enable_rule(req.rule_name)
    else:
        engine.business_rules.disable_rule(req.rule_name)
    return {"rule_name": req.rule_name, "enabled": req.enabled}


@router.get("/history")
async def validation_history(
    current_user: dict = Depends(get_current_user),
):
    """Get validation history scoped to the user's organization."""
    history = []
    user_org = current_user.get("organization_id")
    is_super = is_super_admin(current_user)
    for sid, session in sorted(_sessions.items()):
        if not is_super and session.get("organization_id") != user_org:
            continue
        result = session["result"]
        history.append(
            {
                "session_id": sid,
                "dataset_name": result.dataset_name,
                "status": result.status.value,
                "quality_score": result.quality_score.overall if result.quality_score else None,
                "total_errors": result.total_errors,
                "total_warnings": result.total_warnings,
                "validated_at": result.validated_at,
            }
        )
    return {"history": history, "total": len(history)}


@router.get("/audit")
async def validation_audit_log(
    event_type: str | None = None,
    session_id: int | None = None,
    current_user: dict = Depends(get_current_user),
):
    """Get validation audit log entries."""
    entries = ValidationAuditLogger.get_entries(event_type=event_type, session_id=session_id)
    return {"entries": entries, "total": len(entries)}
