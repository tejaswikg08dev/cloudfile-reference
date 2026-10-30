"""File metadata ORM model.

Note: this table is shared conceptually with the search service, which reads
the same metadata. In a strict microservices setup each service owns its own
schema; here files owns the write model and search reads it (CQRS-lite).
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import BigInteger, DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column

from .database import Base


def _uuid() -> str:
    return str(uuid.uuid4())


class FileMetadata(Base):
    __tablename__ = "files"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    owner_id: Mapped[str] = mapped_column(String(36), index=True, nullable=False)
    filename: Mapped[str] = mapped_column(String(512), nullable=False)
    content_type: Mapped[str] = mapped_column(String(255), nullable=False)
    size_bytes: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    s3_key: Mapped[str] = mapped_column(String(1024), unique=True, nullable=False)

    # "pending" until the client confirms upload; "ready" after confirmation;
    # "processed" after the Lambda extracts metadata/thumbnail.
    status: Mapped[str] = mapped_column(String(32), default="pending", nullable=False)
    thumbnail_key: Mapped[str | None] = mapped_column(String(1024), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
