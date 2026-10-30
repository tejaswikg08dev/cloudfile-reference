"""Data-access layer for the files service."""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .models import FileMetadata


class FileRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def create(self, file: FileMetadata) -> FileMetadata:
        self._db.add(file)
        await self._db.commit()
        await self._db.refresh(file)
        return file

    async def get_by_id(self, file_id: str) -> FileMetadata | None:
        result = await self._db.execute(
            select(FileMetadata).where(FileMetadata.id == file_id)
        )
        return result.scalar_one_or_none()

    async def list_by_owner(self, owner_id: str) -> list[FileMetadata]:
        result = await self._db.execute(
            select(FileMetadata)
            .where(FileMetadata.owner_id == owner_id)
            .order_by(FileMetadata.created_at.desc())
        )
        return list(result.scalars().all())

    async def update(self, file: FileMetadata) -> FileMetadata:
        await self._db.commit()
        await self._db.refresh(file)
        return file

    async def delete(self, file: FileMetadata) -> None:
        await self._db.delete(file)
        await self._db.commit()
