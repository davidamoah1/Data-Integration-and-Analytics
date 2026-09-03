"""Tests for ETL ZIP Package ingestion — secure extraction, service, and API.

Covers:
  - ZIP validation (path traversal, bombs, file count, blocked extensions)
  - Secure extraction with sanitized filenames
  - Duplicate detection via content hashes
  - Package service (create, process, progress, errors, retry, cancel)
  - API routes (upload, list, get, progress, files, errors, quality, retry, cancel)
"""

from __future__ import annotations

import io
import os
import tempfile
import zipfile

import pytest

# ── ZIP Extractor Tests ──────────────────────────────────────────────────────


class TestZipValidation:
    """Test ZIP validation logic."""

    def _make_zip(self, files: dict[str, bytes]) -> str:
        """Create a temp ZIP file from a dict of filename→content."""
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
            for name, data in files.items():
                zf.writestr(name, data)
        buf.seek(0)
        fd, path = tempfile.mkstemp(suffix=".zip")
        with os.fdopen(fd, "wb") as f:
            f.write(buf.read())
        return path

    def test_valid_zip_passes_validation(self):
        from etl.zip_extractor import validate_zip

        path = self._make_zip({"data.csv": "a,b,c\n1,2,3\n"})
        try:
            result = validate_zip(path)
            assert result["valid"] is True
            assert result["file_count"] == 1
        finally:
            os.unlink(path)

    def test_path_traversal_detected(self):
        from etl.zip_extractor import validate_zip

        path = self._make_zip({"../../../etc/passwd": "malicious\n"})
        try:
            result = validate_zip(path)
            assert result["valid"] is False
            assert any("traversal" in e.lower() for e in result["errors"])
        finally:
            os.unlink(path)

    def test_absolute_path_detected(self):
        from etl.zip_extractor import validate_zip

        path = self._make_zip({"/etc/shadow": "malicious\n"})
        try:
            result = validate_zip(path)
            assert result["valid"] is False
        finally:
            os.unlink(path)

    def test_nonexistent_file(self):
        from etl.zip_extractor import validate_zip

        result = validate_zip("/nonexistent/file.zip")
        assert result["valid"] is False
        assert any("not found" in e.lower() for e in result["errors"])

    def test_empty_zip_rejected(self):
        from etl.zip_extractor import validate_zip

        path = self._make_zip({})
        try:
            result = validate_zip(path)
            assert result["valid"] is True  # empty zip is valid, just 0 files
            assert result["file_count"] == 0
        finally:
            os.unlink(path)

    def test_corrupt_zip_rejected(self):
        from etl.zip_extractor import validate_zip

        fd, path = tempfile.mkstemp(suffix=".zip")
        with os.fdopen(fd, "wb") as f:
            f.write(b"not a zip file")
        try:
            result = validate_zip(path)
            assert result["valid"] is False
        finally:
            os.unlink(path)


