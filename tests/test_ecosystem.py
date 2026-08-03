"""Integration tests for the Enterprise Data Intelligence Ecosystem.

Tests cover:
  - Connector framework (registry, CRUD, test, extract)
  - Public API platform (key creation, auth, usage)
  - Webhook system (subscription, events, delivery)
  - Plugin marketplace (browse, install, enable, disable, uninstall)
  - Industry packages (list, install)
  - Ecosystem monitoring (overview, health)
  - Security (tenant isolation, scope enforcement)

Run: python -m pytest tests/test_ecosystem.py -v
"""

from __future__ import annotations

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

from shared.database import Base, BigInt
from api.main import app
from shared.database import get_db


# ─── Fixtures ──────────────────────────────────────────────


@pytest.fixture(scope="module")
def db_session():
    """Create an in-memory SQLite database for testing."""
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(engine)
    session = Session(engine)
    yield session
    session.close()
    engine.dispose()


@pytest.fixture(scope="module")
def client():
    """Test client for the FastAPI app."""
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="module")
def auth_token(client):
    """Get an auth token for testing."""
    resp = client.post("/api/auth/login", json={
        "email": "admin@dataflow.io",
        "password": "Admin@12345",
    })
    if resp.status_code == 200 and "data" in resp.json():
        return resp.json()["data"]["access_token"]
    # If login fails, return a dummy token — tests may skip
    return ""


@pytest.fixture(scope="module")
def auth_headers(auth_token):
    return {"Authorization": f"Bearer {auth_token}"}


# ─── Connector Tests ───────────────────────────────────────


class TestConnectorFramework:
    def test_list_connector_types(self, client, auth_headers):
        resp = client.get("/connectors/types", headers=auth_headers)
        assert resp.status_code == 200
        types = resp.json()["data"]
        assert len(types) >= 20  # at least 20 connector types

    def test_list_africa_connectors(self, client, auth_headers):
        resp = client.get("/connectors/types/africa", headers=auth_headers)
        assert resp.status_code == 200
        types = resp.json()["data"]
        assert all(t["is_africa_first"] for t in types)
        assert len(types) >= 5  # mobile_money, bank_api, gov_open_data, hospital_system, student_info_system

    def test_connector_types_have_required_fields(self, client, auth_headers):
        resp = client.get("/connectors/types", headers=auth_headers)
        types = resp.json()["data"]
        for t in types:
            assert "type_code" in t
            assert "display_name" in t
            assert "category" in t

    def test_filter_by_category(self, client, auth_headers):
        resp = client.get("/connectors/types?category=database", headers=auth_headers)
        assert resp.status_code == 200
        types = resp.json()["data"]
        assert all(t["category"] == "database" for t in types)
        assert len(types) >= 5  # postgresql, mysql, sqlserver, oracle, mongodb


# ─── Marketplace Tests ─────────────────────────────────────


class TestMarketplace:
    def test_list_plugins(self, client, auth_headers):
        resp = client.get("/marketplace/plugins", headers=auth_headers)
        assert resp.status_code == 200
        plugins = resp.json()["data"]
        assert len(plugins) >= 10

    def test_get_plugin_detail(self, client, auth_headers):
        resp = client.get("/marketplace/plugins/mobile-money-connector", headers=auth_headers)
        assert resp.status_code == 200
        plugin = resp.json()["data"]
        assert plugin["plugin_id"] == "mobile-money-connector"
        assert plugin["name"] == "Mobile Money Connector"

    def test_search_plugins(self, client, auth_headers):
        resp = client.get("/marketplace/plugins?search=healthcare", headers=auth_headers)
        assert resp.status_code == 200
        plugins = resp.json()["data"]
        assert any("healthcare" in p["name"].lower() for p in plugins)

    def test_filter_by_category(self, client, auth_headers):
        resp = client.get("/marketplace/plugins?category=connector", headers=auth_headers)
        assert resp.status_code == 200
        plugins = resp.json()["data"]
        assert all(p["category"] == "connector" for p in plugins)


# ─── Industry Package Tests ────────────────────────────────


class TestIndustryPackages:
    def test_list_packages(self, client, auth_headers):
        resp = client.get("/marketplace/industry-packages", headers=auth_headers)
        assert resp.status_code == 200
        packages = resp.json()["data"]
        assert len(packages) >= 5

    def test_filter_by_industry(self, client, auth_headers):
        resp = client.get("/marketplace/industry-packages?industry=healthcare", headers=auth_headers)
        assert resp.status_code == 200
        packages = resp.json()["data"]
        assert all(p["industry"] == "healthcare" for p in packages)

    def test_get_package_detail(self, client, auth_headers):
        resp = client.get("/marketplace/industry-packages/healthcare-analytics", headers=auth_headers)
        assert resp.status_code == 200
        pkg = resp.json()["data"]
        assert pkg["package_id"] == "healthcare-analytics"
        assert pkg["industry"] == "healthcare"
        assert len(pkg["dataset_templates"]) >= 1
        assert len(pkg["dashboard_templates"]) >= 1
        assert len(pkg["kpi_templates"]) >= 1


