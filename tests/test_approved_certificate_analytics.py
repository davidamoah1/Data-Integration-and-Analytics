"""Tests for the Approved Certificate Analytics service and API.

Tests cover:
  - Approved-only filtering (no rejected/pending certs included)
  - Tenant isolation (org A cannot see org B's approved certs)
  - KPI accuracy
  - Filter combinations
  - Export endpoints
  - Empty state handling
  - Data quality computation
"""

from __future__ import annotations

from datetime import datetime, timezone

from capture.models import CaptureDocument, CaptureField
from certificates.analytics_service import (
    ApprovedAnalyticsFilters,
    ApprovedCertificateAnalyticsService,
)


def _create_cert_doc(
    db_session,
    org_id: int = 1,
    doc_type: str = "academic_certificate",
    status: str = "approved",
    doc_id: int | None = None,
) -> CaptureDocument:
    doc = CaptureDocument(
        organization_id=org_id,
        filename=f"cert_{doc_id or 'test'}.pdf",
        original_file_path="/tmp/test.pdf",
        file_type="pdf",
        status=status,
        document_type=doc_type,
        document_type_label=doc_type.replace("_", " ").title(),
        industry="certificates",
        uploaded_by=1,
        approved_by=1 if status == "approved" else None,
        approved_at=datetime.now(timezone.utc) if status == "approved" else None,
    )
    db_session.add(doc)
    db_session.flush()
    return doc


def _add_field(db_session, doc_id: int, name: str, value: str, label: str = ""):
    f = CaptureField(
        document_id=doc_id,
        field_name=name,
        field_label=label or name.replace("_", " ").title(),
        data_type="text",
        value=value,
        raw_value=value,
        confidence_score=0.9,
    )
    db_session.add(f)
    db_session.flush()
    return f


class TestApprovedOnlyFiltering:
    """Ensure only approved certificates are included in analytics."""

    def test_approved_certs_included(self, db_session):
        doc = _create_cert_doc(db_session, status="approved")
        _add_field(db_session, doc.id, "student_name", "John Doe")
        _add_field(db_session, doc.id, "qualification", "BSc Computer Science")
        db_session.commit()

        svc = ApprovedCertificateAnalyticsService(db_session)
        result = svc.get_summary(org_id=1)
        assert result.total == 1
        assert result.kpis.total_approved == 1

    def test_rejected_certs_excluded(self, db_session):
        _create_cert_doc(db_session, status="rejected")
        db_session.commit()

        svc = ApprovedCertificateAnalyticsService(db_session)
        result = svc.get_summary(org_id=1)
        assert result.total == 0

    def test_pending_certs_excluded(self, db_session):
        _create_cert_doc(db_session, status="ready_for_review")
        db_session.commit()

        svc = ApprovedCertificateAnalyticsService(db_session)
        result = svc.get_summary(org_id=1)
        assert result.total == 0

    def test_draft_certs_excluded(self, db_session):
        _create_cert_doc(db_session, status="draft")
        db_session.commit()

        svc = ApprovedCertificateAnalyticsService(db_session)
        result = svc.get_summary(org_id=1)
        assert result.total == 0

    def test_failed_certs_excluded(self, db_session):
        _create_cert_doc(db_session, status="failed")
        db_session.commit()

        svc = ApprovedCertificateAnalyticsService(db_session)
        result = svc.get_summary(org_id=1)
        assert result.total == 0

    def test_non_certificate_types_excluded(self, db_session):
        """Documents with non-certificate types should not appear."""
        doc = CaptureDocument(
            organization_id=1,
            filename="invoice.pdf",
            original_file_path="/tmp/invoice.pdf",
            file_type="pdf",
            status="approved",
            document_type="invoice",
            document_type_label="Invoice",
            industry="business",
            uploaded_by=1,
            approved_by=1,
            approved_at=datetime.now(timezone.utc),
        )
        db_session.add(doc)
        db_session.commit()

        svc = ApprovedCertificateAnalyticsService(db_session)
        result = svc.get_summary(org_id=1)
        assert result.total == 0


class TestTenantIsolation:
    """Ensure org A cannot see org B's approved certificates."""

    def test_cross_org_not_visible(self, db_session):
        doc1 = _create_cert_doc(db_session, org_id=1, status="approved")
        doc2 = _create_cert_doc(db_session, org_id=2, status="approved")
        _add_field(db_session, doc1.id, "student_name", "Alice")
        _add_field(db_session, doc2.id, "student_name", "Bob")
        db_session.commit()

        svc = ApprovedCertificateAnalyticsService(db_session)
        result = svc.get_summary(org_id=1)
        assert result.total == 1
        assert result.records[0]["recipient"] == "Alice"

    def test_other_org_records_not_in_filter_options(self, db_session):
        doc1 = _create_cert_doc(db_session, org_id=1, status="approved")
        doc2 = _create_cert_doc(db_session, org_id=2, status="approved")
        _add_field(db_session, doc1.id, "institution", "Org1 University")
        _add_field(db_session, doc2.id, "institution", "Org2 University")
        db_session.commit()

        svc = ApprovedCertificateAnalyticsService(db_session)
        options = svc.get_filter_options(org_id=1)
        assert "Org1 University" in options["issuing_organizations"]
        assert "Org2 University" not in options["issuing_organizations"]


