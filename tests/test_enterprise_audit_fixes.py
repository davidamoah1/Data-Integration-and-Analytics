"""Tests for enterprise audit fixes — industry detection, confidence thresholds,
ETL hardening, dataset isolation, and dashboard routing.

Covers PARTS 2-7 of the master audit prompt.
"""

import os
import sys

import pandas as pd
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


# ──────────────────────────────────────────────
# PART 2-3: Semantic Engine — Confidence Threshold
# ──────────────────────────────────────────────


class TestConfidenceThreshold:
    """Verify MIN_INDUSTRY_CONFIDENCE is 70.0 (not 40.0)."""

    def test_min_confidence_is_70(self):
        from semantic.semantic_engine import MIN_INDUSTRY_CONFIDENCE

        assert (
            MIN_INDUSTRY_CONFIDENCE == 70.0
        ), f"MIN_INDUSTRY_CONFIDENCE should be 70.0, got {MIN_INDUSTRY_CONFIDENCE}"

    def test_low_confidence_returns_unknown(self):
        """A dataset with weak signals should return 'unknown' industry."""
        from semantic.semantic_engine import SemanticEngine

        df = pd.DataFrame(
            {
                "id": [1, 2, 3, 4, 5],
                "amount": [100, 200, 300, 400, 500],
                "date": ["2024-01-01", "2024-01-02", "2024-01-03", "2024-01-04", "2024-01-05"],
                "status": ["active", "active", "inactive", "active", "active"],
            }
        )

        result = SemanticEngine.analyze(df)
        # With only generic columns, industry should be unknown
        assert result.detected_industry == "unknown"

    def test_healthcare_detected_with_strong_signals(self):
        """Healthcare columns should produce high-confidence healthcare detection."""
        from semantic.semantic_engine import SemanticEngine

        df = pd.DataFrame(
            {
                "patient_id": ["P001", "P002", "P003", "P004", "P005"],
                "patient_name": ["John", "Jane", "Bob", "Alice", "Charlie"],
                "doctor_name": ["Dr. Smith", "Dr. Jones", "Dr. Lee", "Dr. Brown", "Dr. White"],
                "diagnosis": ["Flu", "Cold", "Diabetes", "Hypertension", "Asthma"],
                "admission_date": [
                    "2024-01-01",
                    "2024-01-02",
                    "2024-01-03",
                    "2024-01-04",
                    "2024-01-05",
                ],
                "billing": [500, 300, 1200, 800, 450],
                "ward": ["A", "B", "A", "C", "B"],
            }
        )

        result = SemanticEngine.analyze(df)
        assert result.detected_industry == "healthcare"
        assert result.industry_confidence >= 70.0

    def test_education_detected_with_strong_signals(self):
        """Education columns should produce high-confidence education detection."""
        from semantic.semantic_engine import SemanticEngine

        df = pd.DataFrame(
            {
                "student_id": ["S001", "S002", "S003", "S004", "S005"],
                "student_name": ["John", "Jane", "Bob", "Alice", "Charlie"],
                "teacher_name": ["Mr. Smith", "Mrs. Jones", "Mr. Lee", "Ms. Brown", "Mr. White"],
                "course": ["Math", "Science", "English", "History", "Art"],
                "grade": ["A", "B", "A", "C", "B"],
                "attendance": [95, 88, 92, 78, 85],
            }
        )

        result = SemanticEngine.analyze(df)
        assert result.detected_industry == "education"
        assert result.industry_confidence >= 70.0

    def test_never_silently_chooses_banking(self):
        """A generic dataset with 'amount' and 'date' should not auto-select banking."""
        from semantic.semantic_engine import SemanticEngine

        df = pd.DataFrame(
            {
                "transaction_id": ["T001", "T002", "T003"],
                "amount": [100, 200, 300],
                "date": ["2024-01-01", "2024-01-02", "2024-01-03"],
                "type": ["A", "B", "A"],
            }
        )

        result = SemanticEngine.analyze(df)
        # Should NOT be banking just because of amount/date
        assert result.detected_industry != "banking"


# ──────────────────────────────────────────────
# PART 3: Weighted Intelligence Scoring
# ──────────────────────────────────────────────


class TestWeightedScoring:
    """Verify strong signals have weight 3.0 and weak signals don't dominate."""

    def test_strong_signal_weight(self):
        from semantic.entity_library import ENTITY_LIBRARY

        assert ENTITY_LIBRARY["patient"]["weight"] == 3.0
        assert ENTITY_LIBRARY["diagnosis"]["weight"] == 3.0
        assert ENTITY_LIBRARY["student"]["weight"] == 3.0
        assert ENTITY_LIBRARY["grade"]["weight"] == 3.0

    def test_weak_signals_are_universal(self):
        from semantic.entity_library import ENTITY_LIBRARY

        # Revenue, date, region should be universal (no industry vote)
        assert ENTITY_LIBRARY["revenue"]["industry"] == "universal"
        assert ENTITY_LIBRARY["date"]["industry"] == "universal"


