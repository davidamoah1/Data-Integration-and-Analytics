"""ORM model for file metadata.

The database stores only metadata â€” the actual file content lives in
object storage (R2, S3, Supabase, or local disk). This separation
keeps the database lean and enables CDN delivery, multipart uploads,
and storage-tier migration without touching the DB schema.
"""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import (
    Column,
    DateTime,
    Integer,
    String,
    Text,
)

from shared.database import Base, BigInt


class FileRecord(Base):
    """Metadata for a file stored in object storage.

    Fields:
      file_id        â€” UUID-based public identifier (used in URLs/API)
      organization_id â€” Tenant scope
      filename       â€” Original filename from upload
      storage_backend â€” Which backend stored the file (local, r2, s3, supabase)
      storage_bucket â€” Bucket/container name
      storage_key    â€” Object key/path within the bucket
      storage_url    â€” Full URL or path to retrieve the file
      mime_type      â€” MIME type (e.g., image/png, application/pdf)
      file_size      â€” Size in bytes
      checksum       â€” SHA-256 hash for integrity verification
      metadata       â€” JSON string for extra info (page count, dimensions, etc.)
      uploaded_by    â€” User ID who uploaded the file
      is_public      â€” Whether the file is publicly accessible
      created_at     â€” Upload timestamp
      accessed_at    â€” Last download timestamp
      deleted_at     â€” Soft-delete timestamp (file removed from storage)
    """

    __tablename__ = "file_records"

    id = Column(BigInt, primary_key=True, autoincrement=True)
    file_id = Column(String(64), nullable=False, unique=True, index=True)
    organization_id = Column(BigInt, nullable=False, index=True)

    filename = Column(String(500), nullable=False)

    # Storage location
    storage_backend = Column(String(32), nullable=False, default="local")
    storage_bucket = Column(String(255), nullable=True)
    storage_key = Column(String(1000), nullable=False)
    storage_url = Column(String(2000), nullable=True)

    # File metadata
    mime_type = Column(String(100), nullable=True)
    file_size = Column(Integer, nullable=True)
    checksum = Column(String(64), nullable=True)
    file_metadata = Column(Text, nullable=True)  # JSON string

    # Ownership
    uploaded_by = Column(BigInt, nullable=True)
    is_public = Column(Integer, default=0, nullable=False)  # 0 or 1 for SQLite compat

    # Timestamps
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    accessed_at = Column(DateTime, nullable=True)
    deleted_at = Column(DateTime, nullable=True)

    @property
    def is_deleted(self) -> bool:
        return self.deleted_at is not None

    def to_dict(self) -> dict:
        import json

        return {
            "id": self.id,
            "file_id": self.file_id,
            "organization_id": self.organization_id,
            "filename": self.filename,
            "storage_backend": self.storage_backend,
            "storage_bucket": self.storage_bucket,
            "storage_key": self.storage_key,
            "storage_url": self.storage_url,
            "mime_type": self.mime_type,
            "file_size": self.file_size,
            "checksum": self.checksum,
            "metadata": json.loads(self.file_metadata) if self.file_metadata else None,
            "uploaded_by": self.uploaded_by,
            "is_public": bool(self.is_public),
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "accessed_at": self.accessed_at.isoformat() if self.accessed_at else None,
            "deleted_at": self.deleted_at.isoformat() if self.deleted_at else None,
        }
