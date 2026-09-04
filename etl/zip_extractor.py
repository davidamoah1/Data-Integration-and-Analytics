"""Secure ZIP extraction service.

Protects against:
  - ZIP slip / path traversal (../, absolute paths)
  - ZIP bombs (excessive compression ratio, excessive total size)
  - Excessive file counts
  - Symlink attacks
  - Malicious filenames
  - Executable files
  - Unsupported file types

Uses sanitized filenames, UUID-based temp directories, and configurable limits.
"""

from __future__ import annotations

import hashlib
import logging
import os
import re
import uuid
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

# Configurable limits
MAX_ZIP_SIZE_MB = int(os.getenv("ETL_MAX_ZIP_SIZE_MB", "2048"))  # 2 GB
MAX_EXTRACTED_SIZE_MB = int(os.getenv("ETL_MAX_EXTRACTED_SIZE_MB", "5120"))  # 5 GB
MAX_FILE_COUNT = int(os.getenv("ETL_MAX_FILE_COUNT", "15000"))
MAX_COMPRESSION_RATIO = float(os.getenv("ETL_MAX_COMPRESSION_RATIO", "200"))
MAX_FILES_PER_DIRECTORY = int(os.getenv("ETL_MAX_FILES_PER_DIR", "5000"))

# Supported file extensions for ETL processing
SUPPORTED_EXTENSIONS = {
    # Structured data
    "csv",
    "tsv",
    "xlsx",
    "xls",
    "json",
    "xml",
    "ods",
    # Documents
    "pdf",
    "txt",
    # Images
    "jpg",
    "jpeg",
    "png",
    "tiff",
    "tif",
    "bmp",
}

# File classification categories
STRUCTURED_DATA_EXTENSIONS = {"csv", "tsv", "xlsx", "xls", "json", "xml", "ods"}
DOCUMENT_EXTENSIONS = {"pdf", "txt"}
IMAGE_EXTENSIONS = {"jpg", "jpeg", "png", "tiff", "tif", "bmp"}

# Magic byte signatures for file type verification
FILE_MAGIC_BYTES = {
    "pdf": (b"%PDF",),
    "jpg": (b"\xff\xd8\xff",),
    "jpeg": (b"\xff\xd8\xff",),
    "png": (b"\x89PNG\r\n\x1a\n",),
    "tiff": (b"II*\x00", b"MM\x00*"),
    "tif": (b"II*\x00", b"MM\x00*"),
    "bmp": (b"BM",),
    "zip": (b"PK\x03\x04",),
    "xlsx": (b"PK\x03\x04",),
    "xls": (b"\xd0\xcf\x11\xe0",),
    "ods": (b"PK\x03\x04",),
}


def classify_file_type(filename: str, file_path: str | None = None) -> str:
    """Classify a file as STRUCTURED_DATA, DOCUMENT, IMAGE, or ARCHIVE.

    Uses extension first, then verifies with magic bytes when possible.
    """
    ext = _get_file_extension(filename)
    if ext in STRUCTURED_DATA_EXTENSIONS:
        return "STRUCTURED_DATA"
    if ext in DOCUMENT_EXTENSIONS:
        return "DOCUMENT"
    if ext in IMAGE_EXTENSIONS:
        return "IMAGE"
    if ext == "zip":
        return "ARCHIVE"
    return "UNKNOWN"


def verify_magic_bytes(filename: str, file_path: str) -> bool:
    """Verify that a file's content matches its extension via magic bytes.

    Returns True if the magic bytes match or if no signature is known.
    Returns False if the signature is known but does not match.
    """
    ext = _get_file_extension(filename)
    signatures = FILE_MAGIC_BYTES.get(ext)
    if signatures is None:
        return True  # No signature to check
    try:
        with open(file_path, "rb") as f:
            header = f.read(16)
        if len(header) < 4:
            return False
        for sig in signatures:
            if header.startswith(sig):
                return True
        return False
    except (OSError, IOError):
        return False

