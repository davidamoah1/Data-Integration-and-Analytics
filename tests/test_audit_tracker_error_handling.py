"""Regression test: track_action decorator must log (not silently swallow)
audit-logging failures, so gaps in the audit trail are visible in logs.
"""

from __future__ import annotations

import asyncio
import logging

from platform_features.audit_tracker import AuditCategory, track_action


def test_track_action_logs_warning_on_audit_failure(caplog):
    @track_action("test_action", AuditCategory.DATA_ACCESS, "dataset")
    async def handler(*, current_user=None, request=None, db=None):
        return {"ok": True}

    class ExplodingDb:
        """Stand-in `db` that causes AuditTracker construction/logging to fail."""

        def query(self, *a, **kw):
            raise RuntimeError("db unavailable")

        def commit(self):
            raise RuntimeError("db unavailable")

    with caplog.at_level(logging.WARNING, logger="platform_features.audit_tracker"):
        result = asyncio.run(
            handler(current_user={"id": 1, "organization_id": 1}, request=None, db=ExplodingDb())
        )

    assert result == {"ok": True}
    assert any("Audit logging failed" in r.message for r in caplog.records)
