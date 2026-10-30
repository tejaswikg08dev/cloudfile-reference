"""Select a notification provider based on configuration."""
from __future__ import annotations

from ..config import get_settings
from .base import NotificationProvider
from .console_provider import ConsoleProvider


def get_provider() -> NotificationProvider:
    settings = get_settings()
    provider = settings.notification_provider.lower()

    if provider == "ses":
        # Imported lazily so boto3/SES is only required when actually used.
        from .ses_provider import SESProvider

        return SESProvider()
    if provider == "smtp":
        from .smtp_provider import SMTPProvider

        return SMTPProvider()
    return ConsoleProvider()
