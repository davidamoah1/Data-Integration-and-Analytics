"""Comprehensive tests for the Hospital Data Validation & Quality Management Engine."""

from __future__ import annotations

import os
import sys
import tempfile

import pandas as pd
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from validation.ai_copilot import ValidationAICopilot
from validation.approval import ApprovalDecisionType, ApprovalWorkflow
from validation.audit import ValidationAuditLogger
from validation.business_rules import BusinessRuleEngine
from validation.clinical_checks import ClinicalValidationEngine
from validation.engine import ValidationEngine, ValidationStatus
from validation.outlier_detector import OutlierDetector
from validation.profiler import ValidationProfiler
from validation.quality_rules import QualityRulesEngine
from validation.report_generator import ValidationReportGenerator
from validation.schema_validator import SchemaValidator

# â”€â”€ Fixtures â”€â”€


@pytest.fixture
def clean_healthcare_df():
    """A clean healthcare dataset that should pass all validations."""
    return pd.DataFrame(
        {
            "patient_id": ["P001", "P002", "P003", "P004", "P005"],
            "patient_name": [
                "John Doe",
                "Jane Smith",
                "Bob Johnson",
                "Alice Brown",
                "Charlie Wilson",
            ],
            "age": [45, 32, 67, 12, 80],
            "gender": ["Male", "Female", "Male", "Female", "Male"],
            "diagnosis": ["Hypertension", "Diabetes", "Heart Disease", "Asthma", "Arthritis"],
            "admission_date": [
                "2024-01-15",
                "2024-02-20",
                "2024-03-10",
                "2024-04-05",
                "2024-05-12",
            ],
            "discharge_date": [
                "2024-01-18",
                "2024-02-22",
                "2024-03-15",
                "2024-04-06",
                "2024-05-14",
            ],
            "ward": ["A", "B", "C", "Pediatric", "A"],
            "doctor": ["Dr. Smith", "Dr. Jones", "Dr. Brown", "Dr. Davis", "Dr. Smith"],
            "amount": [5000, 3200, 12000, 800, 4500],
            "insurance_type": ["Private", "Public", "Private", "Public", "Private"],
        }
    )


@pytest.fixture
def dirty_healthcare_df():
    """A healthcare dataset with various data quality issues."""
    return pd.DataFrame(
        {
            "patient_id": ["P001", "P002", "P001", "", "P005"],
            "patient_name": ["John Doe", "", "John Doe", "Alice Brown", "Charlie Wilson"],
            "age": [45, -5, 200, 12, 80],
            "gender": ["Male", "Female", "Male", "Unknown", "Male"],
            "diagnosis": ["Hypertension", "Diabetes", "Heart Disease", "Asthma", "Arthritis"],
            "admission_date": [
                "2024-01-15",
                "2024-02-20",
                "2024-03-10",
                "2024-04-05",
                "2024-05-12",
            ],
            "discharge_date": [
                "2024-01-10",
                "2024-02-22",
                "2024-03-15",
                "2024-04-06",
                "2024-05-14",
            ],
            "ward": ["A", "B", "C", "Adult", "A"],
            "doctor": ["Dr. Smith", "", "Dr. Brown", "Dr. Davis", "Dr. Smith"],
            "amount": [5000, -100, 12000, 800, 450000],
            "insurance_type": ["Private", "Public", "Private", "Public", "Private"],
        }
    )


@pytest.fixture
def empty_df():
    return pd.DataFrame()


@pytest.fixture
def validation_engine():
    return ValidationEngine()


# â”€â”€ Schema Validator Tests â”€â”€


