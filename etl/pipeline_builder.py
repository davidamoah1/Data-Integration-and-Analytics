"""ETL Pipeline Builder — create, version, execute, and manage reusable pipelines.

Pipelines consist of steps (extract, validate, clean, transform, load, report, notify).
Each step has configuration, validation, logging, execution status, duration, and retry count.
"""

from datetime import datetime
from typing import Optional, Any
import pandas as pd
from sqlalchemy.orm import Session as DbSession

from etl.models import (
    ETLPipeline, ETLPipelineVersion, ETLPipelineStep, ETLJob,
    ETLDataProfile, ETLQualityReport, ETLDataLineage,
)
from etl.connectors.connectors import get_connector
from etl.profiling import DataProfiler
from etl.quality import DataQualityEngine
from etl.transformations import TransformationEngine
from etl.load_engine import LoadEngine, LoadMode
from etl.lineage import LineageTracker
from etl.reports import ReportGenerator
from etl.logging_config import logger


class PipelineBuilder:
    """Creates and manages ETL pipeline definitions and versions."""

    def __init__(self, db: DbSession):
        self.db = db

    def create_pipeline(self, name: str, description: str = "", steps: list[dict] = None, created_by: Optional[int] = None) -> ETLPipeline:
        """Create a new pipeline with an initial version."""
        pipeline = ETLPipeline(
            name=name,
            description=description,
            status="active",
            current_version=1,
            created_by=created_by,
        )
        self.db.add(pipeline)
        self.db.flush()

        version = ETLPipelineVersion(
            pipeline_id=pipeline.id,
            version_number=1,
            step_config=steps or [],
            created_by=created_by,
            is_active=1,
        )
        self.db.add(version)
        self.db.commit()
        logger.info(f"Pipeline created: '{name}' (id={pipeline.id}, version=1)")
        return pipeline

    def update_pipeline(self, pipeline_id: int, steps: list[dict], created_by: Optional[int] = None) -> ETLPipelineVersion:
        """Create a new version of an existing pipeline."""
        pipeline = self.db.query(ETLPipeline).filter(ETLPipeline.id == pipeline_id).first()
        if not pipeline:
            raise ValueError(f"Pipeline not found: {pipeline_id}")

        # Deactivate old versions
        old_versions = self.db.query(ETLPipelineVersion).filter(
            ETLPipelineVersion.pipeline_id == pipeline_id,
            ETLPipelineVersion.is_active == 1,
        ).all()
        for v in old_versions:
            v.is_active = 0

        new_version_num = pipeline.current_version + 1
        version = ETLPipelineVersion(
            pipeline_id=pipeline_id,
            version_number=new_version_num,
            step_config=steps,
            created_by=created_by,
            is_active=1,
        )
        self.db.add(version)
        pipeline.current_version = new_version_num
        self.db.commit()
        logger.info(f"Pipeline {pipeline_id} updated to version {new_version_num}")
        return version

    def rollback_version(self, pipeline_id: int, version_number: int) -> ETLPipelineVersion:
        """Rollback to a previous pipeline version."""
        target = self.db.query(ETLPipelineVersion).filter(
            ETLPipelineVersion.pipeline_id == pipeline_id,
            ETLPipelineVersion.version_number == version_number,
        ).first()
        if not target:
            raise ValueError(f"Version {version_number} not found for pipeline {pipeline_id}")

        # Deactivate current
        self.db.query(ETLPipelineVersion).filter(
            ETLPipelineVersion.pipeline_id == pipeline_id,
            ETLPipelineVersion.is_active == 1,
        ).update({"is_active": 0})

        target.is_active = 1
        pipeline = self.db.query(ETLPipeline).filter(ETLPipeline.id == pipeline_id).first()
        if pipeline:
            pipeline.current_version = version_number
        self.db.commit()
        logger.info(f"Pipeline {pipeline_id} rolled back to version {version_number}")
        return target

    def get_pipeline(self, pipeline_id: int) -> Optional[dict]:
        """Get pipeline with current version config."""
        pipeline = self.db.query(ETLPipeline).filter(ETLPipeline.id == pipeline_id).first()
        if not pipeline:
            return None
        version = self.db.query(ETLPipelineVersion).filter(
            ETLPipelineVersion.pipeline_id == pipeline_id,
            ETLPipelineVersion.is_active == 1,
        ).first()
        return {
            "id": pipeline.id,
            "name": pipeline.name,
            "description": pipeline.description,
            "status": pipeline.status,
            "current_version": pipeline.current_version,
            "steps": version.step_config if version else [],
            "created_by": pipeline.created_by,
            "created_at": str(pipeline.created_at) if pipeline.created_at else None,
        }

    def list_pipelines(self) -> list[dict]:
        """List all pipelines."""
        pipelines = self.db.query(ETLPipeline).filter(ETLPipeline.status != "archived").all()
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

    def get_version_history(self, pipeline_id: int) -> list[dict]:
        """Get version history for a pipeline."""
        versions = self.db.query(ETLPipelineVersion).filter(
            ETLPipelineVersion.pipeline_id == pipeline_id,
        ).order_by(ETLPipelineVersion.version_number.desc()).all()
        return [
            {
                "id": v.id,
                "version_number": v.version_number,
                "is_active": bool(v.is_active),
                "created_by": v.created_by,
                "created_at": str(v.created_at) if v.created_at else None,
            }
            for v in versions
        ]


