"""FastAPI dependencies for the notification service."""
from __future__ import annotations

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from .auth_utils import TokenData, TokenVerificationError, verify_token
from .config import get_settings
from .database import get_db
from .exceptions import UnauthorizedError
from .providers.factory import get_provider
from .repository import NotificationRepository
from .service import NotificationService

_bearer = HTTPBearer(auto_error=False)


def get_notification_service(
    db: AsyncSession = Depends(get_db),
) -> NotificationService:
    return NotificationService(NotificationRepository(db), get_provider())


async def get_current_token(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
) -> TokenData:
    if credentials is None:
        raise UnauthorizedError("Missing authentication token")
    settings = get_settings()
    try:
        return verify_token(
            credentials.credentials, settings.jwt_secret_key, settings.jwt_algorithm
        )
    except TokenVerificationError as exc:
        raise UnauthorizedError(str(exc)) from exc
