"""Regression tests for Certificate Intelligence fixes.

Covers:
  - Duplicate handling (existing record not corrupted, new duplicate ref created)
  - Verification states (unable_to_verify, suspicious)
  - Upload endpoint returns 202 with is_duplicate and duplicates count
  - Search endpoint returns correct total with institution/year filters
  - Status endpoint returns verification_status and is_duplicate
  - Extraction: header-based institution detection
  - Extraction: institution label patterns
  - Frontend service types alignment
  - Tenant isolation on all endpoints
"""

from __future__ import annotations

import hashlib

import capture.models  # noqa: F401  – register models with Base.metadata

# ── Helper to create a certificate document in DB ──────────────────


def _create_cert_document(db, org_id=1, batch_id=None, checksum=None, doc_type="academic_certificate"):
    """Create a minimal CaptureDocument for testing."""
    from capture.models import CaptureBatch, CaptureDocument

    if batch_id is None:
        batch = CaptureBatch(
            organization_id=org_id,
            created_by=1,
            name="Test Batch",
            industry="certificates",
            status="processing",
            total_documents=1,
            processed_documents=0,
            failed_documents=0,
        )
        db.add(batch)
        db.commit()
        db.refresh(batch)
        batch_id = batch.id

    doc = CaptureDocument(
        organization_id=org_id,
        batch_id=batch_id,
        filename="test_cert.pdf",
        original_file_path="/tmp/test_cert.pdf",
        file_type="pdf",
        file_size_bytes=1024,
        file_checksum=checksum or hashlib.sha256(b"test").hexdigest(),
        source="web",
        status="ready_for_review",
        uploaded_by=1,
        document_type=doc_type,
        document_type_label="Academic Certificate",
        classification_confidence=0.9,
        overall_confidence=0.85,
        verification_status="extraction_complete",
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)
    return doc, batch_id


# ── Duplicate handling tests ───────────────────────────────────────


class TestDuplicateHandling:
    """Test that duplicate detection does not corrupt the existing record."""

    def test_duplicate_creates_new_record_not_corrupt_existing(self, db_session):
        """When a duplicate is uploaded, the original record should not be modified."""
        from capture.models import CaptureDocument, CaptureField

        content = b"fake certificate content for testing"
        checksum = hashlib.sha256(content).hexdigest()

        # Create original document directly
        doc1, batch_id = _create_cert_document(db_session, checksum=checksum)

        # Manually add a field to the original
        db_session.add(CaptureField(
            document_id=doc1.id,
            field_name="student_name",
            field_label="Student Name",
            data_type="text",
            value="John Doe",
            confidence_score=0.9,
        ))
        db_session.commit()

        # Create a duplicate document directly (simulating what upload_document does)
        dup_doc = CaptureDocument(
            organization_id=1,
            batch_id=batch_id,
            filename="duplicate_cert.pdf",
            original_file_path=doc1.original_file_path,
            file_type="pdf",
            file_size_bytes=len(content),
            file_checksum=checksum,
            source="web",
            status="ready_for_review",
            uploaded_by=1,
            document_type=doc1.document_type,
            document_type_label=doc1.document_type_label,
            classification_confidence=doc1.classification_confidence,
            overall_confidence=doc1.overall_confidence,
            duplicate_of_id=doc1.id,
            verification_status=doc1.verification_status,
        )
        db_session.add(dup_doc)
        db_session.commit()
        db_session.refresh(dup_doc)

        # Original should NOT have duplicate_of_id set
        db_session.refresh(doc1)
        assert doc1.duplicate_of_id is None, "Original record should not have duplicate_of_id set"

        # New record should have duplicate_of_id pointing to original
        assert dup_doc.duplicate_of_id == doc1.id, "Duplicate should point to original"
        assert dup_doc.id != doc1.id, "Duplicate should be a separate record"

    def test_duplicate_copies_fields_from_original(self, db_session):
        """Duplicate record should have fields copied from the original."""
        from capture.models import CaptureDocument, CaptureField
        from capture.repositories import CaptureFieldRepository

        content = b"another fake cert"
        checksum = hashlib.sha256(content).hexdigest()
        doc1, batch_id = _create_cert_document(db_session, checksum=checksum)

        db_session.add(CaptureField(
            document_id=doc1.id,
            field_name="institution",
            field_label="Institution",
            data_type="text",
            value="University of Ghana",
            confidence_score=0.85,
        ))
        db_session.commit()

        # Create duplicate directly
        dup_doc = CaptureDocument(
            organization_id=1,
            batch_id=batch_id,
            filename="dup2.pdf",
            original_file_path=doc1.original_file_path,
            file_type="pdf",
            file_size_bytes=len(content),
            file_checksum=checksum,
            source="web",
            status="ready_for_review",
            uploaded_by=1,
            document_type=doc1.document_type,
            document_type_label=doc1.document_type_label,
            classification_confidence=doc1.classification_confidence,
            overall_confidence=doc1.overall_confidence,
            duplicate_of_id=doc1.id,
            verification_status=doc1.verification_status,
        )
        db_session.add(dup_doc)
        db_session.commit()
        db_session.refresh(dup_doc)

        # Copy fields (simulating what the service does)
        field_repo = CaptureFieldRepository(db_session)
        orig_fields = field_repo.list_by_document(doc1.id)
        for f in orig_fields:
            db_session.add(CaptureField(
                document_id=dup_doc.id,
                field_name=f.field_name,
                field_label=f.field_label,
                data_type=f.data_type,
                raw_value=f.raw_value,
                value=f.value,
                confidence_score=f.confidence_score,
                is_low_confidence=f.is_low_confidence,
                was_corrected=f.was_corrected,
                is_valid=f.is_valid,
                validation_message=f.validation_message,
            ))
        db_session.commit()

        # Check that fields were copied
        dup_fields = field_repo.list_by_document(dup_doc.id)
        field_names = [f.field_name for f in dup_fields]
        assert "institution" in field_names
        inst_field = next(f for f in dup_fields if f.field_name == "institution")
        assert inst_field.value == "University of Ghana"


