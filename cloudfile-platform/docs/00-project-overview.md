# 00 — Project Overview

## What is CloudFile?

CloudFile is a cloud-native file management and processing platform. Users
register, upload files, those files are processed asynchronously (thumbnails
for images, metadata extraction), and users can search and manage their files.

It is intentionally built as a **microservices system across two repositories**
to demonstrate real-world engineering patterns for interviews and learning.

## Why this project exists

- Learn Python, FastAPI, microservices, AWS, Docker, Kubernetes, CI/CD by
  building one coherent system end to end.
- Produce an interview-ready portfolio piece you can explain deeply.
- Practice both the **monorepo** and **separate-repo (polyrepo)** patterns.

## The two repositories

| Repo | Pattern | Contains |
|------|---------|----------|
| `cloudfile-platform` | Monorepo | auth, files, search services + processor Lambda |
| `notification-service` | Separate repo | one standalone microservice |

## Features

- User registration and login (JWT-based auth)
- Direct-to-S3 uploads using presigned URLs (service never proxies bytes)
- Asynchronous processing via an S3-triggered Lambda (thumbnails + metadata)
- File search with filtering and pagination
- Notifications on key events (pluggable: console locally, SES on AWS)
- Full observability basics: health checks + structured JSON logs

## High-level architecture (one glance)

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

## Tech stack (summary)

Python 3.11 · FastAPI · Pydantic v2 · SQLAlchemy 2.0 (async) · Alembic ·
PostgreSQL · Redis · JWT · boto3 · httpx · Docker · Docker Compose ·
LocalStack · Kubernetes (minikube/EKS) · Terraform · GitHub Actions ·
pytest · ruff · mypy · AWS (S3, Lambda, RDS, ECS Fargate, ECR, IAM, SES).

## Timeline (3 hrs/day)

| Day | Outcome |
|-----|---------|
| 1 | Understand + run auth |
| 2 | Files + S3 upload flow |
| 3 | Search + Lambda |
| 4 | Both repos wired together locally |
| 5 | Kubernetes on minikube |
| 6 | CI/CD green on GitHub |
| 7 | AWS deploy + destroy, docs, interview prep |

## 30-second elevator pitch (for interviews)

> "CloudFile is a microservices file platform. Three FastAPI services handle
> auth, file management, and search; a separate service handles notifications.
> Files upload directly to S3 via presigned URLs, and an S3 event triggers a
> Lambda that generates thumbnails and extracts metadata. It runs on Kubernetes
> locally and deploys to AWS via Terraform with GitHub Actions CI/CD. I used a
> monorepo for the core services and a separate repo for notifications to show
> both code-organization patterns."
