# 01 — Requirements & Use Cases

## Actors

| Actor | Description |
|-------|-------------|
| User | Registers, logs in, uploads/searches/downloads files |
| Files Service | Calls the notification service after uploads |
| S3 | Stores objects; emits events on object creation |
| Processor Lambda | Reacts to S3 events; produces thumbnails/metadata |

## Functional Requirements

### Auth
- FR-A1: A user can register with email, password, and full name.
- FR-A2: Passwords are stored hashed (bcrypt), never in plain text.
- FR-A3: A user can log in and receive a JWT access token.
- FR-A4: A user can fetch their own profile with a valid token.
- FR-A5: Any service can verify a token using the shared secret.

### Files
- FR-F1: An authenticated user can request a presigned upload URL.
- FR-F2: The client uploads bytes directly to S3 (not through the service).
- FR-F3: The user confirms the upload; the file is marked "ready".
- FR-F4: Confirming an upload triggers a notification.
- FR-F5: A user can list their own files.
- FR-F6: A user can get a presigned download URL for their own file.
- FR-F7: A user can delete their own file (object + metadata).
- FR-F8: A user cannot access another user's files.

### Search
- FR-S1: A user can search their files by filename (partial match).
- FR-S2: A user can filter by content type.
- FR-S3: Results are paginated with total count and total pages.
- FR-S4: Search only ever returns the caller's own files.

### Processing
- FR-P1: When an image lands in S3, a thumbnail is generated.
- FR-P2: Processing updates file status/metadata in the database.
- FR-P3: Thumbnail objects do not re-trigger processing.

### Notification
- FR-N1: The service records every notification it is asked to send.
- FR-N2: Delivery provider is pluggable (console/SES).
- FR-N3: A user can list notifications addressed to their email.

## Non-Functional Requirements

| ID | Requirement | How it's met |
|----|-------------|--------------|
| NFR-1 | Stateless services (horizontal scale) | No in-process session; JWT; S3 for files |
| NFR-2 | Security | bcrypt, JWT, non-root containers, private S3 |
| NFR-3 | Observability | `/health` endpoints, structured JSON logs |
| NFR-4 | Resilience | Notification failure never breaks uploads |
| NFR-5 | Portability | 12-factor config via env vars; Docker images |
| NFR-6 | Cost efficiency | Fargate over EKS; destroy-after-demo; free tier |
| NFR-7 | Testability | Layered design; unit tests with SQLite + fakes |

## Key Use Cases

### UC-1: Upload a file (happy path)
1. User logs in → receives JWT.
2. User calls `POST /files/upload` with file metadata.
3. Service stores a `pending` row, returns a presigned PUT URL + file_id.
4. Client `PUT`s the bytes to S3.
5. User calls `POST /files/confirm` with file_id → status becomes `ready`.
6. Files service calls notification service (fire-and-forget).
7. S3 event triggers the Lambda → thumbnail + status `processed`.

### UC-2: Search files
1. User calls `GET /search?name=report&page=1&page_size=20`.
2. Search service queries the files read model with filters + pagination.
3. Returns a `Page` with items, total, page, page_size, total_pages.

### UC-3: Access control
1. User B requests User A's file download URL.
2. Files service checks ownership → returns 403 Forbidden.

## Out of Scope (deliberately)

- Multi-part/resumable uploads
- Sharing files between users / ACLs beyond ownership
- Full-text content search (only filename/type metadata)
- A web frontend (API-first; use Swagger UI at `/docs`)
