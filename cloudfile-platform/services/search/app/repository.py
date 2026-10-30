"""Read-only data access for the search service."""
from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from .models import FileRecord


class SearchRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    def _base_filters(
        self,
        owner_id: str,
        name: str | None,
        content_type: str | None,
    ):
        conditions = [FileRecord.owner_id == owner_id]
        if name:
            conditions.append(FileRecord.filename.ilike(f"%{name}%"))
        if content_type:
            conditions.append(FileRecord.content_type == content_type)
        return conditions

    async def search(
        self,
        owner_id: str,
        name: str | None,
        content_type: str | None,
        offset: int,
        limit: int,
    ) -> tuple[list[FileRecord], int]:
        conditions = self._base_filters(owner_id, name, content_type)

        count_stmt = select(func.count()).select_from(FileRecord).where(*conditions)
        total = (await self._db.execute(count_stmt)).scalar_one()

        stmt = (
            select(FileRecord)
            .where(*conditions)
            .order_by(FileRecord.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        rows = list((await self._db.execute(stmt)).scalars().all())
        return rows, int(total)
