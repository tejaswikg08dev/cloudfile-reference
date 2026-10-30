# 16 — Manual Testing Walkthrough (beginner-friendly)

This guide explains **what the project is**, **how it works**, and walks you
through testing every feature by hand using the Swagger UI (the `/docs` pages).
No tools beyond a browser needed.

---

## What is CloudFile?

A file storage + management backend, built as **microservices** (several small
independent services). Like a simplified Dropbox/Google Drive backend:

- Create an account, log in.
- Upload files (stored in AWS S3; LocalStack emulates S3 locally).
- Files are processed in the background (thumbnails).
- Search and manage your files.
- Get notified when things happen.

### The services

| Service | Port | Role (plain English) |
|---------|------|----------------------|
| auth | 8001 | Security guard — sign-up, login, hands out a token (your "pass") |
| files | 8002 | File clerk — upload link, record details, download, delete |
| search | 8003 | Librarian — find files by name/type, paginated |
| notification | 8004 | Messenger — records/sends a notice (separate repo) |
| processor | Lambda | Background worker — makes thumbnails when a file arrives |

### The main flow

```
LOGIN (auth) → get token
  → ask files to UPLOAD → get a temporary S3 upload link
  → PUT the file to that link (goes straight to S3)
  → CONFIRM (files) → marks file "ready" + notifies
  → SEARCH (search) → find it
```

Key idea: file bytes go **directly to S3**, not through the services. Services
only exchange small JSON + a token. This keeps them fast, stateless, and cheap.

---

## Before you start

Both stacks must be running:

```bash
# Terminal 1
cd cloudfile-platform && docker compose up --build

# Terminal 2
cd notification-service && docker compose up --build
```

Confirm these pages open in your browser:
- http://localhost:8001/docs  (auth)
- http://localhost:8002/docs  (files)
- http://localhost:8003/docs  (search)
- http://localhost:8004/docs  (notification)

Each `/docs` page is an interactive API explorer (Swagger UI). You click an
endpoint → **Try it out** → fill the body → **Execute** → see the response.

---

## Step 1 — Register a user (auth, 8001)

1. Open http://localhost:8001/docs
2. Expand **POST /api/v1/auth/register** → **Try it out**
3. Paste this body and **Execute**:
   ```json
   {
     "email": "me@example.com",
     "password": "password123",
     "full_name": "Me"
   }
   ```
4. **Expected:** `201 Created` with your user (note: no password is returned).
5. Try registering the SAME email again → **Expected:** `409 Conflict` with
   `"code": "conflict"`. (Good — duplicates are blocked.)
6. Try a short password (`"123"`) → **Expected:** `422` validation error.

---

## Step 2 — Log in and copy your token (auth, 8001)

1. Expand **POST /api/v1/auth/login** → **Try it out**
2. Body → **Execute**:
   ```json
   { "email": "me@example.com", "password": "password123" }
   ```
3. **Expected:** `200 OK` with:
   ```json
   { "access_token": "eyJhbGc...", "token_type": "bearer", "expires_in": 3600 }
   ```
4. **Copy the `access_token` value.** This is your pass for every other call.
5. Try a wrong password → **Expected:** `401 Unauthorized`.

### Authorize Swagger with your token
At the top-right of the **files** and **search** docs pages there's an
**Authorize** button (a padlock). Click it, paste:
```
<paste the access_token here>
```
(If it asks for a scheme, the value is just the token — Swagger adds "Bearer".)
Now your calls on that page are authenticated automatically.

---

## Step 3 — Check your profile (auth, 8001)

1. Expand **GET /api/v1/auth/me** → Authorize with the token (padlock) → **Execute**
2. **Expected:** `200 OK` with your email and full name.
3. Without a token → **Expected:** `401 Unauthorized`.

---

## Step 4 — Start a file upload (files, 8002)

1. Open http://localhost:8002/docs → **Authorize** with your token.
2. Expand **POST /api/v1/files/upload** → **Try it out** → body → **Execute**:
   ```json
   {
     "filename": "notes.txt",
     "content_type": "text/plain",
     "size_bytes": 12
   }
   ```
3. **Expected:** `201 Created` with:
   ```json
   {
     "file_id": "....",
     "upload_url": "http://localhost:4566/cloudfile-uploads/uploads/....",
     "s3_key": "uploads/....",
     "expires_in": 3600
   }
   ```
4. **Copy `file_id` and `upload_url`.** `upload_url` is a temporary link to put
   the actual file bytes into storage.
5. Try `size_bytes: 999999999` (over 100 MB) → **Expected:** `422` (size cap).

---

