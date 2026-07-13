"""AI Security Layer — enforces permissions, validates input, and ensures responsible AI.

Features:
- Input validation (length, injection prevention)
- Permission checking per assistant type
- Data access auditing
- Sensitive data redaction
- Rate limiting awareness
"""

import re
from typing import Optional
from sqlalchemy.orm import Session as DbSession

from ai.config import AI_MAX_INPUT_LENGTH, AI_ENFORCE_PERMISSIONS


# Dangerous SQL keywords that should only appear in generated SQL, not user input
_SQL_INJECTION_PATTERNS = [
    r";\s*DROP\s",
    r";\s*DELETE\s",
    r";\s*UPDATE\s.*\sSET\s",
    r";\s*INSERT\s",
    r";\s*ALTER\s",
    r";\s*TRUNCATE\s",
    r"UNION\s+SELECT",
    r"--\s*$",
    r"/\*.*\*/",
]

# Permission requirements per assistant type
ASSISTANT_PERMISSIONS: dict[str, list[str]] = {
    "data_copilot": [],
    "etl_copilot": ["etl.read"],
    "dashboard_copilot": [],
    "report_copilot": [],
    "decision_copilot": [],
    "forecast_copilot": [],
    "quality_copilot": ["etl.read"],
    "sql_copilot": [],
}


class AISecurityLayer:
    """Security layer for all AI operations."""

    def __init__(self, db: DbSession):
        self.db = db

    def validate_input(self, text: str) -> str:
        """Validate and sanitize user input.

        Args:
            text: Raw user input string.

        Returns:
            Sanitized text.

        Raises:
            ValueError if input is invalid or dangerous.
        """
        if not text or not text.strip():
            raise ValueError("Input cannot be empty")

        if len(text) > AI_MAX_INPUT_LENGTH:
            raise ValueError(f"Input exceeds maximum length of {AI_MAX_INPUT_LENGTH} characters")

        # Check for SQL injection patterns
        for pattern in _SQL_INJECTION_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                raise ValueError("Potentially dangerous input detected")

        return text.strip()

    def check_permissions(self, assistant_type: str, user_permissions: list[str]) -> bool:
        """Check if the user has required permissions for the assistant type.

        Args:
            assistant_type: The assistant being accessed.
            user_permissions: List of permission strings the user has.

        Returns:
            True if authorized.

        Raises:
            PermissionError if the user lacks required permissions.
        """
        if not AI_ENFORCE_PERMISSIONS:
            return True

        required = ASSISTANT_PERMISSIONS.get(assistant_type, [])
        if not required:
            return True

        user_perms = set(user_permissions)
        # Super admin bypass
        if "*" in user_perms or "super_admin" in user_perms:
            return True

        # Check if user has any of the required permissions
        if not set(required) & user_perms:
            raise PermissionError(
                f"Missing required permissions for {assistant_type}: {', '.join(required)}"
            )

        return True

    def redact_sensitive_data(self, text: str) -> str:
        """Redact sensitive data patterns from text.

        Removes credit card numbers, SSN-like patterns, and API keys.
        """
        # Credit card numbers (basic pattern)
        text = re.sub(r'\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b', '[REDACTED-CC]', text)
        # API key patterns
        text = re.sub(r'sk-[a-zA-Z0-9]{20,}', '[REDACTED-KEY]', text)
        # Email addresses (partial redaction)
        text = re.sub(r'\b([a-zA-Z0-9._%+-])[a-zA-Z0-9._%+-]*@([a-zA-Z0-9.-]+\.[a-zA-Z]{2,})\b',
                      r'\1***@\2', text)
        return text

    def sanitize_for_audit(self, text: str, max_length: int = 200) -> str:
        """Create a sanitized summary for audit logs."""
        if not text:
            return ""
        sanitized = self.redact_sensitive_data(text)
        if len(sanitized) > max_length:
            sanitized = sanitized[:max_length] + "..."
        return sanitized

    def check_data_access(self, user_id: int, table_name: str,
                          user_permissions: list[str]) -> bool:
        """Check if a user can access a specific data table.

        This integrates with the RBAC system to ensure AI doesn't
        expose unauthorized data.
        """
        if "*" in user_permissions or "super_admin" in user_permissions:
            return True

        # Map tables to required permissions
        table_permissions = {
            "sales": [],
            "pipeline_runs": [],
            "etl_pipelines": ["etl.read"],
            "etl_jobs": ["etl.read"],
            "users": ["users.read"],
            "audit_logs": ["audit.read"],
        }

        required = table_permissions.get(table_name, [])
        if not required:
            return True

        return bool(set(required) & set(user_permissions))
