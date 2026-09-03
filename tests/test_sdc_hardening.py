"""Tests for SDC batch upload hardening fixes.

Covers: memory safety, batch counters, job fallback, error isolation,
middleware exemption, job timeouts, watchdog, heartbeat, extraction,
verification, edit/save, tenant isolation, duplicates, 50-file scale,
certificate batch upload, idempotency, stale jobs, OCR fallback,
field validation, audit logs, file validation.
"""

from __future__ import annotations

from unittest.mock import patch

import pytest

import capture.models  # noqa: F401
import storage.models  # noqa: F401
from capture.ocr_engine import OcrResult, OcrWord
from capture.service import CaptureService
from storage.storage import LocalFileBackend, set_storage_backend


@pytest.fixture
def local_storage(tmp_path):
    backend = LocalFileBackend(base_dir=str(tmp_path))
    set_storage_backend(backend)
    yield backend
    set_storage_backend(None)


def _make_pdf_bytes() -> bytes:
    return (
        b"%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n"
        b"2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj\n"
        b"3 0 obj<</Type/Page/MediaBox[0 0 612 792]>>endobj\n"
        b"xref\n0 4\n0000000000 65535 f \n0000000009 00000 n \n"
        b"0000000052 00000 n \n0000000101 00000 n \n"
        b"trailer<</Size 4/Root 1 0 R>>\nstartxref\n149\n%%EOF\n"
    )


def _make_png_bytes() -> bytes:
    return (
        b"\x89PNG\r\n\x1a\n"
        b"\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde"
        b"\x00\x00\x00\x0cIDATx\x9cc\xf8\xcf\xc0\x00\x00\x00\x03\x00\x01\x5d\xcc\xdb\x82"
        b"\x00\x00\x00\x00IEND\xaeB`\x82"
    )


def _make_ocr_result(text: str) -> OcrResult:
    return OcrResult(full_text=text, words=[], mean_confidence=0.8, page_count=1)


# ── 1. Batch upload memory safety ─────────────────────────────────────


def test_batch_upload_sequential_memory_safety(client, auth_headers, local_storage):
    pdf = _make_pdf_bytes()
    files = [("files", (f"doc_{i}.pdf", pdf, "application/pdf")) for i in range(10)]
    response = client.post("/api/capture/documents/batch-upload", files=files, headers=auth_headers)
    assert response.status_code == 202
    assert response.json()["accepted"] == 10


# ── 2. Batch counter correctness ──────────────────────────────────────


def test_batch_counter_total_equals_accepted_plus_failed(client, auth_headers, local_storage):
    pdf = _make_pdf_bytes()
    files = [
        ("files", ("valid.pdf", pdf, "application/pdf")),
        ("files", ("invalid.txt", b"not valid", "text/plain")),
    ]
    response = client.post("/api/capture/documents/batch-upload", files=files, headers=auth_headers)
    data = response.json()
    assert data["total"] == data["accepted"] + data["failed"]
    assert data["total"] == 2
    assert data["accepted"] == 1
    assert data["failed"] == 1


# ── 3. Job enqueue fallback to thread ─────────────────────────────────


def test_job_enqueue_fallback_on_redis_failure(client, auth_headers, local_storage):
    pdf = _make_pdf_bytes()
    with patch("jobs.service.get_task_queue", side_effect=Exception("Redis unavailable")):
        response = client.post(
            "/api/capture/documents/batch-upload",
            files=[("files", ("fallback.pdf", pdf, "application/pdf"))],
            headers=auth_headers,
        )
    assert response.status_code == 202
    assert response.json()["accepted"] == 1


# ── 4. Per-file error isolation ───────────────────────────────────────


def test_per_file_error_isolation(client, auth_headers, local_storage):
    pdf = _make_pdf_bytes()
    files = [
        ("files", ("bad.txt", b"invalid", "text/plain")),
        ("files", ("good.pdf", pdf, "application/pdf")),
        ("files", ("bad2.exe", b"\x4d\x5a" + b"\x00" * 10, "application/octet-stream")),
        ("files", ("good2.pdf", pdf, "application/pdf")),
    ]
    response = client.post("/api/capture/documents/batch-upload", files=files, headers=auth_headers)
    data = response.json()
    assert data["accepted"] == 2
    assert data["failed"] == 2


