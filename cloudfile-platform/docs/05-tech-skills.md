# 05 — Tech Skills (what you use and learn)

## By category

### Language & Framework
| Skill | Where it's used | What to say in interviews |
|-------|-----------------|---------------------------|
| Python 3.11 | everywhere | modern typing, `str | None`, `from __future__` |
| FastAPI | all services | async endpoints, dependency injection, OpenAPI |
| Pydantic v2 | schemas, settings | validation, `model_validate`, `ConfigDict` |
| async/await | services, DB, httpx | non-blocking I/O, event loop |

### Data
| Skill | Where | Talking point |
|-------|-------|---------------|
| SQLAlchemy 2.0 (async) | repositories | `AsyncSession`, `select()`, `mapped_column` |
| Alembic | migrations | versioned schema, async env.py |
| PostgreSQL | all data | relational modeling, indexing, ILIKE search |
| Pagination | search | offset/limit + total + total_pages |

### Auth & Security
| Skill | Where | Talking point |
|-------|-------|---------------|
| JWT | auth + verify everywhere | HS256, claims, expiry |
| bcrypt | auth | salted password hashing |
| Authorization | files | per-resource ownership checks |

### Cloud (AWS)
| Skill | Where | Talking point |
|-------|-------|---------------|
| S3 | files + processor | presigned URLs, event notifications |
| Lambda | processor | event-driven, scales to zero |
| RDS | prod DB | managed Postgres, db.t3.micro |
| ECS Fargate | prod deploy | serverless containers, no control-plane fee |
| ECR | images | private registry |
| IAM | all AWS | least-privilege roles/policies |
| SES | notifications (opt) | transactional email |
| EKS | optional demo | managed Kubernetes |

### DevOps
| Skill | Where | Talking point |
|-------|-------|---------------|
| Docker | every service | multi-stage builds, non-root, slim images |
| Docker Compose | local dev | multi-service, healthchecks, depends_on |
| LocalStack | local S3 | emulate AWS offline |
| Kubernetes | infra/k8s | Deployments, Services, Ingress, HPA, ConfigMaps, Secrets, probes |
| Terraform | infra/terraform | IaC, providers, for_each, outputs |
| GitHub Actions | CI/CD | matrix builds, ECR login, deploy step |

### Engineering practices
| Skill | Where | Talking point |
|-------|-------|---------------|
| Layered architecture | all services | separation of concerns |
| Testing | tests/ | pytest, async tests, fakes/mocks, SQLite |
| Linting/typing | pyproject | ruff, mypy |
| 12-factor config | config.py | env-based settings |
| Structured logging | shared logging | JSON logs for aggregation |
| Microservices patterns | whole system | decomposition, inter-service calls, CQRS-lite |
| Monorepo vs polyrepo | both repos | code organization trade-offs |

## Resume bullet examples

- Built a microservices file platform (FastAPI, PostgreSQL, S3, Lambda)
  deployed on Kubernetes and AWS ECS Fargate with Terraform and GitHub Actions.
- Designed direct-to-S3 uploads using presigned URLs and an event-driven
  Lambda pipeline for thumbnail/metadata processing.
- Implemented JWT authentication with cross-service verification and
  per-resource authorization.
- Authored CI/CD with matrixed test/build/deploy and cost-controlled IaC
  (destroy-after-demo, Fargate over EKS).
