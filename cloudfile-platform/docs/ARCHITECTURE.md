# Architecture

## Overview

CloudFile is a microservices platform for uploading, processing, and searching
files. It is split across two repositories to demonstrate both the monorepo
and polyrepo patterns.

```
┌──────────────────────── cloudfile-platform (monorepo) ───────────────────────┐
│                                                                               │
│  Client ─► Ingress ─► Auth   (8001) ─────────► PostgreSQL (cloudfile_auth)    │
│              │                                                                │
│              ├──────► Files  (8002) ─► S3 ─► Lambda (processor) ─► DB update   │
│              │           │                                                    │
│              │           └─► httpx + JWT ─────────────────────┐               │
│              │                                                │               │
│              └──────► Search (8003) ─────────► PostgreSQL (cloudfile_files)    │
│                                                               │               │
└───────────────────────────────────────────────────────────────┼─────────────┘
                                                                  ▼
                   ┌──────── notification-service (separate repo) ────────┐
                   │   Notification (8004) ─► console / AWS SES           │
                   │   PostgreSQL (notifications)                         │
                   └──────────────────────────────────────────────────────┘
```

## Services

### Auth (8001)
Issues and verifies JWTs. Owns the `users` table. Other services verify tokens
locally with the shared secret (no network hop), and may also call `/verify`.

### Files (8002)
Owns the `files` table. Issues S3 presigned URLs so clients upload directly to
S3 (the service never proxies file bytes). After a client confirms an upload,
it calls the notification service.

### Search (8003)
Reads the `files` table (read model). Provides filtering + pagination. Never
writes — a lightweight CQRS split.

### Processor (Lambda)
Triggered by S3 `ObjectCreated` events. Generates thumbnails for images and
updates file metadata/status in the database.

### Notification (8004, separate repo)
Sends and records notifications. Pluggable providers (console/SES).

## Key Design Decisions

- **Layered architecture**: router → service → repository → model. Business
  logic has no HTTP or DB framework knowledge leaking across boundaries.
- **Presigned URLs**: offload file transfer to S3, keeping services stateless
  and cheap to scale.
- **Local JWT verification**: avoids a hard dependency on auth being up for
  every request while keeping one source of truth for the token format.
- **Async everywhere**: FastAPI + async SQLAlchemy + httpx for throughput.
- **Shared DB for files/search**: pragmatic read model. In a larger system
  this would become an event-driven projection into a separate datastore.
- **Fail-open notifications**: a notification failure never breaks an upload.

## Data Ownership

| Table | Owner | Readers |
|-------|-------|---------|
| users | auth | auth |
| files | files | files (write), search (read), processor (update) |
| notifications | notification | notification |

## Security

- Passwords hashed with bcrypt.
- JWTs signed with a shared secret (HS256); expiry enforced.
- Containers run as a non-root user.
- S3 bucket blocks public access; access via presigned URLs only.
- Inter-service calls carry the caller's JWT.
