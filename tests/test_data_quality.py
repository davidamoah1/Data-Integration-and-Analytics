"""Tests for Data Quality Intelligence.

Tests cover:
  - Quality checks (missing values, duplicates, sentinels, out-of-range, formats, types)
  - Data drift detection (PSI for numeric, frequency for categorical, time drift)
  - Schema change monitoring (added/removed/renamed columns, type changes)
  - Quality engine (composite scoring, recommendations, summary)
  - Pipeline integration
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from data_quality import (
    DriftDetector,
    DriftResult,
    QualityCheckEngine,
    QualityEngine,
    QualityFinding,
    SchemaMonitor,
    Severity,
)
from data_quality.quality_engine import QualityIntelligenceResult, QualityScore

# â”€â”€ Fixtures â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€


@pytest.fixture
def clean_df():
    return pd.DataFrame(
        {
            "id": range(1, 101),
            "name": [f"Person_{i}" for i in range(1, 101)],
            "age": [25 + i % 40 for i in range(100)],
            "email": [f"person{i}@example.com" for i in range(1, 101)],
            "revenue": [1000 + i * 10 for i in range(100)],
            "category": ["A", "B", "C", "D"] * 25,
            "date": pd.date_range("2024-01-01", periods=100, freq="D"),
        }
    )


@pytest.fixture
def dirty_df():
    """DataFrame with various quality issues."""
    return pd.DataFrame(
        {
            "id": [1, 2, 3, 3, 5, 6, 7, 8, 9, 10],  # duplicate id=3
            "name": ["Alice", "Bob", "", "Diana", "Eve", None, "Grace", "Heidi", "Ivan", "Judy"],
            "age": [
                25,
                30,
                999,
                45,
                -1,
                35,
                40,
                150,
                28,
                50,
            ],  # 999 and -1 are sentinels, 150 out of range
            "email": [
                "alice@test.com",
                "bob@test.com",
                "invalid",
                "diana@test.com",
                "eve@test.com",
                "frank@test.com",
                "grace@test.com",
                "heidi@test.com",
                "ivan@test.com",
                "judy@test.com",
            ],
            "revenue": [
                1000,
                2000,
                3000,
                3000,
                5000,
                6000,
                7000,
                8000,
                9000,
                10000,
            ],  # duplicate revenue=3000
            "category": ["A", "B", "A", "B", "a", "A", "B", "A", "B", "A"],  # mixed case
            "empty_col": [None] * 10,
            "constant_col": ["X"] * 10,
        }
    )


@pytest.fixture
def drift_old_df():
    np.random.seed(42)
    return pd.DataFrame(
        {
            "numeric_col": np.random.normal(100, 15, 200),
            "category_col": np.random.choice(["A", "B", "C"], 200, p=[0.5, 0.3, 0.2]),
        }
    )


@pytest.fixture
def drift_new_df():
    np.random.seed(99)
    return pd.DataFrame(
        {
            "numeric_col": np.random.normal(130, 20, 200),  # shifted mean
            "category_col": np.random.choice(
                ["A", "B", "C", "D"], 200, p=[0.3, 0.3, 0.2, 0.2]
            ),  # new category D
        }
    )


# â”€â”€ Quality Check Engine Tests â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€


class TestQualityCheckEngine:
    def test_run_returns_findings(self, dirty_df):
        findings = QualityCheckEngine.run(dirty_df)
        assert len(findings) > 0
        assert all(isinstance(f, QualityFinding) for f in findings)

    def test_detects_missing_values(self, dirty_df):
        findings = QualityCheckEngine.run(dirty_df)
        missing = [f for f in findings if f.check_name == "missing_values"]
        assert len(missing) > 0
        assert any(f.column == "name" for f in missing)

    def test_detects_blank_fields(self, dirty_df):
        findings = QualityCheckEngine.run(dirty_df)
        blanks = [f for f in findings if f.check_name == "blank_fields"]
        assert len(blanks) > 0

    def test_detects_duplicate_rows(self):
        df = pd.DataFrame({"a": [1, 2, 2, 3], "b": [10, 20, 20, 30]})
        findings = QualityCheckEngine.run(df)
        dups = [f for f in findings if f.check_name == "duplicate_rows"]
        assert len(dups) > 0
        assert dups[0].affected_rows == 1

    def test_detects_duplicate_ids(self, dirty_df):
        findings = QualityCheckEngine.run(dirty_df)
        dup_ids = [f for f in findings if f.check_name == "duplicate_ids"]
        assert len(dup_ids) > 0

    def test_detects_empty_columns(self, dirty_df):
        findings = QualityCheckEngine.run(dirty_df)
        empties = [f for f in findings if f.check_name == "empty_column"]
        assert len(empties) > 0
        assert any(f.column == "empty_col" for f in empties)

    def test_detects_sentinel_999(self, dirty_df):
        findings = QualityCheckEngine.run(dirty_df)
        sentinels = [f for f in findings if f.check_name == "sentinel_value" and f.column == "age"]
        assert len(sentinels) > 0
        assert any(999 in f.sample_values for f in sentinels)

    def test_detects_sentinel_negative_one(self, dirty_df):
        findings = QualityCheckEngine.run(dirty_df)
        sentinels = [f for f in findings if f.check_name == "sentinel_value" and f.column == "age"]
        assert any(-1 in f.sample_values for f in sentinels)

    def test_detects_out_of_range_age(self, dirty_df):
        findings = QualityCheckEngine.run(dirty_df)
        oob = [f for f in findings if f.check_name == "out_of_range" and f.column == "age"]
        assert len(oob) > 0
        assert 150 in oob[0].sample_values

    def test_detects_invalid_emails(self, dirty_df):
        findings = QualityCheckEngine.run(dirty_df)
        emails = [f for f in findings if f.check_name == "invalid_emails"]
        assert len(emails) > 0
        assert "invalid" in emails[0].sample_values

    def test_detects_constant_column(self, dirty_df):
        findings = QualityCheckEngine.run(dirty_df)
        constants = [f for f in findings if f.check_name == "constant_column"]
        assert len(constants) > 0
        assert any(f.column == "constant_col" for f in constants)

    def test_detects_mixed_case(self, dirty_df):
        findings = QualityCheckEngine.run(dirty_df)
        mixed = [f for f in findings if f.check_name == "mixed_case"]
        assert len(mixed) > 0
        assert any(f.column == "category" for f in mixed)

    def test_detects_negative_values(self, dirty_df):
        findings = QualityCheckEngine.run(dirty_df)
        negatives = [f for f in findings if f.check_name == "negative_values"]
        assert len(negatives) > 0

    def test_findings_sorted_by_severity(self, dirty_df):
        findings = QualityCheckEngine.run(dirty_df)
        severity_order = {"critical": 0, "error": 1, "warning": 2, "info": 3}
        for i in range(len(findings) - 1):
            s1 = severity_order.get(findings[i].severity.value, 99)
            s2 = severity_order.get(findings[i + 1].severity.value, 99)
            assert s1 <= s2

    def test_finding_to_dict(self, dirty_df):
        findings = QualityCheckEngine.run(dirty_df)
        d = findings[0].to_dict()
        assert "check_name" in d
        assert "severity" in d
        assert "message" in d

    def test_clean_df_has_few_findings(self, clean_df):
        findings = QualityCheckEngine.run(clean_df)
        # Clean data should have very few findings
        errors = [f for f in findings if f.severity in (Severity.ERROR, Severity.CRITICAL)]
        assert len(errors) == 0


# â”€â”€ Drift Detector Tests â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€


class TestDriftDetector:
    def test_detect_numeric_drift(self, drift_old_df, drift_new_df):
        result = DriftDetector.detect(drift_old_df, drift_new_df)
        assert isinstance(result, DriftResult)
        assert result.drift_detected

    def test_numeric_psi_computed(self, drift_old_df, drift_new_df):
        result = DriftDetector.detect(drift_old_df, drift_new_df)
        numeric_drifts = [c for c in result.drifted_columns if c.drift_type == "numeric"]
        assert len(numeric_drifts) > 0
        assert numeric_drifts[0].psi is not None
        assert numeric_drifts[0].psi > 0.10  # Should detect drift

    def test_categorical_drift_new_category(self, drift_old_df, drift_new_df):
        result = DriftDetector.detect(drift_old_df, drift_new_df)
        cat_drifts = [c for c in result.drifted_columns if c.drift_type == "categorical"]
        assert len(cat_drifts) > 0
        assert "D" in cat_drifts[0].new_categories

    def test_no_drift_on_same_data(self, drift_old_df):
        result = DriftDetector.detect(drift_old_df, drift_old_df.copy())
        assert not result.drift_detected

    def test_time_drift_detection(self):
        df = pd.DataFrame(
            {
                "date": pd.date_range("2024-01-01", periods=100, freq="D"),
                "value": [50 + i for i in range(50)] + [200 + i * 2 for i in range(50)],
            }
        )
        result = DriftDetector.detect_time_drift(df, "date")
        assert isinstance(result, DriftResult)

    def test_time_drift_no_date_column(self):
        df = pd.DataFrame({"value": range(100)})
        result = DriftDetector.detect_time_drift(df, "date")
        assert not result.drift_detected

    def test_drift_summary_generated(self, drift_old_df, drift_new_df):
        result = DriftDetector.detect(drift_old_df, drift_new_df)
        assert result.summary != ""

    def test_drift_to_dict(self, drift_old_df, drift_new_df):
        result = DriftDetector.detect(drift_old_df, drift_new_df)
        d = result.to_dict()
        assert "drift_detected" in d
        assert "drifted_columns" in d

    def test_drift_severity_levels(self, drift_old_df, drift_new_df):
        result = DriftDetector.detect(drift_old_df, drift_new_df)
        severities = {c.drift_severity for c in result.drifted_columns}
        assert "significant" in severities or "moderate" in severities


# â”€â”€ Schema Monitor Tests â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€


class TestSchemaMonitor:
    def test_detect_added_column(self):
        old = pd.DataFrame({"a": [1, 2], "b": [3, 4]})
        new = pd.DataFrame({"a": [1, 2], "b": [3, 4], "c": [5, 6]})
        result = SchemaMonitor.compare(old, new)
        assert result.changes_detected
        added = [c for c in result.changes if c.change_type == "added"]
        assert len(added) == 1
        assert added[0].column == "c"

    def test_detect_removed_column(self):
        old = pd.DataFrame({"a": [1, 2], "b": [3, 4], "c": [5, 6]})
        new = pd.DataFrame({"a": [1, 2], "b": [3, 4]})
        result = SchemaMonitor.compare(old, new)
        assert result.changes_detected
        removed = [c for c in result.changes if c.change_type == "removed"]
        assert len(removed) == 1
        assert removed[0].column == "c"

    def test_detect_type_change(self):
        old = pd.DataFrame({"a": [1, 2, 3], "b": [3, 4, 5]})
        new = pd.DataFrame({"a": ["1", "2", "3"], "b": [3, 4, 5]})
        result = SchemaMonitor.compare(old, new)
        type_changes = [c for c in result.changes if c.change_type == "type_changed"]
        assert len(type_changes) > 0
        assert type_changes[0].column == "a"

    def test_no_changes(self):
        old = pd.DataFrame({"a": [1, 2], "b": [3, 4]})
        new = pd.DataFrame({"a": [5, 6], "b": [7, 8]})
        result = SchemaMonitor.compare(old, new)
        assert not result.changes_detected

    def test_detect_renames(self):
        old = pd.DataFrame({"customer_id": range(100), "name": [f"P{i}" for i in range(100)]})
        new = pd.DataFrame({"client_id": range(100), "name": [f"P{i}" for i in range(100)]})
        renames = SchemaMonitor.detect_renames(old, new)
        assert len(renames) > 0
        assert "customer_id" in renames[0].old_value
        assert "client_id" in renames[0].new_value

    def test_schema_to_dict(self):
        old = pd.DataFrame({"a": [1, 2]})
        new = pd.DataFrame({"a": [1, 2], "b": [3, 4]})
        result = SchemaMonitor.compare(old, new)
        d = result.to_dict()
        assert "changes_detected" in d
        assert "changes" in d

    def test_schema_summary(self):
        old = pd.DataFrame({"a": [1, 2]})
        new = pd.DataFrame({"a": [1, 2], "b": [3, 4]})
        result = SchemaMonitor.compare(old, new)
        assert result.summary != ""
        assert "added" in result.summary.lower()

    def test_changes_sorted_by_severity(self):
        old = pd.DataFrame({"a": [1, 2], "b": [3, 4], "c": [5, 6]})
        new = pd.DataFrame({"a": ["1", "2"], "d": [7, 8]})  # type change + removed + added
        result = SchemaMonitor.compare(old, new)
        severity_order = {"error": 0, "warning": 1, "info": 2}
        for i in range(len(result.changes) - 1):
            s1 = severity_order.get(result.changes[i].severity, 99)
            s2 = severity_order.get(result.changes[i + 1].severity, 99)
            assert s1 <= s2


# â”€â”€ Quality Engine Tests â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€


class TestQualityEngine:
    def test_run_returns_result(self, dirty_df):
        engine = QualityEngine()
        result = engine.run(dirty_df)
        assert isinstance(result, QualityIntelligenceResult)

    def test_result_has_findings(self, dirty_df):
        engine = QualityEngine()
        result = engine.run(dirty_df)
        assert len(result.findings) > 0

    def test_result_has_score(self, dirty_df):
        engine = QualityEngine()
        result = engine.run(dirty_df)
        assert result.score is not None
        assert isinstance(result.score, QualityScore)

    def test_score_in_range(self, dirty_df):
        engine = QualityEngine()
        result = engine.run(dirty_df)
        assert 0 <= result.score.overall <= 100

    def test_score_traffic_light(self, dirty_df):
        engine = QualityEngine()
        result = engine.run(dirty_df)
        assert result.score.traffic_light in ("green", "yellow", "red")

    def test_score_grade(self, dirty_df):
        engine = QualityEngine()
        result = engine.run(dirty_df)
        assert result.score.grade in ("A", "B", "C", "D", "F")

    def test_clean_data_scores_high(self, clean_df):
        engine = QualityEngine()
        result = engine.run(clean_df)
        assert result.score.overall >= 80

    def test_dirty_data_scores_lower(self, dirty_df):
        engine = QualityEngine()
        result = engine.run(dirty_df)
        assert result.score.overall < 90

    def test_has_recommendations(self, dirty_df):
        engine = QualityEngine()
        result = engine.run(dirty_df)
        assert len(result.recommendations) > 0

    def test_has_summary(self, dirty_df):
        engine = QualityEngine()
        result = engine.run(dirty_df)
        assert result.summary != ""
        assert "Score" in result.summary

    def test_error_warning_counts(self, dirty_df):
        engine = QualityEngine()
        result = engine.run(dirty_df)
        assert result.error_count > 0
        assert result.warning_count > 0

    def test_to_dict(self, dirty_df):
        engine = QualityEngine()
        result = engine.run(dirty_df)
        d = result.to_dict()
        assert "findings" in d
        assert "score" in d
        assert "summary" in d

    def test_with_drift_detection(self, drift_old_df, drift_new_df):
        engine = QualityEngine(reference_df=drift_old_df)
        result = engine.run(drift_new_df)
        assert result.drift_result is not None

    def test_with_schema_monitoring(self):
        baseline = pd.DataFrame({"a": [1, 2], "b": [3, 4]})
        current = pd.DataFrame({"a": [1, 2], "c": [5, 6]})
        engine = QualityEngine(baseline_schema=baseline)
        result = engine.run(current)
        assert result.schema_result is not None
        assert result.schema_result.changes_detected

    def test_time_drift_in_engine(self):
        df = pd.DataFrame(
            {
                "date": pd.date_range("2024-01-01", periods=100, freq="D"),
                "value": list(range(50, 150)),
            }
        )
        engine = QualityEngine()
        result = engine.run(df)
        assert result.drift_result is not None


# â”€â”€ Pipeline Integration Tests â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€


class TestPipelineIntegration:
    def test_quality_in_mapping_result(self, dirty_df):
        from semantic.mapping_engine import SemanticMappingEngine

        result = SemanticMappingEngine.analyze(dirty_df, "dirty.csv")
        assert result.quality_intelligence is not None

    def test_quality_in_to_dict(self, dirty_df):
        from semantic.mapping_engine import SemanticMappingEngine

        result = SemanticMappingEngine.analyze(dirty_df, "dirty.csv")
        d = result.to_dict()
        assert "quality_intelligence" in d
        assert d["quality_intelligence"] is not None

    def test_quality_score_in_pipeline(self, dirty_df):
        from semantic.mapping_engine import SemanticMappingEngine

        result = SemanticMappingEngine.analyze(dirty_df, "dirty.csv")
        qi = result.quality_intelligence
        assert qi.score is not None
        assert qi.score.overall > 0

    def test_quality_findings_in_pipeline(self, dirty_df):
        from semantic.mapping_engine import SemanticMappingEngine

        result = SemanticMappingEngine.analyze(dirty_df, "dirty.csv")
        qi = result.quality_intelligence
        assert len(qi.findings) > 0

    def test_clean_data_pipeline_quality(self, clean_df):
        from semantic.mapping_engine import SemanticMappingEngine

        result = SemanticMappingEngine.analyze(clean_df, "clean.csv")
        qi = result.quality_intelligence
        assert qi.score.overall >= 80
