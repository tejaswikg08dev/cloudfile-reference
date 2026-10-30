"""Business logic for the notification service."""
from __future__ import annotations

from .logging_config import get_logger
from .models import Notification
from .providers.base import NotificationProvider
from .repository import NotificationRepository
from .schemas import NotifyRequest

logger = get_logger("notification.service")


class NotificationService:
    def __init__(self, repo: NotificationRepository, provider: NotificationProvider) -> None:
        self._repo = repo
        self._provider = provider

    async def notify(self, data: NotifyRequest) -> Notification:
        status = "sent"
        try:
            await self._provider.send(data.recipient, data.subject, data.message)
        except Exception as exc:  # noqa: BLE001 - record the failure but still persist
            status = "failed"
            # Log the ACTUAL delivery error so misconfig (bad SMTP creds, wrong
            # host/port, TLS issues) is visible instead of silently "failed".
            logger.warning(
                "notification_delivery_failed",
                extra={
                    "provider": type(self._provider).__name__,
                    "recipient": data.recipient,
                    "error": f"{type(exc).__name__}: {exc}",
                },
            )

        notification = Notification(
            recipient=data.recipient,
            subject=data.subject,
            message=data.message,
            channel=data.channel,
            status=status,
        )
        return await self._repo.create(notification)

    async def list_for(self, recipient: str) -> list[Notification]:
        return await self._repo.list_by_recipient(recipient)
