# 08 — Testing

## Philosophy

- Each service is tested in isolation with fast, dependency-free unit/API tests.
- Databases are replaced with in-memory SQLite (async) so no Postgres is needed.
- External systems (S3, the notification service) are replaced with fakes.
- Tests exercise the real FastAPI app via `httpx.ASGITransport` (no network).

## What is covered

| Service | Tests |
|---------|-------|
| auth | health, register (success/duplicate/short password), login (success/wrong), me (with/without token) |
| files | health, auth required, full upload→confirm→list→download→delete flow, size cap, cross-user 403 |
| search | health, auth required, owner-only results, filter by name, filter by type, pagination |
| notification | health, auth required, notify+list, invalid channel |

## How to run (monorepo)

Each service is run from its own directory so imports resolve. A per-service
`conftest.py` injects the right `sys.path`, so this works in an IDE too.

```bash
cd cloudfile-platform

# auth
cd services/auth
pip install -r requirements-dev.txt
PYTHONPATH=.:../.. pytest
cd ../..

# files
cd services/files
pip install -r requirements-dev.txt
PYTHONPATH=.:../.. pytest
cd ../..

# search
cd services/search
pip install -r requirements-dev.txt
PYTHONPATH=.:../.. pytest
cd ../..
```

Or use the Makefile:
```bash
make test     # runs all three
```

## How to run (notification-service)

```bash
cd notification-service
pip install -r requirements-dev.txt
pytest
```

## Linting & typing

```bash
# monorepo
ruff check services shared
mypy services shared

# notification-service
ruff check app
mypy app
```

## In CI

- Monorepo `.github/workflows/ci.yml` runs a matrix over the 3 services:
  install deps → `ruff check` → `pytest`.
- Notification `.github/workflows/ci-cd.yml` runs lint + test, then (on main)
  builds and pushes the image.

## Writing a new test (pattern)

```python
import pytest

@pytest.mark.asyncio
async def test_something(client, auth_headers):
    resp = await client.get("/api/v1/...", headers=auth_headers)
    assert resp.status_code == 200
```
`client` and `auth_headers` come from the service's `tests/conftest.py`.

## Why SQLite for tests?

The business logic is DB-agnostic (plain SQLAlchemy Core/ORM queries), so an
in-memory SQLite database gives fast, isolated tests. Postgres-specific
behavior (e.g., concurrency, specific SQL) would be validated in integration
tests against the real Dockerized Postgres — a natural next step.
