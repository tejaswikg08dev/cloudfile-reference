# 03 — High-Level Design (HLD)

## Component Diagram

```
                              ┌───────────────┐
                              │    Client     │
                              │ (curl / app)  │
                              └───────┬───────┘
                                      │ HTTPS
                              ┌───────▼───────┐
                              │  Ingress / LB │
                              └───┬───┬───┬───┘
              ┌───────────────────┘   │   └───────────────────┐
              ▼                       ▼                       ▼
      ┌───────────────┐      ┌───────────────┐      ┌───────────────┐
      │  Auth Service │      │ Files Service │      │ Search Service│
      │   FastAPI     │      │   FastAPI     │      │   FastAPI     │
      └───────┬───────┘      └───┬───────┬───┘      └───────┬───────┘
              │                  │       │                  │
              ▼                  │       ▼                  ▼
      ┌───────────────┐          │   ┌───────┐      ┌───────────────┐
      │  PostgreSQL   │          │   │  S3   │      │  PostgreSQL   │
      │   (users)     │          │   └───┬───┘      │   (files)     │
      └───────────────┘          │       │          └───────────────┘
                                 │       │ ObjectCreated
                                 │       ▼
                                 │  ┌───────────────┐
                                 │  │ Processor     │
                                 │  │ Lambda        │──► updates files DB
                                 │  └───────────────┘
                                 │ httpx + JWT
                                 ▼
                        ┌───────────────────┐
                        │ Notification Svc  │ (separate repo)
                        │   FastAPI         │──► console / SES
                        └───────────────────┘
```

## Component Responsibilities

| Component | Responsibility | Does NOT do |
|-----------|----------------|-------------|
| Auth | identity, tokens | store files |
| Files | file lifecycle, S3 URLs, ownership | search, send emails |
| Search | read-only queries | write files |
| Processor | async image/metadata work | serve HTTP |
| Notification | deliver + record messages | know about files logic |

## Data Flow Traces

### Flow 1: Register + Login
```
Client → Auth /register → hash password → INSERT users → 201
Client → Auth /login → verify bcrypt → sign JWT → { access_token }
```

### Flow 2: Upload
```
Client → Files /upload (JWT)
  → verify JWT locally
  → INSERT files(status=pending)
  → s3.generate_presigned_url(put) → { upload_url, file_id }
Client → PUT bytes → S3
Client → Files /confirm (JWT)
  → ownership check → UPDATE files SET status='ready'
  → httpx POST Notification /notify (JWT forwarded)   [fire-and-forget]
S3 ObjectCreated → Lambda
  → if image: make thumbnail → put thumbnails/<key>
  → UPDATE files SET status='processed', thumbnail_key=...
```

### Flow 3: Search
```
Client → Search /search?name=..&page=1 (JWT)
  → verify JWT → SELECT ... WHERE owner_id=? AND filename ILIKE ?
  → COUNT(*) for total → build Page → return
```

## Module Dependency Map

```
shared/ ──────────────┐  (used by auth, files, search)
  responses, exceptions, logging, auth_utils, pagination

auth    → shared
files   → shared, (httpx → notification-service)
search  → shared
processor → boto3, Pillow, psycopg2 (standalone)
notification-service → self-contained (own copies, no shared/)
```

## Technology Choices (rationale)

| Choice | Why | Alternative considered |
|--------|-----|------------------------|
| FastAPI | async, typed, auto OpenAPI | Flask (sync), Django (heavy) |
| async SQLAlchemy | non-blocking DB under async app | sync SQLAlchemy |
| PostgreSQL | relational metadata, strong querying | DynamoDB (no joins) |
| S3 presigned URLs | offload bytes, stateless services | proxy through service (slow) |
| Lambda | event-driven, scales to zero | always-on worker (costs idle) |
| Fargate | no control-plane fee | EKS (expensive for a demo) |
| Terraform | reproducible infra, teaches IaC | console clicks (not repeatable) |

## Scaling Strategy

- Stateless services → scale horizontally behind the ingress (HPA on CPU).
- S3 and Lambda scale independently of the services.
- PostgreSQL: start single instance; add read replicas for search if needed.
- Hot path (search) can add Redis caching later without API changes.
