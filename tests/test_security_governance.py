"""Tests for enterprise security, governance, tenant isolation, and admin services."""

from __future__ import annotations

import io
from unittest.mock import MagicMock

import pandas as pd
import pytest
from fastapi import HTTPException

from governance import (
    DataClassification,
    DatasetLifecycle,
    classify_dataset,
    detect_sensitive_columns,
)
from shared.exceptions import AuthorizationError
from shared.tenant import (
    get_current_organization_id,
    is_super_admin,
    require_organization_access,
)


class TestTenantContext:
    """Organization isolation helpers."""

    def test_get_current_organization_id_success(self):
        user = {"id": 1, "organization_id": 42, "roles": ["analyst"]}
        assert get_current_organization_id(user) == 42

    def test_get_current_organization_id_missing(self):
        user = {"id": 1, "roles": ["analyst"]}
        with pytest.raises(HTTPException) as exc:
            get_current_organization_id(user)
        assert exc.value.status_code == 403

    def test_is_super_admin(self):
        assert is_super_admin({"id": 1, "roles": ["super_admin"]}) is True
        assert is_super_admin({"id": 1, "roles": ["analyst"]}) is False

    def test_require_organization_access_same_org(self):
        user = {"id": 1, "organization_id": 10, "roles": ["analyst"]}
        assert require_organization_access(user, 10) == 10

    def test_require_organization_access_without_target_returns_user_org(self):
        user = {"id": 1, "organization_id": 10, "roles": ["analyst"]}
        assert require_organization_access(user) == 10

    def test_require_organization_access_cross_org_denied(self):
        user = {"id": 1, "organization_id": 10, "roles": ["analyst"]}
        with pytest.raises(AuthorizationError):
            require_organization_access(user, 20)

    def test_require_organization_access_super_admin_bypass(self):
        user = {"id": 1, "organization_id": 10, "roles": ["super_admin"]}
        assert require_organization_access(user, 20) == 20


class TestPrivacyDetection:
    """PII and sensitive data detection."""

    def test_detect_email_column(self):
        df = pd.DataFrame({
            "email": ["alice@example.com", "bob@example.com"],
            "value": [1, 2],
        })
        flagged = detect_sensitive_columns(df)
        assert "email" in flagged
        assert "email" in flagged["email"]

    def test_detect_name_column(self):
        df = pd.DataFrame({
            "full_name": ["Alice Smith", "Bob Jones"],
            "phone": ["+1-555-123-4567", "+1-555-765-4321"],
        })
        flagged = detect_sensitive_columns(df)
        assert "full_name" in flagged
        assert "phone" in flagged

    def test_no_false_positives_on_generic_columns(self):
        df = pd.DataFrame({
            "product_id": [101, 102],
            "quantity": [5, 10],
        })
        flagged = detect_sensitive_columns(df)
        assert "product_id" not in flagged
        assert "quantity" not in flagged


class TestGovernanceClassification:
    """Dataset classification and lifecycle controls."""

    def test_sensitive_dataset_blocks_publishing(self):
        df = pd.DataFrame({
            "patient_name": ["Alice", "Bob"],
            "diagnosis": ["Flu", "Cold"],
            "ssn": ["123456789", "987654321"],
        })
        result = classify_dataset(df, lifecycle=DatasetLifecycle.PUBLISHED)
        assert result.classification == DataClassification.SENSITIVE
        assert "publishing" in result.blocked_actions
        assert any("Sensitive datasets cannot be published" in w for w in result.warnings)

    def test_public_dataset_no_warnings(self):
        df = pd.DataFrame({
            "year": [2024, 2025],
            "revenue": [1000, 2000],
        })
        result = classify_dataset(df)
        assert result.classification == DataClassification.INTERNAL
        assert not result.sensitive_columns
        assert not result.warnings


class TestAdminServiceOrganizationIsolation:
    """Admin service enforces organization boundaries."""

    def test_regular_admin_cannot_list_other_org(self):
        from admin.service import AdminService

        db = MagicMock()
        user = {"id": 1, "organization_id": 5, "roles": ["organization_admin"]}
        service = AdminService(db, user)

        with pytest.raises(AuthorizationError):
            service.list_users(org_id=99)

    def test_super_admin_can_list_any_org(self):
        from admin.service import AdminService

        db = MagicMock()
        user = {"id": 1, "organization_id": 5, "roles": ["super_admin"]}
        service = AdminService(db, user)

        db.execute.return_value.scalar.return_value = 0
        db.execute.return_value.scalars.return_value.all.return_value = []
        result = service.list_users(org_id=99)
        assert result == []


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
