"""JWT verification (standalone copy for this repo).

The notification service verifies tokens issued by the auth service using the
shared JWT secret, so inter-service calls can be authenticated.
"""
from __future__ import annotations

from jose import JWTError, jwt
from pydantic import BaseModel


class TokenData(BaseModel):
    user_id: str
    email: str


class TokenVerificationError(Exception):
    pass


def verify_token(token: str, secret_key: str, algorithm: str = "HS256") -> TokenData:
    try:
        payload = jwt.decode(token, secret_key, algorithms=[algorithm])
    except JWTError as exc:
        raise TokenVerificationError(f"Invalid token: {exc}") from exc

    user_id = payload.get("sub")
    email = payload.get("email")
    if not user_id or not email:
        raise TokenVerificationError("Token missing required claims")
    return TokenData(user_id=str(user_id), email=str(email))
