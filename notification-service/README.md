# Notification Service

A standalone microservice (its own repository) that sends notifications and
records them. It demonstrates the **separate-repo (polyrepo)** pattern alongside
the `cloudfile-platform` monorepo.

It is called by the files service after a successful upload, and authenticates
requests using the same shared JWT secret as the rest of the platform.

## Tech Stack

- Python 3.11, FastAPI, Pydantic v2
- SQLAlchemy 2.0 (async) + asyncpg, Alembic
- PostgreSQL
- JWT verification (python-jose)
- Pluggable providers: `console` (dev) and `ses` (AWS SES)
- Docker, Kubernetes, GitHub Actions

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | /api/v1/notifications/notify | Send + record a notification (auth required) |
| GET  | /api/v1/notifications | List notifications for the caller's email |
| GET  | /health | Health check |

## Quick Start (Local)

```bash
cp .env.example .env
docker compose up --build
# docs: http://localhost:8004/docs
```

## Tests

```bash
pip install -r requirements-dev.txt
pytest
```

## How it connects to the platform

The files service (in the `cloudfile-platform` repo) calls this service at
`NOTIFICATION_SERVICE_URL`. Locally that is `http://host.docker.internal:8004`
so the monorepo's containers can reach this service running on the host.

## Providers

- `NOTIFICATION_PROVIDER=console` — logs the notification (free, default).
- `NOTIFICATION_PROVIDER=ses` — sends real email via AWS SES. Requires verified
  sender/recipient in SES sandbox and appropriate IAM permissions.

## Documentation

Full docs in [`docs/`](docs/README.md):

| Doc | Topic |
|-----|-------|
| 00 | Overview |
| 01 | Design (API, data model, providers) |
| 02 | Local deployment |
| 03 | Testing |
| 04 | Cloud deployment |

## Visual docs

Interactive visual guides (including the monorepo-vs-polyrepo and cloud
deployment pages that cover this service) live in the platform repo at
`../cloudfile-platform/visual-docs/index.html`.
