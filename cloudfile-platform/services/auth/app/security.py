"""Password hashing and JWT creation for the auth service."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from jose import jwt
from passlib.context import CryptContext

from .config import get_settings

_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(plain: str) -> str:
    """Hash a plaintext password with bcrypt."""
    return _pwd_context.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    """Check a plaintext password against a bcrypt hash."""
    return _pwd_context.verify(plain, hashed)


def create_access_token(user_id: str, email: str) -> tuple[str, int]:
    """Create a signed JWT access token.

    Returns:
        A tuple of (token, expires_in_seconds).
    """
    settings = get_settings()
    expires_in = settings.jwt_access_token_expire_minutes * 60
    expire = datetime.now(timezone.utc) + timedelta(seconds=expires_in)

    claims = {
        "sub": user_id,
        "email": email,
        "exp": expire,
        "iat": datetime.now(timezone.utc),
    }
    token = jwt.encode(claims, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
    return token, expires_in
