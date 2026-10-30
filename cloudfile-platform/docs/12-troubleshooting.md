# 12 — Troubleshooting & Fixes Applied

This document records every startup issue encountered on a fresh machine, the
root cause, and the fix that is now baked into the repo. If you hit a NEW issue,
add it here.

---

## Fixes already applied in this repo

### 1. CRLF line endings broke the init script
- **Error:** `/bin/bash^M: bad interpreter: No such file or directory`
- **Cause:** the `.sh` script was saved/checked out with Windows CRLF endings.
- **Fix applied:**
  - Added `.gitattributes` forcing `*.sh`, Dockerfiles, YAML, etc. to `eol=lf`.
  - So even on Windows, Git checks these out with Unix line endings.
- **If it still happens** (e.g. you edited the file in a Windows editor):
  ```bash
  dos2unix scripts/init-multiple-dbs.sh
  # or, without dos2unix:
  sed -i 's/\r$//' scripts/init-multiple-dbs.sh
  ```

### 2. Bash-only syntax in an Alpine (`/bin/sh`) container
- **Error:** `syntax error: unexpected redirection`, array failures.
- **Cause:** the script used bash features (`function`, `local`, `<<<`, arrays)
  but `postgres:15-alpine` only ships `/bin/sh` (BusyBox).
- **Fix applied:** `scripts/init-multiple-dbs.sh` rewritten in POSIX `sh`:
  - shebang `#!/bin/sh`
  - no `function` keyword, no `local`, no `<<<`, no arrays
  - comma-splitting done by swapping `IFS` and iterating

### 3. Postgres "trust authentication" warning
- **Warning:** `initdb: warning: enabling "trust" authentication for local connections`
- **Cause:** default local auth method is `trust`.
- **Fix applied:** compose sets
  `POSTGRES_HOST_AUTH_METHOD: scram-sha-256` and
  `POSTGRES_INITDB_ARGS: "--auth-host=scram-sha-256 --auth-local=scram-sha-256"`.
  Services connect over TCP with a password, so this is secure and quiet.

### 4. Locale warnings (`locale: not found`)
- **Warning:** `sh: locale: not found` / `no usable system locales were found`.
- **Cause:** Alpine ships minimal locales.
- **Decision:** harmless for this project — ignored. If you ever need advanced
  collation, switch the base image to `postgres:15` (Debian) or install
  `musl-locales`.

### 5. Duplicate table / type creation on startup
- **Error:** `duplicate key value violates unique constraint
  "pg_type_typname_nsp_index"` during `CREATE TABLE`, and `auth-1 exited with
  code 3`.
- **Real cause:** gunicorn runs **2 workers**; both call `create_all` at the
  same time and race on creating the same Postgres types/tables. (`create_all`
  is idempotent for one caller, but not against concurrent callers.)
- **Fix applied:** a shared helper `shared/db_init.py` (and a standalone copy in
  `notification-service/app/db_init.py`) that:
  1. only runs when `DB_AUTO_CREATE` is enabled (default true for dev),
  2. takes a **Postgres advisory lock** so workers serialize,
  3. calls `create_all(..., checkfirst=True)`,
  4. tolerates `IntegrityError`/`ProgrammingError` if a race still slips through.
  All three app `main.py` lifespans now call `create_all_safe(engine, Base.metadata)`.

### 6. Container exited with code 3
- **Cause:** the unhandled exception from issue #5 crashed the worker.
- **Fix:** resolved by #5. Startup is now race-safe and tolerant.

### 7. passlib + bcrypt version mismatch
- **Error/warning:** `(trapped) error reading bcrypt version` /
  `AttributeError: module 'bcrypt' has no attribute '__about__'`.
- **Cause:** `passlib==1.7.4` can't read the version of `bcrypt>=4.1`.
- **Fix applied:** pinned `bcrypt==4.0.1` in `services/auth/requirements.txt`.

---

## Production vs dev schema management

For a clean production setup, don't create tables from app startup. Instead:
```bash
# disable auto-create and use migrations
export DB_AUTO_CREATE=false
cd services/auth  && alembic upgrade head
cd services/files && alembic upgrade head
```
`DB_AUTO_CREATE=false` makes `create_all_safe` a no-op, so Alembic is the single
source of truth.

---

## Clean restart (fixes most "stuck" states)

```bash
docker compose down -v        # -v wipes the DB volume so init runs fresh
docker compose up --build
```
The `-v` matters: the init script in `/docker-entrypoint-initdb.d` only runs on
a FIRST, empty data directory. If you changed it, you must remove the volume.

### 8. Still seeing the OLD error after fixing the code?

Symptom: logs show `main.py line 22: await conn.run_sync(Base.metadata.create_all)`
even though the file now calls `create_all_safe`, OR `database "notify" does not
exist` repeating, OR the duplicate-key crash persists.

Cause: Docker is running a **cached image / old volume** built before the fix.
The container is NOT running your latest code.

Full hard reset (do this after pulling the fixes):
```bash
# In the failing repo (e.g. notification-service/)
docker compose down -v --remove-orphans      # stop + delete volumes
docker compose build --no-cache               # rebuild image from scratch
docker compose up                             # start fresh
```
`--no-cache` guarantees the new `main.py`, `db_init.py`, and Dockerfile
(now 1 worker) are actually baked into the image. `-v` guarantees a clean DB
so the `notifications` database is created fresh.

### 9. Why 1 gunicorn worker now?

The Dockerfiles were changed from `--workers 2` to `--workers 1`. With 2
workers, both tried to create tables at startup and raced (issue #5). One worker
is plenty for local/dev and removes the race entirely. In production you scale
with Kubernetes replicas and let Alembic own the schema (`DB_AUTO_CREATE=false`).

---

## Other issues you may hit (and fixes)

| Symptom | Cause | Fix |
|---------|-------|-----|
| `files` can't reach `notification` | notification stack not up / wrong URL | start notification on 8004; check `NOTIFICATION_SERVICE_URL` |
| `host.docker.internal` not resolving on Linux | Docker Desktop-only name | compose adds `extra_hosts: host-gateway`; on plain Linux use the host IP |
| LocalStack presigned PUT signature error | strict S3v4 signing vs LocalStack | metadata flow still works; for real S3 it's fine. The e2e script continues past this. |
| `database "cloudfile_auth" does not exist` | init ran before your script change | `docker compose down -v && up` to re-init |
| port 5432/8001 already in use | another process bound it | stop it or change the published port in compose |
| `pytest` can't import `app`/`shared` | path not set | run from the service dir with `PYTHONPATH=.:../..` (the per-service `conftest.py` also handles this) |
| ARM/Apple Silicon image pulls slow/fail | arch mismatch | images used are multi-arch; ensure Docker Desktop is up to date |

---

## How to report a NEW issue to your other machine

Capture:
1. The exact command you ran.
2. The full error output (copy the whole stack trace).
3. `docker compose ps` and `docker compose logs <service>` for the failing one.

That's enough to diagnose and fix precisely.
