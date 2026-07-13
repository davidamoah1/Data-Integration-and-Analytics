"""Tests for data quality engine."""

import pytest
import pandas as pd

from etl.quality import DataQualityEngine, QualityCheck


@pytest.fixture
def dirty_df():
    return pd.DataFrame({
        "name": ["Alice", "Bob", "Alice", None, "Eve"],
        "email": ["a@test.com", "invalid", "a@test.com", "d@test.com", None],
        "phone": ["+1234567890", "abc", "+1234567890", "+9876543210", None],
        "age": [30, -5, 30, 40, 25],
        "empty_col": [None, None, None, None, None],
    })


class TestDataQualityEngine:
    def test_run_checks(self, dirty_df):
        engine = DataQualityEngine()
        result = engine.run_checks(dirty_df, source_name="test")
        assert "overall_score" in result
        assert "checks_passed" in result
        assert "checks_failed" in result
        assert "recommendations" in result

    def test_missing_values_detected(self, dirty_df):
        engine = DataQualityEngine()
        result = engine.run_checks(dirty_df)
        missing_check = [c for c in result["checks"] if c["check"] == "missing_values"][0]
        assert not missing_check["passed"]

    def test_duplicates_detected(self, dirty_df):
        engine = DataQualityEngine()
        result = engine.run_checks(dirty_df)
        dup_check = [c for c in result["checks"] if c["check"] == "duplicate_rows"][0]
        assert not dup_check["passed"]

    def test_empty_columns_detected(self, dirty_df):
        engine = DataQualityEngine()
        result = engine.run_checks(dirty_df)
        empty_check = [c for c in result["checks"] if c["check"] == "empty_columns"][0]
        assert not empty_check["passed"]

    def test_invalid_emails_detected(self, dirty_df):
        engine = DataQualityEngine()
        result = engine.run_checks(dirty_df)
        email_check = [c for c in result["checks"] if c["check"] == "invalid_emails"][0]
        assert not email_check["passed"]

    def test_negative_values_detected(self, dirty_df):
        engine = DataQualityEngine()
        result = engine.run_checks(dirty_df)
        neg_check = [c for c in result["checks"] if c["check"] == "negative_numeric_values"][0]
        assert not neg_check["passed"]

    def test_apply_fix_dedup(self, dirty_df):
        engine = DataQualityEngine()
        fixed = engine.apply_fixes(dirty_df, check_names=["duplicate_rows"])
        assert len(fixed) < len(dirty_df)

    def test_quality_score_range(self, dirty_df):
        engine = DataQualityEngine()
        result = engine.run_checks(dirty_df)
        assert 0 <= result["overall_score"] <= 100

    def test_recommendations_generated(self, dirty_df):
        engine = DataQualityEngine()
        result = engine.run_checks(dirty_df)
        assert len(result["recommendations"]) > 0

    def test_custom_check(self):
        df = pd.DataFrame({"x": [1, 2, 3]})
        engine = DataQualityEngine()
        engine.add_check(QualityCheck(
            "custom", "error",
            lambda df: {"passed": df["x"].sum() > 10, "affected_rows": 0, "message": "sum too low"},
        ))
        result = engine.run_checks(df)
        custom = [c for c in result["checks"] if c["check"] == "custom"][0]
        assert not custom["passed"]

    def test_clean_data_passes(self):
        df = pd.DataFrame({"name": ["Alice", "Bob"], "age": [30, 25]})
        engine = DataQualityEngine()
        result = engine.run_checks(df)
        assert result["overall_score"] > 50
