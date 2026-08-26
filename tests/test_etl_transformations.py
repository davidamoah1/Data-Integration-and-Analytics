"""Tests for transformation engine."""

import pandas as pd
import pytest

from etl.transformations import TransformationEngine


@pytest.fixture
def sample_df():
    return pd.DataFrame(
        {
            "First Name": ["Alice", "Bob", "Carol"],
            "Last Name": ["Smith", "Jones", "Brown"],
            "Age": ["30", "25", "35"],
            "Score": [85.5, 90.0, 78.5],
            "City": ["  Lagos  ", " Accra", "Cairo "],
        }
    )


class TestTransformationEngine:
    def test_rename(self, sample_df):
        engine = TransformationEngine()
        df = engine.apply(sample_df, [{"type": "rename", "mapping": {"First Name": "first_name"}}])
        assert "first_name" in df.columns
        assert "First Name" not in df.columns

    def test_drop(self, sample_df):
        engine = TransformationEngine()
        df = engine.apply(sample_df, [{"type": "drop", "columns": ["Score"]}])
        assert "Score" not in df.columns

    def test_filter_eq(self, sample_df):
        engine = TransformationEngine()
        df = engine.apply(
            sample_df, [{"type": "filter", "column": "Age", "operator": "eq", "value": "30"}]
        )
        assert len(df) == 1

    def test_fill_value(self, sample_df):
        engine = TransformationEngine()
        df = sample_df.copy()
        df.loc[0, "Age"] = None
        df = engine.apply(df, [{"type": "fill", "column": "Age", "method": "value", "value": "0"}])
        assert df["Age"].iloc[0] == "0"

    def test_convert_to_int(self, sample_df):
        engine = TransformationEngine()
        df = engine.apply(sample_df, [{"type": "convert", "column": "Age", "to": "int"}])
        assert df["Age"].dtype == "int64"

    def test_calculate(self, sample_df):
        engine = TransformationEngine()
        df = engine.apply(
            sample_df,
            [{"type": "calculate", "new_column": "double_score", "expression": "Score * 2"}],
        )
        assert "double_score" in df.columns
        assert df["double_score"].iloc[0] == 171.0

    def test_split(self, sample_df):
        engine = TransformationEngine()
        df = engine.apply(
            sample_df,
            [
                {
                    "type": "split",
                    "column": "First Name",
                    "delimiter": " ",
                    "new_columns": ["first", "rest"],
                }
            ],
        )
        assert "first" in df.columns

    def test_merge(self, sample_df):
        engine = TransformationEngine()
        df = engine.apply(
            sample_df,
            [
                {
                    "type": "merge",
                    "columns": ["First Name", "Last Name"],
                    "new_column": "full_name",
                    "separator": " ",
                }
            ],
        )
        assert "full_name" in df.columns
        assert "Alice Smith" in df["full_name"].values

    def test_sort(self, sample_df):
        engine = TransformationEngine()
        df = engine.apply(sample_df, [{"type": "sort", "by": ["Age"], "ascending": True}])
        assert df["Age"].iloc[0] == "25"

    def test_deduplicate(self):
        df = pd.DataFrame({"x": [1, 1, 2], "y": ["a", "a", "b"]})
        engine = TransformationEngine()
        df = engine.apply(df, [{"type": "deduplicate", "subset": ["x"], "keep": "first"}])
        assert len(df) == 2

    def test_standardize_trim(self, sample_df):
        engine = TransformationEngine()
        df = engine.apply(
            sample_df, [{"type": "standardize", "column": "City", "operation": "trim"}]
        )
        assert df["City"].iloc[0] == "Lagos"

    def test_standardize_lower(self, sample_df):
        engine = TransformationEngine()
        df = engine.apply(
            sample_df, [{"type": "standardize", "column": "City", "operation": "lower"}]
        )
        assert df["City"].iloc[0] == "  lagos  "

    def test_chained_transformations(self, sample_df):
        engine = TransformationEngine()
        df = engine.apply(
            sample_df,
            [
                {"type": "rename", "mapping": {"First Name": "first_name"}},
                {"type": "standardize", "column": "City", "operation": "trim"},
                {"type": "convert", "column": "Age", "to": "int"},
            ],
        )
        assert "first_name" in df.columns
        assert df["City"].iloc[0] == "Lagos"
        assert df["Age"].dtype == "int64"

    def test_unknown_transformation(self, sample_df):
        engine = TransformationEngine()
        with pytest.raises(ValueError, match="Unknown transformation type"):
            engine.apply(sample_df, [{"type": "invalid"}])
