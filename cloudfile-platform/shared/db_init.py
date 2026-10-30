"""Safe, idempotent table creation for local/dev startup.

Why this exists:
- `create_all` is idempotent by default (it issues checkfirst), but when a
  service runs multiple workers (gunicorn --workers 2), both workers can call
  it concurrently and race on creating the same Postgres types/tables, which
  surfaces as: `duplicate key value violates unique constraint
  "pg_type_typname_nsp_index"`.
- In production, Alembic owns the schema and this is skipped entirely.

This helper:
1. Skips creation unless DB_AUTO_CREATE is enabled (default on for dev).
2. Passes checkfirst=True explicitly.
3. Serializes creation with a Postgres advisory lock so concurrent workers
   don't race. On non-Postgres (e.g. SQLite in tests) it just runs directly.
4. Tolerates the duplicate-object error if it still slips through.
"""
from __future__ import annotations

import os

from sqlalchemy import text
from sqlalchemy.exc import DBAPIError, IntegrityError, ProgrammingError
from sqlalchemy.ext.asyncio import AsyncEngine

# A fixed, arbitrary lock key shared by all workers of a service.
_ADVISORY_LOCK_KEY = 991_001


def _auto_create_enabled() -> bool:
    return os.getenv("DB_AUTO_CREATE", "true").lower() in ("1", "true", "yes")


async def create_all_safe(engine: AsyncEngine, metadata) -> None:
    """Create tables idempotently and race-safely.

    Args:
        engine: the async engine.
        metadata: SQLAlchemy MetaData (e.g. Base.metadata).
    """
    if not _auto_create_enabled():
        return

    is_postgres = engine.url.get_backend_name().startswith("postgres")

    try:
        async with engine.begin() as conn:
            if is_postgres:
                # Serialize across workers/instances. The lock is released when
                # the transaction (this `engine.begin()` block) commits.
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
        # Safe to ignore; the schema now exists.
        pass