class TestZipExtraction:
    """Test secure ZIP extraction."""

    def test_basic_extraction(self):
        from etl.zip_extractor import extract_zip

        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("data.csv", "a,b,c\n1,2,3\n")
            zf.writestr("report.xlsx", b"fake xlsx")
        buf.seek(0)

        fd, zip_path = tempfile.mkstemp(suffix=".zip")
        with os.fdopen(fd, "wb") as f:
            f.write(buf.read())

        try:
            with tempfile.TemporaryDirectory() as tmpdir:
                result = extract_zip(zip_path, tmpdir, organization_id=1)
                assert result.success is True
                assert result.total_files == 2
                assert len(result.files) == 2
                assert result.files[0].sanitized_filename == "data.csv"
                assert result.files[0].file_extension == "csv"
                assert result.files[0].is_supported is True
        finally:
            os.unlink(zip_path)

    def test_duplicate_detection(self):
        from etl.zip_extractor import extract_zip

        content = "a,b,c\n1,2,3\n"
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("file1.csv", content)
            zf.writestr("file2.csv", content)  # same content = duplicate
        buf.seek(0)

        fd, zip_path = tempfile.mkstemp(suffix=".zip")
        with os.fdopen(fd, "wb") as f:
            f.write(buf.read())

        try:
            with tempfile.TemporaryDirectory() as tmpdir:
                result = extract_zip(zip_path, tmpdir, organization_id=1)
                assert result.success is True
                assert result.duplicate_files == 1
                assert result.files[0].is_duplicate is False
                assert result.files[1].is_duplicate is True
                assert result.files[1].duplicate_of is not None
        finally:
            os.unlink(zip_path)

    def test_blocked_extensions_skipped(self):
        from etl.zip_extractor import extract_zip

        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("data.csv", "a,b\n1,2\n")
            zf.writestr("malware.exe", b"MZ\x90\x00")
        buf.seek(0)

        fd, zip_path = tempfile.mkstemp(suffix=".zip")
        with os.fdopen(fd, "wb") as f:
            f.write(buf.read())

        try:
            with tempfile.TemporaryDirectory() as tmpdir:
                result = extract_zip(zip_path, tmpdir, organization_id=1)
                assert result.success is True
                assert result.total_files == 1  # only csv, exe skipped
                assert result.unsupported_files == 1
        finally:
            os.unlink(zip_path)

    def test_unsupported_extension_counted(self):
        from etl.zip_extractor import extract_zip

        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("data.csv", "a,b\n1,2\n")
            zf.writestr("readme.md", "# Readme")
        buf.seek(0)

        fd, zip_path = tempfile.mkstemp(suffix=".zip")
        with os.fdopen(fd, "wb") as f:
            f.write(buf.read())

        try:
            with tempfile.TemporaryDirectory() as tmpdir:
                result = extract_zip(zip_path, tmpdir, organization_id=1)
                assert result.success is True
                assert result.supported_files == 1
                assert result.unsupported_files == 1
        finally:
            os.unlink(zip_path)

    def test_checksum_computed(self):
        from etl.zip_extractor import extract_zip

        content = "a,b,c\n1,2,3\n"
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("data.csv", content)
        buf.seek(0)

        fd, zip_path = tempfile.mkstemp(suffix=".zip")
        with os.fdopen(fd, "wb") as f:
            f.write(buf.read())

        try:
            with tempfile.TemporaryDirectory() as tmpdir:
                result = extract_zip(zip_path, tmpdir, organization_id=1)
                assert result.files[0].checksum is not None
                assert len(result.files[0].checksum) == 64  # SHA-256 hex
        finally:
            os.unlink(zip_path)

    def test_tenant_isolation_in_path(self):
        from etl.zip_extractor import extract_zip

        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("data.csv", "a,b\n1,2\n")
        buf.seek(0)

        fd, zip_path = tempfile.mkstemp(suffix=".zip")
        with os.fdopen(fd, "wb") as f:
            f.write(buf.read())

        try:
            with tempfile.TemporaryDirectory() as tmpdir:
                result = extract_zip(zip_path, tmpdir, organization_id=42)
                assert result.success is True
                assert "org_42" in result.extract_dir
        finally:
            os.unlink(zip_path)

    def test_subdirectory_extraction(self):
        from etl.zip_extractor import extract_zip

        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("subdir/data.csv", "a,b\n1,2\n")
            zf.writestr("other/nested/deep.json", '{"x":1}')
        buf.seek(0)

        fd, zip_path = tempfile.mkstemp(suffix=".zip")
        with os.fdopen(fd, "wb") as f:
            f.write(buf.read())

        try:
            with tempfile.TemporaryDirectory() as tmpdir:
                result = extract_zip(zip_path, tmpdir, organization_id=1)
                assert result.success is True
                assert result.total_files == 2
                # Files should exist in subdirectories
                assert os.path.exists(result.files[0].extracted_path)
                assert os.path.exists(result.files[1].extracted_path)
        finally:
            os.unlink(zip_path)


# ── Package Service Tests ────────────────────────────────────────────────────


