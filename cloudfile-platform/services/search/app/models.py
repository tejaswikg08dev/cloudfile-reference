"""Read model mirroring the files table.

The search service reads the same `files` table owned by the files service.
It never writes. Defining the model here keeps search decoupled at the code
level even though it shares the physical table (CQRS-lite / shared-DB read).

IMPORTANT: the column definitions here MUST match the files service's
`FileMetadata` exactly (nullability, unique, index). In local/dev either
service may create the table first (create_all is race-safe); if the two
definitions differed, the table could be created without a constraint. Keeping
them identical guarantees the same schema regardless of startup order.
"""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import BigInteger, DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column

from .database import Base


class FileRecord(Base):
    __tablename__ = "files"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    owner_id: Mapped[str] = mapped_column(String(36), index=True, nullable=False)
    filename: Mapped[str] = mapped_column(String(512), nullable=False)
    content_type: Mapped[str] = mapped_column(String(255), nullable=False)
    size_bytes: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    s3_key: Mapped[str] = mapped_column(String(1024), unique=True, nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="pending", nullable=False)
    thumbnail_key: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
