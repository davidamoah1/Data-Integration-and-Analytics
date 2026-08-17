"""Tests for the Enterprise Dataset Workflow Orchestrator.

Tests cover:
  - Full workflow execution
  - Stage status progression
  - Error handling and retries
  - Caching
  - Individual stage results
"""

from __future__ import annotations

import pandas as pd
import pytest

from services.dataset_workflow import (
    DatasetWorkflowOrchestrator,
    StageStatus,
    WorkflowStage,
)


@pytest.fixture
def sample_df():
    """Create a sample healthcare-like dataset."""
    return pd.DataFrame(
        {
            "patient_id": [1, 2, 3, 4, 5],
            "patient_name": [
                "John Doe",
                "Jane Smith",
                "Bob Wilson",
                "Alice Brown",
                "Charlie Davis",
            ],
            "age": [45, 32, 67, 28, 55],
            "diagnosis": ["E11.9", "J45.909", "I10", "E11.9", "M54.5"],
            "doctor": ["Dr. Smith", "Dr. Jones", "Dr. Smith", "Dr. Lee", "Dr. Jones"],
            "ward": ["A", "B", "A", "C", "B"],
            "admission_date": pd.to_datetime(
                ["2024-01-15", "2024-02-20", "2024-03-10", "2024-04-05", "2024-05-12"]
            ),
            "billing_amount": [1500.00, 3200.50, 8900.00, 750.00, 4200.00],
        }
    )


@pytest.fixture
def retail_df():
    """Create a sample retail dataset."""
    return pd.DataFrame(
        {
            "product_id": [101, 102, 103, 104, 105],
            "product_name": ["Widget A", "Widget B", "Gadget C", "Gadget D", "Tool E"],
            "category": ["Electronics", "Electronics", "Tools", "Tools", "Tools"],
            "price": [29.99, 49.99, 15.50, 25.00, 39.99],
            "quantity": [100, 50, 200, 75, 30],
            "sales": [2999.00, 2499.50, 3100.00, 1875.00, 1199.70],
            "region": ["North", "South", "North", "East", "West"],
            "order_date": pd.to_datetime(
                ["2024-01-01", "2024-01-15", "2024-02-01", "2024-02-15", "2024-03-01"]
            ),
        }
    )


@pytest.fixture
def empty_df():
    return pd.DataFrame()


@pytest.fixture
def orchestrator():
    return DatasetWorkflowOrchestrator(max_retries=1)


