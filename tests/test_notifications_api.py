"""Integration tests for notification REST endpoints."""

import pytest

from notifications.models import Notification
from notifications.service import NotificationService


@pytest.fixture
def sample_notification(db_session):
    return NotificationService(db_session).send_in_app(subject="Test", body="Hello", user_id=1)


def test_list_notifications_requires_auth(client):
    response = client.get("/notifications")
    assert response.status_code == 401


def test_list_notifications_returns_user_items(client, auth_headers):
    response = client.get("/notifications", headers=auth_headers)
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_mark_read(client, auth_headers, db_session):
    result = NotificationService(db_session).send_in_app(
        subject="Read me", body="Please", user_id=1
    )
    notif_id = result["id"]
    response = client.post(f"/notifications/{notif_id}/read", headers=auth_headers)
    assert response.status_code == 200
    assert response.json() == {"id": notif_id, "read": True}


def test_mark_read_forbidden_for_other_user(client, auth_headers, db_session):
    result = NotificationService(db_session).send_in_app(
        subject="Private", body="Not yours", user_id=999
    )
    notif_id = result["id"]
    response = client.post(f"/notifications/{notif_id}/read", headers=auth_headers)
    assert response.status_code == 403


def test_delete_notification(client, auth_headers, db_session):
    result = NotificationService(db_session).send_in_app(subject="Delete me", body="Bye", user_id=1)
    notif_id = result["id"]
    response = client.delete(f"/notifications/{notif_id}", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["deleted"] is True
    assert db_session.query(Notification).filter(Notification.id == notif_id).first() is None