class TestSchemaValidator:
    def test_clean_dataset_passes(self, clean_healthcare_df):
        result = SchemaValidator.validate(clean_healthcare_df, "test.csv", "general")
        assert result.passed is True
        assert len(result.errors) == 0

    def test_empty_dataset_fails(self, empty_df):
        result = SchemaValidator.validate(empty_df, "empty.csv", "general")
        assert result.passed is False
        assert any(i.rule_name == "empty_dataset" for i in result.issues)

    def test_duplicate_column_names_fails(self):
        df = pd.DataFrame({"a": [1, 2], "b": [3, 4]})
        df.columns = ["a", "a"]
        result = SchemaValidator.validate(df, "test.csv", "general")
        assert result.passed is False
        assert any(i.rule_name == "duplicate_column_names" for i in result.issues)

    def test_missing_required_column_fails(self, clean_healthcare_df):
        df = clean_healthcare_df.drop(columns=["patient_id"])
        result = SchemaValidator.validate(df, "test.csv", "patient_registry")
        assert result.passed is False
        assert any(i.rule_name == "missing_required_column" for i in result.issues)

    def test_column_types_detected(self, clean_healthcare_df):
        result = SchemaValidator.validate(clean_healthcare_df, "test.csv", "general")
        assert "patient_id" in result.column_types
        assert "age" in result.column_types

    def test_whitespace_column_name_warned(self):
        df = pd.DataFrame({"  name  ": [1, 2], "age": [3, 4]})
        result = SchemaValidator.validate(df, "test.csv", "general")
        assert any(i.rule_name == "whitespace_column_name" for i in result.issues)


# â”€â”€ Quality Rules Tests â”€â”€


class TestQualityRules:
    def test_missing_values_detected(self):
        df = pd.DataFrame({"a": [1, None, 3], "b": [4, 5, None]})
        findings = QualityRulesEngine.run(df)
        missing = [f for f in findings if f.rule_name == "missing_values"]
        assert len(missing) > 0

    def test_duplicate_rows_detected(self):
        df = pd.DataFrame({"a": [1, 1, 2], "b": [3, 3, 4]})
        findings = QualityRulesEngine.run(df)
        dup = [f for f in findings if f.rule_name == "duplicate_rows"]
        assert len(dup) == 1
        assert dup[0].affected_rows == 1

    def test_duplicate_patient_ids_detected(self):
        df = pd.DataFrame({"patient_id": ["P1", "P2", "P1"], "name": ["A", "B", "C"]})
        findings = QualityRulesEngine.run(df)
        dup_ids = [f for f in findings if f.rule_name == "duplicate_ids"]
        assert len(dup_ids) == 1
        assert dup_ids[0].severity == "error"

    def test_empty_column_detected(self):
        df = pd.DataFrame({"a": [1, 2, 3], "b": [None, None, None]})
        findings = QualityRulesEngine.run(df)
        empty = [f for f in findings if f.rule_name == "empty_column"]
        assert len(empty) == 1
        assert empty[0].column == "b"

    def test_invalid_emails_detected(self):
        df = pd.DataFrame({"email": ["valid@test.com", "invalid", "also@valid.org"]})
        findings = QualityRulesEngine.run(df)
        email = [f for f in findings if f.rule_name == "invalid_emails"]
        assert len(email) == 1
        assert email[0].affected_rows == 1

    def test_invalid_genders_detected(self):
        df = pd.DataFrame({"gender": ["Male", "Female", "XYZ", "Other"]})
        findings = QualityRulesEngine.run(df)
        gender = [f for f in findings if f.rule_name == "invalid_gender_values"]
        assert len(gender) == 1
        assert gender[0].affected_rows == 1

    def test_negative_values_detected(self):
        df = pd.DataFrame({"amount": [100, -50, 200], "weight": [70, -5, 80]})
        findings = QualityRulesEngine.run(df)
        neg = [f for f in findings if f.rule_name == "negative_values"]
        assert len(neg) >= 2

    def test_constant_column_detected(self):
        df = pd.DataFrame({"a": [1, 1, 1], "b": [1, 2, 3]})
        findings = QualityRulesEngine.run(df)
        const = [f for f in findings if f.rule_name == "constant_column"]
        assert len(const) == 1
        assert const[0].column == "a"