class TestWorkflowOrchestrator:
    """Tests for the DatasetWorkflowOrchestrator."""

    def test_full_workflow_completes(self, orchestrator, sample_df):
        """Test that a full workflow completes all stages."""
        state = orchestrator.start(sample_df, dataset_name="test_healthcare.csv")

        assert state.is_complete
        assert not state.has_errors
        assert state.current_stage == WorkflowStage.ANALYSIS_COMPLETE

    def test_all_stages_completed(self, orchestrator, sample_df):
        """Test that all stages are marked as completed."""
        state = orchestrator.start(sample_df, dataset_name="test.csv")

        for stage in WorkflowStage:
            assert stage in state.stages
            assert state.stages[stage].status == StageStatus.COMPLETED

    def test_upload_stage_result(self, orchestrator, sample_df):
        """Test that the upload stage captures correct metadata."""
        state = orchestrator.start(sample_df, dataset_name="test.csv")
        upload_result = state.stages[WorkflowStage.UPLOADED].result

        assert upload_result["row_count"] == 5
        assert upload_result["column_count"] == 8
        assert "memory_mb" in upload_result

    def test_validation_stage(self, orchestrator, sample_df):
        """Test that validation passes for a valid dataset."""
        state = orchestrator.start(sample_df, dataset_name="test.csv")
        validation = state.stages[WorkflowStage.VALIDATED].result

        assert validation["is_valid"] is True
        assert isinstance(validation["issues"], list)

    def test_validation_fails_on_empty_dataset(self, orchestrator, empty_df):
        """Test that validation fails for an empty dataset."""
        state = orchestrator.start(empty_df, dataset_name="empty.csv")

        assert state.has_errors
        assert state.stages[WorkflowStage.VALIDATED].status == StageStatus.FAILED

    def test_profile_stage(self, orchestrator, sample_df):
        """Test that profiling generates a complete profile."""
        state = orchestrator.start(sample_df, dataset_name="test.csv")
        profile = state.stages[WorkflowStage.PROFILED].result

        assert profile["row_count"] == 5
        assert profile["column_count"] == 8
        assert "overall_quality_score" in profile
        assert "columns" in profile
        assert len(profile["columns"]) == 8

    def test_quality_stage(self, orchestrator, sample_df):
        """Test that quality check produces a score."""
        state = orchestrator.start(sample_df, dataset_name="test.csv")
        quality = state.stages[WorkflowStage.QUALITY_CHECKED].result

        assert "findings" in quality
        assert "score" in quality
        assert "summary" in quality

    def test_industry_detection(self, orchestrator, sample_df):
        """Test that industry detection identifies healthcare."""
        state = orchestrator.start(sample_df, dataset_name="test.csv")
        industry = state.stages[WorkflowStage.INDUSTRY_IDENTIFIED].result

        assert "industry" in industry
        assert "confidence" in industry
        assert "detected_entities" in industry

    def test_insights_generated(self, orchestrator, sample_df):
        """Test that AI insights are generated."""
        state = orchestrator.start(sample_df, dataset_name="test.csv")
        insights = state.stages[WorkflowStage.INSIGHTS_GENERATED].result

        assert "insights" in insights
        assert "executive_summary" in insights
        assert "total_insights" in insights

    def test_dashboard_recommendation(self, orchestrator, sample_df):
        """Test that dashboard recommendations are generated."""
        state = orchestrator.start(sample_df, dataset_name="test.csv")
        dashboard = state.stages[WorkflowStage.DASHBOARD_READY].result

        assert "recommended" in dashboard
        assert "reasoning" in dashboard
        assert "recommended_charts" in dashboard

    def test_analysis_summary(self, orchestrator, sample_df):
        """Test that the final analysis summary is correct."""
        state = orchestrator.start(sample_df, dataset_name="test.csv")
        summary = state.stages[WorkflowStage.ANALYSIS_COMPLETE].result

        assert summary["dataset_name"] == "test.csv"
        assert summary["row_count"] == 5
        assert summary["column_count"] == 8

    def test_workflow_state_serializable(self, orchestrator, sample_df):
        """Test that workflow state can be serialized to dict."""
        state = orchestrator.start(sample_df, dataset_name="test.csv")
        data = state.to_dict()

        assert "workflow_id" in data
        assert "stages" in data
        assert "is_complete" in data
        assert isinstance(data["stages"], dict)

    def test_caching_same_dataset(self, orchestrator, sample_df):
        """Test that identical datasets return cached results."""
        state1 = orchestrator.start(sample_df, dataset_name="test.csv")
        state2 = orchestrator.start(sample_df, dataset_name="test.csv")

        # Should return a cached state (different workflow ID but same results)
        assert state2.is_complete
        assert state1.workflow_id != state2.workflow_id
        assert state2.stages[WorkflowStage.UPLOADED].result["row_count"] == 5

    def test_cache_hit_reattributes_ownership_to_current_caller(self, orchestrator, sample_df):
        """A cache hit must not leak the first caller's org/user attribution."""
        state1 = orchestrator.start(
            sample_df, dataset_name="shared.csv", created_by=1, organization_id=100
        )
        assert state1.created_by == 1
        assert state1.organization_id == 100

        # Second caller, different org/user, identical dataset content+name -
        # must hit the cache but be attributed to itself, not the first caller.
        state2 = orchestrator.start(
            sample_df, dataset_name="shared.csv", created_by=2, organization_id=200
        )
        assert state2.workflow_id != state1.workflow_id
        assert state2.created_by == 2
        assert state2.organization_id == 200
        # Original workflow's attribution must be unaffected.
        assert orchestrator.get_state(state1.workflow_id).organization_id == 100

    def test_caching_different_dataset(self, orchestrator, sample_df, retail_df):
        """Test that different datasets are not cached."""
        state1 = orchestrator.start(sample_df, dataset_name="healthcare.csv")
        state2 = orchestrator.start(retail_df, dataset_name="retail.csv")

        assert state1.workflow_id != state2.workflow_id
        assert state2.stages[WorkflowStage.UPLOADED].result["row_count"] == 5

    def test_retail_dataset_workflow(self, orchestrator, retail_df):
        """Test that retail datasets complete the workflow."""
        state = orchestrator.start(retail_df, dataset_name="retail.csv")

        assert state.is_complete
        assert not state.has_errors

    def test_stage_durations_logged(self, orchestrator, sample_df):
        """Test that each stage logs execution duration."""
        state = orchestrator.start(sample_df, dataset_name="test.csv")

        for stage in WorkflowStage:
            result = state.stages[stage]
            assert result.duration_seconds >= 0
            assert result.started_at != ""
            assert result.completed_at != ""


