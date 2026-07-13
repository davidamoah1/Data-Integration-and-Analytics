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

    # Patch DB_URL in all modules that imported it at module level
    from database import repositories
    monkeypatch.setattr(repositories, "DB_URL", db_url)
    from database import db_setup
    monkeypatch.setattr(db_setup, "DB_URL", db_url)

    monkeypatch.setenv("API_KEY", "test-api-key")

    from database.db_setup import Base
    from sqlalchemy import create_engine
    engine = create_engine(db_url)
    Base.metadata.create_all(engine)

    from api.main import app
    return TestClient(app)


def test_root_endpoint(client):
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "DataFlow — Enterprise Data Intelligence API"


def test_health_check(client):
    response = client.get("/health", headers={"X-API-Key": "test-api-key"})
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "database_connected" in data
    assert "record_count" in data


def test_health_check_no_api_key(client):
    response = client.get("/health")
    assert response.status_code == 401


def test_health_check_wrong_api_key(client):
    response = client.get("/health", headers={"X-API-Key": "wrong-key"})
    assert response.status_code == 401


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
