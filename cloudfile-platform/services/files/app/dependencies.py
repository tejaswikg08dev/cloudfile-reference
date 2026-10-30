"""FastAPI dependencies for the files service."""
from __future__ import annotations

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from shared.auth_utils import TokenData, TokenVerificationError, verify_token
from shared.exceptions import UnauthorizedError

from .config import get_settings
from .database import get_db
from .repository import FileRepository
from .s3_client import S3Client
from .service import FileService

_bearer = HTTPBearer(auto_error=False)

# A single S3 client is reused; boto3 clients are thread-safe for our usage.
_s3_singleton: S3Client | None = None


def get_s3_client() -> S3Client:
    global _s3_singleton
    if _s3_singleton is None:
        _s3_singleton = S3Client()
    return _s3_singleton


def get_file_service(
    db: AsyncSession = Depends(get_db),
    s3: S3Client = Depends(get_s3_client),
) -> FileService:
    return FileService(FileRepository(db), s3)


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


async def get_raw_token(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
) -> str:
    """Return the raw bearer token string, for forwarding to other services."""
    if credentials is None:
        raise UnauthorizedError("Missing authentication token")
    return credentials.credentials
