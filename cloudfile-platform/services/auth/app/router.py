"""HTTP routes for the auth service."""
from __future__ import annotations

from fastapi import APIRouter, Depends, status

from shared.auth_utils import TokenData
from shared.exceptions import NotFoundError

from .dependencies import get_auth_service, get_current_token, get_user_repository
from .repository import UserRepository
from .schemas import Token, TokenVerifyResponse, UserCreate, UserLogin, UserOut
from .service import AuthService

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def register(
    data: UserCreate,
    service: AuthService = Depends(get_auth_service),
) -> UserOut:
    user = await service.register(data)
    return UserOut.model_validate(user)


@router.post("/login", response_model=Token)
async def login(
    data: UserLogin,
    service: AuthService = Depends(get_auth_service),
) -> Token:
    return await service.login(data)


@router.get("/me", response_model=UserOut)
async def me(
    token: TokenData = Depends(get_current_token),
    repo: UserRepository = Depends(get_user_repository),
) -> UserOut:
    user = await repo.get_by_id(token.user_id)
    if user is None:
        raise NotFoundError("User not found")
    return UserOut.model_validate(user)


@router.get("/verify", response_model=TokenVerifyResponse)
async def verify(token: TokenData = Depends(get_current_token)) -> TokenVerifyResponse:
    """Verify a token. Used by other services if they prefer a network check."""
    return TokenVerifyResponse(valid=True, user_id=token.user_id, email=token.email)
