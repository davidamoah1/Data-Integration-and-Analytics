"""REST routes for scheduled report jobs."""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.orm import Session as DbSession

from scheduler.models import ScheduledReport
from scheduler.report_scheduler import ReportScheduler
from shared.database import get_db
from shared.dependencies import get_current_user

router = APIRouter(prefix="/scheduler/reports", tags=["Scheduled Reports"])


class ScheduledReportCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    report_type: str = Field(..., min_length=1, max_length=50)
    title: str | None = Field(None, max_length=500)
    cron: str = Field("0 8 * * *", max_length=100)
    parameters: dict | None = Field(default_factory=dict)


class ScheduledReportResponse(BaseModel):
    id: int
    name: str
    report_type: str
    title: str | None
    cron: str
    is_active: bool
    last_run_at: str | None
    created_at: str | None

    model_config = ConfigDict(from_attributes=True)


@router.get("", response_model=list[ScheduledReportResponse])
async def list_scheduled_reports(
    db: DbSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """List scheduled reports for the current user."""
    reports = (
        db.query(ScheduledReport)
        .filter(ScheduledReport.user_id == current_user["id"])
        .order_by(ScheduledReport.created_at.desc())
        .all()
    )
    return [
        {
            "id": r.id,
            "name": r.name,
            "report_type": r.report_type,
            "title": r.title,
            "cron": r.cron,
            "is_active": r.is_active,
            "last_run_at": str(r.last_run_at) if r.last_run_at else None,
            "created_at": str(r.created_at) if r.created_at else None,
        }
        for r in reports
    ]


@router.post("", response_model=ScheduledReportResponse, status_code=201)
async def create_scheduled_report(
    request: ScheduledReportCreate,
    db: DbSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Create a new scheduled report."""
    report = ScheduledReport(
        name=request.name,
        report_type=request.report_type,
        title=request.title,
        cron=request.cron,
        parameters=request.parameters or {},
        user_id=current_user["id"],
        organization_id=current_user.get("organization_id"),
    )
    db.add(report)
    db.commit()
    db.refresh(report)
    return {
        "id": report.id,
        "name": report.name,
        "report_type": report.report_type,
        "title": report.title,
        "cron": report.cron,
        "is_active": report.is_active,
        "last_run_at": str(report.last_run_at) if report.last_run_at else None,
        "created_at": str(report.created_at) if report.created_at else None,
    }


@router.post("/{report_id}/toggle", response_model=dict)
async def toggle_scheduled_report(
    report_id: int,
    db: DbSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Enable or disable a scheduled report."""
    report = db.query(ScheduledReport).filter(ScheduledReport.id == report_id).first()
    if not report or report.user_id != current_user["id"]:
        raise HTTPException(status_code=404, detail="Scheduled report not found")
    report.is_active = not report.is_active
    db.commit()
    return {"id": report.id, "is_active": report.is_active}


@router.delete("/{report_id}", response_model=dict)
async def delete_scheduled_report(
    report_id: int,
    db: DbSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Delete a scheduled report."""
    report = db.query(ScheduledReport).filter(ScheduledReport.id == report_id).first()
    if not report or report.user_id != current_user["id"]:
        raise HTTPException(status_code=404, detail="Scheduled report not found")
    db.delete(report)
    db.commit()
    return {"deleted": True, "id": report_id}


@router.post("/sync", response_model=dict)
async def sync_scheduled_reports(
    db: DbSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Sync active scheduled reports into the background runner."""
    scheduler = ReportScheduler()
    scheduler.sync_jobs()
    return {"synced": True}
