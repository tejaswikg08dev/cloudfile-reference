"""Pytest fixtures for the auth service.

Tests use an in-memory SQLite database (async) so they run fast and require
no external services. The business logic is DB-agnostic, so this is a valid
way to test it.
"""
from __future__ import annotations

import os

import pytest
import pytest_asyncio

# Configure env before importing app modules that read settings.
os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key-for-tests-only-1234567890")
os.environ.setdefault("AUTH_DATABASE_URL", "sqlite+aiosqlite:///:memory:")

from httpx import ASGITransport, AsyncClient  # noqa: E402
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine  # noqa: E402

from app.database import Base, get_db  # noqa: E402
from app.main import app  # noqa: E402


@pytest_asyncio.fixture
async def db_session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    maker = async_sessionmaker(engine, expire_on_commit=False)
    async with maker() as session:
        yield session

    await engine.dispose()


@pytest_asyncio.fixture
async def client(db_session):
    async def _override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = _override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c
    app.dependency_overrides.clear()
