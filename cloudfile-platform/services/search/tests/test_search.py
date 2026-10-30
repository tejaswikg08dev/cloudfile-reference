"""Tests for the search service."""
from __future__ import annotations

import pytest

SEARCH = "/api/v1/search"


@pytest.mark.asyncio
async def test_health(client):
    resp = await client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["service"] == "search"


@pytest.mark.asyncio
async def test_search_requires_auth(client):
    resp = await client.get(SEARCH)
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_search_returns_only_own_files(client, auth_headers):
    resp = await client.get(SEARCH, headers=auth_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 3  # user-1 has 3 files, user-2's file excluded
    filenames = {item["filename"] for item in body["items"]}
    assert "secret.txt" not in filenames


@pytest.mark.asyncio
async def test_search_filter_by_name(client, auth_headers):
    resp = await client.get(SEARCH, params={"name": "resume"}, headers=auth_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 1
    assert body["items"][0]["filename"] == "resume.pdf"


@pytest.mark.asyncio
async def test_search_filter_by_content_type(client, auth_headers):
    resp = await client.get(
        SEARCH, params={"content_type": "image/jpeg"}, headers=auth_headers
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 1
    assert body["items"][0]["filename"] == "vacation.jpg"


@pytest.mark.asyncio
async def test_search_pagination(client, auth_headers):
    resp = await client.get(
        SEARCH, params={"page": 1, "page_size": 2}, headers=auth_headers
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 3
    assert body["total_pages"] == 2
    assert len(body["items"]) == 2
