"""Tests for the Certificate Intelligence Engine.

Tests cover:
  - Field normalization (names, dates, GPA, certificate numbers, grades)
  - Certificate analysis (completeness, consistency, academic performance,
    anomaly detection, recommendations)
  - Batch analytics aggregation
  - Migration sanity checks

All test data is realistic — no mocks or fabricated analysis results.
"""

import pytest
from certificates.normalizer import (
    normalize_name,
    normalize_date,
    normalize_gpa,
    normalize_certificate_number,
    normalize_grade,
    normalize_field,
)
from certificates.analysis import (
    analyze_certificate,
    analyze_batch,
    batch_analytics,
    assess_completeness,
    check_consistency,
    summarize_academic_performance,
    detect_anomalies,
    generate_recommendations,
)


# ═══════════════════════════════════════════════════════════════
# Normalization Tests
# ═══════════════════════════════════════════════════════════════


class TestNormalizeName:
    def test_all_upper(self):
        assert normalize_name("JOHN DOE") == "John Doe"

    def test_all_lower(self):
        assert normalize_name("jane smith") == "Jane Smith"

    def test_mixed_case_preserved(self):
        assert normalize_name("McDonald O'Brien") == "McDonald O'Brien"

    def test_extra_whitespace_collapsed(self):
        assert normalize_name("  John   Doe  ") == "John Doe"

    def test_none_input(self):
        assert normalize_name(None) is None

    def test_empty_string(self):
        assert normalize_name("") == ""


class TestNormalizeDate:
    def test_dd_mm_yyyy(self):
        assert normalize_date("15/01/2024") == "2024-01-15"

    def test_yyyy_mm_dd(self):
        assert normalize_date("2024-01-15") == "2024-01-15"

    def test_dotted_format(self):
        assert normalize_date("15.01.2024") == "2024-01-15"

    def test_month_name_format(self):
        assert normalize_date("January 15, 2024") == "2024-01-15"

    def test_short_month_name(self):
        assert normalize_date("Jan 15, 2024") == "2024-01-15"

    def test_two_digit_year(self):
        assert normalize_date("15/01/24") == "2024-01-15"

    def test_unparseable_returns_original(self):
        assert normalize_date("some date text") == "some date text"

    def test_none_input(self):
        assert normalize_date(None) is None


class TestNormalizeGpa:
    def test_simple_number(self):
        assert normalize_gpa("3.75") == "3.75"

    def test_with_text(self):
        assert normalize_gpa("CGPA: 3.50 out of 4.0") == "3.50"

    def test_integer_gpa(self):
        assert normalize_gpa("4") == "4.00"

    def test_out_of_range_returns_original(self):
        assert normalize_gpa("15.5") == "15.5"

    def test_none_input(self):
        assert normalize_gpa(None) is None


class TestNormalizeCertificateNumber:
    def test_uppercase_conversion(self):
        assert normalize_certificate_number("abc-123-xyz") == "ABC-123-XYZ"

    def test_strip_punctuation(self):
        assert normalize_certificate_number("CERT/2024/001.") == "CERT/2024/001"

    def test_none_input(self):
        assert normalize_certificate_number(None) is None


class TestNormalizeGrade:
    def test_first_class(self):
        assert normalize_grade("first class") == "First Class"

    def test_distinction(self):
        assert normalize_grade("distinction") == "Distinction"

    def test_unknown_returns_original(self):
        assert normalize_grade("Superior") == "Superior"

    def test_none_input(self):
        assert normalize_grade(None) is None


class TestNormalizeFieldDispatch:
    def test_name_field_dispatches_to_name_normalizer(self):
        assert normalize_field("full_name", "JOHN DOE") == "John Doe"

    def test_date_field_dispatches_to_date_normalizer(self):
        assert normalize_field("date_awarded", "15/01/2024") == "2024-01-15"

    def test_gpa_field_dispatches_to_gpa_normalizer(self):
        assert normalize_field("gpa", "3.5") == "3.50"

    def test_unknown_field_returns_original(self):
        assert normalize_field("unknown_field", "some value") == "some value"

    def test_none_value_returns_none(self):
        assert normalize_field("full_name", None) is None


