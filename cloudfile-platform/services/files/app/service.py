"""Business logic for the files service."""
from __future__ import annotations

import uuid

from fastapi.concurrency import run_in_threadpool

from shared.exceptions import ForbiddenError, NotFoundError

from .config import get_settings
from .models import FileMetadata
from .notifier import notify_upload_complete
from .repository import FileRepository
from .s3_client import S3Client


class FileService:
    def __init__(self, repo: FileRepository, s3: S3Client) -> None:
        self._repo = repo
        self._s3 = s3
        self._settings = get_settings()

    @staticmethod
    def _build_key(owner_id: str, filename: str) -> str:
        return f"uploads/{owner_id}/{uuid.uuid4()}/{filename}"

    async def initiate_upload(
        self, owner_id: str, filename: str, content_type: str, size_bytes: int
    ) -> tuple[FileMetadata, str]:
        key = self._build_key(owner_id, filename)
        file = FileMetadata(
            owner_id=owner_id,
            filename=filename,
            content_type=content_type,
            size_bytes=size_bytes,
            s3_key=key,
            status="pending",
        )
        file = await self._repo.create(file)
        upload_url = await run_in_threadpool(
            self._s3.generate_upload_url, key, content_type
        )
        return file, upload_url

    async def _get_owned(self, file_id: str, owner_id: str) -> FileMetadata:
        file = await self._repo.get_by_id(file_id)
        if file is None:
            raise NotFoundError("File not found")
        if file.owner_id != owner_id:
            raise ForbiddenError("You do not have access to this file")
        return file

    async def confirm_upload(
        self, file_id: str, owner_id: str, user_email: str, token: str
    ) -> FileMetadata:
        file = await self._get_owned(file_id, owner_id)
        file.status = "ready"
        file = await self._repo.update(file)
        await notify_upload_complete(user_email, file.filename, token)
        return file

    async def get_download_url(self, file_id: str, owner_id: str) -> str:
        file = await self._get_owned(file_id, owner_id)
        return await run_in_threadpool(self._s3.generate_download_url, file.s3_key)

    async def list_files(self, owner_id: str) -> list[FileMetadata]:
        return await self._repo.list_by_owner(owner_id)

    async def delete_file(self, file_id: str, owner_id: str) -> None:
        file = await self._get_owned(file_id, owner_id)
        await run_in_threadpool(self._s3.delete_object, file.s3_key)
        if file.thumbnail_key:
            await run_in_threadpool(self._s3.delete_object, file.thumbnail_key)
        await self._repo.delete(file)
