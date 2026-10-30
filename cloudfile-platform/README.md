# CloudFile Platform

A production-grade, microservices-based file management and processing platform demonstrating modern backend and cloud-native engineering.

This repository (`cloudfile-platform`) is a **monorepo** containing three microservices plus a Lambda. A fourth microservice (`notification-service`) lives in its own repository to demonstrate the **separate-repo (polyrepo)** pattern.

---

## Services

| Service | Port | Responsibility |
|---------|------|----------------|
| auth | 8001 | Registration, login, JWT issuing & verification |
| files | 8002 | File upload/download via S3 presigned URLs, metadata |
| search | 8003 | Query file metadata with filters & pagination |
| processor | (Lambda) | S3-triggered metadata extraction + thumbnails |

## Architecture

```
Client
  │
  ▼
Ingress ──► Auth    (8001) ──► PostgreSQL
  │
  ├───────► Files   (8002) ──► S3 ──► Lambda (processor)
  │                │
  │                └─► calls Notification Service (separate repo)
  │
  └───────► Search  (8003) ──► PostgreSQL
```

## Tech Stack

- Python 3.11, FastAPI, Pydantic v2
- SQLAlchemy 2.0 (async) + asyncpg, Alembic
- PostgreSQL, Redis
- JWT (python-jose), bcrypt (passlib)
- boto3 (S3/Lambda), httpx (inter-service calls)
- Docker, Docker Compose, LocalStack
- Kubernetes (minikube/EKS), Terraform
- GitHub Actions CI/CD
- pytest, ruff, mypy

## Local setup — step by step

> Prerequisites: Docker Desktop (running), Git, `jq`. On Windows use Git Bash.
> Full teaching guide with "what you should see" at each step:
> [docs/13-local-setup-complete.md](docs/13-local-setup-complete.md).

**Step 1 — configure env (first time only)**
```bash
cp .env.example .env
```
Defaults work for local. The only value that must match across all services is
`JWT_SECRET_KEY` (it's the same in both compose files already).

**Step 2 — start the platform**
```bash
docker compose up --build
```
Startup order: `postgres` (creates `cloudfile_auth` + `cloudfile_files`) →
`localstack` (S3 on 4566) → `auth` (8001), `files` (8002), `search` (8003).
Wait until you see each `*_service_started` and `Application startup complete`.

**Step 3 — open the API docs**
- Auth:   http://localhost:8001/docs
- Files:  http://localhost:8002/docs
- Search: http://localhost:8003/docs

**Step 4 — start the notification service** (separate repo, second terminal)
```bash
cd ../notification-service && cp .env.example .env && docker compose up --build
# http://localhost:8004/docs
```

**Step 5 — verify end to end**
```bash
bash scripts/e2e-demo.sh    # register → login → upload → confirm → search → notify
```

**Step 6 — or test with Postman** — import from [`postman/`](postman/README.md)
and run the folders top to bottom (login auto-saves the token; upload auto-saves
the file id and presigned URL).

### Local commands

```bash
make up        # start everything
make down      # stop everything
make test      # run all tests
make lint      # ruff + mypy
make migrate   # run DB migrations

bash scripts/reset.sh   # HARD reset: down -v + build --no-cache + up
```

> After pulling any code/Dockerfile change, run `bash scripts/reset.sh` so you
> never run stale cached images. This avoids the most common class of errors.

## Testing

- Postman: [`postman/`](postman/README.md) — full collection + local environment.
- Automated: see [docs/08-testing.md](docs/08-testing.md).
- Troubleshooting any startup error: [docs/12-troubleshooting.md](docs/12-troubleshooting.md).

## Visual docs (interactive)

Open [`visual-docs/index.html`](visual-docs/index.html) in a browser — animated,
offline, zero dependencies. Highlights: the Upload Journey, Local Deployment,
Cloud Deployment, and Monorepo-vs-Polyrepo pages.

## Documentation

Full docs live in [`docs/`](docs/README.md):

| Doc | Topic |
|-----|-------|
| 00 | Project overview |
| 01 | Requirements & use cases |
| 02 | System design |
| 03 | High-level design (HLD) |
| 04 | Low-level design (LLD) |
| 05 | Tech skills |
| 06 | Environment setup |
| 07 | Local deployment (step by step) |
| 08 | Testing |
| 09 | Development guide |
| 10 | Cloud deployment (K8s + AWS) |
| 11 | Interview prep |
| 12 | Troubleshooting (every known error + fix) |
| 13 | Complete local setup (clone → tested) |
| 14 | Complete production setup (AWS, step by step) |

## Cost Warning (AWS)

Always run `terraform destroy` after testing AWS deployments. EKS and NAT
Gateways accrue charges hourly. See `infra/terraform/README.md`.