# ═══════════════════════════════════════════════════════════════
# Completeness Tests
# ═══════════════════════════════════════════════════════════════


class TestCompleteness:
    def test_all_required_filled(self):
        fields = {
            "full_name": {"value": "John Doe"},
            "qualification": {"value": "Bachelor of Science"},
            "institution": {"value": "University of Ghana"},
            "date_awarded": {"value": "2024-01-15"},
            "certificate_number": {"value": "CERT-001"},
        }
        result = assess_completeness("academic_certificate", fields)
        assert result.completeness_pct == 100.0
        assert len(result.missing_required) == 0

    def test_missing_required_fields(self):
        fields = {
            "full_name": {"value": "John Doe"},
        }
        result = assess_completeness("academic_certificate", fields)
        assert result.completeness_pct < 100.0
        assert len(result.missing_required) > 0
        assert "Institution" in result.missing_required or "institution" in [m.lower() for m in result.missing_required]

    def test_no_spec_treats_all_as_optional(self):
        fields = {
            "custom_field": {"value": "test"},
        }
        result = assess_completeness(None, fields)
        assert result.required_fields == 0
        assert result.completeness_pct == 100.0

    def test_empty_fields(self):
        result = assess_completeness("academic_certificate", {})
        assert result.required_filled == 0
        assert result.completeness_pct == 0.0
        assert len(result.missing_required) > 0


# ═══════════════════════════════════════════════════════════════
# Consistency Check Tests
# ═══════════════════════════════════════════════════════════════


class TestConsistencyChecks:
    def test_date_awarded_vs_graduation_within_year(self):
        fields = {
            "date_awarded": {"value": "2024-01-15"},
            "graduation_date": {"value": "2024-06-15"},
        }
        checks = check_consistency("academic_certificate", fields)
        date_check = [c for c in checks if c.check_name == "date_awarded_vs_graduation"]
        assert len(date_check) == 1
        assert date_check[0].passed is True

    def test_date_awarded_vs_graduation_far_apart(self):
        fields = {
            "date_awarded": {"value": "2024-01-15"},
            "graduation_date": {"value": "2020-01-15"},
        }
        checks = check_consistency("academic_certificate", fields)
        date_check = [c for c in checks if c.check_name == "date_awarded_vs_graduation"]
        assert len(date_check) == 1
        assert date_check[0].passed is False
        assert date_check[0].severity == "warning"

    def test_expiry_before_issue_error(self):
        fields = {
            "date_issued": {"value": "2024-06-01"},
            "expiry_date": {"value": "2024-01-01"},
        }
        checks = check_consistency("license_certification", fields)
        expiry_check = [c for c in checks if c.check_name == "expiry_before_issue"]
        assert len(expiry_check) == 1
        assert expiry_check[0].passed is False
        assert expiry_check[0].severity == "error"

    def test_gpa_out_of_range(self):
        fields = {
            "gpa": {"value": "15.5"},
        }
        checks = check_consistency("academic_certificate", fields)
        gpa_check = [c for c in checks if c.check_name == "gpa_range"]
        assert len(gpa_check) == 1
        assert gpa_check[0].passed is False

    def test_name_with_digits_flagged(self):
        fields = {
            "full_name": {"value": "John D0e"},
        }
        checks = check_consistency("academic_certificate", fields)
        name_check = [c for c in checks if c.check_name == "name_format"]
        assert len(name_check) == 1
        assert name_check[0].passed is False

    def test_missing_certificate_number_for_academic(self):
        fields = {
            "full_name": {"value": "John Doe"},
        }
        checks = check_consistency("academic_certificate", fields)
        cert_check = [c for c in checks if c.check_name == "certificate_number_present"]
        assert len(cert_check) == 1
        assert cert_check[0].passed is False


