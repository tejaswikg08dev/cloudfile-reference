"""HTTP routes for the notification service."""
from __future__ import annotations

from fastapi import APIRouter, Depends, status

from .auth_utils import TokenData
from .dependencies import get_current_token, get_notification_service
from .schemas import NotificationOut, NotifyRequest
from .service import NotificationService

router = APIRouter(prefix="/api/v1/notifications", tags=["notifications"])


@router.post("/notify", response_model=NotificationOut, status_code=status.HTTP_201_CREATED)
async def notify(
    data: NotifyRequest,
    _token: TokenData = Depends(get_current_token),
    service: NotificationService = Depends(get_notification_service),
) -> NotificationOut:
    notification = await service.notify(data)
    return NotificationOut.model_validate(notification)


@router.get("", response_model=list[NotificationOut])
async def list_notifications(
    token: TokenData = Depends(get_current_token),
    service: NotificationService = Depends(get_notification_service),
) -> list[NotificationOut]:
    # Users can list notifications sent to their own email.
    items = await service.list_for(token.email)
    return [NotificationOut.model_validate(n) for n in items]
