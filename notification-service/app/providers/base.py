"""Provider interface for sending notifications."""
from __future__ import annotations

from abc import ABC, abstractmethod


class NotificationProvider(ABC):
    """Strategy interface. Concrete providers implement `send`."""

    @abstractmethod
    async def send(self, recipient: str, subject: str, message: str) -> None:
        """Deliver a notification. Raise on hard failure."""
        raise NotImplementedError
