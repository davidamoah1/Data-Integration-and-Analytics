"""FastAPI routes for the ETL Engine — imports, pipelines, schedules, profiling, quality, jobs, lineage, templates."""

# ruff: noqa: B008  # FastAPI Depends() calls in default arguments are intentional

import os
import tempfile
from datetime import datetime, timezone

from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, Query, UploadFile
from sqlalchemy.orm import Session as DbSession

from audit.service import log_audit_event
from etl.ai_hooks import list_ai_hooks
from etl.connectors.connectors import get_connector
from etl.file_security import FileSecurityError, FileValidator
from etl.lineage import LineageTracker
from etl.logging_config import logger
from etl.models import (
    ETLDataProfile,
    ETLImportTemplate,
    ETLJob,
    ETLPipeline,
    ETLQualityReport,
    ETLSchedule,
    ETLTransformation,
)
from etl.pipeline_builder import JobMonitor, PipelineBuilder, PipelineExecutor
from etl.profiling import DataProfiler
from etl.quality import DataQualityEngine
from etl.reports import ReportGenerator
from etl.schemas import (
    AIHooksResponse,
    ApplyFixRequest,
    DashboardResponse,
    ImportPreviewResponse,
    ImportRequest,
    ImportResponse,
    ImportTemplateResponse,
    JobResponse,
    JobStatsResponse,
    LineageResponse,
    PipelineCreate,
    PipelineExecuteResponse,
    PipelineResponse,
    PipelineUpdate,
    ProfileResponse,
    QualityResponse,
    RollbackRequest,
    ScheduleCreate,
    ScheduleResponse,
    TransformationTemplateCreate,
    TransformRequest,
    TransformResponse,
    VersionHistoryItem,
)
from etl.transformations import TransformationEngine
from shared.database import get_db
from shared.dependencies import get_current_user
from shared.tenant import get_current_organization_id, get_tenant_context, verify_resource_ownership

router = APIRouter(prefix="/etl", tags=["ETL Engine"])

# --- File Upload Security ---------------------------------------------------
_validator = FileValidator()
_profiler = DataProfiler()
_quality_engine = DataQualityEngine()
_transform_engine = TransformationEngine()
_report_gen = ReportGenerator()


# --- Connector discovery endpoints -----------------------------------------


@router.post("/connectors/test", response_model=dict)
async def test_connector(
    request: ImportRequest,
    current_user=Depends(get_current_user),
):
    connector = get_connector(request.source_type, request.source_config)
    return connector.test_connection()


@router.post("/connectors/discover", response_model=dict)
async def discover_connector(
    request: ImportRequest,
    preview_rows: int = Query(default=10, ge=1, le=100),
    current_user=Depends(get_current_user),
):
    connector = get_connector(request.source_type, request.source_config)
    with connector:
        metadata = connector.discover_metadata()
        preview = connector.preview(preview_rows).to_dict(orient="records")
    return {**metadata, "preview": preview}


# --- Import endpoints -------------------------------------------------------