class PipelineExecutor:
    """Executes a pipeline step by step with full tracking."""

    def __init__(self, db: DbSession, load_engine: Optional[LoadEngine] = None):
        self.db = db
        self.profiler = DataProfiler()
        self.quality_engine = DataQualityEngine()
        self.transform_engine = TransformationEngine()
        self.load_engine = load_engine or LoadEngine()
        self.report_gen = ReportGenerator()
        self.lineage = LineageTracker(db)

    def execute(self, pipeline_id: int, user_id: Optional[int] = None, trigger_type: str = "manual") -> dict:
        """Execute a pipeline by ID.

        Returns:
            Dict with job metrics and step results.
        """
        # Load pipeline config
        pipeline = self.db.query(ETLPipeline).filter(ETLPipeline.id == pipeline_id).first()
        if not pipeline:
            raise ValueError(f"Pipeline not found: {pipeline_id}")

        version = self.db.query(ETLPipelineVersion).filter(
            ETLPipelineVersion.pipeline_id == pipeline_id,
            ETLPipelineVersion.is_active == 1,
        ).first()
        if not version:
            raise ValueError(f"No active version for pipeline {pipeline_id}")

        steps = version.step_config or []

        # Create job record
        job = ETLJob(
            pipeline_id=pipeline_id,
            job_type="pipeline",
            status="running",
            trigger_type=trigger_type,
            started_at=datetime.utcnow(),
            created_by=user_id,
        )
        self.db.add(job)
        self.db.commit()
        self.db.refresh(job)

        logger.info(f"Pipeline execution started: job_id={job.id}, pipeline_id={pipeline_id}")

        metrics = {
            "job_id": job.id,
            "pipeline_id": pipeline_id,
            "status": "running",
            "rows_extracted": 0,
            "rows_transformed": 0,
            "rows_loaded": 0,
            "rows_rejected": 0,
            "duration_seconds": 0,
        }

        start_time = datetime.utcnow()
        df = None
        step_records = []

        try:
            for step_config in steps:
                step_record = self._execute_step(job.id, step_config, df, user_id, pipeline_id)
                step_records.append(step_record)
                if step_config["type"] == "extract" and step_record["status"] == "completed":
                    df = step_record.get("data")
                if step_config["type"] in ("clean", "transform") and step_record["status"] == "completed":
                    df = step_record.get("data")
                if step_config["type"] == "load" and step_record["status"] == "completed":
                    metrics["rows_loaded"] = step_record.get("rows_processed", 0)

            if df is not None:
                metrics["rows_extracted"] = len(df) if "extract" in [s["type"] for s in steps] else 0
                metrics["rows_transformed"] = len(df) if "transform" in [s["type"] for s in steps] else 0

            duration = (datetime.utcnow() - start_time).total_seconds()
            metrics["duration_seconds"] = round(duration, 2)
            metrics["status"] = "completed"

            job.status = "completed"
            job.rows_extracted = metrics["rows_extracted"]
            job.rows_transformed = metrics["rows_transformed"]
            job.rows_loaded = metrics["rows_loaded"]
            job.duration_seconds = int(duration)
            job.completed_at = datetime.utcnow()
            self.db.commit()

        except Exception as e:
            metrics["status"] = "failed"
            job.status = "failed"
            job.error_message = str(e)
            job.completed_at = datetime.utcnow()
            self.db.commit()
            logger.error(f"Pipeline execution failed: {e}")
            raise

        metrics["steps"] = step_records
        return metrics

    def _execute_step(self, job_id: int, config: dict, df: Optional[pd.DataFrame], user_id: Optional[int], pipeline_id: int) -> dict:
        """Execute a single pipeline step."""
        step_type = config["type"]
        step_name = config.get("name", step_type)

        step = ETLPipelineStep(
            job_id=job_id,
            step_name=step_name,
            step_type=step_type,
            status="running",
            config=config,
            started_at=datetime.utcnow(),
        )
        self.db.add(step)
        self.db.commit()
        self.db.refresh(step)

        result = {"step_name": step_name, "step_type": step_type, "status": "completed", "rows_processed": 0}

        try:
            if step_type == "extract":
                source_type = config["source_type"]
                source_config = config["source_config"]
                connector = get_connector(source_type, source_config)
                with connector:
                    df = connector.extract()
                result["data"] = df
                result["rows_processed"] = len(df)
                self.lineage.record(
                    source_name=config.get("source_name", source_type),
                    source_type=source_type,
                    job_id=job_id,
                    pipeline_id=pipeline_id,
                    user_id=user_id,
                )

            elif step_type == "validate":
                if df is not None:
                    quality_result = self.quality_engine.run_checks(df)
                    result["quality_result"] = quality_result
                    result["rows_processed"] = len(df)
                    report = ETLQualityReport(
                        job_id=job_id,
                        source_name=config.get("source_name", "pipeline"),
                        overall_score=quality_result["overall_score"],
                        checks_passed=quality_result["checks_passed"],
                        checks_failed=quality_result["checks_failed"],
                        checks_warning=quality_result["checks_warning"],
                        report_data=quality_result,
                        recommendations=quality_result.get("recommendations"),
                    )
                    self.db.add(report)
                    self.db.commit()

            elif step_type == "clean":
                if df is not None:
                    df = self.quality_engine.apply_fixes(df)
                    result["data"] = df
                    result["rows_processed"] = len(df)

            elif step_type == "transform":
                if df is not None:
                    transformations = config.get("transformations", [])
                    before = len(df)
                    df = self.transform_engine.apply(df, transformations)
                    result["data"] = df
                    result["rows_processed"] = len(df)
                    self.lineage.record(
                        source_name="transformed_data",
                        source_type="transform",
                        transformation=str([t.get("type") for t in transformations]),
                        job_id=job_id,
                        pipeline_id=pipeline_id,
                        user_id=user_id,
                    )

            elif step_type == "profile":
                if df is not None:
                    profile = self.profiler.profile(df, config.get("source_name", "pipeline"))
                    result["profile"] = profile
                    result["rows_processed"] = len(df)
                    profile_rec = ETLDataProfile(
                        job_id=job_id,
                        source_name=config.get("source_name", "pipeline"),
                        source_type="pipeline",
                        row_count=profile["row_count"],
                        column_count=profile["column_count"],
                        profile_data=profile,
                        quality_score=profile.get("quality_score"),
                    )
                    self.db.add(profile_rec)
                    self.db.commit()

            elif step_type == "load":
                if df is not None:
                    table = config["table"]
                    mode_str = config.get("mode", "insert")
                    mode = LoadMode(mode_str)
                    conflict_columns = config.get("conflict_columns")
                    load_result = self.load_engine.load(df, table, mode, conflict_columns)
                    result["rows_processed"] = load_result.get("rows_inserted", 0) + load_result.get("rows_updated", 0)
                    result["load_result"] = load_result
                    self.lineage.record(
                        source_name=config.get("source_name", "transformed_data"),
                        source_type="transform",
                        destination_name=table,
                        destination_type="database",
                        job_id=job_id,
                        pipeline_id=pipeline_id,
                        user_id=user_id,
                    )

            elif step_type == "report":
                report_type = config.get("report_type", "pipeline")
                if report_type == "quality" and df is not None:
                    qr = self.quality_engine.run_checks(df)
                    result["report"] = self.report_gen.quality_report(qr)
                else:
                    result["report"] = self.report_gen.pipeline_report(metrics={"job_id": job_id})

            elif step_type == "notify":
                result["notification"] = config.get("message", "Pipeline step completed")

            step.status = "completed"
            step.completed_at = datetime.utcnow()
            step.rows_processed = result.get("rows_processed", 0)
            if step.started_at:
                step.duration_seconds = int((step.completed_at - step.started_at).total_seconds())

        except Exception as e:
            step.status = "failed"
            step.error_message = str(e)
            step.completed_at = datetime.utcnow()
            result["status"] = "failed"
            result["error"] = str(e)
            self.db.commit()
            raise

        self.db.commit()
        return result


