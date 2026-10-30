"""HTTP routes for the files service."""
from __future__ import annotations

from fastapi import APIRouter, Depends, status

from shared.auth_utils import TokenData

from .config import get_settings
from .dependencies import get_current_token, get_file_service, get_raw_token
from .schemas import (
    ConfirmUploadRequest,
    DownloadResponse,
    FileOut,
    UploadRequest,
    UploadResponse,
)
from .service import FileService

router = APIRouter(prefix="/api/v1/files", tags=["files"])


@router.post("/upload", response_model=UploadResponse, status_code=status.HTTP_201_CREATED)
async def initiate_upload(
    data: UploadRequest,
    token: TokenData = Depends(get_current_token),
    service: FileService = Depends(get_file_service),
) -> UploadResponse:
    file, upload_url = await service.initiate_upload(
        token.user_id, data.filename, data.content_type, data.size_bytes
    )
    return UploadResponse(
        file_id=file.id,
        upload_url=upload_url,
        s3_key=file.s3_key,
        expires_in=get_settings().presigned_url_expire_seconds,
    )


@router.post("/confirm", response_model=FileOut)
async def confirm_upload(
    data: ConfirmUploadRequest,
    token: TokenData = Depends(get_current_token),
    raw_token: str = Depends(get_raw_token),
    service: FileService = Depends(get_file_service),
) -> FileOut:
    file = await service.confirm_upload(
        data.file_id, token.user_id, token.email, raw_token
    )
    return FileOut.model_validate(file)


@router.get("/{file_id}/download", response_model=DownloadResponse)
async def download(
    file_id: str,
    token: TokenData = Depends(get_current_token),
    service: FileService = Depends(get_file_service),
) -> DownloadResponse:
    url = await service.get_download_url(file_id, token.user_id)
    return DownloadResponse(
        download_url=url, expires_in=get_settings().presigned_url_expire_seconds
    )


@router.get("", response_model=list[FileOut])
async def list_files(
    token: TokenData = Depends(get_current_token),
    service: FileService = Depends(get_file_service),
) -> list[FileOut]:
    files = await service.list_files(token.user_id)
    return [FileOut.model_validate(f) for f in files]


@router.delete("/{file_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_file(
    file_id: str,
    token: TokenData = Depends(get_current_token),
    service: FileService = Depends(get_file_service),
) -> None:
    await service.delete_file(file_id, token.user_id)