@router.post("/import/upload", response_model=ImportPreviewResponse)
async def upload_file(
    file: UploadFile = File(...),
    db: DbSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Upload a file for import. Returns a preview of the data.

    Validates file security (MIME type, size, structure) before processing.
    """
    # Save to temp file
    suffix = os.path.splitext(file.filename or "")[1]
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name

    # Validate
    ext = suffix.lstrip(".").lower()
    try:
        validation = _validator.validate(
            tmp_path, expected_type=ext if ext in ("csv", "xlsx", "xls", "json", "xml") else None
        )
        if not validation["valid"]:
            raise HTTPException(status_code=422, detail=validation["errors"])
    except FileSecurityError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    finally:
        os.unlink(tmp_path)

    # Re-save for processing (file was deleted)
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(content)
        tmp_path = tmp.name

    try:
        config = {"file_path": tmp_path}
        connector = get_connector(ext, config)
        with connector:
            df = connector.extract()

        preview_rows = df.head(10).to_dict(orient="records")

        log_audit_event(
            db=db,
            action="dataset.upload",
            user_id=current_user.get("id"),
            organization_id=get_current_organization_id(current_user, db),
            resource_type="dataset",
            metadata={"filename": file.filename, "rows": len(df), "columns": len(df.columns)},
        )
        db.commit()

        return ImportPreviewResponse(
            columns=list(df.columns),
            rows=preview_rows,
            row_count=len(df),
            column_count=len(df.columns),
        )
    finally:
        os.unlink(tmp_path)


@router.post("/import/preview", response_model=ImportPreviewResponse)
async def preview_import(
    request: ImportRequest,
    current_user=Depends(get_current_user),
):
    """Preview data from a configured source without loading it."""
    connector = get_connector(request.source_type, request.source_config)
    with connector:
        df = connector.extract()

    preview_rows = df.head(10).to_dict(orient="records")
    return ImportPreviewResponse(
        columns=list(df.columns),
        rows=preview_rows,
        row_count=len(df),
        column_count=len(df.columns),
    )


@router.post("/import/execute", response_model=ImportResponse)
async def execute_import(
    request: ImportRequest,
    db: DbSession = Depends(get_db),
    tenant: dict = Depends(get_tenant_context),
):
    """Execute a full import: extract, validate, transform, profile, and optionally load."""
    current_user = tenant["user"]
    org_id = tenant["organization_id"]
    # Create job record
    job = ETLJob(
        organization_id=org_id,
        job_type="import",
        status="running",
        trigger_type="api",
        started_at=datetime.now(timezone.utc).replace(tzinfo=None),
        created_by=current_user["id"] if current_user else None,
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    try:
        # Extract
        connector = get_connector(request.source_type, request.source_config)
        with connector:
            df = connector.extract()

        rows_imported = len(df)

        # Apply transformations if provided
        if request.transformations:
            df = _transform_engine.apply(df, request.transformations)

        # Apply column mapping if provided
        if request.column_mapping:
            df = df.rename(columns=request.column_mapping)

        # Profile
        profile = _profiler.profile(
            df, source_name=request.source_config.get("file_path", request.source_type)
        )

        # Quality check
        quality = _quality_engine.run_checks(df, source_name=request.source_type)

        # Record lineage
        lineage = LineageTracker(db)
        lineage.record(
            source_name=request.source_config.get("file_path", request.source_type),
            source_type=request.source_type,
            destination_name="import_preview",
            destination_type="dataframe",
            job_id=job.id,
            user_id=current_user["id"] if current_user else None,
            organization_id=org_id,
        )

        # Save profile
        profile_rec = ETLDataProfile(
            organization_id=org_id,
            job_id=job.id,
            source_name=request.source_config.get("file_path", request.source_type),
            source_type=request.source_type,
            row_count=profile["row_count"],
            column_count=profile["column_count"],
            profile_data=profile,
            quality_score=profile.get("quality_score"),
        )
        db.add(profile_rec)

        # Save quality report
        quality_rec = ETLQualityReport(
            organization_id=org_id,
            job_id=job.id,
            source_name=request.source_type,
            overall_score=quality["overall_score"],
            checks_passed=quality["checks_passed"],
            checks_failed=quality["checks_failed"],
            checks_warning=quality["checks_warning"],
            report_data=quality,
            recommendations=quality.get("recommendations"),
        )
        db.add(quality_rec)

        # Save template if requested
        if request.template_name:
            template = ETLImportTemplate(
                organization_id=org_id,
                name=request.template_name,
                source_type=request.source_type,
                source_config=request.source_config,
                column_mapping=request.column_mapping,
                transformations=request.transformations,
                validation_rules=request.validation_rules,
                created_by=current_user["id"] if current_user else None,
            )
            db.add(template)

        job.status = "completed"
        job.rows_extracted = rows_imported
        job.rows_transformed = rows_imported
        job.completed_at = datetime.now(timezone.utc).replace(tzinfo=None)
        db.commit()

        return ImportResponse(
            job_id=job.id,
            status="completed",
            rows_imported=rows_imported,
            quality_score=quality["overall_score"],
        )

    except Exception as e:
        job.status = "failed"
        job.error_message = str(e)
        job.completed_at = datetime.now(timezone.utc).replace(tzinfo=None)
        db.commit()
        logger.error(f"Import failed: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


# --- Profiling endpoints ----------------------------------------------------


@router.post("/profile", response_model=ProfileResponse)
async def profile_data(
    request: ImportRequest,
    current_user=Depends(get_current_user),
):
    """Profile a data source and return statistics."""
    connector = get_connector(request.source_type, request.source_config)
    with connector:
        df = connector.extract()

    profile = _profiler.profile(
        df, source_name=request.source_config.get("file_path", request.source_type)
    )
    return ProfileResponse(
        source_name=profile["source_name"],
        row_count=profile["row_count"],
        column_count=profile["column_count"],
        quality_score=profile["quality_score"],
        columns=profile["columns"],
        duplicate_rows=profile["duplicate_rows"],
        duplicate_percentage=profile["duplicate_percentage"],
    )


@router.get("/profiles/{job_id}", response_model=dict)
async def get_profile(
    job_id: int,
    db: DbSession = Depends(get_db),
    tenant: dict = Depends(get_tenant_context),
):
    """Get a saved data profile by job ID."""
    org_id = tenant["organization_id"]
    profile = (
        db.query(ETLDataProfile)
        .filter(ETLDataProfile.job_id == job_id, ETLDataProfile.organization_id == org_id)
        .first()
    )
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    return {
        "id": profile.id,
        "job_id": profile.job_id,
        "source_name": profile.source_name,
        "source_type": profile.source_type,
        "row_count": profile.row_count,
        "column_count": profile.column_count,
        "quality_score": profile.quality_score,
        "profile_data": profile.profile_data,
        "created_at": str(profile.created_at) if profile.created_at else None,
    }


# --- Quality endpoints ------------------------------------------------------


@router.post("/quality/check", response_model=QualityResponse)
async def check_quality(
    request: ImportRequest,
    current_user=Depends(get_current_user),
):
    """Run quality checks on a data source."""
    connector = get_connector(request.source_type, request.source_config)
    with connector:
        df = connector.extract()

    result = _quality_engine.run_checks(df, source_name=request.source_type)
    return QualityResponse(**result)


@router.post("/quality/fix", response_model=dict)
async def apply_fixes(
    request: ImportRequest,
    fix_request: ApplyFixRequest,
    current_user=Depends(get_current_user),
):
    """Apply auto-fixes for detected quality issues."""
    connector = get_connector(request.source_type, request.source_config)
    with connector:
        df = connector.extract()

    fixed_df = _quality_engine.apply_fixes(df, check_names=fix_request.check_names)
    return {
        "rows_before": len(df),
        "rows_after": len(fixed_df),
        "rows_fixed": len(df) - len(fixed_df),
    }


@router.get("/quality/reports/{job_id}", response_model=dict)
async def get_quality_report(
    job_id: int,
    db: DbSession = Depends(get_db),
    tenant: dict = Depends(get_tenant_context),
):
    """Get a saved quality report by job ID."""
    org_id = tenant["organization_id"]
    report = (
        db.query(ETLQualityReport)
        .filter(ETLQualityReport.job_id == job_id, ETLQualityReport.organization_id == org_id)
        .first()
    )
    if not report:
        raise HTTPException(status_code=404, detail="Quality report not found")
    return {
        "id": report.id,
        "job_id": report.job_id,
        "source_name": report.source_name,
        "overall_score": report.overall_score,
        "checks_passed": report.checks_passed,
        "checks_failed": report.checks_failed,
        "checks_warning": report.checks_warning,
        "report_data": report.report_data,
        "recommendations": report.recommendations,
        "created_at": str(report.created_at) if report.created_at else None,
    }


# --- Transformation endpoints ------------------------------------------------


@router.post("/transform", response_model=TransformResponse)
async def transform_data(
    body: TransformRequest,
    current_user=Depends(get_current_user),
):
    """Apply transformations to a data source."""
    connector = get_connector(body.source_type, body.source_config)
    with connector:
        df = connector.extract()

    before = len(df)
    df = _transform_engine.apply(df, body.transformations)
    after = len(df)
    return TransformResponse(
        rows_before=before,
        rows_after=after,
        rows_changed=before - after,
        transformations_applied=len(body.transformations),
    )


@router.post("/transformations/templates", response_model=dict)
async def create_transformation_template(
    template: TransformationTemplateCreate,
    db: DbSession = Depends(get_db),
    tenant: dict = Depends(get_tenant_context),
):
    """Create a reusable transformation template."""
    current_user = tenant["user"]
    org_id = tenant["organization_id"]
    t = ETLTransformation(
        organization_id=org_id,
        name=template.name,
        description=template.description,
        transformation_type=template.transformation_type,
        config=template.config,
        created_by=current_user["id"] if current_user else None,
    )
    db.add(t)
    db.commit()
    db.refresh(t)
    return {"id": t.id, "name": t.name, "type": t.transformation_type}


@router.get("/transformations/templates", response_model=list[dict])
async def list_transformation_templates(
    db: DbSession = Depends(get_db),
    tenant: dict = Depends(get_tenant_context),
):
    """List all transformation templates."""
    org_id = tenant["organization_id"]
    templates = (
        db.query(ETLTransformation).filter(ETLTransformation.organization_id == org_id).all()
    )
    return [
        {
            "id": t.id,
            "name": t.name,
            "description": t.description,
            "transformation_type": t.transformation_type,
            "config": t.config,
            "is_builtin": bool(t.is_builtin),
        }
        for t in templates
    ]


# --- Pipeline endpoints -----------------------------------------------------


@router.post("/pipelines", response_model=PipelineResponse)
async def create_pipeline(
    request: PipelineCreate,
    db: DbSession = Depends(get_db),
    tenant: dict = Depends(get_tenant_context),
):
    """Create a new ETL pipeline."""
    current_user = tenant["user"]
    org_id = tenant["organization_id"]
    builder = PipelineBuilder(db)
    pipeline = builder.create_pipeline(
        name=request.name,
        description=request.description or "",
        steps=request.steps,
        created_by=current_user["id"] if current_user else None,
        organization_id=org_id,
    )
    return PipelineResponse(
        id=pipeline.id,
        name=pipeline.name,
        description=pipeline.description,
        status=pipeline.status,
        current_version=pipeline.current_version,
        steps=request.steps,
        created_at=str(pipeline.created_at) if pipeline.created_at else None,
    )


@router.get("/pipelines", response_model=list[dict])
async def list_pipelines(
    db: DbSession = Depends(get_db),
    tenant: dict = Depends(get_tenant_context),
):
    """List all pipelines."""
    org_id = tenant["organization_id"]
    pipelines = db.query(ETLPipeline).filter(ETLPipeline.organization_id == org_id).all()
    return [
        {
            "id": p.id,
            "name": p.name,
            "description": p.description,
            "status": p.status,
            "current_version": p.current_version,
            "created_at": str(p.created_at) if p.created_at else None,
        }
        for p in pipelines
    ]


@router.get("/pipelines/{pipeline_id}", response_model=PipelineResponse)
async def get_pipeline(
    pipeline_id: int,
    db: DbSession = Depends(get_db),
    tenant: dict = Depends(get_tenant_context),
):
    """Get a pipeline by ID."""
    org_id = tenant["organization_id"]
    verify_resource_ownership(db, ETLPipeline, pipeline_id, org_id)
    builder = PipelineBuilder(db)
    pipeline_data = builder.get_pipeline(pipeline_id)
    if not pipeline_data:
        raise HTTPException(status_code=404, detail="Pipeline not found")
    return PipelineResponse(**pipeline_data)


@router.put("/pipelines/{pipeline_id}", response_model=dict)
async def update_pipeline(
    pipeline_id: int,
    request: PipelineUpdate,
    db: DbSession = Depends(get_db),
    tenant: dict = Depends(get_tenant_context),
):
    """Update a pipeline (creates a new version)."""
    current_user = tenant["user"]
    org_id = tenant["organization_id"]
    verify_resource_ownership(db, ETLPipeline, pipeline_id, org_id)
    builder = PipelineBuilder(db)
    version = builder.update_pipeline(
        pipeline_id=pipeline_id,
        steps=request.steps,
        created_by=current_user["id"] if current_user else None,
    )
    return {"pipeline_id": pipeline_id, "new_version": version.version_number}


@router.get("/pipelines/{pipeline_id}/versions", response_model=list[VersionHistoryItem])
async def get_version_history(
    pipeline_id: int,
    db: DbSession = Depends(get_db),
    tenant: dict = Depends(get_tenant_context),
):
    """Get version history for a pipeline."""
    org_id = tenant["organization_id"]
    verify_resource_ownership(db, ETLPipeline, pipeline_id, org_id)
    builder = PipelineBuilder(db)
    return builder.get_version_history(pipeline_id)


@router.post("/pipelines/{pipeline_id}/rollback", response_model=dict)
async def rollback_pipeline(
    pipeline_id: int,
    request: RollbackRequest,
    db: DbSession = Depends(get_db),
    tenant: dict = Depends(get_tenant_context),
):
    """Rollback a pipeline to a previous version."""
    org_id = tenant["organization_id"]
    verify_resource_ownership(db, ETLPipeline, pipeline_id, org_id)
    builder = PipelineBuilder(db)
    version = builder.rollback_version(pipeline_id, request.version_number)
    return {"pipeline_id": pipeline_id, "rolled_back_to": version.version_number}


@router.post("/pipelines/{pipeline_id}/execute", response_model=PipelineExecuteResponse)
async def execute_pipeline(
    pipeline_id: int,
    background_tasks: BackgroundTasks,
    db: DbSession = Depends(get_db),
    tenant: dict = Depends(get_tenant_context),
):
    """Execute a pipeline. Runs in the background for large datasets."""
    current_user = tenant["user"]
    org_id = tenant["organization_id"]
    verify_resource_ownership(db, ETLPipeline, pipeline_id, org_id)
    executor = PipelineExecutor(db)

    def run():
        try:
            executor.execute(
                pipeline_id=pipeline_id,
                user_id=current_user["id"] if current_user else None,
                trigger_type="api",
                organization_id=org_id,
            )
        except Exception as e:
            logger.error(f"Pipeline execution failed: {e}")

    background_tasks.add_task(run)

    return PipelineExecuteResponse(
        job_id=0,
        status="triggered",
        rows_extracted=0,
        rows_transformed=0,
        rows_loaded=0,
        duration_seconds=0,
    )


# --- Job endpoints ----------------------------------------------------------


@router.get("/jobs", response_model=list[JobResponse])
async def list_jobs(
    status: str | None = Query(None, description="Filter by status"),
    limit: int = Query(50, ge=1, le=200),
    db: DbSession = Depends(get_db),
    tenant: dict = Depends(get_tenant_context),
):
    """List ETL jobs with optional status filter."""
    org_id = tenant["organization_id"]
    query = db.query(ETLJob).filter(ETLJob.organization_id == org_id)
    if status:
        query = query.filter(ETLJob.status == status)
    jobs = query.order_by(ETLJob.created_at.desc()).limit(limit).all()
    return [
        JobResponse(
            id=j.id,
            pipeline_id=j.pipeline_id,
            job_type=j.job_type,
            status=j.status,
            trigger_type=j.trigger_type,
            rows_extracted=j.rows_extracted,
            rows_transformed=j.rows_transformed,
            rows_loaded=j.rows_loaded,
            rows_rejected=j.rows_rejected,
            error_message=j.error_message,
            started_at=str(j.started_at) if j.started_at else None,
            completed_at=str(j.completed_at) if j.completed_at else None,
            duration_seconds=j.duration_seconds,
            created_at=str(j.created_at) if j.created_at else None,
        )
        for j in jobs
    ]


@router.get("/jobs/stats", response_model=JobStatsResponse)
async def get_job_stats(
    db: DbSession = Depends(get_db),
    tenant: dict = Depends(get_tenant_context),
):
    """Get aggregate job statistics."""
    org_id = tenant["organization_id"]
    monitor = JobMonitor(db)
    stats = monitor.get_stats(organization_id=org_id)
    return JobStatsResponse(**stats)


@router.get("/jobs/{job_id}", response_model=JobResponse)
async def get_job(
    job_id: int,
    db: DbSession = Depends(get_db),
    tenant: dict = Depends(get_tenant_context),
):
    """Get a specific job by ID."""
    org_id = tenant["organization_id"]
    job = verify_resource_ownership(db, ETLJob, job_id, org_id)
    return JobResponse(
        id=job.id,
        pipeline_id=job.pipeline_id,
        job_type=job.job_type,
        status=job.status,
        trigger_type=job.trigger_type,
        rows_extracted=job.rows_extracted,
        rows_transformed=job.rows_transformed,
        rows_loaded=job.rows_loaded,
        rows_rejected=job.rows_rejected,
        error_message=job.error_message,
        started_at=str(job.started_at) if job.started_at else None,
        completed_at=str(job.completed_at) if job.completed_at else None,
        duration_seconds=job.duration_seconds,
        created_at=str(job.created_at) if job.created_at else None,
    )


@router.get("/jobs/{job_id}/steps", response_model=list[dict])
async def get_job_steps(
    job_id: int,
    db: DbSession = Depends(get_db),
    tenant: dict = Depends(get_tenant_context),
):
    """Get step-level execution details for a job."""
    org_id = tenant["organization_id"]
    verify_resource_ownership(db, ETLJob, job_id, org_id)
    monitor = JobMonitor(db)
    return monitor.get_steps(job_id)


# --- Lineage endpoints ------------------------------------------------------


@router.get("/lineage", response_model=LineageResponse)
async def get_lineage_graph(
    job_id: int | None = Query(None),
    db: DbSession = Depends(get_db),
    tenant: dict = Depends(get_tenant_context),
):
    """Get data lineage graph (nodes + edges)."""
    org_id = tenant["organization_id"]
    if job_id is not None:
        verify_resource_ownership(db, ETLJob, job_id, org_id)
    lineage = LineageTracker(db)
    graph = lineage.build_graph(job_id=job_id, organization_id=org_id)
    return LineageResponse(**graph)


@router.get("/lineage/entries", response_model=list[dict])
async def get_lineage_entries(
    source_name: str | None = Query(None),
    job_id: int | None = Query(None),
    limit: int = Query(100, ge=1, le=500),
    db: DbSession = Depends(get_db),
    tenant: dict = Depends(get_tenant_context),
):
    """Get raw lineage entries."""
    org_id = tenant["organization_id"]
    if job_id is not None:
        verify_resource_ownership(db, ETLJob, job_id, org_id)
    lineage = LineageTracker(db)
    return lineage.get_lineage(
        source_name=source_name, job_id=job_id, organization_id=org_id, limit=limit
    )


# --- Schedule endpoints -----------------------------------------------------


@router.post("/schedules", response_model=ScheduleResponse)
async def create_schedule(
    request: ScheduleCreate,
    db: DbSession = Depends(get_db),
    tenant: dict = Depends(get_tenant_context),
):
    """Create a pipeline execution schedule."""
    current_user = tenant["user"]
    org_id = tenant["organization_id"]
    # Verify pipeline belongs to org
    verify_resource_ownership(db, ETLPipeline, request.pipeline_id, org_id)
    schedule = ETLSchedule(
        organization_id=org_id,
        pipeline_id=request.pipeline_id,
        schedule_type=request.schedule_type,
        cron_expr=request.cron_expr,
        created_by=current_user["id"] if current_user else None,
    )
    db.add(schedule)
    db.commit()
    db.refresh(schedule)
    return ScheduleResponse(
        id=schedule.id,
        pipeline_id=schedule.pipeline_id,
        schedule_type=schedule.schedule_type,
        cron_expr=schedule.cron_expr,
        is_active=bool(schedule.is_active),
        last_run_at=str(schedule.last_run_at) if schedule.last_run_at else None,
        next_run_at=str(schedule.next_run_at) if schedule.next_run_at else None,
    )


@router.get("/schedules", response_model=list[ScheduleResponse])
async def list_schedules(
    db: DbSession = Depends(get_db),
    tenant: dict = Depends(get_tenant_context),
):
    """List all schedules."""
    org_id = tenant["organization_id"]
    schedules = (
        db.query(ETLSchedule)
        .filter(ETLSchedule.is_active == 1, ETLSchedule.organization_id == org_id)
        .all()
    )
    return [
        ScheduleResponse(
            id=s.id,
            pipeline_id=s.pipeline_id,
            schedule_type=s.schedule_type,
            cron_expr=s.cron_expr,
            is_active=bool(s.is_active),
            last_run_at=str(s.last_run_at) if s.last_run_at else None,
            next_run_at=str(s.next_run_at) if s.next_run_at else None,
        )
        for s in schedules
    ]


@router.delete("/schedules/{schedule_id}", response_model=dict)
async def delete_schedule(
    schedule_id: int,
    db: DbSession = Depends(get_db),
    tenant: dict = Depends(get_tenant_context),
):
    """Deactivate a schedule."""
    org_id = tenant["organization_id"]
    schedule = verify_resource_ownership(db, ETLSchedule, schedule_id, org_id)
    schedule.is_active = 0
    db.commit()
    return {"id": schedule_id, "status": "deactivated"}


# --- Import Templates -------------------------------------------------------


@router.get("/templates", response_model=list[ImportTemplateResponse])
async def list_templates(
    db: DbSession = Depends(get_db),
    tenant: dict = Depends(get_tenant_context),
):
    """List all import templates."""
    org_id = tenant["organization_id"]
    templates = (
        db.query(ETLImportTemplate).filter(ETLImportTemplate.organization_id == org_id).all()
    )
    return [
        ImportTemplateResponse(
            id=t.id,
            name=t.name,
            source_type=t.source_type,
            source_config=t.source_config,
            column_mapping=t.column_mapping,
            transformations=t.transformations,
            created_at=str(t.created_at) if t.created_at else None,
        )
        for t in templates
    ]


@router.get("/templates/{template_id}", response_model=ImportTemplateResponse)
async def get_template(
    template_id: int,
    db: DbSession = Depends(get_db),
    tenant: dict = Depends(get_tenant_context),
):
    """Get an import template by ID."""
    org_id = tenant["organization_id"]
    template = verify_resource_ownership(db, ETLImportTemplate, template_id, org_id)
    return ImportTemplateResponse(
        id=template.id,
        name=template.name,
        source_type=template.source_type,
        source_config=template.source_config,
        column_mapping=template.column_mapping,
        transformations=template.transformations,
        created_at=str(template.created_at) if template.created_at else None,
    )


# --- Dashboard --------------------------------------------------------------


@router.get("/dashboard", response_model=DashboardResponse)
async def get_dashboard(
    db: DbSession = Depends(get_db),
    tenant: dict = Depends(get_tenant_context),
):
    """Get ETL dashboard metrics."""
    org_id = tenant["organization_id"]
    monitor = JobMonitor(db)
    stats = monitor.get_stats(organization_id=org_id)

    pipelines = (
        db.query(ETLPipeline)
        .filter(ETLPipeline.status == "active", ETLPipeline.organization_id == org_id)
        .count()
    )

    recent_jobs = (
        db.query(ETLJob)
        .filter(ETLJob.organization_id == org_id)
        .order_by(ETLJob.created_at.desc())
        .limit(10)
        .all()
    )
    recent_activity = [
        {
            "job_id": j.id,
            "type": j.job_type,
            "status": j.status,
            "created_at": str(j.created_at) if j.created_at else None,
        }
        for j in recent_jobs
    ]

    avg_quality = (
        db.query(ETLDataProfile)
        .filter(
            ETLDataProfile.quality_score.isnot(None),
            ETLDataProfile.organization_id == org_id,
        )
        .all()
    )
    avg_q = (
        round(sum(p.quality_score for p in avg_quality) / len(avg_quality), 2)
        if avg_quality
        else None
    )

    return DashboardResponse(
        total_jobs=stats["total_jobs"],
        running_jobs=stats["running"],
        completed_jobs=stats["completed"],
        failed_jobs=stats["failed"],
        success_rate=stats["success_rate"],
        average_quality_score=avg_q,
        recent_activity=recent_activity,
        active_pipelines=pipelines,
    )


# --- AI Hooks --------------------------------------------------------------


@router.get("/ai/hooks", response_model=AIHooksResponse)
async def get_ai_hooks(
    current_user=Depends(get_current_user),
):
    """List available AI hooks and their status."""
    return AIHooksResponse(hooks=list_ai_hooks())