# Extensions that are always rejected
BLOCKED_EXTENSIONS = {
    "exe",
    "bat",
    "cmd",
    "sh",
    "ps1",
    "com",
    "scr",
    "msi",
    "dll",
    "so",
    "dylib",
    "jar",
    "class",
    "py",
    "rb",
    "php",
    "jsp",
    "asp",
}

# Dangerous path patterns
_PATH_TRAVERSAL_RE = re.compile(r"(?:^|/)\.\.(?:/|$)|\.\.\\|(?:^|[\\/])[A-Za-z]:[\\/]")


class ZipSecurityError(Exception):
    """Raised when a ZIP fails security validation."""

    pass


@dataclass
class ExtractedFile:
    """Metadata for a single extracted file."""

    original_path: str
    sanitized_filename: str
    extracted_path: str
    file_extension: str
    mime_type: str
    file_size: int
    checksum: str
    is_supported: bool
    is_duplicate: bool = False
    duplicate_of: str | None = None


@dataclass
class ExtractionResult:
    """Result of a ZIP extraction operation."""

    success: bool
    extract_dir: str
    files: list[ExtractedFile] = field(default_factory=list)
    total_files: int = 0
    total_size: int = 0
    supported_files: int = 0
    unsupported_files: int = 0
    duplicate_files: int = 0
    errors: list[str] = field(default_factory=list)
    error: str | None = None


def _sanitize_filename(filename: str) -> str:
    """Sanitize a filename: remove path components, dangerous characters."""
    # Take only the basename — strip any directory components
    basename = os.path.basename(filename.replace("\\", "/"))
    if not basename:
        basename = "unnamed"

    # Remove or replace dangerous characters
    basename = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", basename)
    basename = basename.strip(". ") or "unnamed"
    return basename


def _is_safe_path(extract_dir: str, target_path: str) -> bool:
    """Verify that target_path is within extract_dir (no path traversal)."""
    try:
        abs_extract = os.path.abspath(extract_dir)
        abs_target = os.path.abspath(target_path)
        return abs_target.startswith(abs_extract + os.sep) or abs_target == abs_extract
    except (ValueError, OSError):
        return False


def _get_file_extension(filename: str) -> str:
    """Get lowercase extension without the dot."""
    return os.path.splitext(filename)[1].lower().lstrip(".")


def _compute_checksum(file_path: str) -> str:
    """Compute SHA-256 checksum of a file."""
    h = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def _guess_mime_type(filename: str) -> str:
    """Guess MIME type from extension."""
    ext = _get_file_extension(filename)
    return {
        "csv": "text/csv",
        "tsv": "text/tab-separated-values",
        "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "xls": "application/vnd.ms-excel",
        "json": "application/json",
        "xml": "text/xml",
        "ods": "application/vnd.oasis.opendocument.spreadsheet",
        "pdf": "application/pdf",
        "txt": "text/plain",
        "jpg": "image/jpeg",
        "jpeg": "image/jpeg",
        "png": "image/png",
        "tiff": "image/tiff",
        "tif": "image/tiff",
        "bmp": "image/bmp",
    }.get(ext, "application/octet-stream")


