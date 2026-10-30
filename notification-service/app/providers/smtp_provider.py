"""SMTP provider — sends real email via any SMTP server (e.g. Mailtrap).

Great for local/dev: point it at a Mailtrap sandbox inbox and you actually
see the emails arrive, without AWS. smtplib is synchronous, so we offload the
send to a thread to avoid blocking the event loop.
"""
from __future__ import annotations

import smtplib
from email.mime.text import MIMEText

from fastapi.concurrency import run_in_threadpool

from ..config import get_settings
from ..logging_config import get_logger
from .base import NotificationProvider

logger = get_logger("notification.smtp")


class SMTPProvider(NotificationProvider):
    def __init__(self) -> None:
        self._s = get_settings()

    def _send_sync(self, recipient: str, subject: str, message: str) -> None:
        msg = MIMEText(message, "plain", "utf-8")
        msg["Subject"] = subject
        msg["From"] = self._s.smtp_sender
        msg["To"] = recipient

        with smtplib.SMTP(self._s.smtp_host, self._s.smtp_port, timeout=10) as server:
            if self._s.smtp_use_tls:
                server.starttls()
            if self._s.smtp_username:
                server.login(self._s.smtp_username, self._s.smtp_password)
            server.sendmail(self._s.smtp_sender, [recipient], msg.as_string())

    async def send(self, recipient: str, subject: str, message: str) -> None:
        await run_in_threadpool(self._send_sync, recipient, subject, message)
        logger.info("notification_smtp_sent", extra={"recipient": recipient})