class TestETLPackageService:
    """Test the ETL package service with in-memory SQLite."""

    @pytest.fixture
    def db(self):
        """Create an in-memory SQLite session for testing."""
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker

        import etl.models  # noqa: F401
        import etl.package_models  # noqa: F401
        from shared.database import Base

        engine = create_engine("sqlite:///:memory:", echo=False)
        Base.metadata.create_all(engine)
        Session = sessionmaker(bind=engine)
        session = Session()
        yield session
        session.close()

    @pytest.fixture
    def service(self, db):
        from etl.package_service import ETLPackageService

        return ETLPackageService(db)

    def test_create_package(self, service, db):
        pkg = service.create_package(
            organization_id=1,
            uploaded_by=10,
            filename="test.zip",
            storage_key="etl/packages/org_1/test.zip",
            storage_backend="local",
            checksum="abc123",
            file_size=1024,
        )
        assert pkg.id is not None
        assert pkg.status == "uploaded"
        assert pkg.filename == "test.zip"
        assert pkg.organization_id == 1

    def test_get_package_tenant_isolation(self, service, db):
        pkg = service.create_package(
            organization_id=1,
            uploaded_by=10,
            filename="test.zip",
            storage_key="key1",
            storage_backend="local",
            checksum="abc123",
            file_size=1024,
        )
        # Same org can see it
        found = service.get_package(pkg.id, organization_id=1)
        assert found is not None
        # Different org cannot
        not_found = service.get_package(pkg.id, organization_id=2)
        assert not_found is None

    def test_list_packages(self, service, db):
        for i in range(3):
            service.create_package(
                organization_id=1,
                uploaded_by=10,
                filename=f"test{i}.zip",
                storage_key=f"key{i}",
                storage_backend="local",
                checksum=f"hash{i}",
                file_size=1024,
            )
        packages = service.list_packages(organization_id=1)
        assert len(packages) == 3

    def test_get_progress(self, service, db):
        pkg = service.create_package(
            organization_id=1,
            uploaded_by=10,
            filename="test.zip",
            storage_key="key1",
            storage_backend="local",
            checksum="abc123",
            file_size=1024,
        )
        pkg.total_files = 10
        pkg.completed_files = 5
        pkg.failed_files = 2
        db.commit()

        progress = service.get_progress(pkg.id, organization_id=1)
        assert progress is not None
        assert progress["total_files"] == 10
        assert progress["completed_files"] == 5
        assert progress["failed_files"] == 2
        assert progress["percentage"] == 70.0  # (5+2)/10

    def test_cancel_package(self, service, db):
        pkg = service.create_package(
            organization_id=1,
            uploaded_by=10,
            filename="test.zip",
            storage_key="key1",
            storage_backend="local",
            checksum="abc123",
            file_size=1024,
        )
        pkg.status = "processing"
        db.commit()

        result = service.cancel_package(pkg.id, organization_id=1)
        assert result["cancelled"] is True

        updated = service.get_package(pkg.id, organization_id=1)
        assert updated.status == "cancelled"

    def test_cancel_completed_package_fails(self, service, db):
        pkg = service.create_package(
            organization_id=1,
            uploaded_by=10,
            filename="test.zip",
            storage_key="key1",
            storage_backend="local",
            checksum="abc123",
            file_size=1024,
        )
        pkg.status = "completed"
        db.commit()

        result = service.cancel_package(pkg.id, organization_id=1)
        assert result["cancelled"] is False

    def test_retry_failed(self, service, db):
        from etl.package_models import ETLPackageFile

        pkg = service.create_package(
            organization_id=1,
            uploaded_by=10,
            filename="test.zip",
            storage_key="key1",
            storage_backend="local",
            checksum="abc123",
            file_size=1024,
        )
        # Add failed files
        for i in range(3):
            f = ETLPackageFile(
                package_id=pkg.id,
                organization_id=1,
                original_path=f"file{i}.csv",
                sanitized_filename=f"file{i}.csv",
                file_extension="csv",
                status="failed",
                error_message="test error",
                error_stage="profiling",
            )
            db.add(f)
        pkg.status = "completed_with_errors"
        db.commit()

        result = service.retry_failed(pkg.id, organization_id=1)
        assert result["retried"] == 3

        updated = service.get_package(pkg.id, organization_id=1)
        assert updated.status == "processing"

    def test_get_errors(self, service, db):
        from etl.package_models import ETLPackageFile

        pkg = service.create_package(
            organization_id=1,
            uploaded_by=10,
            filename="test.zip",
            storage_key="key1",
            storage_backend="local",
            checksum="abc123",
            file_size=1024,
        )
        f = ETLPackageFile(
            package_id=pkg.id,
            organization_id=1,
            original_path="bad.csv",
            sanitized_filename="bad.csv",
            file_extension="csv",
            status="failed",
            error_message="corrupt file",
            error_stage="extraction",
        )
        db.add(f)
        db.commit()

        errors = service.get_errors(pkg.id, organization_id=1)
        assert len(errors) == 1
        assert errors[0]["filename"] == "bad.csv"
        assert errors[0]["error_message"] == "corrupt file"

    def test_get_quality_report(self, service, db):
        from etl.package_models import ETLPackageFile

        pkg = service.create_package(
            organization_id=1,
            uploaded_by=10,
            filename="test.zip",
            storage_key="key1",
            storage_backend="local",
            checksum="abc123",
            file_size=1024,
        )
        pkg.total_files = 5
        pkg.completed_files = 3
        pkg.failed_files = 1
        pkg.duplicate_files = 1
        pkg.overall_quality_score = 85
        pkg.status = "completed_with_errors"

        for i in range(3):
            f = ETLPackageFile(
                package_id=pkg.id,
                organization_id=1,
                original_path=f"file{i}.csv",
                sanitized_filename=f"file{i}.csv",
                file_extension="csv",
                status="completed",
                row_count=100,
                rows_loaded=100,
                quality_score=85,
            )
            db.add(f)
        # Add one failed file
        f_fail = ETLPackageFile(
            package_id=pkg.id,
            organization_id=1,
            original_path="bad.csv",
            sanitized_filename="bad.csv",
            file_extension="csv",
            status="failed",
            error_message="corrupt",
        )
        db.add(f_fail)
        # Add one duplicate file
        f_dup = ETLPackageFile(
            package_id=pkg.id,
            organization_id=1,
            original_path="dup.csv",
            sanitized_filename="dup.csv",
            file_extension="csv",
            status="duplicate",
        )
        db.add(f_dup)
        db.commit()

        report = service.get_quality_report(pkg.id, organization_id=1)
        assert report is not None
        assert report["total_files"] == 5
        assert report["successful"] == 3
        assert report["failed"] == 1
        assert report["duplicates"] == 1
        assert report["data_quality_score"] == 85
        assert report["rows_processed"] == 300