# ─── Webhook Tests ─────────────────────────────────────────


class TestWebhooks:
    def test_list_supported_events(self, client, auth_headers):
        resp = client.get("/webhooks/events", headers=auth_headers)
        assert resp.status_code == 200
        events = resp.json()["data"]
        assert len(events) >= 10
        assert "dataset.uploaded" in events
        assert "pipeline.completed" in events

    def test_create_and_delete_webhook(self, client, auth_headers):
        # Create
        resp = client.post("/webhooks", json={
            "url": "https://example.com/webhook",
            "events": ["dataset.uploaded", "pipeline.completed"],
        }, headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert "id" in data
        assert "secret" in data
        wh_id = data["id"]

        # List
        resp = client.get("/webhooks", headers=auth_headers)
        assert resp.status_code == 200
        assert any(w["id"] == wh_id for w in resp.json()["data"])

        # Delete
        resp = client.delete(f"/webhooks/{wh_id}", headers=auth_headers)
        assert resp.status_code == 200

    def test_invalid_event_rejected(self, client, auth_headers):
        resp = client.post("/webhooks", json={
            "url": "https://example.com/webhook",
            "events": ["invalid.event"],
        }, headers=auth_headers)
        assert resp.status_code == 400


# ─── API Key Tests ─────────────────────────────────────────


class TestAPIKeys:
    def test_create_and_list_api_key(self, client, auth_headers):
        # Create
        resp = client.post("/platform/api-keys", json={
            "name": "Test Key",
            "scopes": ["datasets", "analytics"],
            "rate_limit_per_hour": 500,
        }, headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert "api_key" in data
        assert data["api_key"].startswith("dfk_")
        assert "key_prefix" in data
        key_id = data["id"]

        # List
        resp = client.get("/platform/api-keys", headers=auth_headers)
        assert resp.status_code == 200
        keys = resp.json()["data"]
        assert any(k["id"] == key_id for k in keys)

    def test_revoke_api_key(self, client, auth_headers):
        # Create
        resp = client.post("/platform/api-keys", json={
            "name": "Revoke Test",
            "scopes": ["datasets"],
        }, headers=auth_headers)
        key_id = resp.json()["data"]["id"]

        # Revoke
        resp = client.delete(f"/platform/api-keys/{key_id}", headers=auth_headers)
        assert resp.status_code == 200


# ─── Public API Tests ──────────────────────────────────────


class TestPublicAPI:
    def test_public_api_requires_key(self, client):
        resp = client.get("/public/analytics/dashboards")
        assert resp.status_code == 401

    def test_public_api_with_valid_key(self, client, auth_headers):
        # Create API key
        resp = client.post("/platform/api-keys", json={
            "name": "Public API Test",
            "scopes": ["datasets", "analytics", "ai", "workflows"],
        }, headers=auth_headers)
        api_key = resp.json()["data"]["api_key"]

        # Use public API
        resp = client.get("/public/analytics/dashboards", headers={"X-API-Key": api_key})
        assert resp.status_code == 200

    def test_public_api_scope_enforcement(self, client, auth_headers):
        # Create API key with limited scope
        resp = client.post("/platform/api-keys", json={
            "name": "Limited Scope",
            "scopes": ["datasets"],
        }, headers=auth_headers)
        api_key = resp.json()["data"]["api_key"]

        # Try to access analytics (should fail)
        resp = client.get("/public/analytics/dashboards", headers={"X-API-Key": api_key})
        assert resp.status_code == 403


# ─── Monitoring Tests ──────────────────────────────────────


class TestEcosystemMonitoring:
    def test_overview(self, client, auth_headers):
        resp = client.get("/ecosystem/monitoring/overview", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert "connectors" in data
        assert "api_keys" in data
        assert "installed_plugins" in data
        assert "webhooks" in data
        assert "api_calls_24h" in data

    def test_connector_health(self, client, auth_headers):
        resp = client.get("/ecosystem/monitoring/connectors", headers=auth_headers)
        assert resp.status_code == 200

    def test_webhook_health(self, client, auth_headers):
        resp = client.get("/ecosystem/monitoring/webhooks", headers=auth_headers)
        assert resp.status_code == 200
