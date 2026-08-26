"""Unit tests for the notification service and workflow wiring."""

from unittest.mock import patch

from ai.workflow import WorkflowEngine
from notifications.models import Notification
from notifications.service import NotificationService


def test_send_in_app_creates_record(db_session):
    service = NotificationService(db_session)
    result = service.send_in_app(subject="Hello", body="World", user_id=1)
    assert result["sent"] is True
    assert result["channel"] == "in_app"
    assert result["id"] is not None
    record = db_session.query(Notification).filter(Notification.id == result["id"]).first()
    assert record is not None
    assert record.subject == "Hello"
    assert record.body == "World"
    assert record.user_id == 1


def test_send_email_skipped_without_smtp(db_session):
    service = NotificationService(db_session)
    result = service.send_email(to="user@example.com", subject="Hi", body=" there", user_id=1)
    assert result["sent"] is False
    assert result["channel"] == "email"
    assert "SMTP not configured" in result["note"]


def test_send_email_uses_smtp_when_configured(db_session):
    service = NotificationService(db_session)
    with (
        patch.dict(
            "os.environ",
            {
                "SMTP_HOST": "smtp.example.com",
                "SMTP_PORT": "587",
                "SMTP_USER": "user",
                "SMTP_PASSWORD": "pass",
                "SMTP_FROM": "from@example.com",
            },
            clear=False,
        ),
        patch("notifications.service.smtplib.SMTP") as mock_smtp,
    ):
        result = service.send_email(to="to@example.com", subject="Hi", body="there", user_id=1)
        assert result["sent"] is True
        assert result["to"] == "to@example.com"
        mock_smtp.assert_called_once()


def test_workflow_notify_step_creates_notification(db_session):
    engine = WorkflowEngine(db_session)
    result = engine._step_notify({"message": "Pipeline done"}, {}, user_id=5)
    assert result["notification_sent"] is True
    assert result["message"] == "Pipeline done"
    record = db_session.query(Notification).filter(Notification.id == result["id"]).first()
    assert record.body == "Pipeline done"
    assert record.user_id == 5


def test_workflow_email_step_requires_recipient(db_session):
    engine = WorkflowEngine(db_session)
    result = engine._step_email({}, {}, user_id=5)
    assert result["email_sent"] is False
    assert "No recipient" in result["note"]
