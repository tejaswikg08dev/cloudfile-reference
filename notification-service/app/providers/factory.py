"""Select a notification provider based on configuration."""
from __future__ import annotations

from ..config import get_settings
from .base import NotificationProvider
from .console_provider import ConsoleProvider


def get_provider() -> NotificationProvider:
    settings = get_settings()
    if settings.notification_provider == "ses":
        # Imported lazily so boto3/SES is only required when actually used.
        from .ses_provider import SESProvider

        return SESProvider()
    return ConsoleProvider()