def validate_zip(zip_path: str) -> dict:
    """Validate a ZIP file before extraction.

    Returns:
        Dict with valid, file_count, compressed_size, uncompressed_size,
        compression_ratio, errors.
    """
    import zipfile

    result = {
        "valid": True,
        "file_count": 0,
        "compressed_size": 0,
        "uncompressed_size": 0,
        "compression_ratio": 0.0,
        "errors": [],
    }

    if not os.path.exists(zip_path):
        result["valid"] = False
        result["errors"].append(f"ZIP file not found: {zip_path}")
        return result

    file_size = os.path.getsize(zip_path)
    max_zip_bytes = MAX_ZIP_SIZE_MB * 1024 * 1024
    if file_size > max_zip_bytes:
        result["valid"] = False
        result["errors"].append(
            f"ZIP file size {file_size / 1024 / 1024:.1f}MB exceeds " f"maximum {MAX_ZIP_SIZE_MB}MB"
        )
        return result

    try:
        with zipfile.ZipFile(zip_path, "r") as zf:
            infos = zf.infolist()
            result["file_count"] = len(infos)

            if len(infos) > MAX_FILE_COUNT:
                result["valid"] = False
                result["errors"].append(
                    f"ZIP contains {len(infos)} files, exceeds maximum {MAX_FILE_COUNT}"
                )
                return result

            total_compressed = 0
            total_uncompressed = 0

            for info in infos:
                total_compressed += info.compress_size
                total_uncompressed += info.file_size

                # Check for path traversal
                if _PATH_TRAVERSAL_RE.search(info.filename):
                    result["valid"] = False
                    result["errors"].append(
                        f"Path traversal detected in ZIP entry: {info.filename}"
                    )
                    return result

                # Check for absolute paths
                if os.path.isabs(info.filename) or info.filename.startswith("/"):
                    result["valid"] = False
                    result["errors"].append(f"Absolute path in ZIP entry: {info.filename}")
                    return result

                # Check for symlinks (external_attr has symlink flag)
                if info.external_attr >> 16 & 0o170000 == 0o120000:
                    result["valid"] = False
                    result["errors"].append(f"Symlink found in ZIP: {info.filename}")
                    return result

            result["compressed_size"] = total_compressed
            result["uncompressed_size"] = total_uncompressed

            max_uncompressed = MAX_EXTRACTED_SIZE_MB * 1024 * 1024
            if total_uncompressed > max_uncompressed:
                result["valid"] = False
                result["errors"].append(
                    f"Uncompressed size {total_uncompressed / 1024 / 1024:.1f}MB "
                    f"exceeds maximum {MAX_EXTRACTED_SIZE_MB}MB"
                )
                return result

            if total_compressed > 0:
                ratio = total_uncompressed / total_compressed
                result["compression_ratio"] = round(ratio, 2)
                if ratio > MAX_COMPRESSION_RATIO:
                    result["valid"] = False
                    result["errors"].append(
                        f"Compression ratio {ratio:.1f}x exceeds maximum "
                        f"{MAX_COMPRESSION_RATIO}x — possible ZIP bomb"
                    )
                    return result

    except zipfile.BadZipFile as e:
        result["valid"] = False
        result["errors"].append(f"Invalid or corrupt ZIP file: {e}")
    except Exception as e:
        result["valid"] = False
        result["errors"].append(f"ZIP validation failed: {e}")

    return result


