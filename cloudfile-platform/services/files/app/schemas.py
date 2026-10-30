"""Pydantic schemas for the files service."""
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class UploadRequest(BaseModel):
    filename: str = Field(min_length=1, max_length=512)
    content_type: str = Field(min_length=1, max_length=255)
    size_bytes: int = Field(ge=0, le=100 * 1024 * 1024)  # 100 MB cap


class UploadResponse(BaseModel):
    file_id: str
    upload_url: str
    s3_key: str
    expires_in: int


class ConfirmUploadRequest(BaseModel):
    file_id: str


class FileOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    owner_id: str
    filename: str
    content_type: str
    size_bytes: int
    status: str
    thumbnail_key: str | None
    created_at: datetime


class DownloadResponse(BaseModel):
    download_url: str
    expires_in: int
