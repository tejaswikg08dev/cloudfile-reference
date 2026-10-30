"""Pytest fixtures for the files service.

The S3 client is replaced with a fake so tests need no AWS/LocalStack, and the
notifier is patched to a no-op. Auth tokens are generated with the same shared
secret used by the app.
"""
from __future__ import annotations

import os

import pytest
import pytest_asyncio

os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key-for-tests-only-1234567890")
os.environ.setdefault("FILES_DATABASE_URL", "sqlite+aiosqlite:///:memory:")
os.environ.setdefault("S3_BUCKET_NAME", "test-bucket")

from httpx import ASGITransport, AsyncClient  # noqa: E402
from jose import jwt  # noqa: E402
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine  # noqa: E402

from app.database import Base, get_db  # noqa: E402
from app.dependencies import get_s3_client  # noqa: E402
from app.main import app  # noqa: E402


class FakeS3:
    """In-memory stand-in for S3Client."""

    def __init__(self) -> None:
        self.deleted: list[str] = []

    @property
    def bucket(self) -> str:
        return "test-bucket"

    def generate_upload_url(self, key: str, content_type: str) -> str:
        return f"https://s3.test/upload/{key}"

    def generate_download_url(self, key: str) -> str:
        return f"https://s3.test/download/{key}"

    def delete_object(self, key: str) -> None:
        self.deleted.append(key)

    def ensure_bucket(self) -> None:
        pass


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
async def client(db_session, monkeypatch):
    async def _override_get_db():
        yield db_session

    # No-op notifier so no network calls happen.
    import app.service as service_module

    async def _fake_notify(*_args, **_kwargs):
        return None

    monkeypatch.setattr(service_module, "notify_upload_complete", _fake_notify)

    app.dependency_overrides[get_db] = _override_get_db
    app.dependency_overrides[get_s3_client] = lambda: FakeS3()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def auth_headers():
    return {"Authorization": f"Bearer {make_token()}"}