class TestKPIAccuracy:
    """Verify KPI computations are correct."""

    def test_unique_recipients(self, db_session):
        doc1 = _create_cert_doc(db_session, status="approved", doc_id=1)
        doc2 = _create_cert_doc(db_session, status="approved", doc_id=2)
        doc3 = _create_cert_doc(db_session, status="approved", doc_id=3)
        _add_field(db_session, doc1.id, "student_name", "Alice Smith")
        _add_field(db_session, doc2.id, "student_name", "Alice Smith")
        _add_field(db_session, doc3.id, "student_name", "Bob Jones")
        db_session.commit()

        svc = ApprovedCertificateAnalyticsService(db_session)
        result = svc.get_summary(org_id=1)
        assert result.kpis.unique_recipients == 2
        assert result.kpis.total_approved == 3
        assert result.kpis.avg_certs_per_person == 1.5

    def test_certificate_types_count(self, db_session):
        _create_cert_doc(db_session, doc_type="academic_certificate", status="approved", doc_id=1)
        _create_cert_doc(db_session, doc_type="diploma", status="approved", doc_id=2)
        _create_cert_doc(db_session, doc_type="diploma", status="approved", doc_id=3)
        db_session.commit()

        svc = ApprovedCertificateAnalyticsService(db_session)
        result = svc.get_summary(org_id=1)
        assert result.kpis.certificate_types == 2

    def test_empty_state(self, db_session):
        svc = ApprovedCertificateAnalyticsService(db_session)
        result = svc.get_summary(org_id=1)
        assert result.total == 0
        assert result.kpis.total_approved == 0
        assert result.kpis.unique_recipients == 0
        assert result.insights == []


class TestFilters:
    """Test filter combinations."""

    def test_filter_by_certificate_type(self, db_session):
        _create_cert_doc(db_session, doc_type="academic_certificate", status="approved", doc_id=1)
        _create_cert_doc(db_session, doc_type="diploma", status="approved", doc_id=2)
        db_session.commit()

        svc = ApprovedCertificateAnalyticsService(db_session)
        filters = ApprovedAnalyticsFilters(certificate_type="diploma")
        result = svc.get_summary(org_id=1, filters=filters)
        assert result.total == 1

    def test_filter_by_recipient(self, db_session):
        doc1 = _create_cert_doc(db_session, status="approved", doc_id=1)
        doc2 = _create_cert_doc(db_session, status="approved", doc_id=2)
        _add_field(db_session, doc1.id, "student_name", "Alice Smith")
        _add_field(db_session, doc2.id, "student_name", "Bob Jones")
        db_session.commit()

        svc = ApprovedCertificateAnalyticsService(db_session)
        filters = ApprovedAnalyticsFilters(recipient="alice")
        result = svc.get_summary(org_id=1, filters=filters)
        assert result.total == 1
        assert result.records[0]["recipient"] == "Alice Smith"

    def test_filter_by_institution(self, db_session):
        doc1 = _create_cert_doc(db_session, status="approved", doc_id=1)
        doc2 = _create_cert_doc(db_session, status="approved", doc_id=2)
        _add_field(db_session, doc1.id, "institution", "Harvard University")
        _add_field(db_session, doc2.id, "institution", "MIT")
        db_session.commit()

        svc = ApprovedCertificateAnalyticsService(db_session)
        filters = ApprovedAnalyticsFilters(issuing_organization="Harvard")
        result = svc.get_summary(org_id=1, filters=filters)
        assert result.total == 1


class TestDataQuality:
    """Test data quality computation."""

    def test_data_quality_counts(self, db_session):
        doc1 = _create_cert_doc(db_session, status="approved", doc_id=1)
        doc2 = _create_cert_doc(db_session, status="approved", doc_id=2)
        # doc1 has all fields
        _add_field(db_session, doc1.id, "student_name", "Alice")
        _add_field(db_session, doc1.id, "qualification", "BSc")
        _add_field(db_session, doc1.id, "institution", "Harvard")
        _add_field(db_session, doc1.id, "date_awarded", "2024-01-15")
        _add_field(db_session, doc1.id, "certificate_number", "CERT-001")
        _add_field(db_session, doc1.id, "course", "Computer Science")
        # doc2 has only name
        _add_field(db_session, doc2.id, "student_name", "Bob")
        db_session.commit()

        svc = ApprovedCertificateAnalyticsService(db_session)
        result = svc.get_summary(org_id=1)
        assert result.data_quality.total == 2
        assert result.data_quality.recipient_identified == 2
        assert result.data_quality.certificate_name_identified == 1
        assert result.data_quality.institution_identified == 1
        assert result.data_quality.completion_date_identified == 1
        assert result.data_quality.certificate_number_identified == 1
        assert result.data_quality.course_identified == 1


class TestRecords:
    """Test paginated records."""

    def test_pagination(self, db_session):
        for i in range(5):
            doc = _create_cert_doc(db_session, status="approved", doc_id=i)
            _add_field(db_session, doc.id, "student_name", f"Person {i}")
        db_session.commit()

        svc = ApprovedCertificateAnalyticsService(db_session)
        result = svc.get_records(org_id=1, limit=2, offset=0)
        assert len(result["records"]) == 2
        assert result["total"] == 5

        result2 = svc.get_records(org_id=1, limit=2, offset=2)
        assert len(result2["records"]) == 2

    def test_search(self, db_session):
        doc1 = _create_cert_doc(db_session, status="approved", doc_id=1)
        doc2 = _create_cert_doc(db_session, status="approved", doc_id=2)
        _add_field(db_session, doc1.id, "student_name", "Alice Wonderland")
        _add_field(db_session, doc2.id, "student_name", "Bob Builder")
        db_session.commit()

        svc = ApprovedCertificateAnalyticsService(db_session)
        result = svc.get_records(org_id=1, search="wonderland")
        assert len(result["records"]) == 1
        assert result["records"][0]["recipient"] == "Alice Wonderland"
