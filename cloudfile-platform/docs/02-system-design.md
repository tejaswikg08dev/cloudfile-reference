# 02 — System Design

## API Design

Base path for every service: `/api/v1/...`. All responses for errors use a
consistent envelope: `{"success": false, "error": {"code", "message", "details"}}`.

### Auth Service (8001)

| Method | Path | Auth | Body / Query | Returns |
|--------|------|------|--------------|---------|
| POST | /api/v1/auth/register | no | email, password, full_name | UserOut (201) |
| POST | /api/v1/auth/login | no | email, password | Token |
| GET | /api/v1/auth/me | yes | — | UserOut |
| GET | /api/v1/auth/verify | yes | — | TokenVerifyResponse |
| GET | /health | no | — | status |

### Files Service (8002)

| Method | Path | Auth | Body / Query | Returns |
|--------|------|------|--------------|---------|
| POST | /api/v1/files/upload | yes | filename, content_type, size_bytes | UploadResponse (201) |
| POST | /api/v1/files/confirm | yes | file_id | FileOut |
| GET | /api/v1/files | yes | — | FileOut[] |
| GET | /api/v1/files/{id}/download | yes | — | DownloadResponse |
| DELETE | /api/v1/files/{id} | yes | — | 204 |
| GET | /health | no | — | status |

### Search Service (8003)

| Method | Path | Auth | Query | Returns |
|--------|------|------|-------|---------|
| GET | /api/v1/search | yes | name?, content_type?, page, page_size | Page[FileResult] |
| GET | /health | no | — | status |

### Notification Service (8004, separate repo)

| Method | Path | Auth | Body | Returns |
|--------|------|------|------|---------|
| POST | /api/v1/notifications/notify | yes | recipient, subject, message, channel | NotificationOut (201) |
| GET | /api/v1/notifications | yes | — | NotificationOut[] |
| GET | /health | no | — | status |

## Data Model

### users (owned by auth)
```sql
CREATE TABLE users (
  id              VARCHAR(36)  PRIMARY KEY,
  email           VARCHAR(255) UNIQUE NOT NULL,
  hashed_password VARCHAR(255) NOT NULL,
  full_name       VARCHAR(255) NOT NULL,
  is_active       BOOLEAN NOT NULL DEFAULT TRUE,
  created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

### files (owned by files; read by search; updated by processor)
```sql
CREATE TABLE files (
  id            VARCHAR(36)   PRIMARY KEY,
  owner_id      VARCHAR(36)   NOT NULL,          -- indexed
  filename      VARCHAR(512)  NOT NULL,
  content_type  VARCHAR(255)  NOT NULL,
  size_bytes    BIGINT        NOT NULL DEFAULT 0,
  s3_key        VARCHAR(1024) UNIQUE NOT NULL,
  status        VARCHAR(32)   NOT NULL DEFAULT 'pending',  -- pending|ready|processed
  thumbnail_key VARCHAR(1024),
  created_at    TIMESTAMPTZ   NOT NULL DEFAULT now()
);
```

### notifications (owned by notification)
```sql
CREATE TABLE notifications (
  id         VARCHAR(36)  PRIMARY KEY,
  recipient  VARCHAR(255) NOT NULL,              -- indexed
  subject    VARCHAR(512) NOT NULL,
  message    TEXT NOT NULL,
  channel    VARCHAR(32)  NOT NULL DEFAULT 'email',
  status     VARCHAR(32)  NOT NULL DEFAULT 'sent',
  created_at TIMESTAMPTZ  NOT NULL DEFAULT now()
);
```

## Capacity (back-of-envelope)

Assume 10k users, 100k files, average file 2 MB:
- Object storage: 100k × 2 MB = ~200 GB in S3 (cheap; pay per GB).
- Metadata rows: 100k rows — trivial for PostgreSQL.
- Uploads are direct-to-S3, so the service only handles tiny JSON requests →
  a single small instance per service handles thousands of req/s.
- Processing is event-driven: Lambda scales with upload rate automatically.

## Design Decisions

> **D1: Presigned URLs for upload/download.**
> Rationale: keeps services stateless and cheap; S3 handles the heavy bytes.
> Trade-off: client does two steps (initiate + PUT), and we need a `confirm`.

> **D2: Local JWT verification in each service.**
> Rationale: no network hop to auth on every request; one shared token format.
> Trade-off: rotating the secret requires redeploying all services.

> **D3: Shared files table between files and search (CQRS-lite).**
> Rationale: simple, correct, no sync lag for a learning project.
> Trade-off: not pure microservices isolation. The documented upgrade path is
> an event bus (SNS/SQS) projecting into a search-owned datastore.

> **D4: Fail-open notifications.**
> Rationale: a notification outage should never block a core upload.
> Trade-off: a notification can be silently lost (logged as a warning).

> **D5: Fargate as default AWS target, EKS optional.**
> Rationale: Fargate has no control-plane fee; protects free-tier credits.
> Trade-off: less "Kubernetes on cloud" experience — mitigated by minikube.

## Security Design

- Passwords: bcrypt with per-password salt.
- Tokens: JWT (HS256), short-lived, expiry enforced on verify.
- Transport: TLS terminates at the ingress/load balancer in real deploys.
- S3: public access blocked; all access via time-limited presigned URLs.
- Containers: run as non-root UID 1000.
- Secrets: env vars locally; Kubernetes Secrets / AWS Secrets Manager in prod.
- Authorization: ownership checks on every file operation.
