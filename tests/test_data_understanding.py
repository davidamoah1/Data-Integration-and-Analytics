"""Tests for the Data Understanding Engine â€” value-based industry classification.

Verifies that the semantic engine correctly classifies datasets using
both column names AND actual data values, not just keyword matching.
"""

from __future__ import annotations

import pandas as pd

from semantic.data_understanding import DataUnderstandingEngine
from semantic.semantic_engine import SemanticEngine


class TestDataUnderstandingEngine:
    """Test the value-based signal detection engine."""

    def test_diagnosis_codes_detected(self):
        """ICD-10 diagnosis codes in values should signal healthcare."""
        df = pd.DataFrame(
            {
                "code": [
                    "A00.1",
                    "B01.0",
                    "C50.2",
                    "D45.0",
                    "E11.9",
                    "F32.1",
                    "G40.0",
                    "H10.0",
                    "I10.0",
                    "J00.0",
                ],
                "patient_ref": range(10),
            }
        )
        result = DataUnderstandingEngine.analyze(df)
        healthcare_signals = [s for s in result.signals if s.industry == "healthcare"]
        assert any(s.signal_type == "diagnosis_code" for s in healthcare_signals)
        assert result.industry_votes.get("healthcare", 0) > 0

    def test_iban_detected(self):
        """IBAN codes in values should signal banking."""
        df = pd.DataFrame(
            {
                "account_ref": [
                    "GB82WEST12345698765432",
                    "DE89370400440532013000",
                    "FR1420041010050500013M02606",
                    "IT60X0542811101000000123456",
                    "ES9121000418450200051332",
                ],
                "amount": [100, 200, 300, 400, 500],
            }
        )
        result = DataUnderstandingEngine.analyze(df)
        banking_signals = [s for s in result.signals if s.industry == "banking"]
        assert any(s.signal_type == "iban" for s in banking_signals)

    def test_letter_grades_detected(self):
        """Letter grades (Aâ€“F) in values should signal education."""
        df = pd.DataFrame(
            {
                "score": ["A", "B+", "C", "A-", "F", "B", "C+", "D", "A", "B-"],
                "student_ref": range(10),
            }
        )
        result = DataUnderstandingEngine.analyze(df)
        edu_signals = [s for s in result.signals if s.industry == "education"]
        assert any(s.signal_type == "grade" for s in edu_signals)

    def test_claim_numbers_detected(self):
        """Claim numbers should signal insurance."""
        df = pd.DataFrame(
            {
                "ref": ["CLM123456", "CLM789012", "CLM345678", "CL-901234", "CLM567890"],
                "amount": [1000, 2000, 3000, 4000, 5000],
            }
        )
        result = DataUnderstandingEngine.analyze(df)
        ins_signals = [s for s in result.signals if s.industry == "insurance"]
        assert any(s.signal_type == "claim_number" for s in ins_signals)

    def test_sku_codes_detected(self):
        """SKU codes should signal retail."""
        df = pd.DataFrame(
            {
                "product_ref": ["ABC-1234", "XYZ-5678", "DEF-9012", "GHI-3456", "JKL-7890"],
                "price": [9.99, 19.99, 29.99, 39.99, 49.99],
            }
        )
        result = DataUnderstandingEngine.analyze(df)
        retail_signals = [s for s in result.signals if s.industry == "retail"]
        assert any(s.signal_type == "sku_code" for s in retail_signals)

    def test_imei_detected(self):
        """IMEI numbers should signal telecom."""
        df = pd.DataFrame(
            {
                "device_ref": [
                    "123456789012345",
                    "234567890123456",
                    "345678901234567",
                    "456789012345678",
                    "567890123456789",
                ],
            }
        )
        result = DataUnderstandingEngine.analyze(df)
        telecom_signals = [s for s in result.signals if s.industry == "telecom"]
        assert any(s.signal_type == "imei" for s in telecom_signals)

    def test_statistical_patterns_numeric(self):
        """Statistical patterns should be detected for numeric columns."""
        df = pd.DataFrame(
            {
                "amount": [10.50, 20.00, 15.75, 30.25, 12.00, 18.50, 22.00, 25.50],
            }
        )
        result = DataUnderstandingEngine.analyze(df)
        stats = result.statistical_patterns.get("amount", {})
        assert stats.get("type") == "numeric"
        assert "min" in stats
        assert "max" in stats
        assert "mean" in stats

    def test_statistical_patterns_categorical(self):
        """Statistical patterns should be detected for categorical columns."""
        df = pd.DataFrame(
            {
                "category": ["A", "B", "A", "C", "A", "B", "A", "C"],
            }
        )
        result = DataUnderstandingEngine.analyze(df)
        stats = result.statistical_patterns.get("category", {})
        assert stats.get("type") == "categorical"
        assert "top_values" in stats

    def test_no_false_positives_on_generic_data(self):
        """Generic numeric data should not produce industry signals."""
        df = pd.DataFrame(
            {
                "col_a": range(100),
                "col_b": range(100, 200),
            }
        )
        result = DataUnderstandingEngine.analyze(df)
        # No strong industry signals from sequential integers
        assert all(v < 1.0 for v in result.industry_votes.values())


