"""Report generation for imports, quality, pipeline execution, and transformations."""

from datetime import datetime, timezone


class ReportGenerator:
    """Generates structured reports from ETL operation results."""

    def import_summary(
        self,
        source_name: str,
        source_type: str,
        row_count: int,
        column_count: int,
        quality_score: int | None = None,
        errors: list | None = None,
    ) -> dict:
        return {
            "report_type": "import_summary",
            "generated_at": datetime.now(timezone.utc).replace(tzinfo=None).isoformat(),
            "source_name": source_name,
            "source_type": source_type,
            "row_count": row_count,
            "column_count": column_count,
            "quality_score": quality_score,
            "errors": errors or [],
            "status": "success" if not errors else "completed_with_errors",
        }

    def quality_report(self, quality_result: dict) -> dict:
        return {
            "report_type": "quality_report",
            "generated_at": datetime.now(timezone.utc).replace(tzinfo=None).isoformat(),
            "source_name": quality_result.get("source_name"),
            "overall_score": quality_result.get("overall_score"),
            "checks_passed": quality_result.get("checks_passed"),
            "checks_failed": quality_result.get("checks_failed"),
            "checks_warning": quality_result.get("checks_warning"),
            "recommendations": quality_result.get("recommendations"),
            "checks": quality_result.get("checks"),
        }

    def pipeline_report(self, job_metrics: dict, step_records: list | None = None) -> dict:
        return {
            "report_type": "pipeline_report",
            "generated_at": datetime.now(timezone.utc).replace(tzinfo=None).isoformat(),
            "job_id": job_metrics.get("job_id"),
            "pipeline_id": job_metrics.get("pipeline_id"),
            "status": job_metrics.get("status"),
            "rows_extracted": job_metrics.get("rows_extracted"),
            "rows_transformed": job_metrics.get("rows_transformed"),
            "rows_loaded": job_metrics.get("rows_loaded"),
            "rows_rejected": job_metrics.get("rows_rejected"),
            "duration_seconds": job_metrics.get("duration_seconds"),
            "steps": step_records or [],
        }

    def execution_report(self, jobs: list[dict]) -> dict:
        total = len(jobs)
        completed = sum(1 for j in jobs if j.get("status") == "completed")
        failed = sum(1 for j in jobs if j.get("status") == "failed")
        running = sum(1 for j in jobs if j.get("status") == "running")
        avg_duration = 0
        durations = [j.get("duration_seconds", 0) for j in jobs if j.get("duration_seconds")]
        if durations:
            avg_duration = round(sum(durations) / len(durations), 2)
        return {
            "report_type": "execution_report",
            "generated_at": datetime.now(timezone.utc).replace(tzinfo=None).isoformat(),
            "total_jobs": total,
            "completed": completed,
            "failed": failed,
            "running": running,
            "success_rate": round((completed / max(total, 1)) * 100, 2),
            "failure_rate": round((failed / max(total, 1)) * 100, 2),
            "average_duration_seconds": avg_duration,
        }

    def validation_report(self, validation_results: list[dict]) -> dict:
        passed = sum(1 for v in validation_results if v.get("passed"))
        failed = sum(1 for v in validation_results if not v.get("passed"))
        return {
            "report_type": "validation_report",
            "generated_at": datetime.now(timezone.utc).replace(tzinfo=None).isoformat(),
            "total_checks": len(validation_results),
            "passed": passed,
            "failed": failed,
            "results": validation_results,
        }

    def transformation_report(
        self, transformations: list[dict], before_count: int, after_count: int
    ) -> dict:
        return {
            "report_type": "transformation_report",
            "generated_at": datetime.now(timezone.utc).replace(tzinfo=None).isoformat(),
            "transformations_applied": len(transformations),
            "transformation_types": [t.get("type") for t in transformations],
            "rows_before": before_count,
            "rows_after": after_count,
            "rows_changed": before_count - after_count,
        }

    def performance_report(self, job_metrics: dict) -> dict:
        return {
            "report_type": "performance_report",
            "generated_at": datetime.now(timezone.utc).replace(tzinfo=None).isoformat(),
            "duration_seconds": job_metrics.get("duration_seconds"),
            "rows_per_second": round(
                job_metrics.get("rows_loaded", 0) / max(job_metrics.get("duration_seconds", 1), 1),
                2,
            ),
            "rows_extracted": job_metrics.get("rows_extracted"),
            "rows_transformed": job_metrics.get("rows_transformed"),
            "rows_loaded": job_metrics.get("rows_loaded"),
        }