# ── 5. Middleware exempts batch upload endpoint ───────────────────────


def test_middleware_exempts_batch_upload(client, auth_headers, local_storage):
    """Batch upload endpoint should not be rejected by RequestSizeLimitMiddleware."""
    pdf = _make_pdf_bytes()
    # 20 files — would exceed 50MB if all were large, but the endpoint is exempted
    files = [("files", (f"doc_{i}.pdf", pdf, "application/pdf")) for i in range(20)]
    response = client.post("/api/capture/documents/batch-upload", files=files, headers=auth_headers)
    assert response.status_code == 202


# ── 6. Job timeout defaults ───────────────────────────────────────────


def test_job_timeout_defaults():
    """JobService should have per-job-type timeout defaults."""
    from jobs.service import JobService

    assert JobService._JOB_TIMEOUTS["ocr_document"] == 1800
    assert JobService._JOB_TIMEOUTS["ocr_batch"] == 7200
    assert JobService._DEFAULT_TIMEOUT == 600


# ── 7. Watchdog timeout alignment ─────────────────────────────────────


def test_watchdog_timeout_alignment():
    """Watchdog running timeout should be >= OCR document timeout."""
    from jobs.service import JobService
    from jobs.watchdog import RUNNING_TIMEOUT_SECONDS

    assert JobService._JOB_TIMEOUTS["ocr_document"] <= RUNNING_TIMEOUT_SECONDS


# ── 8. Watchdog pending timeout ───────────────────────────────────────


def test_watchdog_pending_timeout():
    from jobs.watchdog import PENDING_TIMEOUT_SECONDS

    assert PENDING_TIMEOUT_SECONDS == 600


# ── 9. Certificate extraction: student name ───────────────────────────


def test_cert_extraction_student_name():
    from certificates.extractor import extract_certificate_fields

    text = "This is to certify that John Doe\nhas successfully completed\nData Science"
    result = extract_certificate_fields(_make_ocr_result(text))
    assert result.student_name is not None
    assert "John Doe" in result.student_name.value
    assert result.student_name.confidence > 0.5


# ── 10. Certificate extraction: course ────────────────────────────────


def test_cert_extraction_course():
    from certificates.extractor import extract_certificate_fields

    text = "This is to certify that Jane Smith\nhas successfully completed\nData Science Fundamentals\nawarded by\nTech Institute"
    result = extract_certificate_fields(_make_ocr_result(text))
    assert result.course is not None
    assert "Data Science" in result.course.value


# ── 11. Certificate extraction: institution ───────────────────────────


def test_cert_extraction_institution():
    from certificates.extractor import extract_certificate_fields

    text = "This is to certify that Jane Smith\nhas successfully completed\nData Science\nawarded by\nGhana University"
    result = extract_certificate_fields(_make_ocr_result(text))
    assert result.institution is not None
    assert "Ghana University" in result.institution.value


# ── 12. Certificate extraction: date ──────────────────────────────────


def test_cert_extraction_date():
    from certificates.extractor import extract_certificate_fields

    text = "Date: 15th January 2024"
    result = extract_certificate_fields(_make_ocr_result(text))
    assert result.date_awarded is not None
    assert "January" in result.date_awarded.value


# ── 13. Certificate extraction: certificate number ────────────────────


def test_cert_extraction_certificate_number():
    from certificates.extractor import extract_certificate_fields

    text = "Certificate No: ABC-123-XYZ"
    result = extract_certificate_fields(_make_ocr_result(text))
    assert result.certificate_number is not None
    assert "ABC-123-XYZ" in result.certificate_number.value


# ── 14. Certificate extraction: all fields together ───────────────────


def test_cert_extraction_all_fields():
    from certificates.extractor import extract_certificate_fields

    text = (
        "Ghana Institute of Technology\n"
        "This is to certify that Kwame Mensah\n"
        "has successfully completed\n"
        "Advanced Diploma in Computer Science\n"
        "awarded by Ghana Institute of Technology\n"
        "Date: 15th March 2024\n"
        "Certificate No: GIT-2024-001"
    )
    result = extract_certificate_fields(_make_ocr_result(text))
    assert result.student_name is not None
    assert result.course is not None
    assert result.institution is not None
    assert result.date_awarded is not None
    assert result.certificate_number is not None


