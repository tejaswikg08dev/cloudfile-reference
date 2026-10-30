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

## Quick Start (Local)

```bash
cp .env.example .env
docker compose up --build
```

- Auth docs:   http://localhost:8001/docs
- Files docs:  http://localhost:8002/docs
- Search docs: http://localhost:8003/docs

## Local commands

```bash
make up        # start everything
make down      # stop everything
make test      # run all tests
make lint      # ruff + mypy
make migrate   # run DB migrations
```

## End-to-end demo

With both stacks running (this repo + notification-service):

```bash
bash scripts/e2e-demo.sh
```

Runs register → login → upload → PUT to S3 → confirm → list → search → notify.

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

## Cost Warning (AWS)

Always run `terraform destroy` after testing AWS deployments. EKS and NAT
Gateways accrue charges hourly. See `infra/terraform/README.md`.
