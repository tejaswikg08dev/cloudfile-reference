"""HTTP routes for the search service."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from shared.auth_utils import TokenData
from shared.pagination import Page, PaginationParams

from .dependencies import get_current_token, get_search_service
from .schemas import FileResult
from .service import SearchService

router = APIRouter(prefix="/api/v1/search", tags=["search"])


@router.get("", response_model=Page[FileResult])
async def search(
    name: str | None = Query(default=None, max_length=512),
    content_type: str | None = Query(default=None, max_length=255),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    token: TokenData = Depends(get_current_token),
    service: SearchService = Depends(get_search_service),
) -> Page[FileResult]:
    params = PaginationParams(page=page, page_size=page_size)
    return await service.search(token.user_id, name, content_type, params)
