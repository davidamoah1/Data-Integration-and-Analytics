"""FastAPI routes for the background job system.

Endpoints:
  - POST   /api/jobs                 â€” Create a new job
  - GET    /api/jobs                 â€” List jobs (with filters)
  - GET    /api/jobs/active          â€” List active jobs for the org
  - GET    /api/jobs/summary         â€” Job summary stats
  - GET    /api/jobs/types           â€” List registered job types
  - GET    /api/jobs/{job_id}        â€” Get job details
  - POST   /api/jobs/{job_id}/cancel â€” Cancel a pending/running job
  - POST   /api/jobs/{job_id}/retry  â€” Retry a failed/cancelled job
  - GET    /api/jobs/{job_id}/poll   â€” Poll job status (lightweight)
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session as DbSession

from jobs.service import JobService, get_registered_types
from shared.database import get_db
from shared.dependencies import get_current_user
from shared.tenant import get_current_organization_id

router = APIRouter(prefix="/api/jobs", tags=["background-jobs"])


# â”€â”€ Request models â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€


class CreateJobRequest(BaseModel):
    job_type: str = Field(
        ..., description="Type: etl_run, ocr_batch, report_gen, data_import, export"
    )
    name: str = Field(..., description="Human-readable job name")
    description: str | None = None
    payload: dict = Field(default_factory=dict, description="Job-specific parameters")
    max_retries: int = Field(default=3, ge=0, le=10)
    idempotency_key: str | None = Field(
        default=None,
        description="Optional deduplication key. If a pending/running/completed job "
        "with the same key exists for this org, it is returned instead of creating a duplicate.",
    )


# â”€â”€ Routes â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€


@router.get("/types")
async def list_job_types(
    current_user: dict = Depends(get_current_user),
):
    """List all registered job types that can be created."""
    return {"types": get_registered_types()}


@router.post("")
async def create_job(
    request: CreateJobRequest,
    db: DbSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Create a new background job and enqueue it for processing."""
    org_id = get_current_organization_id(current_user, db)
    svc = JobService(db)
    try:
        job = await svc.create_job(
            organization_id=org_id,
            user_id=current_user["id"],
            job_type=request.job_type,
            name=request.name,
            description=request.description,
            payload=request.payload,
            max_retries=request.max_retries,
            idempotency_key=request.idempotency_key,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e)) from e
    return job.to_dict()


@router.get("")
async def list_jobs(
    status: str | None = Query(None),
    job_type: str | None = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: DbSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """List jobs for the current organization with optional filters."""
    org_id = get_current_organization_id(current_user, db)
    svc = JobService(db)
    jobs = svc.list_jobs(
        org_id,
        status=status,
        job_type=job_type,
        user_id=current_user["id"],
        limit=limit,
        offset=offset,
    )
    return {"jobs": [j.to_dict() for j in jobs], "count": len(jobs)}


@router.get("/active")
async def list_active_jobs(
    db: DbSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """List all active (pending/running) jobs for the organization."""
    org_id = get_current_organization_id(current_user, db)
    svc = JobService(db)
    jobs = svc.list_active(org_id)
    return {"jobs": [j.to_dict() for j in jobs], "count": len(jobs)}


@router.get("/summary")
async def job_summary(
    db: DbSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Get job summary statistics for the organization."""
    org_id = get_current_organization_id(current_user, db)
    svc = JobService(db)
    return svc.get_summary(org_id)


@router.get("/{job_id}")
async def get_job(
    job_id: int,
    db: DbSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Get details of a specific job."""
    org_id = get_current_organization_id(current_user, db)
    svc = JobService(db)
    job = svc.get_job(job_id, org_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job.to_dict()


@router.get("/{job_id}/poll")
async def poll_job_status(
    job_id: int,
    db: DbSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Lightweight poll â€” returns only status, progress, and message."""
    org_id = get_current_organization_id(current_user, db)
    svc = JobService(db)
    job = svc.get_job(job_id, org_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return {
        "id": job.id,
        "status": job.status,
        "progress": job.progress,
        "progress_message": job.progress_message,
        "error": job.error,
    }


@router.post("/{job_id}/cancel")
async def cancel_job(
    job_id: int,
    db: DbSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Cancel a pending or running job."""
    org_id = get_current_organization_id(current_user, db)
    svc = JobService(db)
    try:
        job = svc.cancel_job(job_id, org_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job.to_dict()


@router.post("/{job_id}/retry")
async def retry_job(
    job_id: int,
    db: DbSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Retry a failed or cancelled job."""
    org_id = get_current_organization_id(current_user, db)
    svc = JobService(db)
    try:
        job = await svc.retry_job(job_id, org_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e)) from e
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job.to_dict()
