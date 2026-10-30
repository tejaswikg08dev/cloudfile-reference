"""Tests for the auth service."""
from __future__ import annotations

import pytest

REGISTER = "/api/v1/auth/register"
LOGIN = "/api/v1/auth/login"
ME = "/api/v1/auth/me"


@pytest.mark.asyncio
async def test_health(client):
    resp = await client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


@pytest.mark.asyncio
async def test_register_success(client):
    resp = await client.post(
        REGISTER,
        json={"email": "a@example.com", "password": "password123", "full_name": "Ann"},
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["email"] == "a@example.com"
    assert body["full_name"] == "Ann"
    assert "id" in body
    assert "hashed_password" not in body


@pytest.mark.asyncio
async def test_register_duplicate_email(client):
    payload = {"email": "dup@example.com", "password": "password123", "full_name": "Dup"}
    first = await client.post(REGISTER, json=payload)
    assert first.status_code == 201
    second = await client.post(REGISTER, json=payload)
    assert second.status_code == 409
    assert second.json()["error"]["code"] == "conflict"


@pytest.mark.asyncio
async def test_register_short_password(client):
    resp = await client.post(
        REGISTER,
        json={"email": "b@example.com", "password": "short", "full_name": "Bob"},
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_login_success_and_me(client):
    await client.post(
        REGISTER,
        json={"email": "c@example.com", "password": "password123", "full_name": "Cid"},
    )
    login = await client.post(
        LOGIN, json={"email": "c@example.com", "password": "password123"}
    )
    assert login.status_code == 200
    token = login.json()["access_token"]
    assert token

    me = await client.get(ME, headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200
    assert me.json()["email"] == "c@example.com"


@pytest.mark.asyncio
async def test_login_wrong_password(client):
    await client.post(
        REGISTER,
        json={"email": "d@example.com", "password": "password123", "full_name": "Dan"},
    )
    resp = await client.post(
        LOGIN, json={"email": "d@example.com", "password": "wrongpass"}
    )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_me_without_token(client):
    resp = await client.get(ME)
    assert resp.status_code == 401
