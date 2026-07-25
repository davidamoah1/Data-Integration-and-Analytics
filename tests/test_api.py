"""Tests for the FastAPI endpoints."""

import os
import sys

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


@pytest.fixture
def client(tmp_path, monkeypatch):
    """Create a test client with a temporary SQLite database."""
    db_path = str(tmp_path / "test_api.db")
    db_url = f"sqlite:///{db_path}"

    import config

    monkeypatch.setattr(config, "DB_URL", db_url)
    monkeypatch.setattr(config, "DB_TYPE", "sqlite")

    monkeypatch.setenv("API_KEY", "test-api-key")

    from sqlalchemy import create_engine

    from database.db_setup import Base

    engine = create_engine(db_url)
    Base.metadata.create_all(engine)

    from api.main import app

    return TestClient(app)


def test_root_endpoint(client):
    response = client.get("/")
    assert response.status_code == 200
    # Root now serves the landing page (HTML) or a JSON fallback
    content_type = response.headers.get("content-type", "")
    if "text/html" in content_type:
        assert "DataFlow" in response.text
    else:
        data = response.json()
        assert "message" in data or "name" in data


def test_health_check(client):
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "database_connected" in data
    assert "record_count" in data


def test_health_check_ignores_api_key(client):
    response = client.get("/health", headers={"X-API-Key": "wrong-key"})
    assert response.status_code == 200


def test_health_check_returns_request_id(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert "X-Request-ID" in response.headers
    assert response.headers["X-Request-ID"]


def test_health_check_preserves_correlation_id(client):
    response = client.get("/health", headers={"X-Correlation-ID": "test-corr-123"})
    assert response.status_code == 200
    assert response.headers.get("X-Correlation-ID") == "test-corr-123"


def test_get_sales_empty_db(client):
    response = client.get("/api/v1/sales", headers={"X-API-Key": "test-api-key"})
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 0
    assert data["records"] == []


def test_get_kpis_empty_db(client):
    response = client.get("/api/v1/kpis", headers={"X-API-Key": "test-api-key"})
    assert response.status_code == 200
    data = response.json()
    assert data["total_sales"] == 0
    assert data["total_orders"] == 0


def test_get_filters_empty_db(client):
    response = client.get("/api/v1/filters", headers={"X-API-Key": "test-api-key"})
    assert response.status_code == 200
    data = response.json()
    assert data["regions"] == []
    assert data["categories"] == []


def test_api_key_via_query_param(client):
    response = client.get("/health?api_key=test-api-key")
    assert response.status_code == 200