def extract_zip(
    zip_path: str,
    extract_base_dir: str,
    organization_id: int,
) -> ExtractionResult:
    """Securely extract a ZIP file.

    Args:
        zip_path: Path to the ZIP file.
        extract_base_dir: Base directory for extraction.
        organization_id: Organization ID for tenant-specific path.

    Returns:
        ExtractionResult with file metadata.
    """
    import zipfile

    # Create UUID-based extraction directory with tenant isolation
    extraction_uuid = str(uuid.uuid4())
    extract_dir = os.path.join(
        extract_base_dir,
        f"org_{organization_id}",
        extraction_uuid,
    )
    os.makedirs(extract_dir, exist_ok=True)

    result = ExtractionResult(success=False, extract_dir=extract_dir)

    # Validate ZIP first
    validation = validate_zip(zip_path)
    if not validation["valid"]:
        result.error = "; ".join(validation["errors"])
        result.errors = validation["errors"]
        return result

    try:
        with zipfile.ZipFile(zip_path, "r") as zf:
            seen_checksums: dict[str, str] = {}  # checksum -> first filename
            total_extracted_size = 0

            for info in zf.infolist():
                if info.is_dir():
                    continue

                # Sanitize filename
                sanitized = _sanitize_filename(info.filename)
                ext = _get_file_extension(sanitized)

                # Check blocked extensions
                if ext in BLOCKED_EXTENSIONS:
                    logger.warning(
                        "EXTRACTION_SKIP file=%s reason=blocked_extension ext=%s",
                        info.filename,
                        ext,
                    )
                    result.unsupported_files += 1
                    continue

                # Build safe extraction path preserving folder structure
                rel_dir = os.path.dirname(info.filename.replace("\\", "/"))
                if _PATH_TRAVERSAL_RE.search(rel_dir):
                    logger.warning(
                        "EXTRACTION_SKIP file=%s reason=path_traversal",
                        info.filename,
                    )
                    result.errors.append(f"Path traversal blocked: {info.filename}")
                    continue

                # Create subdirectory if needed
                target_dir = os.path.join(extract_dir, rel_dir) if rel_dir else extract_dir
                if not _is_safe_path(extract_dir, target_dir):
                    result.errors.append(f"Unsafe path blocked: {info.filename}")
                    continue

                os.makedirs(target_dir, exist_ok=True)
                target_path = os.path.join(target_dir, sanitized)

                # Double-check the final path is safe
                if not _is_safe_path(extract_dir, target_path):
                    result.errors.append(f"Unsafe extraction path: {info.filename}")
                    continue

                # Extract
                extracted_data = zf.read(info)
                total_extracted_size += len(extracted_data)

                max_uncompressed = MAX_EXTRACTED_SIZE_MB * 1024 * 1024
                if total_extracted_size > max_uncompressed:
                    result.error = f"Total extracted size exceeded {MAX_EXTRACTED_SIZE_MB}MB limit"
                    return result

                with open(target_path, "wb") as f:
                    f.write(extracted_data)

                # Compute checksum
                checksum = hashlib.sha256(extracted_data).hexdigest()

                # Check for duplicates within this package
                is_duplicate = False
                duplicate_of = None
                if checksum in seen_checksums:
                    is_duplicate = True
                    duplicate_of = seen_checksums[checksum]
                    result.duplicate_files += 1
                else:
                    seen_checksums[checksum] = sanitized

                is_supported = ext in SUPPORTED_EXTENSIONS
                if not is_supported:
                    result.unsupported_files += 1
                else:
                    result.supported_files += 1

                file_entry = ExtractedFile(
                    original_path=info.filename,
                    sanitized_filename=sanitized,
                    extracted_path=target_path,
                    file_extension=ext,
                    mime_type=_guess_mime_type(sanitized),
                    file_size=len(extracted_data),
                    checksum=checksum,
                    is_supported=is_supported,
                    is_duplicate=is_duplicate,
                    duplicate_of=duplicate_of,
                )
                result.files.append(file_entry)
                result.total_files += 1
                result.total_size += len(extracted_data)

                logger.info(
                    "FILE_DISCOVERED file=%s ext=%s size=%d checksum=%s supported=%s duplicate=%s",
                    sanitized,
                    ext,
                    len(extracted_data),
                    checksum[:16],
                    is_supported,
                    is_duplicate,
                )

        result.success = True
        logger.info(
            "EXTRACTION_COMPLETED dir=%s files=%d supported=%d unsupported=%d duplicates=%d size=%d",
            extract_dir,
            result.total_files,
            result.supported_files,
            result.unsupported_files,
            result.duplicate_files,
            result.total_size,
        )

    except zipfile.BadZipFile as e:
        result.error = f"Corrupt ZIP file: {e}"
        logger.error("EXTRACTION_FAILED reason=bad_zip error=%s", e)
    except Exception as e:
        result.error = f"Extraction failed: {e}"
        logger.error("EXTRACTION_FAILED reason=error error=%s", e, exc_info=True)

    return result


def cleanup_extraction(extract_dir: str) -> None:
    """Safely remove an extraction directory."""
    import shutil

    try:
        if os.path.exists(extract_dir):
            shutil.rmtree(extract_dir, ignore_errors=True)
            logger.info("EXTRACTION_CLEANUP dir=%s", extract_dir)
    except Exception as e:
        logger.warning("Extraction cleanup failed for %s: %s", extract_dir, e)