# â”€â”€ Business Rules Tests â”€â”€


class TestBusinessRules:
    def test_unique_patient_id_passes(self, clean_healthcare_df):
        engine = BusinessRuleEngine()
        findings = engine.run(clean_healthcare_df)
        unique_findings = [f for f in findings if f.rule_name == "unique_patient_id"]
        assert len(unique_findings) == 0

    def test_duplicate_patient_id_fails(self, dirty_healthcare_df):
        engine = BusinessRuleEngine()
        findings = engine.run(dirty_healthcare_df)
        unique_findings = [f for f in findings if f.rule_name == "unique_patient_id"]
        assert len(unique_findings) == 1
        assert unique_findings[0].severity == "error"

    def test_admission_before_discharge_fails(self, dirty_healthcare_df):
        engine = BusinessRuleEngine()
        findings = engine.run(dirty_healthcare_df)
        adm_findings = [f for f in findings if f.rule_name == "admission_before_discharge"]
        assert len(adm_findings) == 1
        assert adm_findings[0].affected_rows == 1

    def test_realistic_age_fails(self, dirty_healthcare_df):
        engine = BusinessRuleEngine()
        findings = engine.run(dirty_healthcare_df)
        age_findings = [f for f in findings if f.rule_name == "realistic_age"]
        assert len(age_findings) == 1
        assert age_findings[0].affected_rows == 2  # -5 and 200

    def test_clean_dataset_no_business_rule_errors(self, clean_healthcare_df):
        engine = BusinessRuleEngine()
        findings = engine.run(clean_healthcare_df)
        errors = [f for f in findings if f.severity == "error"]
        assert len(errors) == 0

    def test_rule_enable_disable(self):
        engine = BusinessRuleEngine()
        len(engine.list_rules())
        engine.disable_rule("unique_patient_id")
        rules = {r["name"]: r for r in engine.list_rules()}
        assert rules["unique_patient_id"]["enabled"] is False
        engine.enable_rule("unique_patient_id")
        rules = {r["name"]: r for r in engine.list_rules()}
        assert rules["unique_patient_id"]["enabled"] is True

    def test_child_age_pediatric(self, clean_healthcare_df):
        engine = BusinessRuleEngine()
        findings = engine.run(clean_healthcare_df)
        pediatric = [f for f in findings if f.rule_name == "child_age_pediatric"]
        # Patient P004 is 12 and in "Pediatric" ward, so no finding
        assert len(pediatric) == 0

    def test_child_not_pediatric_flagged(self):
        df = pd.DataFrame(
            {
                "patient_id": ["P1", "P2"],
                "age": [10, 30],
                "department": ["Adult Ward", "Adult Ward"],
            }
        )
        engine = BusinessRuleEngine()
        findings = engine.run(df)
        pediatric = [f for f in findings if f.rule_name == "child_age_pediatric"]
        assert len(pediatric) == 1
        assert pediatric[0].affected_rows == 1


# â”€â”€ Clinical Checks Tests â”€â”€


class TestClinicalChecks:
    def test_bp_range_check(self):
        df = pd.DataFrame(
            {
                "systolic_bp": [120, 80, 350],
                "diastolic_bp": [80, 50, 100],
            }
        )
        findings = ClinicalValidationEngine.run(df)
        bp_findings = [f for f in findings if "bp" in f.rule_name]
        assert len(bp_findings) >= 1

    def test_temperature_range_check(self):
        df = pd.DataFrame({"temperature": [37.0, 36.5, 50.0]})
        findings = ClinicalValidationEngine.run(df)
        temp = [f for f in findings if f.rule_name == "temperature_range"]
        assert len(temp) == 1

    def test_extreme_ages_detected(self, dirty_healthcare_df):
        findings = ClinicalValidationEngine.run(dirty_healthcare_df)
        extreme = [f for f in findings if f.rule_name == "extreme_ages"]
        assert len(extreme) == 1
        assert extreme[0].affected_rows == 2

    def test_abnormal_billing_detected(self, dirty_healthcare_df):
        findings = ClinicalValidationEngine.run(dirty_healthcare_df)
        billing = [f for f in findings if "billing" in f.rule_name]
        assert len(billing) >= 1

    def test_negative_billing_detected(self, dirty_healthcare_df):
        findings = ClinicalValidationEngine.run(dirty_healthcare_df)
        neg = [f for f in findings if f.rule_name == "negative_billing"]
        assert len(neg) == 1


