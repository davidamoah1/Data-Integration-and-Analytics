"""Notification service supporting email, SMS, WhatsApp, push, and in-app channels.

Email is sent via SMTP when the required environment variables are set. SMS,
WhatsApp, and push are stubbed with clear configuration messages so that real
providers (Twilio, Firebase, etc.) can be wired in production.
"""

from __future__ import annotations

import os
import smtplib
from datetime import datetime, timezone
from email.mime.text import MIMEText
from typing import Any

from sqlalchemy.orm import Session as DbSession

from etl.logging_config import logger
from notifications.models import Notification


class NotificationService:
    """Send notifications through multiple channels."""

    def __init__(self, db: DbSession | None = None):
        """Initialize with an optional DB session for in-app logging."""
        self.db = db

    def _log(
        self,
        channel: str,
        subject: str,
        body: str,
        status: str,
        user_id: int | None = None,
        org_id: int | None = None,
    ) -> Notification | None:
        """Persist an in-app notification record when a DB session is available."""
        if self.db is None:
            return None
        try:
            record = Notification(
                user_id=user_id,
                organization_id=org_id,
                channel=channel,
                subject=subject,
                body=body,
                status=status,
                sent_at=datetime.now(timezone.utc) if status in ("sent", "skipped") else None,
            )
            self.db.add(record)
            self.db.commit()
            self.db.refresh(record)
            return record
        except Exception:
            logger.exception("Failed to persist notification record")
            if self.db:
                self.db.rollback()
            return None

    def send_in_app(
        self,
        subject: str,
        body: str,
        user_id: int | None = None,
        org_id: int | None = None,
    ) -> dict:
        """Create an in-app notification record."""
        record = self._log("in_app", subject, body, "sent", user_id, org_id)
        return {"sent": True, "channel": "in_app", "id": record.id if record else None}

    def send_email(
        self,
        to: str,
        subject: str,
        body: str,
        user_id: int | None = None,
        org_id: int | None = None,
    ) -> dict:
        """Send an email via SMTP when configured; otherwise return a skip status."""
        host = os.getenv("SMTP_HOST")
        port = int(os.getenv("SMTP_PORT", "587"))
        user = os.getenv("SMTP_USER")
        password = os.getenv("SMTP_PASSWORD")
        from_addr = os.getenv("SMTP_FROM", user or "noreply@dataflow.io")

        if not host or not user or not password:
            logger.warning("SMTP not configured; email notification skipped.")
            self._log("email", subject, body, "skipped", user_id, org_id)
            return {"sent": False, "channel": "email", "note": "SMTP not configured"}

        try:
            msg = MIMEText(body, "plain", "utf-8")
            msg["Subject"] = subject
            msg["From"] = from_addr
            msg["To"] = to

            with smtplib.SMTP(host, port, timeout=30) as server:
                server.starttls()
                server.login(user, password)
                server.sendmail(from_addr, [to], msg.as_string())

            self._log("email", subject, body, "sent", user_id, org_id)
            return {"sent": True, "channel": "email", "to": to}
        except Exception as exc:
            logger.exception("Failed to send email to %s", to)
            self._log("email", subject, body, "failed", user_id, org_id)
            return {"sent": False, "channel": "email", "error": str(exc)}

    def send_sms(
        self,
        phone: str,
        message: str,
        user_id: int | None = None,
        org_id: int | None = None,
    ) -> dict:
        """SMS stub â€” integrate Twilio or similar in production."""
        self._log("sms", "SMS notification", message, "skipped", user_id, org_id)
        return {"sent": False, "channel": "sms", "note": "SMS provider not configured"}

    def send_whatsapp(
        self,
        phone: str,
        message: str,
        user_id: int | None = None,
        org_id: int | None = None,
    ) -> dict:
        """WhatsApp stub â€” integrate Twilio/WhatsApp Business API in production."""
        self._log("whatsapp", "WhatsApp notification", message, "skipped", user_id, org_id)
        return {"sent": False, "channel": "whatsapp", "note": "WhatsApp provider not configured"}

    def send_push(
        self,
        token: str,
        title: str,
        body: str,
        user_id: int | None = None,
        org_id: int | None = None,
    ) -> dict:
        """Push notification stub â€” integrate Firebase Cloud Messaging in production."""
        self._log("push", title, body, "skipped", user_id, org_id)
        return {"sent": False, "channel": "push", "note": "Push provider not configured"}

    def send(
        self,
        channel: str,
        recipient: str,
        subject: str,
        body: str,
        user_id: int | None = None,
        org_id: int | None = None,
    ) -> dict:
        """Dispatch a notification by channel."""
        handlers: dict[str, Any] = {
            "email": lambda: self.send_email(recipient, subject, body, user_id, org_id),
            "sms": lambda: self.send_sms(recipient, body, user_id, org_id),
            "whatsapp": lambda: self.send_whatsapp(recipient, body, user_id, org_id),
            "push": lambda: self.send_push(recipient, subject, body, user_id, org_id),
            "in_app": lambda: self.send_in_app(subject, body, user_id, org_id),
        }
        handler = handlers.get(channel)
        if not handler:
            return {"sent": False, "channel": channel, "note": f"Unsupported channel: {channel}"}
        return handler()