class JobMonitor:
    """Monitors ETL job status and statistics."""

    def __init__(self, db: DbSession):
        self.db = db

    def get_job(self, job_id: int) -> Optional[dict]:
        job = self.db.query(ETLJob).filter(ETLJob.id == job_id).first()
        if not job:
            return None
        return self._job_to_dict(job)

    def list_jobs(self, status: Optional[str] = None, limit: int = 50) -> list[dict]:
        query = self.db.query(ETLJob)
        if status:
            query = query.filter(ETLJob.status == status)
        jobs = query.order_by(ETLJob.created_at.desc()).limit(limit).all()
        return [self._job_to_dict(j) for j in jobs]

    def get_stats(self) -> dict:
        jobs = self.db.query(ETLJob).all()
        total = len(jobs)
        running = sum(1 for j in jobs if j.status == "running")
        completed = sum(1 for j in jobs if j.status == "completed")
        failed = sum(1 for j in jobs if j.status == "failed")
        queued = sum(1 for j in jobs if j.status == "queued")
        durations = [j.duration_seconds for j in jobs if j.duration_seconds]
        avg_duration = round(sum(durations) / len(durations), 2) if durations else 0
        return {
            "total_jobs": total,
            "running": running,
            "completed": completed,
            "failed": failed,
            "queued": queued,
            "success_rate": round((completed / max(total, 1)) * 100, 2),
            "failure_rate": round((failed / max(total, 1)) * 100, 2),
            "average_duration_seconds": avg_duration,
        }

    def get_steps(self, job_id: int) -> list[dict]:
        steps = self.db.query(ETLPipelineStep).filter(ETLPipelineStep.job_id == job_id).all()
        return [
            {
                "id": s.id,
                "step_name": s.step_name,
                "step_type": s.step_type,
                "status": s.status,
                "rows_processed": s.rows_processed,
                "duration_seconds": s.duration_seconds,
                "retry_count": s.retry_count,
                "error_message": s.error_message,
                "started_at": str(s.started_at) if s.started_at else None,
                "completed_at": str(s.completed_at) if s.completed_at else None,
            }
            for s in steps
        ]

    def _job_to_dict(self, job: ETLJob) -> dict:
        return {
            "id": job.id,
            "pipeline_id": job.pipeline_id,
            "job_type": job.job_type,
            "status": job.status,
            "trigger_type": job.trigger_type,
            "rows_extracted": job.rows_extracted,
            "rows_transformed": job.rows_transformed,
            "rows_loaded": job.rows_loaded,
            "rows_rejected": job.rows_rejected,
            "error_message": job.error_message,
            "duration_seconds": job.duration_seconds,
            "started_at": str(job.started_at) if job.started_at else None,
            "completed_at": str(job.completed_at) if job.completed_at else None,
            "created_at": str(job.created_at) if job.created_at else None,
        }