## Step 5 — Upload the actual bytes to the link

The `upload_url` points at S3 (LocalStack). Swagger can't easily do this raw
PUT, so use a terminal:

```bash
echo "hello world!" > notes.txt
curl -X PUT "<paste upload_url>" -H "Content-Type: text/plain" --data-binary @notes.txt
```
**Expected:** no error (HTTP 200). The file is now in storage.

> If you see a signature warning from LocalStack, it's lenient by default and
> still stores the object — you can continue.

---

## Step 6 — Confirm the upload (files, 8002)

1. Expand **POST /api/v1/files/confirm** → **Try it out** → body → **Execute**:
   ```json
   { "file_id": "<paste file_id>" }
   ```
2. **Expected:** `200 OK` with `"status": "ready"`.
3. Behind the scenes this also calls the notification service (fire-and-forget).
   Watch the `files` and `notification` logs — you'll see `notification_sent`.
4. Try confirming a random `file_id` like `"does-not-exist"` →
   **Expected:** `404 Not Found` with `"code": "not_found"` (a clean error).

---

## Step 7 — List your files (files, 8002)

1. Expand **GET /api/v1/files** → **Execute** (token required).
2. **Expected:** `200 OK` with an array containing your `notes.txt`, status `ready`.

---

## Step 8 — Get a download link (files, 8002)

1. Expand **GET /api/v1/files/{file_id}/download** → put your `file_id` → **Execute**.
2. **Expected:** `200 OK` with a `download_url`.
3. Download it in a terminal:
   ```bash
   curl "<paste download_url>"
   # -> prints: hello world!
   ```

---

## Step 9 — Search your files (search, 8003)

1. Open http://localhost:8003/docs → **Authorize** with your token.
2. Expand **GET /api/v1/search** → **Try it out**.
3. Try these and **Execute** each:
   - no filters → returns all your files, paginated
   - `name = notes` → returns files whose name contains "notes"
   - `content_type = text/plain` → filter by type
   - `page = 1`, `page_size = 2` → see pagination (`total`, `total_pages`)
4. **Expected:** `200 OK` with:
   ```json
   {
     "items": [ ... ],
     "total": 1,
     "page": 1,
     "page_size": 20,
     "total_pages": 1
   }
   ```

---

## Step 10 — Notifications (notification, 8004)

1. Open http://localhost:8004/docs → **Authorize** with your token.
2. Expand **GET /api/v1/notifications** → **Execute**.
3. **Expected:** `200 OK` with the notification created in Step 6
   ("Your file was uploaded").
4. You can also send one manually via **POST /api/v1/notifications/notify**:
   ```json
   {
     "recipient": "me@example.com",
     "subject": "Test",
     "message": "Hello from manual testing",
     "channel": "email"
   }
   ```
   **Expected:** `201 Created`, `"status": "sent"`.

---

## Step 11 — Access control (prove isolation)

1. Register a SECOND user (`other@example.com`) and log in as them → new token.
2. On the files docs page, re-**Authorize** with the SECOND user's token.
3. Try **GET /api/v1/files/{file_id}/download** with the FIRST user's `file_id`.
4. **Expected:** `403 Forbidden` — you can only access your own files. 

---

## Step 12 — Delete a file (files, 8002)

1. Back as the first user (re-authorize with their token).
2. Expand **DELETE /api/v1/files/{file_id}** → put your `file_id` → **Execute**.
3. **Expected:** `204 No Content` (empty body = success).
4. List files again → **Expected:** the file is gone.

---

## What you just verified

| Area | Proven |
|------|--------|
| Auth | register, duplicate block, login, bad password, profile, token required |
| Files | presigned upload, confirm, list, download, delete, size cap |
| Storage | bytes go directly to S3 (LocalStack) |
| Inter-service | files → notification on confirm |
| Search | filters + pagination, owner-only results |
| Security | per-user isolation (403 on others' files) |
| Errors | clean 404/409/422/401/403 responses |

That's the entire system, exercised by hand. For an automated version of the
same flow, run `bash scripts/e2e-demo.sh`.

---

## Quick reference — expected status codes

| Code | Meaning | When you'll see it |
|------|---------|--------------------|
| 200 | OK | login, list, search, download link |
| 201 | Created | register, upload initiate, confirm-notify |
| 204 | No Content | delete success |
| 401 | Unauthorized | missing/invalid token, wrong password |
| 403 | Forbidden | accessing another user's file |
| 404 | Not Found | file_id doesn't exist |
| 409 | Conflict | registering an existing email |
| 422 | Validation error | bad input (short password, oversize file) |
