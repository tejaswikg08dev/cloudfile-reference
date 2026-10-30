"""Safe, idempotent table creation for local/dev startup (standalone copy).

See the platform's shared/db_init.py for the rationale. This standalone service
carries its own copy so it depends on no other repo.
"""
from __future__ import annotations

import os

from sqlalchemy import text
from sqlalchemy.exc import DBAPIError, IntegrityError, ProgrammingError
from sqlalchemy.ext.asyncio import AsyncEngine

_ADVISORY_LOCK_KEY = 991_004


def _auto_create_enabled() -> bool:
    return os.getenv("DB_AUTO_CREATE", "true").lower() in ("1", "true", "yes")


async def create_all_safe(engine: AsyncEngine, metadata) -> None:
    if not _auto_create_enabled():
        return

    is_postgres = engine.url.get_backend_name().startswith("postgres")

    try:
        async with engine.begin() as conn:
            if is_postgres:
                # Serialize across workers so concurrent create_all can't race.
                await conn.execute(
                    text("SELECT pg_advisory_xact_lock(:k)").bindparams(
                        k=_ADVISORY_LOCK_KEY
                    )
                )
            await conn.run_sync(
                lambda sync_conn: metadata.create_all(sync_conn, checkfirst=True)
            )
    except (IntegrityError, ProgrammingError, DBAPIError):
        # Another worker created the schema between checkfirst and CREATE.
        # The schema now exists, so this is safe to ignore.
        pass
