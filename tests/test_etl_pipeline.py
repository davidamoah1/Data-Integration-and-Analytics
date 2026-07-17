"""Tests for ETL pipeline builder, executor, and job monitor."""

from etl.models import ETLJob
from etl.pipeline_builder import JobMonitor, PipelineBuilder


class TestPipelineBuilder:
    def test_create_pipeline(self, db_session):
        builder = PipelineBuilder(db_session)
        pipeline = builder.create_pipeline(
            name="Test Pipeline",
            description="A test pipeline",
            steps=[
                {
                    "type": "extract",
                    "source_type": "csv",
                    "source_config": {"file_path": "test.csv"},
                }
            ],
        )
        assert pipeline.id is not None
        assert pipeline.name == "Test Pipeline"
        assert pipeline.current_version == 1

    def test_get_pipeline(self, db_session):
        builder = PipelineBuilder(db_session)
        builder.create_pipeline(name="Get Test", steps=[])
        pipelines = builder.list_pipelines()
        assert len(pipelines) >= 1
        p = builder.get_pipeline(pipelines[0]["id"])
        assert p["name"] == "Get Test"

    def test_update_pipeline_new_version(self, db_session):
        builder = PipelineBuilder(db_session)
        pipeline = builder.create_pipeline(
            name="Version Test",
            steps=[{"type": "extract", "source_type": "csv", "source_config": {}}],
        )
        new_version = builder.update_pipeline(
            pipeline.id, steps=[{"type": "extract", "source_type": "json", "source_config": {}}]
        )
        assert new_version.version_number == 2

    def test_version_history(self, db_session):
        builder = PipelineBuilder(db_session)
        pipeline = builder.create_pipeline(name="History Test", steps=[])
        builder.update_pipeline(pipeline.id, steps=[])
        builder.update_pipeline(pipeline.id, steps=[])
        history = builder.get_version_history(pipeline.id)
        assert len(history) == 3
        assert history[0]["version_number"] == 3

    def test_rollback_version(self, db_session):
        builder = PipelineBuilder(db_session)
        pipeline = builder.create_pipeline(
            name="Rollback Test",
            steps=[{"type": "extract", "source_type": "csv", "source_config": {}}],
        )
        builder.update_pipeline(
            pipeline.id, steps=[{"type": "extract", "source_type": "json", "source_config": {}}]
        )
        rolled = builder.rollback_version(pipeline.id, 1)
        assert rolled.version_number == 1
        assert rolled.is_active == 1

    def test_list_pipelines(self, db_session):
        builder = PipelineBuilder(db_session)
        builder.create_pipeline(name="List A", steps=[])
        builder.create_pipeline(name="List B", steps=[])
        pipelines = builder.list_pipelines()
        assert len(pipelines) >= 2


class TestJobMonitor:
    def test_list_jobs_empty(self, db_session):
        monitor = JobMonitor(db_session)
        jobs = monitor.list_jobs()
        assert isinstance(jobs, list)

    def test_get_stats(self, db_session):
        monitor = JobMonitor(db_session)
        stats = monitor.get_stats()
        assert "total_jobs" in stats
        assert "success_rate" in stats
        assert "failure_rate" in stats

    def test_create_and_get_job(self, db_session):
        job = ETLJob(job_type="import", status="completed", trigger_type="manual")
        db_session.add(job)
        db_session.commit()
        db_session.refresh(job)

        monitor = JobMonitor(db_session)
        result = monitor.get_job(job.id)
        assert result["id"] == job.id
        assert result["status"] == "completed"
