# 13 — Complete Local Setup (clone → running → tested)

A full, teaching walkthrough. Follow top to bottom the first time. Every step
says WHAT you do, WHY, and what you should SEE.

---

## 0. Prerequisites (install once)

| Tool | Check it's installed |
|------|----------------------|
| Git | `git --version` |
| Docker Desktop (running) | `docker --version` then `docker run --rm hello-world` |
| jq (for the demo script) | `jq --version` |
| Python 3.11+ (only if running tests outside Docker) | `python --version` |

> On Windows use **Git Bash** (MINGW64) to run the `.sh` scripts. Make sure
> Docker Desktop is open and shows "Engine running".

---

## 1. Clone the repository

```bash
git clone <your-repo-url> cloudfile
cd cloudfile
```

You will see two folders:
```
cloudfile-platform/      # monorepo: auth, files, search, processor
notification-service/    # separate service
```

**Why two folders:** the project demonstrates a monorepo and a separate repo
that talk to each other over HTTP.

---

## 2. Start the core platform (auth + files + search)

```bash
cd cloudfile-platform
cp .env.example .env         # first time only; defaults work for local
docker compose up --build
```

**What happens, in order:**
1. `postgres` starts and creates two databases (`cloudfile_auth`, `cloudfile_files`).
2. `localstack` starts (emulates AWS S3 on port 4566).
3. `auth` (8001), `files` (8002), `search` (8003) start once Postgres is healthy.

**What you should SEE** (good signs):
```
postgres-1   | ... database system is ready to accept connections
localstack-1 | Ready.
auth-1       | ... "message": "auth_service_started"
files-1      | ... "message": "files_service_started"
search-1     | ... "message": "search_service_started"
auth-1       | [INFO] Application startup complete.
```

**Verify in a browser:**
- http://localhost:8001/docs  (auth)
- http://localhost:8002/docs  (files)
- http://localhost:8003/docs  (search)

**Verify health from a terminal:**
```bash
curl http://localhost:8001/health
curl http://localhost:8002/health
curl http://localhost:8003/health
# each returns: {"status":"ok","service":"..."}
```

---

## 3. Start the notification service (separate repo)

Open a **second terminal**:
```bash
cd cloudfile/notification-service
cp .env.example .env          # first time only
docker compose up --build
```

**What you should SEE:**
```
notify-db-1     | ... database system is ready to accept connections
notification-1  | ... "message": "notification_service_started"
notification-1  | [INFO] Application startup complete.
```
- http://localhost:8004/docs  (notification)

> How they connect: the files service calls the notification service at
> `http://host.docker.internal:8004` (set in the platform `.env`). This works
> on Docker Desktop (Windows/Mac). On plain Linux, Docker Compose adds a
> `host-gateway` entry so it still resolves.

---

## 4. Run the end-to-end demo

Open a **third terminal**:
```bash
cd cloudfile/cloudfile-platform
bash scripts/e2e-demo.sh
```

**What it does and what you should SEE (✓ for each):**
1. Health checks for all 4 services
2. Register a new user
3. Login → get a JWT
4. Initiate an upload → get a presigned URL + file_id
5. PUT bytes to S3 (LocalStack)
6. Confirm the upload (fires a notification)
7. List files
8. Search by name
9. List notifications

Ending with: `Demo complete ✅`

---

## 5. Try it by hand (understand each call)

```bash
# Register
curl -X POST http://localhost:8001/api/v1/auth/register \
  -H 'Content-Type: application/json' \
  -d '{"email":"me@example.com","password":"password123","full_name":"Me"}'

# Login -> capture the token
TOKEN=$(curl -s -X POST http://localhost:8001/api/v1/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"email":"me@example.com","password":"password123"}' | jq -r .access_token)
echo "$TOKEN"

# Initiate an upload
curl -X POST http://localhost:8002/api/v1/files/upload \
  -H "Authorization: Bearer $TOKEN" -H 'Content-Type: application/json' \
  -d '{"filename":"demo.txt","content_type":"text/plain","size_bytes":12}'
# -> copy "upload_url" and "file_id" from the response

# Upload the bytes to the presigned URL
echo "hello world" > demo.txt
curl -X PUT "<upload_url>" -H 'Content-Type: text/plain' --data-binary @demo.txt

# Confirm (fires a notification)
curl -X POST http://localhost:8002/api/v1/files/confirm \
  -H "Authorization: Bearer $TOKEN" -H 'Content-Type: application/json' \
  -d '{"file_id":"<file_id>"}'

# Search
curl "http://localhost:8003/api/v1/search?name=demo" -H "Authorization: Bearer $TOKEN"

# See the notification that was recorded
curl http://localhost:8004/api/v1/notifications -H "Authorization: Bearer $TOKEN"
```

---

## 6. Run the automated tests

Tests run without Docker (in-memory SQLite + fakes). From `cloudfile-platform`:
```bash
# auth
cd services/auth   && pip install -r requirements-dev.txt && PYTHONPATH=.:../.. pytest && cd ../..
# files
cd services/files  && pip install -r requirements-dev.txt && PYTHONPATH=.:../.. pytest && cd ../..
# search
cd services/search && pip install -r requirements-dev.txt && PYTHONPATH=.:../.. pytest && cd ../..
```
Notification service:
```bash
cd ../notification-service && pip install -r requirements-dev.txt && pytest
```
All suites should report passing.

---

## 7. Stop everything

```bash
# In each stack's terminal: Ctrl+C, then:
docker compose down          # keep data
# or
docker compose down -v       # also wipe the database volume (fresh next time)
```

---

## 8. The golden rules (avoid 90% of problems)

1. **After pulling code or Dockerfile changes**, do a hard reset:
   ```bash
   docker compose down -v --remove-orphans
   docker compose build --no-cache
   docker compose up
   ```
   A plain `up --build` can reuse cached layers/volumes and run OLD code.

2. **Keep `JWT_SECRET_KEY` identical** in both compose files, or inter-service
   auth fails.

3. **The DB init script only runs on a fresh volume.** If you changed it, you
   must `down -v` to re-run it.

See [12-troubleshooting.md](12-troubleshooting.md) for every known error and fix.
