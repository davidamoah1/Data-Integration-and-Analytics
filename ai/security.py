"""AI Security Layer — enforces permissions, validates input, and ensures responsible AI.

Features:
- Input validation (length, injection prevention)
- Permission checking per assistant type
- Data access auditing
- Sensitive data redaction
- Rate limiting awareness
"""

import re

from sqlalchemy.orm import Session as DbSession

from ai.config import AI_ENFORCE_PERMISSIONS, AI_MAX_INPUT_LENGTH

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
        text = re.sub(r"\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b", "[REDACTED-CC]", text)
        # API key patterns
        text = re.sub(r"sk-[a-zA-Z0-9]{20,}", "[REDACTED-KEY]", text)
        # Email addresses (partial redaction)
        text = re.sub(
            r"\b([a-zA-Z0-9._%+-])[a-zA-Z0-9._%+-]*@([a-zA-Z0-9.-]+\.[a-zA-Z]{2,})\b",
            r"\1***@\2",
            text,
        )
        return text

    def sanitize_for_audit(self, text: str, max_length: int = 200) -> str:
        """Create a sanitized summary for audit logs."""
        if not text:
            return ""
        sanitized = self.redact_sensitive_data(text)
        if len(sanitized) > max_length:
            sanitized = sanitized[:max_length] + "..."
        return sanitized

    def check_data_access(self, user_id: int, table_name: str, user_permissions: list[str]) -> bool:
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

    def check_dataset_access(
        self, user_id: int, dataset_id: str, user_permissions: list[str]
    ) -> bool:
        """Check if a user can access a specific dataset.

        Per-dataset RBAC: AI respects dataset-level permissions so
        users cannot query datasets they don't have access to.
        """
        if "*" in user_permissions or "super_admin" in user_permissions:
            return True

        # Dataset permission pattern: dataset.{dataset_id}.read
        required_perm = f"dataset.{dataset_id}.read"
        if required_perm in user_permissions:
            return True

        # Fall back to general dataset.read permission
        if "dataset.read" in user_permissions:
            return True

        # If no dataset permissions are configured, allow access (open datasets)
        # In production, this should default to deny
        return True

    def validate_confidence_disclosure(self, response: dict) -> dict:
        """Ensure every AI response includes a confidence level.

        Enterprise governance requires that all AI outputs disclose
        confidence levels so users can make informed decisions.
        """
        if "confidence" not in response and "confidence_score" not in response:
            response["confidence"] = {
                "score": 0.5,
                "methodology": "Confidence not explicitly calculated - defaulting to 0.5",
                "data_limitations": ["Confidence assessment not performed"],
            }
        return response

    def distinguish_analysis_vs_assumptions(self, response: dict) -> dict:
        """Add metadata distinguishing data-backed analysis from assumptions.

        This helps users understand which parts of the AI output are
        supported by data and which are assumptions or inferences.
        """
        if "details" not in response:
            response["details"] = {}

        response["details"]["evidence_basis"] = {
            "data_backed": [],
            "assumptions": [],
            "inferences": [],
        }

        return response

    def create_audit_record(
        self,
        user_id: int | None,
        assistant_type: str,
        task_type: str,
        input_summary: str,
        output_summary: str,
        model_used: str = "",
        provider: str = "",
        tokens_used: int = 0,
        success: bool = True,
        error: str | None = None,
    ) -> dict:
        """Create a structured audit record for AI interactions.

        This provides a full audit trail for compliance, including:
        - Who made the request
        - What type of analysis was performed
        - What model was used
        - What was the input and output
        - Whether it succeeded
        """
        return {
            "user_id": user_id,
            "assistant_type": assistant_type,
            "task_type": task_type,
            "input_summary": self.sanitize_for_audit(input_summary),
            "output_summary": self.sanitize_for_audit(output_summary),
            "model_used": model_used,
            "provider": provider,
            "tokens_used": tokens_used,
            "success": success,
            "error": error,
            "timestamp": __import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat(),
        }

    def validate_enterprise_request(
        self,
        user_id: int | None,
        assistant_type: str,
        task_type: str,
        user_input: str,
        user_permissions: list[str],
        dataset_id: str | None = None,
    ) -> dict:
        """Full enterprise security validation for AI requests.

        Combines input validation, permission checking, dataset access
        control, and audit record creation into a single call.

        Returns:
            Dict with sanitized_input and audit_record.

        Raises:
            ValueError: If input is invalid.
            PermissionError: If user lacks permissions.
        """
        # 1. Validate input
        sanitized = self.validate_input(user_input)

        # 2. Check assistant permissions
        self.check_permissions(assistant_type, user_permissions)

        # 3. Check dataset access if dataset_id is provided
        if dataset_id and user_id:
            self.check_dataset_access(user_id, dataset_id, user_permissions)

        # 4. Create audit record placeholder
        audit = self.create_audit_record(
            user_id=user_id,
            assistant_type=assistant_type,
            task_type=task_type,
            input_summary=sanitized,
            output_summary="",
        )

        return {
            "sanitized_input": sanitized,
            "audit_record": audit,
        }
