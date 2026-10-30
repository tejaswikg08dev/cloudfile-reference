"""JWT verification utilities shared across services.

The auth service *issues* tokens (see services/auth/app/security.py). Other
services only need to *verify* tokens, which they do locally using the shared
secret. This avoids a network round-trip to the auth service on every request
while keeping a single source of truth for the token format.
"""
from __future__ import annotations

from datetime import datetime, timezone

from jose import JWTError, jwt
from pydantic import BaseModel


class TokenData(BaseModel):
    """Decoded JWT claims we care about."""

    user_id: str
    email: str


class TokenVerificationError(Exception):
    """Raised when a token is invalid, expired, or malformed."""


def verify_token(token: str, secret_key: str, algorithm: str = "HS256") -> TokenData:
    """Verify a JWT and return its claims.

    Args:
        token: The raw JWT string (without the "Bearer " prefix).
        secret_key: Shared signing secret.
        algorithm: Signing algorithm (default HS256).

    Returns:
        TokenData with user_id and email.

    Raises:
        TokenVerificationError: If verification fails for any reason.
    """
    try:
        payload = jwt.decode(token, secret_key, algorithms=[algorithm])
    except JWTError as exc:
        raise TokenVerificationError(f"Invalid token: {exc}") from exc

    user_id = payload.get("sub")
    email = payload.get("email")
    if not user_id or not email:
        raise TokenVerificationError("Token missing required claims")

    # jose already checks `exp`, but we double-check defensively.
    exp = payload.get("exp")
    if exp is not None and datetime.now(timezone.utc).timestamp() > exp:
        raise TokenVerificationError("Token has expired")

    return TokenData(user_id=str(user_id), email=str(email))