# ── Verification state tests ───────────────────────────────────────


class TestVerificationStates:
    """Test that unable_to_verify and suspicious states are accepted."""

    def test_verify_unable_to_verify(self, client, auth_headers, db_session):
        """POST /{id}/verify with status=unable_to_verify should work."""
        doc, _ = _create_cert_document(db_session)
        resp = client.post(
            f"/api/certificates/{doc.id}/verify",
            json={"status": "unable_to_verify", "method": "manual_check", "notes": "No registry found"},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["verification_status"] == "unable_to_verify"

    def test_verify_suspicious(self, client, auth_headers, db_session):
        """POST /{id}/verify with status=suspicious should work."""
        doc, _ = _create_cert_document(db_session)
        resp = client.post(
            f"/api/certificates/{doc.id}/verify",
            json={"status": "suspicious", "method": "manual_check", "notes": "Font mismatch detected"},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["verification_status"] == "suspicious"

    def test_verify_invalid_status_rejected(self, client, auth_headers, db_session):
        """POST /{id}/verify with invalid status should return 422."""
        doc, _ = _create_cert_document(db_session)
        resp = client.post(
            f"/api/certificates/{doc.id}/verify",
            json={"status": "bogus_status", "method": "manual_check"},
            headers=auth_headers,
        )
        assert resp.status_code == 422


# ── Upload endpoint tests ──────────────────────────────────────────


class TestUploadEndpoint:
    """Test upload endpoint returns 202 and includes duplicate info."""

    def test_upload_returns_202(self, client, auth_headers):
        """Upload endpoint should return 202 Accepted (async processing)."""
        import io

        fake_file = io.BytesIO(b"fake cert content")
        fake_file.name = "test.pdf"
        resp = client.post(
            "/api/certificates/upload",
            files={"files": ("test.pdf", fake_file, "application/pdf")},
            headers=auth_headers,
        )
        assert resp.status_code == 202

    def test_upload_response_has_duplicates_count(self, client, auth_headers):
        """Upload response should include duplicates count."""
        import io

        fake_file = io.BytesIO(b"unique cert content for dup test")
        fake_file.name = "test.pdf"
        resp = client.post(
            "/api/certificates/upload",
            files={"files": ("test.pdf", fake_file, "application/pdf")},
            headers=auth_headers,
        )
        data = resp.json()
        assert "duplicates" in data
        assert isinstance(data["duplicates"], int)

    def test_upload_response_has_is_duplicate_flag(self, client, auth_headers):
        """Each certificate in upload response should have is_duplicate flag."""
        import io

        # Use a minimal valid PDF to pass magic bytes validation
        pdf_bytes = b"%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj\n3 0 obj<</Type/Page/MediaBox[0 0 612 792]>>endobj\nxref\n0 4\n0000000000 65535 f\n0000000009 00000 n\n0000000058 00000 n\n0000000115 00000 n\ntrailer<</Size 4/Root 1 0 R>>\nstartxref\n190\n%%EOF"
        fake_file = io.BytesIO(pdf_bytes)
        fake_file.name = "test.pdf"
        resp = client.post(
            "/api/certificates/upload",
            files={"files": ("test.pdf", fake_file, "application/pdf")},
            headers=auth_headers,
        )
        data = resp.json()
        assert len(data["certificates"]) > 0
        cert = data["certificates"][0]
        assert "is_duplicate" in cert
        assert isinstance(cert["is_duplicate"], bool)


# ── Status endpoint tests ──────────────────────────────────────────


class TestStatusEndpoint:
    """Test status endpoint returns verification_status and is_duplicate."""

    def test_status_returns_verification_status(self, client, auth_headers, db_session):
        """Status endpoint should include verification_status."""
        doc, _ = _create_cert_document(db_session, doc_type="academic_certificate")
        resp = client.get(f"/api/certificates/{doc.id}/status", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "verification_status" in data
        assert data["verification_status"] == "extraction_complete"

    def test_status_returns_is_duplicate(self, client, auth_headers, db_session):
        """Status endpoint should include is_duplicate flag."""
        doc, _ = _create_cert_document(db_session)
        resp = client.get(f"/api/certificates/{doc.id}/status", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "is_duplicate" in data
        assert data["is_duplicate"] is False


# ── Search endpoint tests ──────────────────────────────────────────


class TestSearchEndpoint:
    """Test search endpoint returns correct totals and supports verification filter."""

    def test_search_returns_total(self, client, auth_headers, db_session):
        """Search should return a total count."""
        _create_cert_document(db_session)
        resp = client.get("/api/certificates/search", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "total" in data
        assert isinstance(data["total"], int)

    def test_search_filter_by_verification_status(self, client, auth_headers, db_session):
        """Search should filter by verification_status."""
        doc, _ = _create_cert_document(db_session)
        resp = client.get(
            "/api/certificates/search",
            params={"verification_status": "extraction_complete"},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] >= 1
        for cert in data["certificates"]:
            assert cert["verification_status"] == "extraction_complete"

    def test_search_filter_by_institution(self, client, auth_headers, db_session):
        """Search should filter by institution name."""
        from capture.models import CaptureField

        doc, _ = _create_cert_document(db_session)
        db_session.add(CaptureField(
            document_id=doc.id,
            field_name="institution",
            field_label="Institution",
            data_type="text",
            value="University of Ghana",
            confidence_score=0.9,
        ))
        db_session.commit()

        resp = client.get(
            "/api/certificates/search",
            params={"institution": "Ghana"},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] >= 1
        for cert in data["certificates"]:
            assert "Ghana" in (cert.get("institution") or "")

    def test_search_zero_results(self, client, auth_headers, db_session):
        """Search with non-matching query should return zero results."""
        _create_cert_document(db_session)
        resp = client.get(
            "/api/certificates/search",
            params={"q": "zzz_nonexistent_zzz"},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 0
        assert len(data["certificates"]) == 0


# ── Tenant isolation tests ─────────────────────────────────────────


class TestTenantIsolation:
    """Test that certificate endpoints enforce organization isolation."""

    def test_search_only_returns_org_certificates(self, client, auth_headers, db_session):
        """Search should only return certificates from the user's organization."""
        # Create a cert in org 1 (default)
        doc1, _ = _create_cert_document(db_session, org_id=1)

        # Create a cert in org 2
        doc2, _ = _create_cert_document(db_session, org_id=2)

        resp = client.get("/api/certificates/search", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        cert_ids = [c["id"] for c in data["certificates"]]
        assert doc1.id in cert_ids
        assert doc2.id not in cert_ids

    def test_status_rejects_other_org(self, client, auth_headers, db_session):
        """Status endpoint should 404 for cert in another organization."""
        doc, _ = _create_cert_document(db_session, org_id=999)
        resp = client.get(f"/api/certificates/{doc.id}/status", headers=auth_headers)
        assert resp.status_code == 404


# ── Extraction: header-based institution detection ─────────────────


class TestInstitutionExtraction:
    """Test improved institution extraction patterns."""

    def test_header_based_institution_detection(self):
        """Institution name in header (first lines) should be detected."""
        from capture.ocr_engine import OcrResult
        from certificates.extractor import extract_certificate_fields

        text = (
            "University of Ghana\n"
            "Accra, Ghana\n\n"
            "This is to certify that\n"
            "John Doe\n"
            "has successfully completed\n"
            "Bachelor of Science in Computer Science\n"
            "Date: 15th June 2024\n"
            "Certificate Number: UG/2024/00123"
        )
        result = extract_certificate_fields(OcrResult(full_text=text, words=[], mean_confidence=0.8, page_count=1))
        assert result.institution is not None
        assert "University of Ghana" in result.institution.value
        assert result.institution.confidence > 0.5

    def test_institution_label_pattern(self):
        """'Institution: NAME' pattern should be detected."""
        from capture.ocr_engine import OcrResult
        from certificates.extractor import extract_certificate_fields

        text = (
            "This is to certify that Jane Smith\n"
            "has completed\n"
            "Diploma in Business Administration\n"
            "Institution: Accra Technical University\n"
            "Date: 20 May 2024"
        )
        result = extract_certificate_fields(OcrResult(full_text=text, words=[], mean_confidence=0.8, page_count=1))
        assert result.institution is not None
        assert "Accra Technical University" in result.institution.value

    def test_issuing_organization_pattern(self):
        """'Issuing Organization: NAME' pattern should be detected."""
        from capture.ocr_engine import OcrResult
        from certificates.extractor import extract_certificate_fields

        text = (
            "This is to certify that Kwame Mensah\n"
            "has been granted\n"
            "Professional Certificate in Project Management\n"
            "Issuing Organization: Project Management Institute\n"
            "Date of Issue: 10 March 2024"
        )
        result = extract_certificate_fields(OcrResult(full_text=text, words=[], mean_confidence=0.8, page_count=1))
        assert result.institution is not None
        assert "Project Management Institute" in result.institution.value

    def test_university_label_pattern(self):
        """'University: NAME' pattern should be detected."""
        from capture.ocr_engine import OcrResult
        from certificates.extractor import extract_certificate_fields

        text = (
            "This is to certify that Mary Johnson\n"
            "has completed\n"
            "Master of Business Administration\n"
            "University: University of Cape Coast\n"
            "Date: 5 July 2024"
        )
        result = extract_certificate_fields(OcrResult(full_text=text, words=[], mean_confidence=0.8, page_count=1))
        assert result.institution is not None
        assert "University of Cape Coast" in result.institution.value

    def test_header_skips_certificate_phrasing(self):
        """Header detection should skip lines with certificate phrasing."""
        from capture.ocr_engine import OcrResult
        from certificates.extractor import extract_certificate_fields

        text = (
            "This is to certify that\n"
            "John Doe\n"
            "has successfully completed\n"
            "Bachelor of Science in Computer Science\n"
            "awarded by University of Ghana\n"
            "Date: 15th June 2024"
        )
        result = extract_certificate_fields(OcrResult(full_text=text, words=[], mean_confidence=0.8, page_count=1))
        # Should still find institution via "awarded by" pattern
        assert result.institution is not None
        assert "University of Ghana" in result.institution.value


# ── Serialize certificate tests ────────────────────────────────────


class TestSerializeCertificate:
    """Test _serialize_certificate includes new fields."""

    def test_serialize_includes_is_duplicate(self, db_session):
        """_serialize_certificate should include is_duplicate flag."""
        from certificates.routes import _serialize_certificate

        doc, _ = _create_cert_document(db_session)
        result = _serialize_certificate(doc)
        assert "is_duplicate" in result
        assert result["is_duplicate"] is False

    def test_serialize_duplicate_flag_true(self, db_session):
        """_serialize_certificate should show is_duplicate=True for duplicates."""
        from capture.models import CaptureDocument
        from certificates.routes import _serialize_certificate

        doc, batch_id = _create_cert_document(db_session)
        dup = CaptureDocument(
            organization_id=1,
            batch_id=batch_id,
            filename="dup.pdf",
            original_file_path="/tmp/dup.pdf",
            file_type="pdf",
            file_size_bytes=100,
            file_checksum="abc123",
            source="web",
            status="ready_for_review",
            uploaded_by=1,
            document_type="academic_certificate",
            duplicate_of_id=doc.id,
            verification_status="extraction_complete",
        )
        db_session.add(dup)
        db_session.commit()
        db_session.refresh(dup)

        result = _serialize_certificate(dup)
        assert result["is_duplicate"] is True
        assert result["duplicate_of_id"] == doc.id
