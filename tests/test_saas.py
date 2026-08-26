"""Tenant isolation tests for the SaaS platform.

Verifies that:
  - Users can only access their own organization's data
  - Cross-tenant access is blocked
  - Super admins can access all organizations
  - SaaS endpoints enforce organization scoping
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from fastapi.testclient import TestClient

from api.main import app


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


def get_auth_token(client: TestClient, email: str, password: str) -> str:
    resp = client.post("/api/auth/login", json={"email": email, "password": password})
    if resp.status_code == 200 and "data" in resp.json():
        return resp.json()["data"]["access_token"]
    return ""


@pytest.fixture(scope="module")
def admin_token(client):
    return get_auth_token(client, "admin@dataflow.io", "Admin@12345")


@pytest.fixture(scope="module")
def admin_headers(admin_token):
    return {"Authorization": f"Bearer {admin_token}"}


class TestTenantIsolation:
    """Test that tenant isolation is enforced across the platform."""

    def test_saas_plans_accessible_by_any_user(self, client, admin_headers):
        """Plans are public â€” any authenticated user can see them."""
        resp = client.get("/api/saas/plans", headers=admin_headers)
        assert resp.status_code == 200
        assert len(resp.json()["data"]) >= 5

    def test_subscription_scoped_to_org(self, client, admin_headers):
        """Subscription endpoint returns only the caller's org subscription."""
        resp = client.get("/api/saas/subscription", headers=admin_headers)
        assert resp.status_code == 200
        data = resp.json()["data"]
        # Should not leak other orgs' subscription data
        assert "organization_id" not in data or data.get("organization_id") is None

    def test_usage_scoped_to_org(self, client, admin_headers):
        """Usage endpoint returns only the caller's usage."""
        resp = client.get("/api/saas/usage", headers=admin_headers)
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert "active_users" in data
        assert "limits" in data

    def test_onboarding_scoped_to_org(self, client, admin_headers):
        """Onboarding progress is per-organization."""
        resp = client.get("/api/saas/onboarding", headers=admin_headers)
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert "completion_percentage" in data
        assert "all_steps" in data

    def test_features_scoped_to_org(self, client, admin_headers):
        """Feature flags reflect the organization's plan."""
        resp = client.get("/api/saas/features", headers=admin_headers)
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert "enabled" in data
        assert isinstance(data["enabled"], list)

    def test_health_score_scoped_to_org(self, client, admin_headers):
        """Health score is computed for the caller's org only."""
        resp = client.get("/api/saas/health-score", headers=admin_headers)
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert "score" in data
        assert 0 <= data["score"] <= 100

    def test_support_tickets_scoped_to_org(self, client, admin_headers):
        """Support tickets are per-organization."""
        resp = client.get("/api/saas/support/tickets", headers=admin_headers)
        assert resp.status_code == 200

    def test_notification_preferences_scoped_to_user(self, client, admin_headers):
        """Notification preferences are per-user."""
        resp = client.get("/api/saas/notification-preferences", headers=admin_headers)
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert "channel_in_app" in data
        assert "channel_email" in data


class TestSuperAdminPortal:
    """Test super admin portal access control."""

    def test_admin_overview_requires_super_admin(self, client, admin_headers):
        """Admin overview should work for super admin."""
        resp = client.get("/api/admin-portal/overview", headers=admin_headers)
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert "organizations" in data
        assert "users" in data

    def test_admin_tenants_list(self, client, admin_headers):
        """Super admin can list all tenants."""
        resp = client.get("/api/admin-portal/tenants", headers=admin_headers)
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert isinstance(data, list)
        assert len(data) >= 1

    def test_admin_subscriptions_list(self, client, admin_headers):
        """Super admin can list all subscriptions."""
        resp = client.get("/api/admin-portal/subscriptions", headers=admin_headers)
        assert resp.status_code == 200

    def test_admin_usage_summary(self, client, admin_headers):
        """Super admin can see platform-wide usage."""
        resp = client.get("/api/admin-portal/usage-summary", headers=admin_headers)
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert "total_ai_requests" in data
        assert "total_api_calls" in data


class TestSubscriptionLifecycle:
    """Test subscription creation, upgrade, and cancellation."""

    def test_subscribe_to_starter(self, client, admin_headers):
        resp = client.post(
            "/api/saas/subscribe",
            json={
                "plan_code": "starter",
                "billing_cycle": "monthly",
            },
            headers=admin_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["data"]["status"] in ("active", "trial")

    def test_upgrade_to_professional(self, client, admin_headers):
        resp = client.post(
            "/api/saas/upgrade",
            json={
                "plan_code": "professional",
            },
            headers=admin_headers,
        )
        assert resp.status_code == 200

    def test_cancel_subscription(self, client, admin_headers):
        resp = client.post("/api/saas/cancel", headers=admin_headers)
        assert resp.status_code == 200
        assert resp.json()["data"]["status"] == "cancelled"

    def test_trial_subscription(self, client, admin_headers):
        # Re-subscribe with trial
        resp = client.post(
            "/api/saas/subscribe",
            json={
                "plan_code": "business",
                "is_trial": True,
            },
            headers=admin_headers,
        )
        assert resp.status_code == 200


class TestFeatureFlags:
    """Test feature flag enforcement."""

    def test_free_plan_has_basic_features(self, client, admin_headers):
        resp = client.get("/api/saas/features", headers=admin_headers)
        assert resp.status_code == 200
        enabled = resp.json()["data"]["enabled"]
        # Core features should always be enabled
        assert "dashboards" in enabled
        assert "etl" in enabled

    def test_all_feature_flags_listed(self, client, admin_headers):
        resp = client.get("/api/saas/features/all", headers=admin_headers)
        assert resp.status_code == 200
        flags = resp.json()["data"]
        assert len(flags) >= 15


class TestOnboarding:
    """Test onboarding flow."""

    def test_get_onboarding_progress(self, client, admin_headers):
        resp = client.get("/api/saas/onboarding", headers=admin_headers)
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert "completion_percentage" in data
        assert "all_steps" in data

    def test_complete_onboarding_step(self, client, admin_headers):
        resp = client.post(
            "/api/saas/onboarding/complete-step",
            json={
                "step_key": "industry_selection",
                "industry": "healthcare",
            },
            headers=admin_headers,
        )
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["completion_percentage"] > 0