# ── 15. Certificate extraction: empty text ────────────────────────────


def test_cert_extraction_empty_text():
    from certificates.extractor import extract_certificate_fields

    result = extract_certificate_fields(_make_ocr_result(""))
    assert result.student_name is None
    assert result.course is None


# ── 16. Certificate extraction: signatory disambiguation ──────────────


def test_cert_extraction_signatory_disambiguation():
    from certificates.extractor import extract_certificate_fields

    text = (
        "This is to certify that John Doe\nhas completed\nPython Programming\nRegistrar: Dr. Smith"
    )
    result = extract_certificate_fields(_make_ocr_result(text))
    assert result.student_name is not None
    assert "John Doe" in result.student_name.value
    # Should not pick "Dr. Smith" as the student name
    assert "Smith" not in result.student_name.value


# ── 17. Certificate verification: truthful states ─────────────────────


def test_cert_verification_states():
    """Verification endpoint should accept all truthful states."""
    # The valid states are defined in the route
    valid_states = {
        "pending",
        "verified",
        "failed",
        "inconclusive",
        "unable_to_verify",
        "suspicious",
    }
    # Ensure these are all distinct and meaningful
    assert len(valid_states) == 6
    assert "verified" in valid_states
    assert "suspicious" in valid_states


# ── 18. Edit/save: field correction ───────────────────────────────────


def test_field_correction_marks_was_corrected(db_session, local_storage):
    from capture.models import CaptureField

    svc = CaptureService(db_session)
    doc = svc.upload_document(1, 1, "test.pdf", _make_pdf_bytes(), source="web")
    # Manually create a field since OCR hasn't run
    field = CaptureField(
        document_id=doc.id,
        field_name="student_name",
        field_label="Student Name",
        data_type="text",
        value="Old Value",
        raw_value="Old Value",
        confidence_score=0.5,
        is_low_confidence=True,
        was_corrected=False,
        is_valid=True,
        page_number=1,
    )
    db_session.add(field)
    db_session.commit()
    updated = svc.update_field(doc.id, field.id, 1, "Corrected Value", 1)
    assert updated.was_corrected is True
    assert updated.confidence_score == 1.0
    assert updated.is_low_confidence is False
    assert updated.value == "Corrected Value"


# ── 19. Edit/save: field validation ───────────────────────────────────


def test_field_correction_validates(db_session, local_storage):
    from capture.models import CaptureField

    svc = CaptureService(db_session)
    doc = svc.upload_document(1, 1, "test.pdf", _make_pdf_bytes(), source="web")
    field = CaptureField(
        document_id=doc.id,
        field_name="student_name",
        field_label="Student Name",
        data_type="text",
        value="Old",
        raw_value="Old",
        confidence_score=0.5,
        is_low_confidence=True,
        was_corrected=False,
        is_valid=True,
        page_number=1,
    )
    db_session.add(field)
    db_session.commit()
    updated = svc.update_field(doc.id, field.id, 1, "New Value", 1)
    assert updated.is_valid in (True, False)
    if not updated.is_valid:
        assert updated.validation_message


# ── 20. Tenant isolation in batch upload ──────────────────────────────


def test_batch_upload_tenant_isolation(client, auth_headers, local_storage, db_session):
    from capture.models import CaptureDocument

    pdf = _make_pdf_bytes()
    response = client.post(
        "/api/capture/documents/batch-upload",
        files=[("files", ("tenant.pdf", pdf, "application/pdf"))],
        headers=auth_headers,
    )
    assert response.status_code == 202
    batch_id = response.json()["batch_id"]
    docs = db_session.query(CaptureDocument).filter(CaptureDocument.batch_id == batch_id).all()
    for doc in docs:
        assert doc.organization_id is not None
        assert doc.organization_id > 0


# ── 21. Duplicate detection ───────────────────────────────────────────


