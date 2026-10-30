"""Pytest fixtures for the search service."""
from __future__ import annotations

import os
import uuid
from datetime import datetime, timezone

import pytest
import pytest_asyncio

os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key-for-tests-only-1234567890")
os.environ.setdefault("SEARCH_DATABASE_URL", "sqlite+aiosqlite:///:memory:")

from httpx import ASGITransport, AsyncClient  # noqa: E402
from jose import jwt  # noqa: E402
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine  # noqa: E402

from app.database import Base, get_db  # noqa: E402
from app.main import app  # noqa: E402
from app.models import FileRecord  # noqa: E402


def make_token(user_id: str = "user-1", email: str = "user@example.com") -> str:
    return jwt.encode(
        {"sub": user_id, "email": email}, os.environ["JWT_SECRET_KEY"], algorithm="HS256"
    )


async def _seed(session, owner_id: str, filename: str, content_type: str) -> None:
    session.add(
        FileRecord(
            id=str(uuid.uuid4()),
            owner_id=owner_id,
            filename=filename,
            content_type=content_type,
            size_bytes=100,
            s3_key=f"uploads/{owner_id}/{filename}",
            status="ready",
            thumbnail_key=None,
            created_at=datetime.now(timezone.utc),
        )
    )


@pytest_asyncio.fixture
async def db_session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    maker = async_sessionmaker(engine, expire_on_commit=False)
    async with maker() as session:
        # Seed sample data for user-1
        await _seed(session, "user-1", "vacation.jpg", "image/jpeg")
        await _seed(session, "user-1", "resume.pdf", "application/pdf")
        await _seed(session, "user-1", "photo.png", "image/png")
        await _seed(session, "user-2", "secret.txt", "text/plain")
        await session.commit()
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