# ═══════════════════════════════════════════════════════════════
# Academic Performance Tests
# ═══════════════════════════════════════════════════════════════


class TestAcademicPerformance:
    def test_full_performance_data(self):
        fields = {
            "gpa": {"value": "3.75"},
            "grade": {"value": "First Class"},
            "qualification": {"value": "Bachelor of Science"},
            "programme": {"value": "Computer Science"},
        }
        result = summarize_academic_performance(fields)
        assert result.has_performance_data is True
        assert result.gpa == "3.75"
        assert result.grade == "First Class"
        assert result.qualification == "Bachelor of Science"
        assert "Computer Science" in result.summary

    def test_no_performance_data(self):
        fields = {}
        result = summarize_academic_performance(fields)
        assert result.has_performance_data is False
        assert "No academic performance data" in result.summary

    def test_partial_data(self):
        fields = {
            "qualification": {"value": "Diploma"},
        }
        result = summarize_academic_performance(fields)
        assert result.has_performance_data is True
        assert result.gpa is None
        assert "Diploma" in result.summary


# ═══════════════════════════════════════════════════════════════
# Anomaly Detection Tests
# ═══════════════════════════════════════════════════════════════


class TestAnomalyDetection:
    def test_low_confidence_field_flagged(self):
        fields = {
            "full_name": {"value": "John", "confidence_score": 0.3, "is_low_confidence": True, "field_label": "Full Name"},
        }
        completeness = assess_completeness("academic_certificate", fields)
        anomalies = detect_anomalies(fields, completeness, [], False, None, 0.9)
        low_conf = [a for a in anomalies if a.anomaly_type == "low_confidence"]
        assert len(low_conf) == 1

    def test_validation_failure_flagged(self):
        fields = {
            "gpa": {"value": "15.5", "confidence_score": 0.9, "is_low_confidence": False, "is_valid": False, "validation_message": "Out of range", "field_label": "GPA"},
        }
        completeness = assess_completeness("academic_certificate", fields)
        anomalies = detect_anomalies(fields, completeness, [], False, None, 0.9)
        val_fail = [a for a in anomalies if a.anomaly_type == "validation_failed"]
        assert len(val_fail) == 1

    def test_duplicate_flagged(self):
        fields = {}
        completeness = assess_completeness("academic_certificate", fields)
        anomalies = detect_anomalies(fields, completeness, [], True, 42, 0.9)
        dup = [a for a in anomalies if a.anomaly_type == "duplicate"]
        assert len(dup) == 1
        assert "42" in dup[0].description

    def test_low_classification_confidence_flagged(self):
        fields = {}
        completeness = assess_completeness("academic_certificate", fields)
        anomalies = detect_anomalies(fields, completeness, [], False, None, 0.2)
        low_class = [a for a in anomalies if a.anomaly_type == "low_classification_confidence"]
        assert len(low_class) == 1

    def test_missing_required_fields_flagged(self):
        fields = {}
        completeness = assess_completeness("academic_certificate", fields)
        anomalies = detect_anomalies(fields, completeness, [], False, None, 0.9)
        missing = [a for a in anomalies if a.anomaly_type == "missing_required_fields"]
        assert len(missing) == 1


# ═══════════════════════════════════════════════════════════════
# Recommendations Tests
# ═══════════════════════════════════════════════════════════════


