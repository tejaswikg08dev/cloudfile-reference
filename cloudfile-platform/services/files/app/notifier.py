"""Client for calling the (separate-repo) notification service.

This demonstrates inter-service communication over HTTP. Failures to notify
must never break the core upload flow, so all errors are swallowed and logged.
The caller's bearer token is forwarded so the notification service can
authenticate the request with the shared JWT secret.
"""
from __future__ import annotations

import httpx

from shared.logging_config import get_logger

from .config import get_settings

logger = get_logger("files.notifier")


async def notify_upload_complete(user_email: str, filename: str, token: str) -> None:
    settings = get_settings()
    if not settings.notification_service_url:
        logger.info("notification_skipped_no_url")
        return

    url = f"{settings.notification_service_url.rstrip('/')}/api/v1/notifications/notify"
    payload = {
        "recipient": user_email,
        "subject": "Your file was uploaded",
        "message": f"Your file '{filename}' was uploaded successfully.",
        "channel": "email",
    }
    headers = {"Authorization": f"Bearer {token}"}
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.post(url, json=payload, headers=headers)
            resp.raise_for_status()
        logger.info("notification_sent", extra={"recipient": user_email})
    except Exception as exc:  # noqa: BLE001 - never fail the upload on notify error
        logger.warning("notification_failed", extra={"error": str(exc)})
