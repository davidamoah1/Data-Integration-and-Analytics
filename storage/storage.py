"""Storage backend abstraction layer.

Provides a unified interface for file operations across multiple backends:
  - LocalFileBackend   â€” Local filesystem (dev / single-server)
  - R2Backend          â€” Cloudflare R2 (S3-compatible API)
  - S3Backend          â€” AWS S3
  - SupabaseBackend    â€” Supabase Storage

All backends implement the StorageBackend protocol:
  upload(key, data, content_type) -> StorageUploadResult
  download(key) -> bytes
  delete(key) -> bool
  get_url(key, expires) -> str  (presigned URL or public URL)
  exists(key) -> bool

The backend is selected via STORAGE_BACKEND env var:
  local (default), r2, s3, supabase
"""

from __future__ import annotations

import hashlib
import logging
import os
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class StorageUploadResult:
    """Result of a file upload operation."""

    key: str
    bucket: str | None
    url: str | None
    checksum: str
    size: int


class StorageBackend(ABC):
    """Abstract base class for file storage backends."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Backend identifier (local, r2, s3, supabase)."""
        ...

    @abstractmethod
    def upload(
        self,
        key: str,
        data: bytes,
        content_type: str | None = None,
    ) -> StorageUploadResult:
        """Upload file data to the storage backend."""
        ...

    @abstractmethod
    def download(self, key: str) -> bytes:
        """Download file data from the storage backend."""
        ...

    @abstractmethod
    def delete(self, key: str) -> bool:
        """Delete a file from the storage backend."""
        ...

    @abstractmethod
    def get_url(self, key: str, expires: int = 3600) -> str:
        """Get a URL to access the file (presigned or public)."""
        ...

    @abstractmethod
    def exists(self, key: str) -> bool:
        """Check if a file exists in the storage backend."""
        ...


# â”€â”€ Local File Backend â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€


class LocalFileBackend(StorageBackend):
    """Local filesystem storage backend.

    Suitable for development, single-server deployments, or when
    object storage is not available.
    """

    def __init__(self, base_dir: str, base_url: str | None = None):
        self.base_dir = os.path.abspath(base_dir)
        self.base_url = base_url or ""
        os.makedirs(self.base_dir, exist_ok=True)

    @property
    def name(self) -> str:
        return "local"

    def _full_path(self, key: str) -> str:
        # Prevent path traversal
        full = os.path.normpath(os.path.join(self.base_dir, key))
        if not full.startswith(self.base_dir):
            raise ValueError(f"Invalid storage key: {key}")
        return full

    def upload(
        self,
        key: str,
        data: bytes,
        content_type: str | None = None,
    ) -> StorageUploadResult:
        full_path = self._full_path(key)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        with open(full_path, "wb") as f:
            f.write(data)
        checksum = hashlib.sha256(data).hexdigest()
        url = f"{self.base_url}/{key}" if self.base_url else None
        return StorageUploadResult(
            key=key,
            bucket=None,
            url=url,
            checksum=checksum,
            size=len(data),
        )

    def download(self, key: str) -> bytes:
        full_path = self._full_path(key)
        if not os.path.exists(full_path):
            raise FileNotFoundError(f"File not found: {key}")
        with open(full_path, "rb") as f:
            return f.read()

    def delete(self, key: str) -> bool:
        full_path = self._full_path(key)
        if os.path.exists(full_path):
            os.remove(full_path)
            return True
        return False

    def get_url(self, key: str, expires: int = 3600) -> str:
        # Local backend doesn't support presigned URLs
        if self.base_url:
            return f"{self.base_url}/{key}"
        return f"/storage/files/{key}"

    def exists(self, key: str) -> bool:
        return os.path.exists(self._full_path(key))


# â”€â”€ S3-Compatible Backend (R2 + S3) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€