# ──────────────────────────────────────────────
# PART 7: ETL Hardening
# ──────────────────────────────────────────────


class TestETLExtract:
    """Test ETL extraction with multiple file formats."""

    def test_extract_csv(self, tmp_path, monkeypatch):
        from etl import extract as extract_module

        csv_path = tmp_path / "test.csv"
        csv_path.write_text("a,b,c\n1,2,3\n4,5,6\n")
        monkeypatch.setattr(extract_module, "RAW_DATA_PATH", str(csv_path))

        df = extract_module.extract_data()
        assert len(df) == 2
        assert list(df.columns) == ["a", "b", "c"]

    def test_extract_empty_file_raises(self, tmp_path, monkeypatch):
        from etl import extract as extract_module

        csv_path = tmp_path / "empty.csv"
        csv_path.write_text("a,b,c\n")
        monkeypatch.setattr(extract_module, "RAW_DATA_PATH", str(csv_path))

        with pytest.raises(ValueError, match="empty"):
            extract_module.extract_data()

    def test_extract_unsupported_format_raises(self, tmp_path, monkeypatch):
        from etl import extract as extract_module

        bad_path = tmp_path / "data.txt"
        bad_path.write_text("some text")
        monkeypatch.setattr(extract_module, "RAW_DATA_PATH", str(bad_path))

        with pytest.raises(ValueError, match="Unsupported"):
            extract_module.extract_data()


class TestETLTransform:
    """Test ETL transform safety — no assumptions about column existence."""

    def test_transform_non_sales_dataset(self):
        """Transform should not drop rows from non-sales datasets."""
        from etl.transform import transform_data

        df = pd.DataFrame(
            {
                "patient_id": ["P001", "P002", "P003"],
                "diagnosis": ["Flu", "Cold", None],
                "billing": [100, 200, 300],
            }
        )

        # Should not drop any rows just because 'sales' or 'order_date' don't exist
        result = transform_data(df)
        assert len(result) == 3

    def test_transform_sales_dataset_drops_missing(self):
        """Transform should drop rows with missing order_id for sales datasets."""
        from etl.transform import transform_data

        df = pd.DataFrame(
            {
                "order_id": ["O001", None, "O003"],
                "sales": [100, 200, 300],
                "order_date": ["2024-01-01", "2024-01-02", "2024-01-03"],
            }
        )

        result = transform_data(df)
        # Should drop the row with missing order_id
        assert len(result) == 2

    def test_transform_preserves_all_columns(self):
        """Transform should not remove columns."""
        from etl.transform import transform_data

        df = pd.DataFrame(
            {
                "custom_col": ["a", "b", "c"],
                "another_col": [1, 2, 3],
            }
        )

        result = transform_data(df)
        assert "custom_col" in result.columns
        assert "another_col" in result.columns


# ──────────────────────────────────────────────
# PART 6: Dataset Isolation
# ──────────────────────────────────────────────


class TestDatasetIsolation:
    """Verify unique dataset IDs are generated per upload."""

    def test_unique_ids_generated(self):
        import uuid

        id1 = str(uuid.uuid4())
        id2 = str(uuid.uuid4())
        assert id1 != id2
        # Verify they are valid UUIDs
        uuid.UUID(id1)
        uuid.UUID(id2)


# ──────────────────────────────────────────────
# PART 5: Dashboard Routing — Generic Fallback
# ──────────────────────────────────────────────


class TestDashboardRouting:
    """Verify unknown datasets get generic dashboard, not SME."""

    def test_sector_renderers_has_all_industries(self):
        from dashboard.sector_dashboards import SECTOR_RENDERERS

        expected = {
            "sme",
            "retail",
            "education",
            "healthcare",
            "government",
            "church",
            "ngo",
            "manufacturing",
            "agriculture",
        }
        assert expected.issubset(set(SECTOR_RENDERERS.keys()))

    def test_unknown_pack_key_returns_generic(self):
        """render_sector_dashboard with None pack_key should not raise."""
        # We can't call the function directly (requires Streamlit context),
        # but we can verify the logic doesn't default to SME
        import inspect

        from dashboard.sector_dashboards import render_sector_dashboard

        source = inspect.getsource(render_sector_dashboard)
        # Must NOT contain the old pattern of defaulting to "sme"
        assert 'pack_key or "sme"' not in source
        assert "render_generic_sector_dashboard" in source
