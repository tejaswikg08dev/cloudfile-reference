# 00 — Overview

## What is the Notification Service?

A small, standalone microservice that **sends and records notifications**. It is
called by the files service (in the `cloudfile-platform` monorepo) after a
successful file upload, and it can also be queried for a user's notification
history.

## Why it's a separate repository

The CloudFile system deliberately splits code across two repos to show two
patterns:

- `cloudfile-platform` — a **monorepo** with auth, files, and search.
- `notification-service` — this **separate repo** (polyrepo).

Keeping notifications in its own repo models a real situation where a service
is owned by a different team and released on its own schedule. It is fully
self-contained: it does NOT import the monorepo's `shared/` package; it carries
its own small copies of logging, exceptions, and JWT verification.

## Where it fits

```
Files Service (monorepo) ──httpx + JWT──► Notification Service (this repo)
                                                   │
                                                   ▼
                                          console (dev) / AWS SES (prod)
                                                   │
                                                   ▼
                                          PostgreSQL (notifications table)
```

## Responsibilities

- Accept a notification request (recipient, subject, message, channel).
- Deliver it through a pluggable provider.
- Record every notification (status `sent` or `failed`).
- Let a user list notifications addressed to their email.

## What it does NOT do

- It doesn't know anything about files, uploads, or search.
- It doesn't manage users (it only *verifies* their tokens).

## Tech stack

Python 3.11 · FastAPI · Pydantic v2 · SQLAlchemy 2.0 (async) · Alembic ·
PostgreSQL · JWT (python-jose) · boto3 (SES, optional) · Docker · Kubernetes ·
GitHub Actions · pytest · ruff · mypy.

## Pitch (interview)

> "The notification service is an independently-deployed microservice. It uses
> a strategy pattern for delivery providers — a console provider for local dev
> and AWS SES for production — and authenticates inter-service calls with the
> same shared-secret JWT as the rest of the platform. It fails open: if delivery
> fails, it records the failure but never blocks the caller."
