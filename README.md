# CloudFile — Reference Project

A production-grade, microservices **file management and processing platform**,
built as a learning + interview-prep reference. It demonstrates modern backend
and cloud-native engineering end to end: Python, FastAPI, microservices, AWS,
Docker, Kubernetes, Terraform, and CI/CD.

> This repository is for **reference and browsing**. It contains two projects
> that are designed to be two independent Git repositories, kept here together
> so they're easy to read in one place.

---

## What's inside

```
cloudfile-reference/
├── cloudfile-platform/      ← MONOREPO: auth + files + search + processor (Lambda)
└── notification-service/    ← SEPARATE REPO: one standalone microservice
```

| Folder | Pattern | Services | Docs |
|--------|---------|----------|------|
| [`cloudfile-platform/`](cloudfile-platform/README.md) | Monorepo | auth, files, search, processor | [docs](cloudfile-platform/docs/README.md) · [visual docs](cloudfile-platform/visual-docs/index.html) |
| [`notification-service/`](notification-service/README.md) | Separate repo | notification | [docs](notification-service/docs/README.md) |

The split is intentional: it shows **both** the monorepo and the separate-repo
(polyrepo) patterns, and how services communicate across that boundary.

---

## What it does

Users register and log in, request a presigned URL to upload a file directly to
S3, confirm the upload (which fires a notification), and search their files. An
S3 event triggers a Lambda that generates thumbnails and extracts metadata.

```
Client
  │
  ▼
Ingress ──► Auth    (8001) ──► PostgreSQL (users)
  │
  ├───────► Files   (8002) ──► S3 ──► Lambda (processor) ──► DB update
  │                │
  │                └─► httpx + JWT ─► Notification (8004, separate repo)
  │
  └───────► Search  (8003) ──► PostgreSQL (files, read)
```

---

## Tech stack

**Backend:** Python 3.11 · FastAPI · Pydantic v2 · SQLAlchemy 2.0 (async) · Alembic
**Data:** PostgreSQL · Redis · JWT · bcrypt
**Cloud (AWS):** S3 · Lambda · RDS · ECS Fargate · ECR · IAM · SES · (optional) EKS
**DevOps:** Docker · Docker Compose · LocalStack · Kubernetes · Terraform · GitHub Actions
**Quality:** pytest · ruff · mypy

---

## Explore it

| I want to... | Go to |
|--------------|-------|
| See the big picture, animated | [visual-docs/index.html](cloudfile-platform/visual-docs/index.html) |
| Understand the design (HLD/LLD) | [03-high-level-design](cloudfile-platform/docs/03-high-level-design.md) · [04-low-level-design](cloudfile-platform/docs/04-low-level-design.md) |
| Run it locally | [07-local-deployment](cloudfile-platform/docs/07-local-deployment.md) |
| Deploy to the cloud | [10-cloud-deployment](cloudfile-platform/docs/10-cloud-deployment.md) |
| Prep for interviews | [11-interview-prep](cloudfile-platform/docs/11-interview-prep.md) |
| Read the notification service | [notification-service/docs](notification-service/docs/README.md) |

---

## Run locally (quick)

```bash
# Terminal 1 — core services
cd cloudfile-platform
cp .env.example .env
docker compose up --build        # auth:8001 files:8002 search:8003 (+postgres +localstack)

# Terminal 2 — notification service
cd notification-service
cp .env.example .env
docker compose up --build        # notification:8004

# Terminal 3 — end-to-end demo
cd cloudfile-platform
bash scripts/e2e-demo.sh
```

Full, step-by-step instructions: [local deployment guide](cloudfile-platform/docs/07-local-deployment.md).

---

## What you learn from this project

Backend engineering (clean layered architecture, async APIs, auth), microservices
(decomposition, inter-service communication, monorepo vs polyrepo), AWS
(S3/Lambda/RDS/ECS/ECR/IAM), DevOps (Docker, Kubernetes, Terraform, CI/CD), and
engineering practices (testing, linting, typing, structured logging, cost
control). See [tech & skills](cloudfile-platform/docs/05-tech-skills.md).

---

## Notes

- Each folder is structured to be its own Git repository; they live together
  here purely for convenient browsing.
- `.env` files are not included (gitignored). `.env.example` files show the
  expected configuration.
- On AWS, always run `terraform destroy` after testing. See the
  [cloud deployment guide](cloudfile-platform/docs/10-cloud-deployment.md).