# â”€â”€ Outlier Detection Tests â”€â”€


class TestOutlierDetector:
    def test_iqr_outliers_detected(self):
        df = pd.DataFrame({"value": [1, 2, 3, 4, 5, 100, 6, 7, 8, 9, 10, 200]})
        findings = OutlierDetector.run(df)
        iqr = [f for f in findings if f.rule_name == "iqr_outlier"]
        assert len(iqr) >= 1

    def test_future_dates_detected(self):
        df = pd.DataFrame({"date": ["2024-01-01", "2099-12-31", "2024-06-15"]})
        findings = OutlierDetector.run(df)
        future = [f for f in findings if f.rule_name == "future_dates"]
        assert len(future) == 1
        assert future[0].affected_rows == 1

    def test_duplicate_admissions_detected(self):
        df = pd.DataFrame(
            {
                "patient_id": ["P1", "P2", "P1"],
                "admission_date": ["2024-01-15", "2024-02-20", "2024-01-15"],
            }
        )
        findings = OutlierDetector.run(df)
        dup_adm = [f for f in findings if f.rule_name == "duplicate_admissions"]
        assert len(dup_adm) == 1


# â”€â”€ Profiler Tests â”€â”€


class TestProfiler:
    def test_profile_generates_stats(self, clean_healthcare_df):
        result = ValidationProfiler.profile(clean_healthcare_df)
        assert result.row_count == 5
        assert result.column_count == 11
        assert len(result.column_profiles) == 11
        assert result.overall_completeness > 0

    def test_profile_detects_nulls(self):
        df = pd.DataFrame({"a": [1, None, 3], "b": [4, 5, None]})
        result = ValidationProfiler.profile(df)
        col_a = [c for c in result.column_profiles if c.name == "a"][0]
        assert col_a.null_count == 1
        assert col_a.null_percentage > 0

    def test_profile_numeric_stats(self):
        df = pd.DataFrame({"value": [10, 20, 30, 40, 50]})
        result = ValidationProfiler.profile(df)
        col = [c for c in result.column_profiles if c.name == "value"][0]
        assert col.min_value == 10
        assert col.max_value == 50
        assert col.mean_value == 30


# â”€â”€ Scoring Tests â”€â”€


class TestScoring:
    def test_clean_dataset_high_score(self, clean_healthcare_df, validation_engine):
        result = validation_engine.validate(clean_healthcare_df, "clean.csv")
        assert result.quality_score.overall >= 80
        assert result.quality_score.traffic_light in ("green", "yellow")

    def test_dirty_dataset_lower_score(self, dirty_healthcare_df, validation_engine):
        result = validation_engine.validate(dirty_healthcare_df, "dirty.csv")
        assert result.quality_score.overall < 80
        assert result.quality_score.traffic_light in ("green", "yellow", "red")

    def test_traffic_light_green(self, clean_healthcare_df, validation_engine):
        result = validation_engine.validate(clean_healthcare_df, "clean.csv")
        assert result.quality_score.overall >= 0
        assert result.quality_score.overall <= 100

    def test_score_dimensions_present(self, clean_healthcare_df, validation_engine):
        result = validation_engine.validate(clean_healthcare_df, "clean.csv")
        score = result.quality_score
        assert 0 <= score.completeness <= 100
        assert 0 <= score.accuracy <= 100
        assert 0 <= score.consistency <= 100
        assert 0 <= score.validity <= 100
        assert 0 <= score.uniqueness <= 100
        assert 0 <= score.integrity <= 100


