"""Tests for the notification service."""
from __future__ import annotations

import pytest

NOTIFY = "/api/v1/notifications/notify"
LIST = "/api/v1/notifications"


@pytest.mark.asyncio
async def test_health(client):
    resp = await client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["service"] == "notification"


@pytest.mark.asyncio
async def test_notify_requires_auth(client):
    resp = await client.post(
        NOTIFY,
        json={"recipient": "u@example.com", "subject": "Hi", "message": "Hello"},
    )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_notify_and_list(client, auth_headers):
    resp = await client.post(
        NOTIFY,
        headers=auth_headers,
        json={
            "recipient": "user@example.com",
            "subject": "Upload complete",
            "message": "Your file was uploaded.",
            "channel": "email",
        },
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["status"] == "sent"  # console provider always succeeds
    assert body["recipient"] == "user@example.com"

    listing = await client.get(LIST, headers=auth_headers)
    assert listing.status_code == 200
    items = listing.json()
    assert len(items) == 1
    assert items[0]["subject"] == "Upload complete"


@pytest.mark.asyncio
async def test_notify_invalid_channel(client, auth_headers):
    resp = await client.post(
        NOTIFY,
        headers=auth_headers,
        json={
            "recipient": "user@example.com",
            "subject": "Hi",
            "message": "Hello",
            "channel": "carrier-pigeon",
        },
    )
    assert resp.status_code == 422
