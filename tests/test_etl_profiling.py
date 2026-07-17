"""Tests for data profiling engine."""

import pandas as pd
import pytest

from etl.profiling import DataProfiler


@pytest.fixture
def sample_df():
    return pd.DataFrame(
        {
            "name": ["Alice", "Bob", "Carol", "Alice", None],
            "age": [30, 25, 35, 30, None],
            "salary": [50000.0, 60000.0, 70000.0, 50000.0, 1000000.0],
            "email": ["a@test.com", "b@test.com", "c@test.com", "a@test.com", None],
        }
    )


class TestDataProfiler:
    def test_profile_basic(self, sample_df):
        profiler = DataProfiler()
        result = profiler.profile(sample_df, source_name="test")
        assert result["row_count"] == 5
        assert result["column_count"] == 4
        assert result["source_name"] == "test"

    def test_profile_columns(self, sample_df):
        profiler = DataProfiler()
        result = profiler.profile(sample_df)
        assert "name" in result["columns"]
        assert "age" in result["columns"]
        assert "salary" in result["columns"]

    def test_numeric_stats(self, sample_df):
        profiler = DataProfiler()
        result = profiler.profile(sample_df)
        age_stats = result["columns"]["age"]
        assert age_stats["dtype"].startswith("float") or age_stats["dtype"].startswith("int")
        assert age_stats["min"] == 25.0
        assert age_stats["max"] == 35.0
        assert age_stats["mean"] is not None

    def test_null_percentage(self, sample_df):
        profiler = DataProfiler()
        result = profiler.profile(sample_df)
        assert result["columns"]["name"]["null_count"] == 1
        assert result["columns"]["name"]["null_percentage"] == 20.0

    def test_duplicate_rows(self, sample_df):
        profiler = DataProfiler()
        result = profiler.profile(sample_df)
        assert result["duplicate_rows"] == 1

    def test_quality_score(self, sample_df):
        profiler = DataProfiler()
        result = profiler.profile(sample_df)
        score = result["quality_score"]
        assert 0 <= score <= 100

    def test_categorical_stats(self, sample_df):
        profiler = DataProfiler()
        result = profiler.profile(sample_df)
        name_stats = result["columns"]["name"]
        assert "top_values" in name_stats
        assert "mode" in name_stats

    def test_empty_dataframe(self):
        profiler = DataProfiler()
        result = profiler.profile(pd.DataFrame())
        assert result["row_count"] == 0
        assert result["quality_score"] == 0

    def test_outliers(self):
        df = pd.DataFrame({"val": [1, 2, 3, 4, 100]})
        profiler = DataProfiler()
        result = profiler.profile(df)
        assert result["columns"]["val"]["outliers"] >= 1