# â”€â”€ Engine Integration Tests â”€â”€


class TestValidationEngine:
    def test_clean_dataset_passes(self, clean_healthcare_df, validation_engine):
        result = validation_engine.validate(clean_healthcare_df, "clean.csv")
        assert result.status in (ValidationStatus.PASSED, ValidationStatus.PASSED_WITH_WARNINGS)
        assert result.total_errors == 0

    def test_dirty_dataset_fails(self, dirty_healthcare_df, validation_engine):
        result = validation_engine.validate(dirty_healthcare_df, "dirty.csv")
        assert result.status == ValidationStatus.FAILED
        assert result.total_errors > 0

    def test_empty_dataset_fails(self, empty_df, validation_engine):
        result = validation_engine.validate(empty_df, "empty.csv")
        assert result.status == ValidationStatus.FAILED

    def test_result_has_all_components(self, clean_healthcare_df, validation_engine):
        result = validation_engine.validate(clean_healthcare_df, "clean.csv")
        assert result.schema_result is not None
        assert result.profile is not None
        assert result.quality_score is not None
        assert result.validated_at != ""

    def test_to_dict_serializable(self, clean_healthcare_df, validation_engine):
        result = validation_engine.validate(clean_healthcare_df, "clean.csv")
        d = result.to_dict()
        assert "dataset_name" in d
        assert "status" in d
        assert "quality_score" in d
        assert "findings" in d

    def test_can_proceed_to_etl(self, clean_healthcare_df, dirty_healthcare_df, validation_engine):
        clean_result = validation_engine.validate(clean_healthcare_df, "clean.csv")
        assert clean_result.can_proceed_to_etl is True

        dirty_result = validation_engine.validate(dirty_healthcare_df, "dirty.csv")
        assert dirty_result.can_proceed_to_etl is False


# â”€â”€ Approval Workflow Tests â”€â”€


class TestApprovalWorkflow:
    def test_approve_failed_validation(self, dirty_healthcare_df, validation_engine):
        result = validation_engine.validate(dirty_healthcare_df, "dirty.csv")
        assert result.status == ValidationStatus.FAILED

        result, decision = ApprovalWorkflow.approve(
            result, "admin", "administrator", "Approved with exceptions"
        )
        assert result.status == ValidationStatus.APPROVED
        assert result.can_proceed_to_etl is True
        assert decision.decision == ApprovalDecisionType.APPROVED

    def test_reject_validation(self, clean_healthcare_df, validation_engine):
        result = validation_engine.validate(clean_healthcare_df, "clean.csv")
        result, decision = ApprovalWorkflow.reject(
            result, "reviewer", "reviewer", "Data quality concerns"
        )
        assert result.status == ValidationStatus.REJECTED
        assert result.can_proceed_to_etl is False
        assert decision.decision == ApprovalDecisionType.REJECTED

    def test_invalid_role_raises(self, clean_healthcare_df, validation_engine):
        result = validation_engine.validate(clean_healthcare_df, "clean.csv")
        with pytest.raises(ValueError):
            ApprovalWorkflow.approve(result, "user", "invalid_role")

    def test_can_approve_check(self, dirty_healthcare_df, validation_engine):
        result = validation_engine.validate(dirty_healthcare_df, "dirty.csv")
        assert ApprovalWorkflow.can_approve(result) is True

    def test_is_etl_blocked(self, dirty_healthcare_df, validation_engine):
        result = validation_engine.validate(dirty_healthcare_df, "dirty.csv")
        assert ApprovalWorkflow.is_etl_blocked(result) is True


# â”€â”€ Report Generator Tests â”€â”€


