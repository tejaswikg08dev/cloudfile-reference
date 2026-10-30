# 11 — Interview Prep

## The 30-second pitch

> "CloudFile is a microservices file platform. Three FastAPI services handle
> auth, files, and search; a separate service handles notifications. Files
> upload directly to S3 via presigned URLs, and an S3 event triggers a Lambda
> that makes thumbnails and extracts metadata. It runs on Kubernetes locally
> and deploys to AWS (ECS Fargate) via Terraform with GitHub Actions CI/CD."

## Architecture Q&A

**Q: Why microservices here, not a monolith?**
Each concern (identity, file lifecycle, search, notifications) has its own
scaling and failure profile. Notifications can be down without breaking
uploads. For a tiny app a modular monolith would be fine — I'd call that out as
an honest trade-off. Microservices here are also a deliberate learning goal.

**Q: Monorepo vs separate repo — why both?**
Monorepo for the three core services: shared library, one CI, atomic changes.
Separate repo for notifications: independently owned and deployed. Crucially,
it's a code-organization choice; the runtime architecture is identical either
way.

**Q: How do services authenticate each other?**
Shared-secret JWT (HS256). Auth issues tokens; every service verifies locally
with the same secret, avoiding a network hop. Inter-service calls forward the
caller's token. Downside: rotating the secret needs a coordinated redeploy.

**Q: Why presigned URLs?**
The client uploads bytes straight to S3, so the service stays stateless and
never proxies large payloads. It does add a two-step flow (initiate + confirm).

**Q: Files and search share a table — isn't that against microservices?**
Yes, strictly. I used a shared read model (CQRS-lite) for simplicity and
correctness in a learning project. The documented upgrade path is an event bus
(SNS/SQS) projecting into a search-owned datastore, which removes the coupling.

**Q: How do you handle failures?**
Notifications are fire-and-forget: failures are logged, never break uploads.
Processing is event-driven with S3 → Lambda; I'd add a dead-letter queue for
failed events in production. Services expose `/health` for probes.

**Q: How would you scale?**
Stateless services scale horizontally (HPA on CPU). S3/Lambda scale on their
own. For read-heavy search, add read replicas and/or Redis caching without
changing the API.

**Q: Security?**
bcrypt passwords, JWT with expiry, non-root containers, S3 public access
blocked (presigned URLs only), per-resource ownership checks, secrets via
K8s Secrets / AWS Secrets Manager.

**Q: How do you control cloud cost?**
Fargate instead of EKS (no control-plane fee), public subnets to avoid NAT
Gateway, db.t3.micro, and `terraform destroy` after every demo. Cost-awareness
is part of the design.

## Deep-dive topics (be ready to whiteboard)

- The upload sequence (initiate → PUT → confirm → S3 event → Lambda).
- JWT structure (header.payload.signature) and why HS256 vs RS256.
- Async request lifecycle in FastAPI (event loop, `run_in_threadpool` for boto3).
- Pagination math (`offset`, `total_pages`).
- Dockerfile multi-stage build and why non-root.
- Kubernetes objects used and what each does.
- Terraform `for_each` to create per-service ECR/ECS resources.

## Likely follow-ups and strong answers

- "What breaks at 10x scale?" → DB connections; add pooling/replicas; move
  search read model off the primary.
- "How do you do zero-downtime deploys?" → rolling updates in K8s / ECS with
  health checks; readiness gates traffic.
- "Observability?" → structured JSON logs now; add metrics (Prometheus) and
  tracing (OpenTelemetry) per service.
- "How do you test?" → unit/API tests per service with SQLite + fakes;
  integration tests against Dockerized Postgres as the next step.

## What you learned (say this confidently)

Python/FastAPI, async SQLAlchemy, JWT auth, microservices decomposition,
inter-service communication, S3/Lambda event pipelines, Docker, Kubernetes,
Terraform IaC, GitHub Actions CI/CD, and cloud cost management.

## Honesty points interviewers respect

- Calling the shared files table a pragmatic trade-off with a clear upgrade
  path.
- Choosing Fargate over EKS for cost, while still demoing EKS briefly.
- Fail-open notifications as a conscious availability decision.
