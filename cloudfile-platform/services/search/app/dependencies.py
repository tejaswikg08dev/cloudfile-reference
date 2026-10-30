"""FastAPI dependencies for the search service."""
from __future__ import annotations

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from shared.auth_utils import TokenData, TokenVerificationError, verify_token
from shared.exceptions import UnauthorizedError

from .config import get_settings
from .database import get_db
from .repository import SearchRepository
from .service import SearchService

_bearer = HTTPBearer(auto_error=False)


def get_search_service(db: AsyncSession = Depends(get_db)) -> SearchService:
    return SearchService(SearchRepository(db))


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
