"""Business logic for the auth service."""
from __future__ import annotations

from shared.exceptions import ConflictError, UnauthorizedError

from .models import User
from .repository import UserRepository
from .schemas import Token, UserCreate, UserLogin
from .security import create_access_token, hash_password, verify_password


class AuthService:
    def __init__(self, repo: UserRepository) -> None:
        self._repo = repo

    async def register(self, data: UserCreate) -> User:
        existing = await self._repo.get_by_email(data.email)
        if existing is not None:
            raise ConflictError("A user with this email already exists")

        user = User(
            email=data.email,
            full_name=data.full_name,
            hashed_password=hash_password(data.password),
        )
        return await self._repo.create(user)

    async def login(self, data: UserLogin) -> Token:
        user = await self._repo.get_by_email(data.email)
        if user is None or not verify_password(data.password, user.hashed_password):
            # Same error for both cases to avoid leaking which emails exist.
            raise UnauthorizedError("Invalid email or password")
        if not user.is_active:
            raise UnauthorizedError("Account is disabled")

        token, expires_in = create_access_token(user.id, user.email)
        return Token(access_token=token, expires_in=expires_in)