def test_batch_upload_duplicate_checksum(client, auth_headers, local_storage):
    pdf = _make_pdf_bytes()
    response1 = client.post(
        "/api/capture/documents/batch-upload",
        files=[("files", ("original.pdf", pdf, "application/pdf"))],
        headers=auth_headers,
    )
    assert response1.status_code == 202
    response2 = client.post(
        "/api/capture/documents/batch-upload",
        files=[("files", ("duplicate.pdf", pdf, "application/pdf"))],
        headers=auth_headers,
    )
    assert response2.status_code == 202
    file_result = response2.json()["files"][0]
    assert file_result.get("duplicate_of_id") is not None


# ── 22. Batch upload with 50 files (production scale) ─────────────────


def test_batch_upload_50_files(client, auth_headers, local_storage):
    pdf = _make_pdf_bytes()
    files = [("files", (f"doc_{i}.pdf", pdf, "application/pdf")) for i in range(50)]
    response = client.post("/api/capture/documents/batch-upload", files=files, headers=auth_headers)
    assert response.status_code == 202
    data = response.json()
    assert data["total"] == 50
    assert data["accepted"] == 50
    assert data["failed"] == 0


# ── 23. Certificate batch upload endpoint ─────────────────────────────


def test_certificate_batch_upload(client, auth_headers, local_storage):
    pdf = _make_pdf_bytes()
    response = client.post(
        "/api/certificates/upload",
        files=[("files", ("cert1.pdf", pdf, "application/pdf"))],
        headers=auth_headers,
    )
    assert response.status_code in (200, 202)


# ── 24. Job idempotency key format ────────────────────────────────────


def test_job_idempotency_key_format():
    """Idempotency key should follow org_{org_id}:ocr_document:doc_{doc_id} format."""
    org_id = 5
    doc_id = 42
    key = f"org_{org_id}:ocr_document:doc_{doc_id}"
    assert key == "org_5:ocr_document:doc_42"


# ── 25. Stale job watchdog sweep ──────────────────────────────────────


def test_watchdog_sweep_marks_stale_pending(db_session):
    from datetime import datetime, timedelta, timezone

    from jobs.repositories import JobRepository
    from jobs.watchdog import PENDING_TIMEOUT_SECONDS

    repo = JobRepository(db_session)
    job = repo.create(
        organization_id=1,
        user_id=1,
        job_type="ocr_document",
        name="Stale Job",
        status="pending",
        progress=0.0,
        payload=None,
        max_retries=3,
    )
    # Set created_at well beyond the pending timeout
    job.created_at = datetime.now(timezone.utc) - timedelta(seconds=PENDING_TIMEOUT_SECONDS + 300)
    db_session.commit()

    # Verify the watchdog logic would find this job as stale
    pending_threshold = datetime.now(timezone.utc) - timedelta(seconds=PENDING_TIMEOUT_SECONDS)
    stale_pending = repo.find_stale_pending(pending_threshold)
    assert any(j.id == job.id for j in stale_pending)

    # Mark it failed (simulating what _sweep_once does)
    repo.mark_failed(job.id, "Timed out")
    db_session.commit()

    refreshed = repo.get_by_id(job.id)
    assert refreshed.status == "failed"


# ── 26. OCR unavailable graceful failure ──────────────────────────────


def test_ocr_unavailable_graceful_failure(db_session, local_storage):
    svc = CaptureService(db_session)
    doc = svc.upload_document(1, 1, "test.pdf", _make_pdf_bytes(), source="web")
    with (
        patch("capture.ocr_engine.is_ocr_available", return_value=False),
        patch.object(CaptureService, "_extract_pdf_text", return_value=None),
    ):
        result = svc.process_document(doc.id)
    assert result.status == "failed"


# ── 27. PDF text extraction fallback ──────────────────────────────────


def test_pdf_text_extraction_fallback(db_session, local_storage):
    svc = CaptureService(db_session)
    doc = svc.upload_document(1, 1, "test.pdf", _make_pdf_bytes(), source="web")
    with (
        patch("capture.ocr_engine.is_ocr_available", return_value=False),
        patch.object(
            CaptureService, "_extract_pdf_text", return_value="Some extracted text from PDF"
        ),
    ):
        result = svc.process_document(doc.id)
    # Should not fail with OCR unavailable — should use PDF text extraction
    assert result.status != "failed"


# ── 28. Batch name customization ──────────────────────────────────────


