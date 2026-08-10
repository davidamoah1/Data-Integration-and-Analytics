"""Regression tests for Smart Data Capture upload security fixes.

Covers:
  - ZIP bomb protection (entry count and total decompressed size caps)
  - CaptureError from a bad/oversized ZIP surfaces as HTTP 400, not 500
  - Corrupted ZIP surfaces as HTTP 400, not 500
"""

from __future__ import annotations

import io
import zipfile

import capture.models  # noqa: F401 — registers tables with shared Base
import pytest
import storage.models  # noqa: F401 — registers tables with shared Base

from capture.service import (
    ZIP_MAX_ENTRIES,
    ZIP_MAX_TOTAL_UNCOMPRESSED_MB,
    CaptureError,
    CaptureService,
)
from storage.storage import LocalFileBackend, set_storage_backend


@pytest.fixture
def local_storage(tmp_path):
    """Point the storage backend at a temp directory for the duration of a test."""
    backend = LocalFileBackend(base_dir=str(tmp_path))
    set_storage_backend(backend)
    yield backend
    set_storage_backend(None)


def _make_zip(entries: dict[str, bytes]) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for name, content in entries.items():
            zf.writestr(name, content)
    return buf.getvalue()


def test_zip_batch_rejects_too_many_entries(db_session, local_storage):
    svc = CaptureService(db_session)
    entries = {f"doc_{i}.pdf": b"%PDF-1.4 fake" for i in range(ZIP_MAX_ENTRIES + 1)}
    zip_bytes = _make_zip(entries)

    with pytest.raises(CaptureError, match="too many entries"):
        svc.upload_zip_batch(
            organization_id=1,
            user_id=1,
            zip_filename="batch.zip",
            zip_content=zip_bytes,
        )


def test_zip_batch_rejects_oversized_decompressed_content(db_session, local_storage):
    svc = CaptureService(db_session)
    # A single entry whose *declared* uncompressed size exceeds the cap.
    # Use highly compressible content so the zip itself stays small (zip-bomb shape).
    huge_content = b"0" * (ZIP_MAX_TOTAL_UNCOMPRESSED_MB * 1024 * 1024 + 1024)
    zip_bytes = _make_zip({"huge.pdf": huge_content})

    with pytest.raises(CaptureError, match="exceeding"):
        svc.upload_zip_batch(
            organization_id=1,
            user_id=1,
            zip_filename="bomb.zip",
            zip_content=zip_bytes,
        )


def test_zip_batch_accepts_valid_small_zip(db_session, local_storage):
    svc = CaptureService(db_session)
    zip_bytes = _make_zip(
        {
            "doc1.pdf": b"%PDF-1.4 fake pdf content",
            "doc2.png": b"\x89PNG\r\n\x1a\nfakepngcontent",
        }
    )

    batch, docs = svc.upload_zip_batch(
        organization_id=1,
        user_id=1,
        zip_filename="batch.zip",
        zip_content=zip_bytes,
    )

    assert batch.total_documents == 2
    assert len(docs) == 2


def test_upload_zip_route_returns_400_for_oversized_zip(client, auth_headers, local_storage):
    huge_content = b"0" * (ZIP_MAX_TOTAL_UNCOMPRESSED_MB * 1024 * 1024 + 1024)
    zip_bytes = _make_zip({"huge.pdf": huge_content})

    response = client.post(
        "/api/capture/batches/upload-zip",
        files={"file": ("bomb.zip", zip_bytes, "application/zip")},
        headers=auth_headers,
    )
    assert response.status_code == 400


def test_upload_zip_route_returns_400_for_corrupted_zip(client, auth_headers, local_storage):
    response = client.post(
        "/api/capture/batches/upload-zip",
        files={"file": ("bad.zip", b"not a real zip file", "application/zip")},
        headers=auth_headers,
    )
    assert response.status_code == 400
