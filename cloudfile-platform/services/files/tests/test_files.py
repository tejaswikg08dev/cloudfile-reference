"""Tests for the files service."""
from __future__ import annotations

import pytest

UPLOAD = "/api/v1/files/upload"
CONFIRM = "/api/v1/files/confirm"
LIST = "/api/v1/files"


@pytest.mark.asyncio
async def test_health(client):
    resp = await client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["service"] == "files"


@pytest.mark.asyncio
async def test_upload_requires_auth(client):
    resp = await client.post(
        UPLOAD, json={"filename": "a.txt", "content_type": "text/plain", "size_bytes": 10}
    )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_full_upload_flow(client, auth_headers):
    # 1. Initiate upload -> get presigned URL + file id
    init = await client.post(
        UPLOAD,
        headers=auth_headers,
        json={"filename": "report.pdf", "content_type": "application/pdf", "size_bytes": 1234},
    )
    assert init.status_code == 201
    body = init.json()
    assert body["upload_url"].startswith("https://s3.test/upload/")
    file_id = body["file_id"]

    # 2. Confirm upload
    confirm = await client.post(CONFIRM, headers=auth_headers, json={"file_id": file_id})
    assert confirm.status_code == 200
    assert confirm.json()["status"] == "ready"

    # 3. List files
    listing = await client.get(LIST, headers=auth_headers)
    assert listing.status_code == 200
    items = listing.json()
    assert len(items) == 1
    assert items[0]["filename"] == "report.pdf"

    # 4. Download URL
    download = await client.get(f"/api/v1/files/{file_id}/download", headers=auth_headers)
    assert download.status_code == 200
    assert download.json()["download_url"].startswith("https://s3.test/download/")

    # 5. Delete
    delete = await client.delete(f"/api/v1/files/{file_id}", headers=auth_headers)
    assert delete.status_code == 204

    # 6. List is now empty
    listing2 = await client.get(LIST, headers=auth_headers)
    assert listing2.json() == []


@pytest.mark.asyncio
async def test_upload_too_large(client, auth_headers):
    resp = await client.post(
        UPLOAD,
        headers=auth_headers,
        json={
            "filename": "big.bin",
            "content_type": "application/octet-stream",
            "size_bytes": 200 * 1024 * 1024,
        },
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_cannot_access_other_users_file(client, auth_headers):
    init = await client.post(
        UPLOAD,
        headers=auth_headers,
        json={"filename": "mine.txt", "content_type": "text/plain", "size_bytes": 5},
    )
    file_id = init.json()["file_id"]

    # Different user's token
    from tests.conftest import make_token

    other = {"Authorization": f"Bearer {make_token(user_id='user-2', email='o@example.com')}"}
    resp = await client.get(f"/api/v1/files/{file_id}/download", headers=other)
    assert resp.status_code == 403
