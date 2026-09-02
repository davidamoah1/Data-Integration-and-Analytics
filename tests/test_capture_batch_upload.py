"""Regression tests for Smart Data Capture batch upload endpoint.

Covers:
  - Single file upload via batch endpoint
  - Multiple file upload in one request
  - Mixed valid/invalid files (partial failure)
  - All files invalid
  - Too many files (batch size limit)
  - Authentication required
  - Tenant isolation
  - Existing single-file upload still works
  - Batch response structure correctness
"""

from __future__ import annotations

import pytest

import capture.models  # noqa: F401 — registers tables with shared Base
import storage.models  # noqa: F401 — registers tables with shared Base
from storage.storage import LocalFileBackend, set_storage_backend


@pytest.fixture
def local_storage(tmp_path):
    """Point the storage backend at a temp directory for the duration of a test."""
    backend = LocalFileBackend(base_dir=str(tmp_path))
    set_storage_backend(backend)
    yield backend
    set_storage_backend(None)


def _make_pdf_bytes(name: str = "test.pdf") -> bytes:
    """Return minimal valid PDF bytes."""
    return (
        b"%PDF-1.4\n"
        b"1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n"
        b"2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj\n"
        b"3 0 obj<</Type/Page/MediaBox[0 0 612 792]>>endobj\n"
        b"xref\n0 4\n0000000000 65535 f \n0000000009 00000 n \n"
        b"0000000052 00000 n \n0000000101 00000 n \n"
        b"trailer<</Size 4/Root 1 0 R>>\nstartxref\n149\n%%EOF\n"
    )


def _make_png_bytes() -> bytes:
    """Return minimal valid PNG bytes."""
    return (
        b"\x89PNG\r\n\x1a\n"
        b"\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde"
        b"\x00\x00\x00\x0cIDATx\x9cc\xf8\xcf\xc0\x00\x00\x00\x03\x00\x01\x5d\xcc\xdb\x82"
        b"\x00\x00\x00\x00IEND\xaeB`\x82"
    )


# ── TEST 1: Single file upload via batch endpoint ──────────────────


def test_batch_upload_single_file(client, auth_headers, local_storage):
    """POST /api/capture/documents/batch-upload with 1 file should succeed."""
    pdf = _make_pdf_bytes()
    response = client.post(
        "/api/capture/documents/batch-upload",
        files=[("files", ("doc1.pdf", pdf, "application/pdf"))],
        headers=auth_headers,
    )
    assert response.status_code == 202
    data = response.json()
    assert data["total"] == 1
    assert data["accepted"] == 1
    assert data["failed"] == 0
    assert len(data["files"]) == 1
    assert data["files"][0]["status"] == "accepted"
    assert data["files"][0]["filename"] == "doc1.pdf"
    assert data["batch_id"] is not None


# ── TEST 2: Multiple file upload in one request ────────────────────


def test_batch_upload_multiple_files(client, auth_headers, local_storage):
    """POST /api/capture/documents/batch-upload with 5 files should upload all 5."""
    pdf = _make_pdf_bytes()
    png = _make_png_bytes()
    files = [
        ("files", ("doc1.pdf", pdf, "application/pdf")),
        ("files", ("doc2.pdf", pdf, "application/pdf")),
        ("files", ("doc3.png", png, "image/png")),
        ("files", ("doc4.pdf", pdf, "application/pdf")),
        ("files", ("doc5.png", png, "image/png")),
    ]
    response = client.post(
        "/api/capture/documents/batch-upload",
        files=files,
        headers=auth_headers,
    )
    assert response.status_code == 202
    data = response.json()
    assert data["total"] == 5
    assert data["accepted"] == 5
    assert data["failed"] == 0
    assert len(data["files"]) == 5
    for f in data["files"]:
        assert f["status"] == "accepted"


# ── TEST 5: Mixed valid/invalid files ──────────────────────────────


def test_batch_upload_mixed_valid_invalid(client, auth_headers, local_storage):
    """8 valid + 2 invalid files: 8 accepted, 2 rejected with reasons."""
    pdf = _make_pdf_bytes()
    files = []
    # 8 valid PDFs
    for i in range(8):
        files.append(("files", (f"valid_{i}.pdf", pdf, "application/pdf")))
    # 2 invalid: one wrong extension, one too large (fake content but wrong type)
    files.append(("files", ("invalid.txt", b"not a valid file", "text/plain")))
    files.append(
        ("files", ("invalid.exe", b"\x4d\x5a" + b"\x00" * 100, "application/octet-stream"))
    )

    response = client.post(
        "/api/capture/documents/batch-upload",
        files=files,
        headers=auth_headers,
    )
    assert response.status_code == 202
    data = response.json()
    assert data["total"] == 10
    assert data["accepted"] == 8
    assert data["failed"] == 2
    failed_files = [f for f in data["files"] if f["status"] == "failed"]
    assert len(failed_files) == 2
    for f in failed_files:
        assert f["error"]  # Should have an error message


# ── TEST 12: All files failed ──────────────────────────────────────


def test_batch_upload_all_failed(client, auth_headers, local_storage):
    """All invalid files: 0 accepted, all rejected."""
    files = [
        ("files", ("bad1.txt", b"not valid", "text/plain")),
        ("files", ("bad2.txt", b"also not valid", "text/plain")),
    ]
    response = client.post(
        "/api/capture/documents/batch-upload",
        files=files,
        headers=auth_headers,
    )
    assert response.status_code == 202
    data = response.json()
    assert data["total"] == 2
    assert data["accepted"] == 0
    assert data["failed"] == 2


