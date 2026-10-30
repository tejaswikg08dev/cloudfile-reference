# 01 — Design

## API

Base path: `/api/v1/notifications`. Auth required (JWT) on all but `/health`.

| Method | Path | Body | Returns |
|--------|------|------|---------|
| POST | /api/v1/notifications/notify | recipient, subject, message, channel | NotificationOut (201) |
| GET | /api/v1/notifications | — | NotificationOut[] (caller's email) |
| GET | /health | — | status |

### Schemas

```python
NotifyRequest:
  recipient: EmailStr
  subject:   str (1..512)
  message:   str (1..5000)
  channel:   "email" | "sms" | "push"   # default "email"

NotificationOut:
  id, recipient, subject, message, channel, status, created_at
```

## Data Model

```sql
CREATE TABLE notifications (
  id         VARCHAR(36)  PRIMARY KEY,
  recipient  VARCHAR(255) NOT NULL,          -- indexed
  subject    VARCHAR(512) NOT NULL,
  message    TEXT NOT NULL,
  channel    VARCHAR(32)  NOT NULL DEFAULT 'email',
  status     VARCHAR(32)  NOT NULL DEFAULT 'sent',   -- sent | failed
  created_at TIMESTAMPTZ  NOT NULL DEFAULT now()
);
```

## Layered Architecture

```
router.py        HTTP endpoints (FastAPI)
  │
service.py       NotificationService: send via provider, persist row
  │
repository.py    NotificationRepository: create, list_by_recipient
  │
models.py        Notification ORM model
```

Supporting modules:
- `config.py` — env-based settings
- `database.py` — async engine/session + `get_db`
- `dependencies.py` — DI wiring + JWT dependency
- `auth_utils.py` — standalone `verify_token`
- `logging_config.py`, `exceptions.py` — standalone copies (no monorepo dep)

## Providers (Strategy pattern)

```
NotificationProvider (ABC)
    .send(recipient, subject, message)
      ├─ ConsoleProvider   logs the message (free, default for dev)
      └─ SESProvider       sends email via AWS SES (boto3 via threadpool)

factory.get_provider()  → picks provider from NOTIFICATION_PROVIDER env var
```

Adding a new channel (e.g., SMS via SNS) = add a provider class + a branch in
the factory. Nothing else changes.

## Key behaviors

- **Fail-open delivery**: if the provider raises, the service records the row
  with `status="failed"` and still returns 201. The caller is never blocked.
- **Auth on /notify**: the endpoint requires a valid JWT. The files service
  forwards the user's token when it calls this service.
- **Ownership on list**: `GET /notifications` lists rows whose `recipient`
  equals the caller's email (from the token).

## Design Decisions

> **D1: Standalone (no shared library).**
> Rationale: a separate repo shouldn't depend on another repo's internal
> package. Trade-off: a little duplicated boilerplate (logging/exceptions/JWT).

> **D2: Strategy pattern for providers.**
> Rationale: swap console/SES/SMS without touching business logic.

> **D3: Record even failed sends.**
> Rationale: observability and retries later; never lose the intent silently.
