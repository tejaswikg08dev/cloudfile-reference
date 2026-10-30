"""Business logic for the notification service."""
from __future__ import annotations

from .models import Notification
from .providers.base import NotificationProvider
from .repository import NotificationRepository
from .schemas import NotifyRequest


class NotificationService:
    def __init__(self, repo: NotificationRepository, provider: NotificationProvider) -> None:
        self._repo = repo
        self._provider = provider

    async def notify(self, data: NotifyRequest) -> Notification:
        status = "sent"
        try:
            await self._provider.send(data.recipient, data.subject, data.message)
        except Exception:  # noqa: BLE001 - record the failure but still persist
            status = "failed"

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
