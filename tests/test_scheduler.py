"""Tests for scheduled report API and scheduler."""

import pytest

from scheduler.models import ScheduledReport


@pytest.fixture(autouse=True)
def _set_pytest_running(monkeypatch):
    monkeypatch.setenv("PYTEST_RUNNING", "1")


def test_list_scheduled_reports_requires_auth(client):
    response = client.get("/api/scheduler/reports")
    assert response.status_code == 401


def test_create_and_list_scheduled_report(client, auth_headers):
    create_resp = client.post(
        "/api/scheduler/reports",
        headers=auth_headers,
        json={
            "name": "Weekly Summary",
            "report_type": "executive",
            "title": "Weekly Executive Summary",
            "cron": "0 8 * * 1",
            "parameters": {"format": "pdf"},
        },
    )
    assert create_resp.status_code == 201
    data = create_resp.json()
    assert data["name"] == "Weekly Summary"
    assert data["cron"] == "0 8 * * 1"

    list_resp = client.get("/api/scheduler/reports", headers=auth_headers)
    assert list_resp.status_code == 200
    reports = list_resp.json()
    assert any(r["name"] == "Weekly Summary" for r in reports)


def test_toggle_and_delete_scheduled_report(client, auth_headers, db_session):
    create_resp = client.post(
        "/api/scheduler/reports",
        headers=auth_headers,
        json={
            "name": "Daily KPI",
            "report_type": "kpi",
            "cron": "0 7 * * *",
        },
    )
    report_id = create_resp.json()["id"]

    toggle_resp = client.post(f"/api/scheduler/reports/{report_id}/toggle", headers=auth_headers)
    assert toggle_resp.status_code == 200
    assert toggle_resp.json()["is_active"] is False

    delete_resp = client.delete(f"/api/scheduler/reports/{report_id}", headers=auth_headers)
    assert delete_resp.status_code == 200
    assert db_session.query(ScheduledReport).filter(ScheduledReport.id == report_id).first() is None


def test_sync_scheduled_reports(client, auth_headers):
    response = client.post("/api/scheduler/reports/sync", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["synced"] is True
