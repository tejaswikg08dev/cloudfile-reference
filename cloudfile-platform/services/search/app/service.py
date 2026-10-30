"""Business logic for the search service."""
from __future__ import annotations

from shared.pagination import Page, PaginationParams

from .repository import SearchRepository
from .schemas import FileResult


class SearchService:
    def __init__(self, repo: SearchRepository) -> None:
        self._repo = repo

    async def search(
        self,
        owner_id: str,
        name: str | None,
        content_type: str | None,
        params: PaginationParams,
    ) -> Page[FileResult]:
        rows, total = await self._repo.search(
            owner_id, name, content_type, params.offset, params.limit
        )
        items = [FileResult.model_validate(r) for r in rows]
        return Page.create(items, total, params)