class S3CompatibleBackend(StorageBackend):
    """S3-compatible storage backend.

    Works with:
      - Cloudflare R2 (set endpoint to R2 S3 API URL)
      - AWS S3 (leave endpoint unset)
      - MinIO, Wasabi, etc.
    """

    def __init__(
        self,
        bucket: str,
        region: str,
        access_key: str,
        secret_key: str,
        endpoint: str | None = None,
        public_base_url: str | None = None,
        backend_name: str = "s3",
    ):
        self.bucket = bucket
        self.region = region
        self.endpoint = endpoint
        self.public_base_url = public_base_url
        self._backend_name = backend_name
        self._client = None
        self._init_client(access_key, secret_key)

    def _init_client(self, access_key: str, secret_key: str) -> None:
        try:
            import boto3
            from botocore.config import Config

            kwargs: dict[str, Any] = {
                "service_name": "s3",
                "aws_access_key_id": access_key,
                "aws_secret_access_key": secret_key,
                "region_name": self.region,
                "config": Config(
                    signature_version="s3v4",
                    retries={"max_attempts": 3, "mode": "standard"},
                ),
            }
            if self.endpoint:
                kwargs["endpoint_url"] = self.endpoint
            self._client = boto3.client(**kwargs)
            logger.info(
                "S3-compatible backend initialized: %s (bucket=%s)", self._backend_name, self.bucket
            )
        except ImportError:
            logger.warning("boto3 not installed â€” S3 backend unavailable")
            raise

    @property
    def name(self) -> str:
        return self._backend_name

    def upload(
        self,
        key: str,
        data: bytes,
        content_type: str | None = None,
    ) -> StorageUploadResult:
        kwargs: dict[str, Any] = {
            "Bucket": self.bucket,
            "Key": key,
            "Body": data,
        }
        if content_type:
            kwargs["ContentType"] = content_type
        self._client.put_object(**kwargs)
        checksum = hashlib.sha256(data).hexdigest()
        url = None
        if self.public_base_url:
            url = f"{self.public_base_url}/{key}"
        return StorageUploadResult(
            key=key,
            bucket=self.bucket,
            url=url,
            checksum=checksum,
            size=len(data),
        )

    def download(self, key: str) -> bytes:
        response = self._client.get_object(Bucket=self.bucket, Key=key)
        return response["Body"].read()

    def delete(self, key: str) -> bool:
        self._client.delete_object(Bucket=self.bucket, Key=key)
        return True

    def get_url(self, key: str, expires: int = 3600) -> str:
        if self.public_base_url:
            return f"{self.public_base_url}/{key}"
        # Generate presigned URL
        return self._client.generate_presigned_url(
            "get_object",
            Params={"Bucket": self.bucket, "Key": key},
            ExpiresIn=expires,
        )

    def exists(self, key: str) -> bool:
        try:
            self._client.head_object(Bucket=self.bucket, Key=key)
            return True
        except Exception:
            return False


class R2Backend(S3CompatibleBackend):
    """Cloudflare R2 storage backend (S3-compatible)."""

    def __init__(
        self,
        bucket: str,
        account_id: str,
        access_key: str,
        secret_key: str,
        public_base_url: str | None = None,
    ):
        endpoint = f"https://{account_id}.r2.cloudflarestorage.com"
        super().__init__(
            bucket=bucket,
            region="auto",
            access_key=access_key,
            secret_key=secret_key,
            endpoint=endpoint,
            public_base_url=public_base_url,
            backend_name="r2",
        )


class S3Backend(S3CompatibleBackend):
    """AWS S3 storage backend."""

    def __init__(
        self,
        bucket: str,
        region: str,
        access_key: str,
        secret_key: str,
        public_base_url: str | None = None,
    ):
        super().__init__(
            bucket=bucket,
            region=region,
            access_key=access_key,
            secret_key=secret_key,
            endpoint=None,
            public_base_url=public_base_url,
            backend_name="s3",
        )


# â”€â”€ Supabase Storage Backend â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€


class SupabaseBackend(StorageBackend):
    """Supabase Storage backend.

    Uses the Supabase Storage REST API for file operations.
    """

    def __init__(
        self,
        bucket: str,
        url: str,
        service_key: str,
        public_base_url: str | None = None,
    ):
        self.bucket = bucket
        self.url = url.rstrip("/")
        self.service_key = service_key
        self.public_base_url = public_base_url or f"{self.url}/storage/v1/object/public"
        self._client = None
        self._init_client()

    def _init_client(self) -> None:
        try:
            from supabase import (
                Client,  # noqa: F401
                create_client,
            )

            self._client = create_client(self.url, self.service_key)
            logger.info("Supabase storage backend initialized (bucket=%s)", self.bucket)
        except ImportError:
            logger.warning("supabase-py not installed â€” Supabase backend unavailable")
            raise

    @property
    def name(self) -> str:
        return "supabase"

    def upload(
        self,
        key: str,
        data: bytes,
        content_type: str | None = None,
    ) -> StorageUploadResult:
        file_options = {}
        if content_type:
            file_options["content_type"] = content_type
        self._client.storage.from_(self.bucket).upload(
            path=key,
            file=data,
            file_options=file_options,
        )
        checksum = hashlib.sha256(data).hexdigest()
        public_url = f"{self.public_base_url}/{self.bucket}/{key}"
        return StorageUploadResult(
            key=key,
            bucket=self.bucket,
            url=public_url,
            checksum=checksum,
            size=len(data),
        )

    def download(self, key: str) -> bytes:
        return self._client.storage.from_(self.bucket).download(key)

    def delete(self, key: str) -> bool:
        self._client.storage.from_(self.bucket).remove([key])
        return True

    def get_url(self, key: str, expires: int = 3600) -> str:
        if expires > 0:
            # Create a signed URL
            return self._client.storage.from_(self.bucket).create_signed_url(key, expires)
        return f"{self.public_base_url}/{self.bucket}/{key}"

    def exists(self, key: str) -> bool:
        try:
            self._client.storage.from_(self.bucket).download(key)
            return True
        except Exception:
            return False