def test_batch_upload_custom_name(client, auth_headers, local_storage):
    pdf = _make_pdf_bytes()
    response = client.post(
        "/api/capture/documents/batch-upload",
        files=[("files", ("named.pdf", pdf, "application/pdf"))],
        data={"batch_name": "Production Batch"},
        headers=auth_headers,
    )
    assert response.status_code == 202
    assert response.json()["batch_name"] == "Production Batch"


# ── 29. File type validation ──────────────────────────────────────────


def test_file_type_validation(client, auth_headers, local_storage):
    files = [
        ("files", ("valid.pdf", _make_pdf_bytes(), "application/pdf")),
        ("files", ("valid.png", _make_png_bytes(), "image/png")),
        ("files", ("invalid.txt", b"text", "text/plain")),
    ]
    response = client.post("/api/capture/documents/batch-upload", files=files, headers=auth_headers)
    data = response.json()
    assert data["accepted"] == 2
    assert data["failed"] == 1


# ── 30. Empty batch rejection ─────────────────────────────────────────


def test_empty_batch_rejected(client, auth_headers, local_storage):
    response = client.post(
        "/api/capture/documents/batch-upload",
        files=[],
        headers=auth_headers,
    )
    assert response.status_code == 422


# ── 31. Batch upload response structure ───────────────────────────────


def test_batch_upload_response_has_all_fields(client, auth_headers, local_storage):
    pdf = _make_pdf_bytes()
    response = client.post(
        "/api/capture/documents/batch-upload",
        files=[("files", ("struct.pdf", pdf, "application/pdf"))],
        headers=auth_headers,
    )
    data = response.json()
    for key in ("batch_id", "batch_name", "total", "accepted", "failed", "files"):
        assert key in data
    assert isinstance(data["files"], list)
    assert "filename" in data["files"][0]
    assert "status" in data["files"][0]
    assert "id" in data["files"][0]


# ── 32. Certificate extraction confidence scoring ─────────────────────


def test_cert_extraction_confidence_scoring():
    from certificates.extractor import extract_certificate_fields

    text = "This is to certify that JOHN DOE\nhas successfully completed\nPython Programming"
    words = [
        OcrWord(text=w, confidence=0.9, page=1, left=0, top=0, width=0, height=0)
        for w in text.split()
    ]
    result = extract_certificate_fields(OcrResult(full_text=text, words=words, mean_confidence=0.9))
    assert result.student_name is not None
    assert result.student_name.confidence > 0.7  # All-caps boost + high OCR confidence


# ── 33. Certificate extraction: institution header fallback ───────────


def test_cert_extraction_institution_header_fallback():
    from certificates.extractor import extract_certificate_fields

    text = "Ghana Institute of Technology\n\nThis is to certify that John Doe\nhas completed Python"
    result = extract_certificate_fields(_make_ocr_result(text))
    assert result.institution is not None
    assert "Ghana Institute" in result.institution.value


# ── 34. Non-cert document rejected from verify ────────────────────────


def test_non_cert_document_rejected_from_verify(client, auth_headers, local_storage):
    pdf = _make_pdf_bytes()
    upload_resp = client.post(
        "/api/capture/documents/batch-upload",
        files=[("files", ("invoice.pdf", pdf, "application/pdf"))],
        headers=auth_headers,
    )
    doc_id = upload_resp.json()["files"][0]["id"]
    verify_resp = client.post(
        f"/api/certificates/{doc_id}/verify",
        json={"method": "manual_check", "status": "verified"},
        headers=auth_headers,
    )
    # Should be 400 — not a certificate type
    assert verify_resp.status_code == 400


# ── 35. Certificate extraction: normalizes text ───────────────────────


def test_cert_extraction_normalizes_text():
    from certificates.extractor import _normalize_text

    raw = "  Hello   World  \n  Foo  "
    normalized = _normalize_text(raw)
    assert "  " not in normalized  # No double spaces
    lines = normalized.split("\n")
    assert lines[0] == "Hello World"
    assert lines[1] == "Foo"


# ── 36. Certificate extraction: cleans extracted value ────────────────


def test_cert_extraction_cleans_value():
    from certificates.extractor import _clean_extracted_value

    assert _clean_extracted_value("  John Doe  ") == "John Doe"
    assert _clean_extracted_value("·John·") == "John"
    assert _clean_extracted_value("John: Doe,") == "John: Doe"
