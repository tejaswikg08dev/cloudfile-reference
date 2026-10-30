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
| Run it locally (full teaching guide) | [13-local-setup-complete](cloudfile-platform/docs/13-local-setup-complete.md) |
| Deploy to AWS (full teaching guide) | [14-production-setup-complete](cloudfile-platform/docs/14-production-setup-complete.md) |
| Test with Postman | [postman/](cloudfile-platform/postman/README.md) |
| Fix a startup error | [12-troubleshooting](cloudfile-platform/docs/12-troubleshooting.md) |
| Prep for interviews | [11-interview-prep](cloudfile-platform/docs/11-interview-prep.md) |
| Read the notification service | [notification-service/docs](notification-service/docs/README.md) |

---

## Run locally — step by step

> Prerequisites: Docker Desktop (running), Git, and `jq`. On Windows use Git Bash.
> Full teaching guide: [13-local-setup-complete.md](cloudfile-platform/docs/13-local-setup-complete.md).

**1) Clone**
```bash
git clone <your-repo-url> cloudfile
cd cloudfile
```

**2) Start the core platform** (Terminal 1)
```bash
cd cloudfile-platform
cp .env.example .env
docker compose up --build        # postgres, localstack, auth:8001, files:8002, search:8003
```
Wait for: `auth_service_started`, `files_service_started`, `search_service_started`.
Open http://localhost:8001/docs, http://localhost:8002/docs, http://localhost:8003/docs.

**3) Start the notification service** (Terminal 2)
```bash
cd notification-service
cp .env.example .env
docker compose up --build        # notify-db + notification:8004
```
Open http://localhost:8004/docs.

**4) Run the end-to-end demo** (Terminal 3)
```bash
cd cloudfile-platform
bash scripts/e2e-demo.sh         # register → login → upload → confirm → search → notify
```

**5) Or test with Postman** — import the collection + environment from
[`cloudfile-platform/postman/`](cloudfile-platform/postman/README.md) and run the
folders top to bottom (login auto-captures the token).

**Hard reset** (after pulling changes, to avoid stale cached code):
```bash
bash scripts/reset.sh            # down -v + build --no-cache + up  (in each repo)
```

Full local guide: [07-local-deployment.md](cloudfile-platform/docs/07-local-deployment.md)
· troubleshooting: [12-troubleshooting.md](cloudfile-platform/docs/12-troubleshooting.md).

## Deploy to the cloud — step by step

Full teaching guide: [14-production-setup-complete.md](cloudfile-platform/docs/14-production-setup-complete.md)
(provision with Terraform → push images to ECR → roll ECS → verify → **destroy**).
Kubernetes-on-minikube alternative (free): [10-cloud-deployment.md](cloudfile-platform/docs/10-cloud-deployment.md).

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
