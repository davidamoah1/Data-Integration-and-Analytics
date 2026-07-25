"""Validation Audit Logger — tracks all validation events for compliance."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any


class ValidationAuditLogger:
    """In-memory audit logger for validation events.

    For production, integrate with the existing audit system (audit.models.AuditLog).
    """

    _entries: list[dict] = []

    @classmethod
    def log(
        cls,
        event_type: str,
        user: str | None = None,
        organization: str | None = None,
        session_id: int | None = None,
        details: dict[str, Any] | None = None,
    ) -> dict:
        entry = {
            "event_type": event_type,
            "user": user,
            "organization": organization,
            "session_id": session_id,
            "details": json.dumps(details) if details else None,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        cls._entries.append(entry)
        return entry

    @classmethod
    def log_upload(cls, dataset_name: str, user: str | None = None, org: str | None = None):
        return cls.log("upload", user=user, organization=org, details={"dataset_name": dataset_name})

    @classmethod
    def log_validation(cls, session_id: int, status: str, score: float | None = None, user: str | None = None, org: str | None = None):
        return cls.log("validation", user=user, organization=org, session_id=session_id, details={"status": status, "score": score})

    @classmethod
    def log_approval(cls, session_id: int, approver: str, decision: str, comments: str = "", org: str | None = None):
        return cls.log("approval", user=approver, organization=org, session_id=session_id, details={"decision": decision, "comments": comments})

    @classmethod
    def log_rejection(cls, session_id: int, approver: str, comments: str = "", org: str | None = None):
        return cls.log("rejection", user=approver, organization=org, session_id=session_id, details={"comments": comments})

    @classmethod
    def log_correction(cls, session_id: int, user: str, correction_type: str, org: str | None = None):
        return cls.log("correction", user=user, organization=org, session_id=session_id, details={"correction_type": correction_type})

    @classmethod
    def log_etl_start(cls, session_id: int, user: str | None = None, org: str | None = None):
        return cls.log("etl_start", user=user, organization=org, session_id=session_id)

    @classmethod
    def log_etl_finish(cls, session_id: int, user: str | None = None, org: str | None = None, success: bool = True):
        return cls.log("etl_finish", user=user, organization=org, session_id=session_id, details={"success": success})

    @classmethod
    def get_entries(cls, event_type: str | None = None, session_id: int | None = None) -> list[dict]:
        entries = cls._entries
        if event_type:
            entries = [e for e in entries if e["event_type"] == event_type]
        if session_id is not None:
            entries = [e for e in entries if e.get("session_id") == session_id]
        return entries

    @classmethod
    def clear(cls):
        cls._entries.clear()
