"""Tests for data lineage tracking and report generation."""

import pytest

from etl.lineage import LineageTracker
from etl.reports import ReportGenerator


class TestLineageTracker:
    def test_record_lineage(self, db_session):
        tracker = LineageTracker(db_session)
        entry = tracker.record(
            source_name="test.csv",
            source_type="csv",
            transformation="rename, filter",
            destination_name="sales",
            destination_type="database",
            organization_id=1,
        )
        assert entry.id is not None
        assert entry.source_name == "test.csv"

    def test_get_lineage(self, db_session):
        tracker = LineageTracker(db_session)
        tracker.record(
            source_name="a.csv",
            source_type="csv",
            destination_name="table_a",
            destination_type="database",
            organization_id=1,
        )
        tracker.record(
            source_name="b.csv",
            source_type="csv",
            destination_name="table_b",
            destination_type="database",
            organization_id=1,
        )
        entries = tracker.get_lineage()
        assert len(entries) >= 2

    def test_get_lineage_by_source(self, db_session):
        tracker = LineageTracker(db_session)
        tracker.record(source_name="unique.csv", source_type="csv", organization_id=1)
        entries = tracker.get_lineage(source_name="unique.csv")
        assert all(e["source_name"] == "unique.csv" for e in entries)

    def test_build_graph(self, db_session):
        tracker = LineageTracker(db_session)
        tracker.record(
            source_name="src.csv",
            source_type="csv",
            destination_name="dest_table",
            destination_type="database",
            transformation="rename",
            organization_id=1,
        )
        graph = tracker.build_graph()
        assert "nodes" in graph
        assert "edges" in graph
        assert len(graph["edges"]) >= 1
        assert any(n["name"] == "src.csv" for n in graph["nodes"])


class TestReportGenerator:
    def test_import_summary(self):
        gen = ReportGenerator()
        report = gen.import_summary("test.csv", "csv", 100, 5, quality_score=85)
        assert report["report_type"] == "import_summary"
        assert report["row_count"] == 100
        assert report["quality_score"] == 85

    def test_quality_report(self):
        gen = ReportGenerator()
        quality = {
            "source_name": "test",
            "overall_score": 80,
            "checks_passed": 5,
            "checks_failed": 1,
            "checks_warning": 1,
            "recommendations": ["Fix duplicates"],
            "checks": [],
        }
        report = gen.quality_report(quality)
        assert report["report_type"] == "quality_report"
        assert report["overall_score"] == 80

    def test_pipeline_report(self):
        gen = ReportGenerator()
        metrics = {
            "job_id": 1,
            "pipeline_id": 1,
            "status": "completed",
            "rows_extracted": 100,
            "rows_transformed": 95,
            "rows_loaded": 90,
            "rows_rejected": 5,
            "duration_seconds": 10.5,
        }
        report = gen.pipeline_report(
            metrics, step_records=[{"step_name": "extract", "status": "completed"}]
        )
        assert report["report_type"] == "pipeline_report"
        assert report["rows_loaded"] == 90

    def test_execution_report(self):
        gen = ReportGenerator()
        jobs = [
            {"status": "completed", "duration_seconds": 10},
            {"status": "failed", "duration_seconds": 5},
            {"status": "completed", "duration_seconds": 15},
        ]
        report = gen.execution_report(jobs)
        assert report["total_jobs"] == 3
        assert report["completed"] == 2
        assert report["failed"] == 1
        assert report["success_rate"] == pytest.approx(66.67, rel=0.1)

    def test_transformation_report(self):
        gen = ReportGenerator()
        report = gen.transformation_report(
            transformations=[{"type": "rename"}, {"type": "filter"}],
            before_count=100,
            after_count=95,
        )
        assert report["rows_before"] == 100
        assert report["rows_after"] == 95
        assert report["rows_changed"] == 5

    def test_performance_report(self):
        gen = ReportGenerator()
        report = gen.performance_report(
            {
                "duration_seconds": 10,
                "rows_loaded": 1000,
                "rows_extracted": 1000,
                "rows_transformed": 950,
            }
        )
        assert report["rows_per_second"] == 100.0
