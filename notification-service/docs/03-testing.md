# 03 — Testing

## What's covered

| Test | Asserts |
|------|---------|
| test_health | `/health` returns ok with service name |
| test_notify_requires_auth | 401 without a token |
| test_notify_and_list | notify returns 201 + `status=sent`; list returns it |
| test_notify_invalid_channel | 422 for an unsupported channel |

Tests use an in-memory async SQLite database and the console provider, so they
need no Postgres and no AWS.

## Run

```bash
cd notification-service
pip install -r requirements-dev.txt
pytest
```

A root `conftest.py` puts the repo root on `sys.path`, and `tests/conftest.py`
sets test env vars (SQLite URL, JWT secret, console provider) before importing
the app, builds an in-memory DB, and overrides `get_db`. Requests go through
the real FastAPI app via `httpx.ASGITransport` (no network).

## Lint & types

```bash
ruff check app
mypy app
```

## CI

`.github/workflows/ci-cd.yml` runs lint + tests on every push/PR, then (on
`main`) builds and pushes the Docker image to ECR.

## Writing a new test (pattern)

```python
import pytest

@pytest.mark.asyncio
async def test_example(client, auth_headers):
    resp = await client.post(
        "/api/v1/notifications/notify",
        headers=auth_headers,
        json={"recipient": "a@b.com", "subject": "s", "message": "m"},
    )
    assert resp.status_code == 201
```
`client` and `auth_headers` come from `tests/conftest.py`.
