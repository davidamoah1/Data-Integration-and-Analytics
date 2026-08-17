"""Tests for the Certificate Intelligence module."""
from __future__ import annotations

import io
from unittest.mock import MagicMock, patch

import pytest

from capture.document_types import (
    CERTIFICATE_TYPES,
    ALL_DOCUMENT_TYPES,
    INDUSTRIES,
    get_document_type,
)


class TestCertificateDocumentTypes:
    """Test certificate document type definitions."""

    def test_certificate_types_exist(self):
        """All 9 certificate types are registered."""
        cert_keys = {t.key for t in CERTIFICATE_TYPES}
        assert cert_keys == {
            "academic_certificate",
            "degree_certificate",
            "diploma",
            "professional_certificate",
            "training_certificate",
            "certificate_of_completion",
            "certificate_of_attendance",
            "membership_certificate",
            "license_certification",
        }

    def test_certificates_in_all_document_types(self):
        """Certificate types are included in the combined registry."""
        cert_keys = {t.key for t in CERTIFICATE_TYPES}
        all_keys = {t.key for t in ALL_DOCUMENT_TYPES}
        assert cert_keys.issubset(all_keys)

    def test_certificates_industry_registered(self):
        """The 'certificates' industry is in the INDUSTRIES list."""
        assert "certificates" in INDUSTRIES

    def test_academic_certificate_fields(self):
        """Academic certificate has the expected fields."""
        t = get_document_type("academic_certificate")
        assert t is not None
        field_names = {f.name for f in t.fields}
        assert "full_name" in field_names
        assert "qualification" in field_names
        assert "institution" in field_names
        assert "date_awarded" in field_names
        assert "certificate_number" in field_names
        assert "gpa" in field_names

    def test_professional_certificate_has_expiry(self):
        """Professional certificate has expiry date field."""
        t = get_document_type("professional_certificate")
        assert t is not None
        field_names = {f.name for f in t.fields}
        assert "expiry_date" in field_names
        assert "license_number" in field_names
        assert "verification_code" in field_names

    def test_all_certificate_types_have_required_fields(self):
        """Every certificate type has at least full_name and institution as required fields."""
        for t in CERTIFICATE_TYPES:
            required_names = {f.name for f in t.fields if f.required}
            assert "full_name" in required_names, f"{t.key} missing required full_name"
            assert any("institution" in f.name or "organization" in f.name for f in t.fields if f.required), \
                f"{t.key} missing required institution/organization field"

    def test_all_certificate_types_have_keywords(self):
        """Every certificate type has classification keywords."""
        for t in CERTIFICATE_TYPES:
            assert len(t.keywords) > 0, f"{t.key} has no keywords"


class TestCertificateValidation:
    """Test certificate-specific validation functions."""

    def test_validate_gpa_valid(self):
        from capture.validators import validate_gpa
        assert validate_gpa("3.5")[0] is True
        assert validate_gpa("4.0")[0] is True
        assert validate_gpa("0")[0] is True

    def test_validate_gpa_invalid(self):
        from capture.validators import validate_gpa
        assert validate_gpa("11.5")[0] is False
        assert validate_gpa("-1")[0] is False
        assert validate_gpa("abc")[0] is False

    def test_certificate_dates_valid(self):
        from capture.validators import validate_certificate_dates
        assert validate_certificate_dates("15/06/2024", "15/06/2026")[0] is True

    def test_certificate_dates_expiry_before_issue(self):
        from capture.validators import validate_certificate_dates
        valid, msg = validate_certificate_dates("15/06/2026", "15/06/2024")
        assert valid is False
        assert "before" in msg.lower()

    def test_certificate_dates_none_values(self):
        from capture.validators import validate_certificate_dates
        assert validate_certificate_dates(None, None)[0] is True
        assert validate_certificate_dates("15/06/2024", None)[0] is True


class TestCertificateClassification:
    """Test that the classifier can identify certificate types."""

    def test_classify_academic_certificate_text(self):
        from capture.classifier import classify_text
        text = """
        CERTIFICATE
        This is to certify that
        John Mensah
        has been awarded the degree of
        Bachelor of Science in Data Analytics
        by ABC University
        Date Awarded: 15/06/2024
        Certificate Number: CERT-2024-001
        """
        result = classify_text(text)
        assert result.document_type is not None
        assert result.document_type.key in ("academic_certificate", "degree_certificate")
        assert result.confidence > 0.3

    def test_classify_professional_certificate_text(self):
        from capture.classifier import classify_text
        text = """
        PROFESSIONAL CERTIFICATE
        This is to certify that
        Jane Smith
        is a Certified Professional
        issued by Professional Body
        License Number: LIC-001
        Date Issued: 01/01/2024
        Expiry: 01/01/2026
        """
        result = classify_text(text)
        assert result.document_type is not None
        assert result.document_type.key in ("professional_certificate", "license_certification")

    def test_classify_training_certificate_text(self):
        from capture.classifier import classify_text
        text = """
        TRAINING CERTIFICATE
        Certificate of Completion
        This is to certify that
        Bob Johnson
        has successfully completed
        Data Analytics Training
        issued by Training Provider
        """
        result = classify_text(text)
        assert result.document_type is not None
        assert result.document_type.key in (
            "training_certificate", "certificate_of_completion"
        )

    def test_classify_empty_text(self):
        from capture.classifier import classify_text
        result = classify_text("")
        assert result.document_type is None
        assert result.needs_confirmation is True


class TestCertificateRoutes:
    """Test certificate API routes (unit-level, mocking DB)."""

    def test_certificate_doc_types_set(self):
        """Test that CERTIFICATE_DOC_TYPES contains all 9 types."""
        from certificates.routes import CERTIFICATE_DOC_TYPES
        assert len(CERTIFICATE_DOC_TYPES) == 9
        assert "academic_certificate" in CERTIFICATE_DOC_TYPES
        assert "license_certification" in CERTIFICATE_DOC_TYPES

    def test_is_certificate_type(self):
        """Test the _is_certificate_type helper."""
        from certificates.routes import _is_certificate_type
        assert _is_certificate_type("academic_certificate") is True
        assert _is_certificate_type("opd_register") is False
        assert _is_certificate_type(None) is False

    def test_get_max_batch_size(self):
        """Test that batch size is configurable."""
        from certificates.routes import _get_max_batch_size
        size = _get_max_batch_size()
        assert size == 50  # default

    def test_serialize_certificate(self):
        """Test the _serialize_certificate helper."""
        from certificates.routes import _serialize_certificate
        doc = MagicMock()
        doc.id = 1
        doc.batch_id = None
        doc.filename = "test.png"
        doc.file_type = "png"
        doc.status = "approved"
        doc.error_message = None
        doc.document_type = "academic_certificate"
        doc.document_type_label = "Academic Certificate"
        doc.classification_confidence = 0.95
        doc.overall_confidence = 0.88
        doc.needs_type_confirmation = False
        doc.verification_status = "verified"
        doc.verification_method = "manual_check"
        doc.verified_at = None
        doc.duplicate_of_id = None
        doc.created_at = None
        doc.processed_at = None
        doc.approved_at = None

        result = _serialize_certificate(doc)
        assert result["id"] == 1
        assert result["filename"] == "test.png"
        assert result["document_type"] == "academic_certificate"
        assert result["verification_status"] == "verified"