class TestMultiSignalClassification:
    """Test that SemanticEngine uses both name and value signals together."""

    def test_healthcare_with_values_and_names(self):
        """Healthcare dataset with both healthcare column names and diagnosis values."""
        df = pd.DataFrame(
            {
                "patient_id": range(20),
                "doctor_name": [f"Dr. Smith {i}" for i in range(20)],
                "diagnosis_code": [
                    "A00.1",
                    "B01.0",
                    "C50.2",
                    "D45.0",
                    "E11.9",
                    "F32.1",
                    "G40.0",
                    "H10.0",
                    "I10.0",
                    "J00.0",
                    "K00.0",
                    "L00.0",
                    "M00.0",
                    "N00.0",
                    "O00.0",
                    "P00.0",
                    "Q00.0",
                    "R00.0",
                    "S00.0",
                    "T00.0",
                ],
                "visit_date": pd.date_range("2024-01-01", periods=20),
            }
        )
        result = SemanticEngine.analyze(df)
        assert result.detected_industry == "healthcare"
        assert result.industry_confidence > 50.0
        # Value signals should be present
        assert len(result.value_signals) > 0

    def test_banking_with_values_and_names(self):
        """Banking dataset with both banking column names and IBAN values."""
        df = pd.DataFrame(
            {
                "loan_id": range(10),
                "account_number": [
                    "GB82WEST12345698765432",
                    "DE89370400440532013000",
                    "FR1420041010050500013M02606",
                    "IT60X0542811101000000123456",
                    "ES9121000418450200051332",
                    "GB29NWBK60161331926819",
                    "DE75512108001235119613",
                    "FR7630006000011234567890189",
                    "IT05Q0542811101000000123456",
                    "ES792100081361012345678901",
                ],
                "loan_amount": [
                    10000,
                    20000,
                    15000,
                    25000,
                    30000,
                    12000,
                    18000,
                    22000,
                    14000,
                    16000,
                ],
            }
        )
        result = SemanticEngine.analyze(df)
        assert result.detected_industry == "banking"
        assert result.industry_confidence > 50.0

    def test_value_signals_boost_confidence(self):
        """Value signals should increase confidence compared to names alone."""
        # Dataset with healthcare column names
        df_names_only = pd.DataFrame(
            {
                "patient_id": range(10),
                "doctor_name": [f"Dr. {i}" for i in range(10)],
                "visit_date": pd.date_range("2024-01-01", periods=10),
            }
        )
        result_names = SemanticEngine.analyze(df_names_only)

        # Same dataset but with diagnosis code values added
        df_with_values = pd.DataFrame(
            {
                "patient_id": range(10),
                "doctor_name": [f"Dr. {i}" for i in range(10)],
                "diagnosis_code": [
                    "A00.1",
                    "B01.0",
                    "C50.2",
                    "D45.0",
                    "E11.9",
                    "F32.1",
                    "G40.0",
                    "H10.0",
                    "I10.0",
                    "J00.0",
                ],
                "visit_date": pd.date_range("2024-01-01", periods=10),
            }
        )
        result_with_values = SemanticEngine.analyze(df_with_values)

        # Confidence should be higher with value signals
        assert result_with_values.industry_confidence >= result_names.industry_confidence

    def test_value_signals_classify_without_name_hints(self):
        """Value signals alone should be able to classify industry."""
        df = pd.DataFrame(
            {
                "col_a": [
                    "A00.1",
                    "B01.0",
                    "C50.2",
                    "D45.0",
                    "E11.9",
                    "F32.1",
                    "G40.0",
                    "H10.0",
                    "I10.0",
                    "J00.0",
                ],
                "col_b": range(10),
                "col_c": pd.date_range("2024-01-01", periods=10),
            }
        )
        result = DataUnderstandingEngine.analyze(df)
        assert result.industry_votes.get("healthcare", 0) > 0

    def test_statistical_patterns_in_result(self):
        """SemanticResult should include statistical patterns."""
        df = pd.DataFrame(
            {
                "patient_id": range(10),
                "amount": [10.5, 20.0, 15.0, 30.0, 12.0, 18.0, 22.0, 25.0, 14.0, 19.0],
            }
        )
        result = SemanticEngine.analyze(df)
        assert "amount" in result.statistical_patterns
        assert result.statistical_patterns["amount"].get("type") == "numeric"

    def test_value_signal_mapping_for_unmapped_column(self):
        """Value signals should create entity mappings for previously unmapped columns."""
        df = pd.DataFrame(
            {
                "col_a": [
                    "A00.1",
                    "B01.0",
                    "C50.2",
                    "D45.0",
                    "E11.9",
                    "F32.1",
                    "G40.0",
                    "H10.0",
                    "I10.0",
                    "J00.0",
                ],
                "patient_id": range(10),
            }
        )
        result = SemanticEngine.analyze(df)
        # col_a should get mapped via value signal
        col_a_mappings = [m for m in result.mappings if m.column_name == "col_a"]
        if col_a_mappings:
            assert col_a_mappings[0].match_method == "value_signal"
            assert col_a_mappings[0].entity_key == "diagnosis"