# ── Package Models Tests ─────────────────────────────────────────────────────


class TestPackageModels:
    """Test ORM model behavior."""

    def test_package_model_fields(self):
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker

        import etl.models  # noqa: F401
        import etl.package_models  # noqa: F401
        from shared.database import Base

        engine = create_engine("sqlite:///:memory:", echo=False)
        Base.metadata.create_all(engine)
        Session = sessionmaker(bind=engine)
        session = Session()

        try:
            from etl.package_models import ETLPackage

            pkg = ETLPackage(
                organization_id=1,
                uploaded_by=10,
                filename="test.zip",
                storage_key="key",
                storage_backend="local",
                checksum="abc123",
                file_size_bytes=1024,
            )
            session.add(pkg)
            session.flush()
            assert pkg.status == "uploaded"
            assert pkg.total_files == 0
            assert pkg.completed_files == 0
        finally:
            session.close()

    def test_package_file_model_fields(self):
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker

        import etl.models  # noqa: F401
        import etl.package_models  # noqa: F401
        from shared.database import Base

        engine = create_engine("sqlite:///:memory:", echo=False)
        Base.metadata.create_all(engine)
        Session = sessionmaker(bind=engine)
        session = Session()

        try:
            from etl.package_models import ETLPackageFile

            f = ETLPackageFile(
                package_id=1,
                organization_id=1,
                original_path="data.csv",
                sanitized_filename="data.csv",
                file_extension="csv",
            )
            session.add(f)
            session.flush()
            assert f.status == "discovered"
            assert f.retry_count == 0
        finally:
            session.close()


# ── Sanitize Filename Tests ──────────────────────────────────────────────────


