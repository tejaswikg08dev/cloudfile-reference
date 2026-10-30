"""Read model mirroring the files table.

The search service reads the same `files` table owned by the files service.
It never writes. Defining the model here keeps search decoupled at the code
level even though it shares the physical table (CQRS-lite / shared-DB read).
"""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import BigInteger, DateTime, String
from sqlalchemy.orm import Mapped, mapped_column

from .database import Base


class FileRecord(Base):
    __tablename__ = "files"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    owner_id: Mapped[str] = mapped_column(String(36), index=True)
    filename: Mapped[str] = mapped_column(String(512))
    content_type: Mapped[str] = mapped_column(String(255))
    size_bytes: Mapped[int] = mapped_column(BigInteger)
    s3_key: Mapped[str] = mapped_column(String(1024))
    status: Mapped[str] = mapped_column(String(32))
    thumbnail_key: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