class TestEnterpriseProfiler:
    """Tests for the EnterpriseDataProfiler."""

    def test_profile_basic(self, sample_df):
        from services.enterprise_profiler import EnterpriseDataProfiler

        profiler = EnterpriseDataProfiler()
        result = profiler.profile(sample_df, source_name="test.csv")

        assert result["row_count"] == 5
        assert result["column_count"] == 8
        assert "overall_quality_score" in result
        assert "columns" in result
        assert len(result["columns"]) == 8

    def test_profile_detects_sensitive_columns(self):
        from services.enterprise_profiler import EnterpriseDataProfiler

        df = pd.DataFrame(
            {
                "name": ["John", "Jane", "Bob"],
                "email": ["john@test.com", "jane@test.com", "bob@test.com"],
                "age": [25, 30, 35],
            }
        )
        profiler = EnterpriseDataProfiler()
        result = profiler.profile(df)

        assert "email" in result["sensitive_columns"]

    def test_profile_detects_primary_keys(self, sample_df):
        from services.enterprise_profiler import EnterpriseDataProfiler

        profiler = EnterpriseDataProfiler()
        result = profiler.profile(sample_df)

        # patient_id should be a strong PK candidate
        assert "patient_id" in result["candidate_primary_keys"]

    def test_profile_correlations(self):
        from services.enterprise_profiler import EnterpriseDataProfiler

        df = pd.DataFrame(
            {
                "x": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
                "y": [2, 4, 6, 8, 10, 12, 14, 16, 18, 20],  # Perfect positive correlation
                "z": [10, 9, 8, 7, 6, 5, 4, 3, 2, 1],  # Perfect negative correlation
            }
        )
        profiler = EnterpriseDataProfiler()
        result = profiler.profile(df)

        assert len(result["correlations"]) > 0
        strong_corr = [c for c in result["correlations"] if c["strength"] == "strong"]
        assert len(strong_corr) >= 2

    def test_profile_empty_dataframe(self):
        from services.enterprise_profiler import EnterpriseDataProfiler

        df = pd.DataFrame()
        profiler = EnterpriseDataProfiler()
        result = profiler.profile(df)

        assert result["row_count"] == 0
        assert result["column_count"] == 0


class TestQualityChecks:
    """Tests for the extended quality checks."""

    def test_invalid_dates_detected(self):
        from data_quality.checks import QualityCheckEngine

        df = pd.DataFrame(
            {
                "order_date": ["2024-01-01", "2024-02-15", "not_a_date", "2024-03-30", "invalid"],
                "amount": [100, 200, 300, 400, 500],
            }
        )
        findings = QualityCheckEngine.run(df)

        date_findings = [f for f in findings if f.check_name == "invalid_dates"]
        assert len(date_findings) > 0
        assert date_findings[0].affected_rows == 2

    def test_invalid_numeric_detected(self):
        from data_quality.checks import QualityCheckEngine

        df = pd.DataFrame(
            {
                "sales_amount": ["100.50", "200.00", "N/A", "$300.00", "400"],
                "category": ["A", "B", "C", "D", "E"],
            }
        )
        findings = QualityCheckEngine.run(df)

        numeric_findings = [f for f in findings if f.check_name == "invalid_numeric"]
        assert len(numeric_findings) > 0

    def test_valid_data_no_false_positives(self, sample_df):
        from data_quality.checks import QualityCheckEngine

        findings = QualityCheckEngine.run(sample_df)
        date_findings = [f for f in findings if f.check_name == "invalid_dates"]
        # admission_date is proper datetime, should not trigger
        assert len(date_findings) == 0