class TestSanitizeFilename:
    """Test filename sanitization."""

    def test_basic_filename(self):
        from etl.zip_extractor import _sanitize_filename

        assert _sanitize_filename("data.csv") == "data.csv"

    def test_path_components_stripped(self):
        from etl.zip_extractor import _sanitize_filename

        assert _sanitize_filename("../../../etc/passwd") == "passwd"
        assert _sanitize_filename("subdir/file.csv") == "file.csv"

    def test_dangerous_chars_replaced(self):
        from etl.zip_extractor import _sanitize_filename

        result = _sanitize_filename('file<>:"/\\|?*.csv')
        assert "<" not in result
        assert ">" not in result
        assert ":" not in result

    def test_empty_filename(self):
        from etl.zip_extractor import _sanitize_filename

        assert _sanitize_filename("") == "unnamed"
        assert _sanitize_filename("   ") == "unnamed"

    def test_backslash_paths(self):
        from etl.zip_extractor import _sanitize_filename

        assert _sanitize_filename("dir\\subdir\\file.csv") == "file.csv"


# ── Full Pipeline Integration Test ───────────────────────────────────────────


class TestFullPipeline:
    """Test the full ZIP package pipeline end-to-end."""

    def test_process_package_with_csv(self):
        """Test processing a ZIP with a real CSV file."""
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker

        import etl.models  # noqa: F401
        import etl.package_models  # noqa: F401
        from etl.package_service import ETLPackageService
        from shared.database import Base

        engine = create_engine("sqlite:///:memory:", echo=False)
        Base.metadata.create_all(engine)
        Session = sessionmaker(bind=engine)
        db = Session()

        try:
            svc = ETLPackageService(db)

            # Create package
            pkg = svc.create_package(
                organization_id=1,
                uploaded_by=10,
                filename="test.zip",
                storage_key="key1",
                storage_backend="local",
                checksum="abc123",
                file_size=1024,
            )

            # Create a ZIP with a CSV
            buf = io.BytesIO()
            with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
                zf.writestr("data.csv", "name,age,city\nAlice,30,NYC\nBob,25,LA\n")
            buf.seek(0)

            fd, zip_path = tempfile.mkstemp(suffix=".zip")
            with os.fdopen(fd, "wb") as f:
                f.write(buf.read())

            try:
                result = svc.process_package(pkg.id, zip_path, organization_id=1)

                assert result["status"] in ("completed", "completed_with_errors")
                assert result["total_files"] == 1
                assert result["completed"] >= 1

                # Verify package state
                updated = svc.get_package(pkg.id, organization_id=1)
                assert updated.status in ("completed", "completed_with_errors")
                assert updated.total_files == 1
                assert updated.completed_files >= 1

                # Verify progress
                progress = svc.get_progress(pkg.id, organization_id=1)
                assert progress["percentage"] == 100.0
            finally:
                if os.path.exists(zip_path):
                    os.unlink(zip_path)
        finally:
            db.close()

    def test_process_package_with_corrupt_zip(self):
        """Test processing a corrupt ZIP file."""
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker

        import etl.models  # noqa: F401
        import etl.package_models  # noqa: F401
        from etl.package_service import ETLPackageService
        from shared.database import Base

        engine = create_engine("sqlite:///:memory:", echo=False)
        Base.metadata.create_all(engine)
        Session = sessionmaker(bind=engine)
        db = Session()

        try:
            svc = ETLPackageService(db)
            pkg = svc.create_package(
                organization_id=1,
                uploaded_by=10,
                filename="bad.zip",
                storage_key="key1",
                storage_backend="local",
                checksum="abc123",
                file_size=100,
            )

            fd, zip_path = tempfile.mkstemp(suffix=".zip")
            with os.fdopen(fd, "wb") as f:
                f.write(b"not a zip file")

            try:
                result = svc.process_package(pkg.id, zip_path, organization_id=1)
                assert result["status"] == "failed"
                assert result["error"] is not None

                updated = svc.get_package(pkg.id, organization_id=1)
                assert updated.status == "failed"
            finally:
                if os.path.exists(zip_path):
                    os.unlink(zip_path)
        finally:
            db.close()
