"""Console provider: logs the notification. Used for local/dev (free)."""
from __future__ import annotations

from ..logging_config import get_logger
from .base import NotificationProvider

logger = get_logger("notification.console")


class ConsoleProvider(NotificationProvider):
    async def send(self, recipient: str, subject: str, message: str) -> None:
        # "message" is a reserved LogRecord attribute; passing it via `extra=`
        # raises KeyError. Use a safe key (body) instead.
        logger.info(
            "notification_console",
            extra={"recipient": recipient, "subject": subject, "body": message},
        )
