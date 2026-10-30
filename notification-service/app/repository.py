"""Data-access layer for the notification service."""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .models import Notification


class NotificationRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def create(self, notification: Notification) -> Notification:
        self._db.add(notification)
        await self._db.commit()
        await self._db.refresh(notification)
        return notification

    async def list_by_recipient(self, recipient: str) -> list[Notification]:
        result = await self._db.execute(
            select(Notification)
            .where(Notification.recipient == recipient)
            .order_by(Notification.created_at.desc())
        )
        return list(result.scalars().all())
