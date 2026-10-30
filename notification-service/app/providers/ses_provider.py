"""AWS SES provider for sending real emails.

Requires SES to be configured and the sender/recipient verified in sandbox
mode. boto3 is synchronous, so we offload the call to a thread.
"""
from __future__ import annotations

import boto3
from fastapi.concurrency import run_in_threadpool

from ..config import get_settings
from ..logging_config import get_logger
from .base import NotificationProvider

logger = get_logger("notification.ses")


class SESProvider(NotificationProvider):
    def __init__(self) -> None:
        settings = get_settings()
        self._sender = settings.ses_sender
        self._client = boto3.client("ses", region_name=settings.aws_region)

    def _send_sync(self, recipient: str, subject: str, message: str) -> None:
        self._client.send_email(
            Source=self._sender,
            Destination={"ToAddresses": [recipient]},
            Message={
                "Subject": {"Data": subject},
                "Body": {"Text": {"Data": message}},
            },
        )

    async def send(self, recipient: str, subject: str, message: str) -> None:
        await run_in_threadpool(self._send_sync, recipient, subject, message)
        logger.info("notification_ses_sent", extra={"recipient": recipient})
