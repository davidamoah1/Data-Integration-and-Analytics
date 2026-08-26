"""Integration tests for backup endpoints."""

import pytest


@pytest.fixture
def backup_path_env(monkeypatch, tmp_path):
    """Use a temporary directory for backup tests."""
    monkeypatch.setenv("BACKUP_PATH", str(tmp_path / "backups"))


def test_backup_endpoints_require_admin(client):
    response = client.post("/platform/backups")
    assert response.status_code == 401


def test_create_and_list_backup(client, admin_token, backup_path_env):
    response = client.post("/platform/backups", headers={"Authorization": f"Bearer {admin_token}"})
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "id" in data["data"]

    response = client.get("/platform/backups", headers={"Authorization": f"Bearer {admin_token}"})
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert len(data["data"]) >= 1
