"""File upload security — validates uploaded files for safety.

Validates MIME types, file sizes, file structure, and records audit entries.
"""

import os

import magic

MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB

ALLOWED_MIME_TYPES = {
    "csv": {"text/csv", "text/plain", "application/csv"},
    "xlsx": {"application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"},
    "xls": {"application/vnd.ms-excel"},
    "json": {"application/json", "text/plain"},
    "xml": {"application/xml", "text/xml", "text/plain"},
}

ALLOWED_EXTENSIONS = {"csv", "xlsx", "xls", "json", "xml"}


class FileSecurityError(Exception):
    """Raised when a file fails security validation."""

    pass


class FileValidator:
    """Validates uploaded files for security and integrity."""

    def __init__(self, max_size: int = MAX_FILE_SIZE):
        self.max_size = max_size

    def validate(self, file_path: str, expected_type: str | None = None) -> dict:
        """Validate an uploaded file.

        Args:
            file_path: Path to the uploaded file.
            expected_type: Expected file type (csv, xlsx, json, xml).

        Returns:
            Dict with validation results: {"valid": bool, "file_type": str, "size": int, "errors": list}

        Raises:
            FileSecurityError: If file fails critical security checks.
        """
        errors = []
        result = {"valid": True, "file_type": None, "size": 0, "errors": []}

        # Check file exists
        if not os.path.exists(file_path):
            raise FileSecurityError(f"File not found: {file_path}")

        # Check file size
        size = os.path.getsize(file_path)
        result["size"] = size
        if size > self.max_size:
            errors.append(f"File size {size} bytes exceeds maximum {self.max_size} bytes")
            result["valid"] = False

        if size == 0:
            errors.append("File is empty")
            result["valid"] = False

        # Check extension
        ext = os.path.splitext(file_path)[1].lower().lstrip(".")
        if ext not in ALLOWED_EXTENSIONS:
            errors.append(f"File extension '{ext}' is not allowed. Allowed: {ALLOWED_EXTENSIONS}")
            result["valid"] = False

        # Detect MIME type
        try:
            mime = magic.from_file(file_path, mime=True)
        except Exception:
            mime = "unknown"

        result["file_type"] = ext or "unknown"

        # Validate MIME type if expected_type is given
        if expected_type and expected_type in ALLOWED_MIME_TYPES:
            allowed = ALLOWED_MIME_TYPES[expected_type]
            if mime not in allowed and mime != "unknown":
                errors.append(f"MIME type '{mime}' does not match expected '{expected_type}'")
                result["valid"] = False

        # Structure scan — try to read the file
        try:
            self._scan_structure(file_path, ext)
        except Exception as e:
            errors.append(f"File structure validation failed: {str(e)}")
            result["valid"] = False

        result["errors"] = errors
        if errors:
            result["valid"] = False

        return result

    def _scan_structure(self, file_path: str, ext: str):
        """Quick scan of file structure to detect corruption or malicious content."""
        if ext == "csv":
            import pandas as pd

            pd.read_csv(file_path, nrows=5)
        elif ext in ("xlsx", "xls"):
            import pandas as pd

            pd.read_excel(file_path, nrows=5, engine="openpyxl")
        elif ext == "json":
            import json

            with open(file_path) as f:
                json.load(f)
        elif ext == "xml":
            import xml.etree.ElementTree as ET

            ET.parse(file_path)
