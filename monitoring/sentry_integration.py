"""Sentry error tracking integration.

Initialises the Sentry SDK when SENTRY_DSN is configured and provides
helpers for capturing exceptions, setting user context, and adding breadcrumbs.

Usage:
    from monitoring.sentry import init_sentry, capture_exception, set_user_context

    init_sentry()  # call once at startup (no-op if SENTRY_DSN is unset)
"""

import logging
import os
from typing import Any

_sentry_initialised = False


def init_sentry() -> bool:
    """Initialise the Sentry SDK if SENTRY_DSN is set.

    Returns True if Sentry was initialised, False otherwise.
    """
    global _sentry_initialised
    if _sentry_initialised:
        return True

    dsn = os.getenv("SENTRY_DSN", "").strip()
    if not dsn:
        return False

    try:
        import sentry_sdk
        from sentry_sdk.integrations.fastapi import FastApiIntegration
        from sentry_sdk.integrations.logging import LoggingIntegration
        from sentry_sdk.integrations.redis import RedisIntegration
        from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
        from sentry_sdk.integrations.threading import ThreadingIntegration
    except ImportError:
        return False

    environment = os.getenv("APP_ENV", "development")
    sample_rate = float(os.getenv("SENTRY_TRACES_SAMPLE_RATE") or "0.1")
    profiles_rate = float(os.getenv("SENTRY_PROFILES_SAMPLE_RATE") or "0.1")

    sentry_sdk.init(
        dsn=dsn,
        environment=environment,
        release=os.getenv("SENTRY_RELEASE", "aedip@1.0.0"),
        send_default_pii=False,
        traces_sample_rate=sample_rate,
        profiles_sample_rate=profiles_rate,
        attach_stackclip=True,
        max_breadcrumbs=100,
        integrations=[
            FastApiIntegration(transaction_style="endpoint"),
            SqlalchemyIntegration(),
            RedisIntegration(),
            LoggingIntegration(
                level=logging.INFO,
                event_level=logging.ERROR,
            ),
            ThreadingIntegration(propagate_hub=True),
        ],
        before_send=_before_send_filter,
    )

    _sentry_initialised = True
    return True


def _before_send_filter(event: dict, hint: dict) -> dict | None:
    """Filter sensitive data before sending to Sentry."""
    # Scrub authorization headers from request data
    if "request" in event:
        headers = event["request"].get("headers", {})
        for key in list(headers):
            lower = key.lower()
            if lower in ("authorization", "cookie", "x-api-key"):
                headers[key] = "[REDACTED]"
        # Scrub request body that may contain passwords
        body = event["request"].get("data")
        if isinstance(body, str):
            for field in ("password", "new_password", "old_password", "token", "refresh_token"):
                if field in body.lower():
                    event["request"]["data"] = "[REDACTED]"
                    break
    return event


def capture_exception(exc: Exception, **kwargs: Any) -> None:
    """Capture an exception and send it to Sentry (no-op if not initialised)."""
    if not _sentry_initialised:
        return
    import sentry_sdk

    sentry_sdk.capture_exception(exc, **kwargs)


def capture_message(message: str, level: str = "info", **kwargs: Any) -> None:
    """Capture a message event and send it to Sentry (no-op if not initialised)."""
    if not _sentry_initialised:
        return
    import sentry_sdk

    sentry_sdk.capture_message(message, level=level, **kwargs)


def set_user_context(
    user_id: str | int | None = None,
    email: str | None = None,
    username: str | None = None,
    org_id: str | int | None = None,
) -> None:
    """Set the Sentry user context for the current scope."""
    if not _sentry_initialised:
        return
    import sentry_sdk

    user_data: dict[str, Any] = {}
    if user_id is not None:
        user_data["id"] = str(user_id)
    if email:
        user_data["email"] = email
    if username:
        user_data["username"] = username
    sentry_sdk.set_user(user_data)
    if org_id is not None:
        sentry_sdk.set_tag("organization_id", str(org_id))


def add_breadcrumb(
    message: str,
    category: str = "custom",
    level: str = "info",
    data: dict | None = None,
) -> None:
    """Add a breadcrumb to the current Sentry scope."""
    if not _sentry_initialised:
        return
    import sentry_sdk

    sentry_sdk.add_breadcrumb(
        message=message,
        category=category,
        level=level,
        data=data or {},
    )


def set_tag(key: str, value: str) -> None:
    """Set a tag on the current Sentry scope."""
    if not _sentry_initialised:
        return
    import sentry_sdk

    sentry_sdk.set_tag(key, value)


def is_initialised() -> bool:
    """Return True if Sentry has been initialised."""
    return _sentry_initialised