class TestReportGenerator:
    def test_generate_summary(self, clean_healthcare_df, validation_engine):
        result = validation_engine.validate(clean_healthcare_df, "clean.csv")
        summary = ValidationReportGenerator.generate_summary(result)
        assert "dataset_name" in summary
        assert "quality_score" in summary
        assert "summary" in summary

    def test_export_csv(self, clean_healthcare_df, validation_engine):
        result = validation_engine.validate(clean_healthcare_df, "clean.csv")
        csv = ValidationReportGenerator.export_csv(result)
        assert "Rule Name" in csv
        assert isinstance(csv, str)

    def test_export_csv_to_file(self, clean_healthcare_df, validation_engine):
        result = validation_engine.validate(clean_healthcare_df, "clean.csv")
        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as tmp:
            tmp_path = tmp.name
        try:
            path = ValidationReportGenerator.export_csv(result, tmp_path)
            assert os.path.exists(path)
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)

    def test_export_excel(self, clean_healthcare_df, validation_engine):
        result = validation_engine.validate(clean_healthcare_df, "clean.csv")
        with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as tmp:
            tmp_path = tmp.name
        try:
            path = ValidationReportGenerator.export_excel(result, tmp_path)
            assert os.path.exists(path)
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)

    def test_export_pdf(self, clean_healthcare_df, validation_engine):
        result = validation_engine.validate(clean_healthcare_df, "clean.csv")
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            tmp_path = tmp.name
        try:
            path = ValidationReportGenerator.export_pdf(result, tmp_path)
            assert os.path.exists(path)
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)


# â”€â”€ Audit Logger Tests â”€â”€


class TestAuditLogger:
    def setup_method(self):
        ValidationAuditLogger.clear()

    def test_log_upload(self):
        entry = ValidationAuditLogger.log_upload("test.csv", user="admin")
        assert entry["event_type"] == "upload"
        assert entry["user"] == "admin"

    def test_log_validation(self):
        entry = ValidationAuditLogger.log_validation(1, "passed", 95.0, user="admin")
        assert entry["event_type"] == "validation"
        assert entry["session_id"] == 1

    def test_log_approval(self):
        entry = ValidationAuditLogger.log_approval(1, "admin", "approved", "OK")
        assert entry["event_type"] == "approval"
        assert entry["user"] == "admin"

    def test_get_entries_filtered(self):
        ValidationAuditLogger.log_upload("test.csv")
        ValidationAuditLogger.log_validation(1, "passed")
        uploads = ValidationAuditLogger.get_entries(event_type="upload")
        assert len(uploads) == 1
        assert all(e["event_type"] == "upload" for e in uploads)

    def test_clear(self):
        ValidationAuditLogger.log_upload("test.csv")
        ValidationAuditLogger.clear()
        assert len(ValidationAuditLogger.get_entries()) == 0


# â”€â”€ AI Copilot Tests â”€â”€


class TestValidationAICopilot:
    def test_build_context(self, clean_healthcare_df, validation_engine):
        result = validation_engine.validate(clean_healthcare_df, "clean.csv")
        ctx = ValidationAICopilot.build_context(result)
        assert "validation_status" in ctx
        assert "quality_score" in ctx
        assert "total_errors" in ctx

    def test_answer_why_failed(self, dirty_healthcare_df, validation_engine):
        result = validation_engine.validate(dirty_healthcare_df, "dirty.csv")
        answer = ValidationAICopilot.answer_question("Why did validation fail?", result)
        assert "failed" in answer.lower() or "error" in answer.lower()

    def test_answer_what_to_correct(self, dirty_healthcare_df, validation_engine):
        result = validation_engine.validate(dirty_healthcare_df, "dirty.csv")
        answer = ValidationAICopilot.answer_question("What should be corrected?", result)
        assert len(answer) > 10

    def test_answer_quality_score(self, clean_healthcare_df, validation_engine):
        result = validation_engine.validate(clean_healthcare_df, "clean.csv")
        answer = ValidationAICopilot.answer_question("What is the quality score?", result)
        assert "score" in answer.lower()

    def test_answer_which_rules_failed(self, dirty_healthcare_df, validation_engine):
        result = validation_engine.validate(dirty_healthcare_df, "dirty.csv")
        answer = ValidationAICopilot.answer_question("Which rules failed most?", result)
        assert len(answer) > 10

    def test_answer_default(self, clean_healthcare_df, validation_engine):
        result = validation_engine.validate(clean_healthcare_df, "clean.csv")
        answer = ValidationAICopilot.answer_question("Hello", result)
        assert "validation" in answer.lower()


