"""Pytest fixtures for the notification service."""
from __future__ import annotations

import os

import pytest
import pytest_asyncio

os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key-for-tests-only-1234567890")
os.environ.setdefault("NOTIFICATION_DATABASE_URL", "sqlite+aiosqlite:///:memory:")
os.environ.setdefault("NOTIFICATION_PROVIDER", "console")

from httpx import ASGITransport, AsyncClient  # noqa: E402
from jose import jwt  # noqa: E402
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine  # noqa: E402

from app.database import Base, get_db  # noqa: E402
from app.main import app  # noqa: E402


def make_token(user_id: str = "user-1", email: str = "user@example.com") -> str:
    return jwt.encode(
        {"sub": user_id, "email": email}, os.environ["JWT_SECRET_KEY"], algorithm="HS256"
    )


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


@pytest.fixture
def auth_headers():
    return {"Authorization": f"Bearer {make_token()}"}