class TestRecommendations:
    def test_missing_required_generates_high_priority_rec(self):
        completeness = assess_completeness("academic_certificate", {})
        recs = generate_recommendations(completeness, [], "not_verified", [])
        high_recs = [r for r in recs if r.priority == "high"]
        assert any(r.action == "review_missing_fields" for r in high_recs)

    def test_not_verified_generates_verification_rec(self):
        completeness = assess_completeness("academic_certificate", {
            "full_name": {"value": "John"},
            "institution": {"value": "Univ"},
            "date_awarded": {"value": "2024-01-01"},
            "certificate_number": {"value": "CERT-001"},
        })
        recs = generate_recommendations(completeness, [], "not_verified", [])
        verify_recs = [r for r in recs if r.action == "initiate_verification"]
        assert len(verify_recs) == 1

    def test_all_good_generates_approve_rec(self):
        fields = {
            "full_name": {"value": "John Doe", "confidence_score": 0.9, "is_low_confidence": False, "is_valid": True, "field_label": "Full Name"},
            "qualification": {"value": "Bachelor of Science", "confidence_score": 0.9, "is_low_confidence": False, "is_valid": True, "field_label": "Qualification"},
            "institution": {"value": "University", "confidence_score": 0.9, "is_low_confidence": False, "is_valid": True, "field_label": "Institution"},
            "date_awarded": {"value": "2024-01-15", "confidence_score": 0.9, "is_low_confidence": False, "is_valid": True, "field_label": "Date Awarded"},
            "certificate_number": {"value": "CERT-001", "confidence_score": 0.9, "is_low_confidence": False, "is_valid": True, "field_label": "Certificate Number"},
        }
        completeness = assess_completeness("academic_certificate", fields)
        anomalies = detect_anomalies(fields, completeness, [], False, None, 0.9)
        recs = generate_recommendations(completeness, anomalies, "verified", [])
        approve_recs = [r for r in recs if r.action == "approve_certificate"]
        assert len(approve_recs) == 1


# ═══════════════════════════════════════════════════════════════
# Full Analysis Tests
# ═══════════════════════════════════════════════════════════════


class TestAnalyzeCertificate:
    def test_full_analysis_well_formed_certificate(self):
        document = {
            "document_type": "academic_certificate",
            "document_type_label": "Academic Certificate",
            "classification_confidence": 0.85,
            "overall_confidence": 0.9,
            "verification_status": "not_verified",
            "duplicate_of_id": None,
            "status": "ready_for_review",
        }
        fields = [
            {"field_name": "full_name", "field_label": "Full Name", "value": "John Doe", "raw_value": "JOHN DOE", "confidence_score": 0.95, "is_low_confidence": False, "is_valid": True, "validation_message": None, "was_corrected": False},
            {"field_name": "institution", "field_label": "Institution", "value": "University of Ghana", "raw_value": "University of Ghana", "confidence_score": 0.9, "is_low_confidence": False, "is_valid": True, "validation_message": None, "was_corrected": False},
            {"field_name": "date_awarded", "field_label": "Date Awarded", "value": "2024-01-15", "raw_value": "15/01/2024", "confidence_score": 0.85, "is_low_confidence": False, "is_valid": True, "validation_message": None, "was_corrected": False},
            {"field_name": "certificate_number", "field_label": "Certificate Number", "value": "CERT-2024-001", "raw_value": "cert-2024-001", "confidence_score": 0.8, "is_low_confidence": False, "is_valid": True, "validation_message": None, "was_corrected": False},
            {"field_name": "gpa", "field_label": "GPA", "value": "3.75", "raw_value": "3.75", "confidence_score": 0.7, "is_low_confidence": False, "is_valid": True, "validation_message": None, "was_corrected": False},
        ]
        analysis = analyze_certificate(document, fields)
        assert analysis.document_type == "academic_certificate"
        assert analysis.completeness.completeness_pct > 0
        assert len(analysis.fields) == 5
        assert analysis.is_duplicate is False

    def test_analysis_with_duplicate(self):
        document = {
            "document_type": "degree_certificate",
            "document_type_label": "Degree Certificate",
            "classification_confidence": 0.9,
            "overall_confidence": 0.85,
            "verification_status": "verified",
            "duplicate_of_id": 15,
            "status": "ready_for_review",
        }
        fields = []
        analysis = analyze_certificate(document, fields)
        assert analysis.is_duplicate is True
        assert analysis.duplicate_of_id == 15

    def test_analysis_with_no_type(self):
        document = {
            "document_type": None,
            "document_type_label": None,
            "classification_confidence": None,
            "overall_confidence": None,
            "verification_status": "not_verified",
            "duplicate_of_id": None,
            "status": "uploaded",
        }
        fields = []
        analysis = analyze_certificate(document, fields)
        assert analysis.document_type is None
        assert analysis.completeness.total_fields == 0