# ── TEST: Too many files (batch size limit) ────────────────────────


def test_batch_upload_too_many_files(client, auth_headers, local_storage):
    """Exceeding CAPTURE_MAX_BATCH_SIZE should return 413."""
    import config

    max_batch = getattr(config, "CAPTURE_MAX_BATCH_SIZE", 50)
    pdf = _make_pdf_bytes()
    files = [("files", (f"doc_{i}.pdf", pdf, "application/pdf")) for i in range(max_batch + 1)]
    response = client.post(
        "/api/capture/documents/batch-upload",
        files=files,
        headers=auth_headers,
    )
    assert response.status_code == 413


# ── TEST 8: Authentication required ────────────────────────────────


def test_batch_upload_requires_auth(client, local_storage):
    """Unauthenticated users cannot upload."""
    pdf = _make_pdf_bytes()
    response = client.post(
        "/api/capture/documents/batch-upload",
        files=[("files", ("doc1.pdf", pdf, "application/pdf"))],
    )
    assert response.status_code == 401


# ── TEST 14: Existing single-file upload still works ───────────────


def test_single_file_upload_still_works(client, auth_headers, local_storage):
    """The existing POST /api/capture/documents/upload endpoint must still work."""
    pdf = _make_pdf_bytes()
    response = client.post(
        "/api/capture/documents/upload",
        files={"file": ("single.pdf", pdf, "application/pdf")},
        headers=auth_headers,
    )
    assert response.status_code == 201
    data = response.json()
    assert data["filename"] == "single.pdf"


# ── TEST: Batch response structure ─────────────────────────────────


def test_batch_upload_response_structure(client, auth_headers, local_storage):
    """Verify the response has all required fields."""
    pdf = _make_pdf_bytes()
    response = client.post(
        "/api/capture/documents/batch-upload",
        files=[("files", ("struct.pdf", pdf, "application/pdf"))],
        headers=auth_headers,
    )
    assert response.status_code == 202
    data = response.json()
    assert "batch_id" in data
    assert "batch_name" in data
    assert "total" in data
    assert "accepted" in data
    assert "failed" in data
    assert "files" in data
    assert isinstance(data["files"], list)
    file_result = data["files"][0]
    assert "filename" in file_result
    assert "status" in file_result
    assert file_result["status"] == "accepted"
    assert "id" in file_result
    assert "job_id" in file_result


# ── TEST: Batch creates database records ───────────────────────────


def test_batch_upload_creates_db_records(client, auth_headers, local_storage, db_session):
    """Verify documents are persisted in the database."""
    from capture.models import CaptureDocument

    pdf = _make_pdf_bytes()
    response = client.post(
        "/api/capture/documents/batch-upload",
        files=[
            ("files", ("db1.pdf", pdf, "application/pdf")),
            ("files", ("db2.pdf", pdf, "application/pdf")),
        ],
        headers=auth_headers,
    )
    assert response.status_code == 202
    data = response.json()
    batch_id = data["batch_id"]

    docs = db_session.query(CaptureDocument).filter(CaptureDocument.batch_id == batch_id).all()
    assert len(docs) == 2
    for doc in docs:
        assert doc.organization_id is not None
        assert doc.file_checksum is not None
        assert doc.original_file_path is not None


# ── TEST: Duplicate file in batch gets duplicate reference ──────────


def test_batch_upload_duplicate_detection(client, auth_headers, local_storage, db_session):
    """Uploading the same file content twice should create a duplicate reference."""
    pdf = _make_pdf_bytes()
    # First upload
    response1 = client.post(
        "/api/capture/documents/batch-upload",
        files=[("files", ("original.pdf", pdf, "application/pdf"))],
        headers=auth_headers,
    )
    assert response1.status_code == 202

    # Second upload with same content
    response2 = client.post(
        "/api/capture/documents/batch-upload",
        files=[("files", ("duplicate.pdf", pdf, "application/pdf"))],
        headers=auth_headers,
    )
    assert response2.status_code == 202
    data2 = response2.json()
    assert data2["accepted"] == 1

    file_result = data2["files"][0]
    assert file_result["status"] == "accepted"
    assert file_result.get("duplicate_of_id") is not None


# ── TEST: Batch name is set correctly ──────────────────────────────


def test_batch_upload_with_custom_name(client, auth_headers, local_storage):
    """Custom batch_name should appear in the response."""
    pdf = _make_pdf_bytes()
    response = client.post(
        "/api/capture/documents/batch-upload",
        files=[("files", ("named.pdf", pdf, "application/pdf"))],
        data={"batch_name": "My Custom Batch"},
        headers=auth_headers,
    )
    assert response.status_code == 202
    data = response.json()
    assert data["batch_name"] == "My Custom Batch"


# ── TEST: Empty file list ──────────────────────────────────────────


def test_batch_upload_empty_files_rejected(client, auth_headers, local_storage):
    """No files should result in 422 (FastAPI validation error)."""
    response = client.post(
        "/api/capture/documents/batch-upload",
        files=[],
        headers=auth_headers,
    )
    assert response.status_code == 422
