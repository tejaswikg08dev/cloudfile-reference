"""Pydantic schemas for the search service."""
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class FileResult(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    filename: str
    content_type: str
    size_bytes: int
    status: str
    created_at: datetime