# ═══════════════════════════════════════════════════════════════
# Batch Analytics Tests
# ═══════════════════════════════════════════════════════════════


class TestBatchAnalytics:
    def test_empty_batch(self):
        result = batch_analytics([])
        assert result.total == 0
        assert "No certificates" in result.summary

    def test_batch_with_multiple_certificates(self):
        docs = [
            {
                "id": 1,
                "document_type": "academic_certificate",
                "document_type_label": "Academic Certificate",
                "classification_confidence": 0.85,
                "overall_confidence": 0.9,
                "verification_status": "verified",
                "duplicate_of_id": None,
                "status": "approved",
            },
            {
                "id": 2,
                "document_type": "degree_certificate",
                "document_type_label": "Degree Certificate",
                "classification_confidence": 0.8,
                "overall_confidence": 0.85,
                "verification_status": "not_verified",
                "duplicate_of_id": 1,
                "status": "ready_for_review",
            },
        ]
        fields_by_doc = {
            1: [
                {"field_name": "full_name", "field_label": "Full Name", "value": "John Doe", "raw_value": "John Doe", "confidence_score": 0.9, "is_low_confidence": False, "is_valid": True, "validation_message": None, "was_corrected": False},
                {"field_name": "qualification", "field_label": "Qualification", "value": "Bachelor of Science", "raw_value": "Bachelor of Science", "confidence_score": 0.9, "is_low_confidence": False, "is_valid": True, "validation_message": None, "was_corrected": False},
                {"field_name": "institution", "field_label": "Institution", "value": "University of Ghana", "raw_value": "University of Ghana", "confidence_score": 0.9, "is_low_confidence": False, "is_valid": True, "validation_message": None, "was_corrected": False},
                {"field_name": "date_awarded", "field_label": "Date Awarded", "value": "2024-01-15", "raw_value": "2024-01-15", "confidence_score": 0.85, "is_low_confidence": False, "is_valid": True, "validation_message": None, "was_corrected": False},
                {"field_name": "certificate_number", "field_label": "Certificate Number", "value": "CERT-001", "raw_value": "CERT-001", "confidence_score": 0.8, "is_low_confidence": False, "is_valid": True, "validation_message": None, "was_corrected": False},
            ],
            2: [
                {"field_name": "full_name", "field_label": "Full Name", "value": "Jane Smith", "raw_value": "JANE SMITH", "confidence_score": 0.3, "is_low_confidence": True, "is_valid": True, "validation_message": None, "was_corrected": False},
            ],
        }
        analyses = analyze_batch(docs, fields_by_doc)
        analytics = batch_analytics(analyses)
        assert analytics.total == 2
        assert analytics.total_duplicates == 1
        assert "Academic Certificate" in analytics.by_type
        assert "Degree Certificate" in analytics.by_type
        assert analytics.avg_confidence > 0
        assert "University of Ghana" in analytics.institutions


# ═══════════════════════════════════════════════════════════════
# Migration Sanity Test
# ═══════════════════════════════════════════════════════════════


class TestMigration:
    def test_checksum_migration_exists(self):
        import os
        migration_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "alembic", "versions",
            "f1a2b3c4d5e6_add_file_checksum_to_capture_documents.py",
        )
        assert os.path.exists(migration_path)
        with open(migration_path) as f:
            content = f.read()
        assert "file_checksum" in content
        assert "f1a2b3c4d5e6" in content
        assert "eb32b7fc465a" in content
