# 07 — Local Deployment (step by step)

Two ways to run locally:
- **A. Docker Compose** (recommended — closest to production)
- **B. Bare Python** (fastest for editing one service)

Both repos run independently. For the full experience (including the notify
step), run both.

---

## A. Run with Docker Compose

### Step 1 — Start the monorepo stack
```bash
cd cloudfile-platform
cp .env.example .env          # first time only
docker compose up --build
```
This starts: `postgres`, `localstack` (S3), `auth` (8001), `files` (8002),
`search` (8003). Wait until logs show each service "started".

Open the interactive API docs:
- http://localhost:8001/docs  (auth)
- http://localhost:8002/docs  (files)
- http://localhost:8003/docs  (search)

### Step 2 — Start the notification service (separate repo)
In a second terminal:
```bash
cd notification-service
cp .env.example .env          # first time only
docker compose up --build
```
- http://localhost:8004/docs  (notification)

> How they connect: the files service reaches the notification service at
> `http://host.docker.internal:8004` (set in the monorepo compose). The
> notification container publishes port 8004 on your host, so this works even
> though they're in separate compose projects.

### Step 3 — Create the S3 bucket in LocalStack (first run)
The files service calls `ensure_bucket()` on startup, so normally the bucket is
created automatically. If you want to do it manually:
```bash
cd cloudfile-platform
S3_ENDPOINT_URL=http://localhost:4566 S3_BUCKET_NAME=cloudfile-uploads \
  bash scripts/init-localstack.sh
```

### Step 4 — Run the end-to-end demo
With both stacks up, in a third terminal:
```bash
cd cloudfile-platform
bash scripts/e2e-demo.sh
```
This runs: health checks → register → login → upload → PUT to S3 → confirm →
list → search → list notifications, printing a ✓ for each step.

### Step 5 — Stop everything
```bash
# in each stack's terminal: Ctrl+C, then
docker compose down          # add -v to also wipe the database volume
```

---

## B. Run with bare Python (single service, fast iteration)

Useful when editing one service. You still need Postgres; the quickest is to
run just the DB via Docker:
```bash
cd cloudfile-platform
docker compose up -d postgres localstack
```

Then run a service locally (example: auth):
```bash
cd services/auth
python -m venv .venv && . .venv/Scripts/activate   # Windows
pip install -r requirements-dev.txt

# Point at the Dockerized Postgres on localhost:
export AUTH_DATABASE_URL="postgresql+asyncpg://cloudfile:cloudfile@localhost:5432/cloudfile_auth"
export JWT_SECRET_KEY="local-dev-secret-change-me-0123456789"

# PYTHONPATH must include the service root and the repo root (for `shared`):
PYTHONPATH=.:../.. uvicorn app.main:app --reload --port 8001
```
Open http://localhost:8001/docs.

Repeat with `files` (8002) and `search` (8003), setting their DB URLs
(`FILES_DATABASE_URL`, `SEARCH_DATABASE_URL`) to the `cloudfile_files` database.

---

## Manual test with curl (no script)

```bash
# 1) Register
curl -X POST http://localhost:8001/api/v1/auth/register \
  -H 'Content-Type: application/json' \
  -d '{"email":"me@example.com","password":"password123","full_name":"Me"}'

# 2) Login -> capture token
TOKEN=$(curl -s -X POST http://localhost:8001/api/v1/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"email":"me@example.com","password":"password123"}' | jq -r .access_token)

# 3) Initiate upload
curl -X POST http://localhost:8002/api/v1/files/upload \
  -H "Authorization: Bearer $TOKEN" -H 'Content-Type: application/json' \
  -d '{"filename":"demo.txt","content_type":"text/plain","size_bytes":12}'

# 4) Confirm (use file_id from step 3)
curl -X POST http://localhost:8002/api/v1/files/confirm \
  -H "Authorization: Bearer $TOKEN" -H 'Content-Type: application/json' \
  -d '{"file_id":"<FILE_ID>"}'

# 5) Search
curl "http://localhost:8003/api/v1/search?name=demo" \
  -H "Authorization: Bearer $TOKEN"
```

---

## Common issues

| Symptom | Fix |
|---------|-----|
| `files` can't reach notification | ensure notification stack is up on 8004; `host.docker.internal` works on Docker Desktop (Win/Mac). On Linux the compose adds `host-gateway`. |
| LocalStack PUT signature errors | expected sometimes; the demo continues. The metadata flow still works. |
| DB "database does not exist" | the init script creates `cloudfile_auth` + `cloudfile_files` on first boot; run `docker compose down -v` then `up` to re-init. |
| Port already in use | change the left side of the `ports:` mapping in compose. |