# â”€â”€ Backend Factory â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€


_backend: StorageBackend | None = None


def get_storage_backend() -> StorageBackend:
    """Get the singleton storage backend based on STORAGE_BACKEND env var.

    Configuration:
      STORAGE_BACKEND  â€” local | r2 | s3 | supabase (default: local)

    Local:
      STORAGE_LOCAL_DIR  â€” Base directory for file storage

    R2:
      R2_BUCKET, R2_ACCOUNT_ID, R2_ACCESS_KEY, R2_SECRET_KEY, R2_PUBLIC_URL

    S3:
      S3_BUCKET, S3_REGION, S3_ACCESS_KEY, S3_SECRET_KEY, S3_PUBLIC_URL

    Supabase:
      SUPABASE_URL, SUPABASE_SERVICE_KEY, SUPABASE_STORAGE_BUCKET
    """
    global _backend
    if _backend is not None:
        return _backend

    backend_name = os.getenv("STORAGE_BACKEND", "local").lower()

    if backend_name == "r2":
        r2_bucket = os.getenv("R2_BUCKET", "")
        r2_account_id = os.getenv("R2_ACCOUNT_ID", "")
        r2_access_key = os.getenv("R2_ACCESS_KEY", "")
        r2_secret_key = os.getenv("R2_SECRET_KEY", "")
        if not all([r2_bucket, r2_account_id, r2_access_key, r2_secret_key]):
            logger.warning(
                "STORAGE_BACKEND=r2 but R2 credentials are incomplete "
                "(R2_BUCKET, R2_ACCOUNT_ID, R2_ACCESS_KEY, R2_SECRET_KEY required). "
                "Falling back to local storage."
            )
            backend_name = "local"
        else:
            _backend = R2Backend(
                bucket=r2_bucket,
                account_id=r2_account_id,
                access_key=r2_access_key,
                secret_key=r2_secret_key,
                public_base_url=os.getenv("R2_PUBLIC_URL"),
            )
    elif backend_name == "s3":
        s3_bucket = os.getenv("S3_BUCKET", "")
        s3_access_key = os.getenv("S3_ACCESS_KEY", "")
        s3_secret_key = os.getenv("S3_SECRET_KEY", "")
        if not all([s3_bucket, s3_access_key, s3_secret_key]):
            logger.warning(
                "STORAGE_BACKEND=s3 but S3 credentials are incomplete "
                "(S3_BUCKET, S3_ACCESS_KEY, S3_SECRET_KEY required). "
                "Falling back to local storage."
            )
            backend_name = "local"
        else:
            _backend = S3Backend(
                bucket=s3_bucket,
                region=os.getenv("S3_REGION", "us-east-1"),
                access_key=s3_access_key,
                secret_key=s3_secret_key,
                public_base_url=os.getenv("S3_PUBLIC_URL"),
            )
    elif backend_name == "supabase":
        sb_url = os.getenv("SUPABASE_URL", "")
        sb_key = os.getenv("SUPABASE_SERVICE_KEY", "")
        if not all([sb_url, sb_key]):
            logger.warning(
                "STORAGE_BACKEND=supabase but Supabase credentials are incomplete "
                "(SUPABASE_URL, SUPABASE_SERVICE_KEY required). "
                "Falling back to local storage."
            )
            backend_name = "local"
        else:
            _backend = SupabaseBackend(
                bucket=os.getenv("SUPABASE_STORAGE_BUCKET", "files"),
                url=sb_url,
                service_key=sb_key,
                public_base_url=os.getenv("SUPABASE_STORAGE_PUBLIC_URL"),
            )
    else:
        # Default: local filesystem
        base_dir = os.getenv("STORAGE_LOCAL_DIR", "storage/files")
        # On Vercel (serverless), the filesystem is read-only except /tmp.
        # Use /tmp/storage as the base directory for local file storage.
        if os.getenv("VERCEL", "").lower() in ("1", "true", "yes"):
            base_dir = os.path.join("/tmp", "storage", "files")  # nosec B108
        if not os.path.isabs(base_dir):
            base_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), base_dir)
        _backend = LocalFileBackend(
            base_dir=base_dir,
            base_url=os.getenv("STORAGE_PUBLIC_URL"),
        )

    logger.info("Storage backend initialized: %s", _backend.name)
    return _backend


def set_storage_backend(backend: StorageBackend) -> None:
    """Override the storage backend (for testing)."""
    global _backend
    _backend = backend