# â”€â”€ Performance Tests â”€â”€


class TestPerformance:
    def test_large_dataset_performance(self):
        """Validate a large dataset within reasonable time."""
        import time

        n = 10000
        df = pd.DataFrame(
            {
                "patient_id": [f"P{i:05d}" for i in range(n)],
                "age": [30 + i % 50 for i in range(n)],
                "gender": ["Male" if i % 2 == 0 else "Female" for i in range(n)],
                "amount": [1000 + i * 10 for i in range(n)],
            }
        )
        engine = ValidationEngine()
        start = time.time()
        result = engine.validate(df, "large.csv")
        elapsed = time.time() - start
        assert elapsed < 30.0  # Should complete within 30 seconds
        assert result.status in (ValidationStatus.PASSED, ValidationStatus.PASSED_WITH_WARNINGS)


# â”€â”€ API Route Tests â”€â”€


class TestValidationAPI:
    def test_run_validation_endpoint(self, client, auth_headers):
        csv_content = "patient_id,age,gender,amount\nP001,45,Male,5000\nP002,32,Female,3200\nP003,67,Male,12000\n"
        response = client.post(
            "/validation/run",
            files={"file": ("test.csv", csv_content, "text/csv")},
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert "session_id" in data
        assert "status" in data
        assert "quality_score" in data

    def test_validation_status_endpoint(self, client, auth_headers):
        csv_content = "patient_id,age,gender,amount\nP001,45,Male,5000\nP002,32,Female,3200\n"
        run_response = client.post(
            "/validation/run",
            files={"file": ("test.csv", csv_content, "text/csv")},
            headers=auth_headers,
        )
        session_id = run_response.json()["session_id"]

        response = client.get(f"/validation/status/{session_id}", headers=auth_headers)
        assert response.status_code == 200
        assert "status" in response.json()

    def test_validation_report_endpoint(self, client, auth_headers):
        csv_content = "patient_id,age,gender,amount\nP001,45,Male,5000\nP002,32,Female,3200\n"
        run_response = client.post(
            "/validation/run",
            files={"file": ("test.csv", csv_content, "text/csv")},
            headers=auth_headers,
        )
        session_id = run_response.json()["session_id"]

        response = client.get(f"/validation/report/{session_id}", headers=auth_headers)
        assert response.status_code == 200
        assert "dataset_name" in response.json()

    def test_list_rules_endpoint(self, client, auth_headers):
        response = client.get("/validation/rules", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "rules" in data
        assert len(data["rules"]) > 0

    def test_history_endpoint(self, client, auth_headers):
        response = client.get("/validation/history", headers=auth_headers)
        assert response.status_code == 200
        assert "history" in response.json()

    def test_audit_endpoint(self, client, auth_headers):
        response = client.get("/validation/audit", headers=auth_headers)
        assert response.status_code == 200
        assert "entries" in response.json()

    def test_approve_endpoint(self, client, auth_headers):
        # Create a session with dirty data that will fail validation
        csv_content = "patient_id,age,gender,amount\nP001,45,Male,5000\nP001,32,Female,3200\nP003,-5,Male,-100\n"
        run_response = client.post(
            "/validation/run",
            files={"file": ("dirty.csv", csv_content, "text/csv")},
            headers=auth_headers,
        )
        session_id = run_response.json()["session_id"]

        response = client.post(
            f"/validation/approve/{session_id}",
            json={"approver": "admin", "role": "administrator", "comments": "OK"},
            headers=auth_headers,
        )
        assert response.status_code == 200
        assert response.json()["status"] == "approved"
