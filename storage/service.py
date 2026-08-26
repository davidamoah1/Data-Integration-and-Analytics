"""File service â€” orchestrates file upload/download/delete.

Bridges the storage backend (R2/S3/Supabase/Local) with the file
metadata database. The service:
  1. Uploads file content to the storage backend
  2. Persists metadata to the database
  3. Returns a FileRecord with the storage location

This is the single entry point for all file operations across the platform.
"""

from __future__ import annotations

import json
import logging
import uuid

from sqlalchemy.orm import Session as DbSession

from storage.models import FileRecord
from storage.repositories import FileRepository
from storage.storage import StorageBackend, StorageUploadResult, get_storage_backend

logger = logging.getLogger(__name__)


class FileService:
    """Service for file upload, download, and management."""

    def __init__(self, db: DbSession, backend: StorageBackend | None = None):
        self.db = db
        self.repo = FileRepository(db)
        self.backend = backend or get_storage_backend()

    # â”€â”€ Upload â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

    def upload(
        self,
        organization_id: int,
        filename: str,
        data: bytes,
        *,
        content_type: str | None = None,
        uploaded_by: int | None = None,
        is_public: bool = False,
        metadata: dict | None = None,
        key_prefix: str = "",
    ) -> FileRecord:
        """Upload a file to storage and persist metadata.

        Args:
          organization_id: Tenant scope
          filename: Original filename
          data: File content bytes
          content_type: MIME type (auto-detected if None)
          uploaded_by: User ID
          is_public: Whether file should be publicly accessible
          metadata: Extra metadata dict (page count, dimensions, etc.)
          key_prefix: Optional prefix for storage key (e.g., "capture/org_1/")

        Returns:
          FileRecord with storage location and metadata.
        """
        # Generate storage key
        file_id = uuid.uuid4().hex
        ext = ""
        if "." in filename:
            ext = "." + filename.rsplit(".", 1)[-1].lower()
        key = f"{key_prefix}{file_id}{ext}" if key_prefix else f"{file_id}{ext}"

        # Auto-detect content type if not provided
        if content_type is None:
            content_type = self._guess_content_type(filename)

        # Upload to storage backend
        result: StorageUploadResult = self.backend.upload(key, data, content_type)
        logger.info(
            "File uploaded to %s: %s (%d bytes, %s)",
            self.backend.name,
            key,
            result.size,
            content_type,
        )

        # Persist metadata
        record = self.repo.create(
            file_id=file_id,
            organization_id=organization_id,
            filename=filename,
            storage_backend=self.backend.name,
            storage_bucket=result.bucket,
            storage_key=result.key,
            storage_url=result.url,
            mime_type=content_type,
            file_size=result.size,
            checksum=result.checksum,
            file_metadata=json.dumps(metadata) if metadata else None,
            uploaded_by=uploaded_by,
            is_public=1 if is_public else 0,
        )
        self.db.commit()
        logger.info("FileRecord created: file_id=%s, id=%d", file_id, record.id)
        return record

    # â”€â”€ Download â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

    def download(self, file_id: str, organization_id: int) -> tuple[bytes, FileRecord]:
        """Download a file by its file_id.

        Returns (data, metadata) tuple.
        """
        record = self.repo.get_by_org(file_id, organization_id)
        if not record or record.is_deleted:
            raise FileNotFoundError(f"File not found: {file_id}")

        data = self.backend.download(record.storage_key)
        self.repo.mark_accessed(record.id)
        self.db.commit()
        return data, record

    # â”€â”€ Get URL â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

    def get_url(self, file_id: str, organization_id: int, expires: int = 3600) -> str:
        """Get a URL to access the file (presigned or public)."""
        record = self.repo.get_by_org(file_id, organization_id)
        if not record or record.is_deleted:
            raise FileNotFoundError(f"File not found: {file_id}")
        return self.backend.get_url(record.storage_key, expires=expires)

    # â”€â”€ Delete â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

    def delete(self, file_id: str, organization_id: int) -> bool:
        """Delete a file from storage and soft-delete metadata."""
        record = self.repo.get_by_org(file_id, organization_id)
        if not record or record.is_deleted:
            return False

        # Delete from storage backend
        try:
            self.backend.delete(record.storage_key)
        except Exception as e:
            logger.warning("Failed to delete file from %s: %s", self.backend.name, e)

        # Soft-delete metadata
        self.repo.soft_delete(record.id)
        self.db.commit()
        logger.info("File deleted: file_id=%s", file_id)
        return True

    # â”€â”€ List â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

    def list_files(
        self,
        organization_id: int,
        *,
        limit: int = 50,
        offset: int = 0,
    ) -> list[FileRecord]:
        """List files for an organization."""
        return self.repo.list_by_org(organization_id, limit=limit, offset=offset)

    def get_file(self, file_id: str, organization_id: int) -> FileRecord | None:
        """Get file metadata by file_id."""
        return self.repo.get_by_org(file_id, organization_id)

    def get_file_count(self, organization_id: int) -> int:
        """Get total file count for an organization."""
        return self.repo.count_by_org(organization_id)

    # â”€â”€ Helpers â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

    @staticmethod
    def _guess_content_type(filename: str) -> str:
        """Guess MIME type from filename."""
        import mimetypes

        ct, _ = mimetypes.guess_type(filename)
        return ct or "application/octet-stream"
