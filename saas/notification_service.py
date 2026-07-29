"""Centralized notification system — multi-channel event notifications.

Channels: in-app, email, SMS (pluggable), webhooks.
Events: workflow completed, dataset processed, subscription changes, security alerts, billing, maintenance.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session as DbSession

from saas.models import NotificationPreference

logger = logging.getLogger("etl_project.notifications")

# Reuse existing notifications model
from notifications.models import Notification  # noqa: E402


# Event type mapping
EVENT_TYPES = {
    "workflow_completed": "event_workflow_completed",
    "dataset_processed": "event_dataset_processed",
    "subscription_changed": "event_subscription_changes",
    "security_alert": "event_security_alerts",
    "billing_reminder": "event_billing_reminders",
    "system_maintenance": "event_system_maintenance",
}


class NotificationService:
    """Centralized notification dispatcher."""

    def __init__(self, db: DbSession):
        self.db = db
        self._email_provider = None
        self._sms_provider = None

    def register_email_provider(self, provider):
        """Register an email provider (e.g., SendGrid, AWS SES)."""
        self._email_provider = provider

    def register_sms_provider(self, provider):
        """Register an SMS provider (e.g., Twilio, Africa's Talking)."""
        self._sms_provider = provider

    def send(
        self,
        user_id: int,
        org_id: int,
        event_type: str,
        subject: str,
        body: str,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Send a notification across enabled channels based on user preferences."""
        pref = self._get_preferences(user_id, org_id)
        pref_field = EVENT_TYPES.get(event_type)

        # Check if the user has this event type enabled
        if pref_field and not getattr(pref, pref_field, True):
            return

        channels_sent = []

        # In-app (always stored)
        if pref.channel_in_app:
            notif = Notification(
                user_id=user_id,
                channel="in_app",
                subject=subject,
                body=body,
                status="pending",
            )
            self.db.add(notif)
            channels_sent.append("in_app")

        # Email
        if pref.channel_email and self._email_provider:
            try:
                self._email_provider.send(user_id, subject, body)
                channels_sent.append("email")
            except Exception as e:
                logger.error(f"Email notification failed: {e}")

        # SMS
        if pref.channel_sms and self._sms_provider:
            try:
                self._sms_provider.send(user_id, body)
                channels_sent.append("sms")
            except Exception as e:
                logger.error(f"SMS notification failed: {e}")

        # Webhook (dispatch to ecosystem webhook system)
        if pref.channel_webhook:
            try:
                from ecosystem.webhooks import WebhookDispatcher
                WebhookDispatcher.dispatch(self.db, org_id, event_type, {
                    "subject": subject,
                    "body": body,
                    "metadata": metadata or {},
                    "user_id": user_id,
                })
                channels_sent.append("webhook")
            except Exception as e:
                logger.error(f"Webhook notification failed: {e}")

        self.db.commit()
        logger.info(f"Notification sent to user {user_id}: {event_type} via {channels_sent}")

    def _get_preferences(self, user_id: int, org_id: int) -> NotificationPreference:
        pref = self.db.execute(
            select(NotificationPreference).where(
                NotificationPreference.user_id == user_id,
                NotificationPreference.organization_id == org_id,
            )
        ).scalar_one_or_none()

        if not pref:
            pref = NotificationPreference(
                user_id=user_id,
                organization_id=org_id,
            )
            self.db.add(pref)
            self.db.flush()
            self.db.commit()
        return pref

    def broadcast_to_org(
        self,
        org_id: int,
        event_type: str,
        subject: str,
        body: str,
    ) -> int:
        """Send a notification to all users in an organization."""
        from authentication.models import User
        users = self.db.execute(
            select(User).where(
                User.organization_id == org_id,
                User.is_active == 1,
                User.is_deleted == 0,
            )
        ).scalars().all()

        count = 0
        for user in users:
            self.send(user.id, org_id, event_type, subject, body)
            count += 1
        return count


# Pluggable provider interfaces


class EmailProviderInterface:
    """Abstract interface for email providers."""

    def send(self, user_id: int, subject: str, body: str) -> None:
        raise NotImplementedError


class SMSProviderInterface:
    """Abstract interface for SMS providers."""

    def send(self, user_id: int, message: str) -> None:
        raise NotImplementedError


class ConsoleEmailProvider(EmailProviderInterface):
    """Development email provider that logs to console."""

    def send(self, user_id: int, subject: str, body: str) -> None:
        logger.info(f"[EMAIL] To user {user_id}: {subject}")


class ConsoleSMSProvider(SMSProviderInterface):
    """Development SMS provider that logs to console."""

    def send(self, user_id: int, message: str) -> None:
        logger.info(f"[SMS] To user {user_id}: {message[:100]}")
