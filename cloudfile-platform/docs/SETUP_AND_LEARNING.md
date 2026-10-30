# Setup, 7-Day Plan, and Interview Prep

This guide walks you from zero to a deployed system, and maps each step to the
skills you are learning. It covers BOTH repositories:

- `cloudfile-platform/` (this repo, monorepo: auth, files, search, processor)
- `notification-service/` (separate repo)

---

## 0. Prerequisites to install (on your personal machine)

| Tool | Why | Link |
|------|-----|------|
| Python 3.11+ | run/test services | https://www.python.org/downloads/ |
| Docker Desktop | build + run containers | https://www.docker.com/products/docker-desktop/ |
| Git | version control, CI/CD | https://git-scm.com/downloads |
| minikube | local Kubernetes (free) | https://minikube.sigs.k8s.io/docs/start/ |
| kubectl | talk to Kubernetes | https://kubernetes.io/docs/tasks/tools/ |
| Terraform | AWS infrastructure | https://developer.hashicorp.com/terraform/downloads |
| AWS CLI | AWS auth + commands | https://aws.amazon.com/cli/ |

On Windows, install Python with "Add Python to PATH" checked. Restart your
terminal after installing.

---

## 1. Verify locally (do this first)

```bash
# In cloudfile-platform/
cp .env.example .env

# Option A: run the test suites (needs Python)
python -m venv .venv && . .venv/Scripts/activate   # Windows
# or: source .venv/bin/activate                     # macOS/Linux
pip install -r services/auth/requirements-dev.txt
cd services/auth && PYTHONPATH=.:../.. pytest && cd ../..
pip install -r services/files/requirements-dev.txt
cd services/files && PYTHONPATH=.:../.. pytest && cd ../..
pip install -r services/search/requirements-dev.txt
cd services/search && PYTHONPATH=.:../.. pytest && cd ../..

# Option B: run the whole stack (needs Docker)
docker compose up --build
# auth   http://localhost:8001/docs
# files  http://localhost:8002/docs
# search http://localhost:8003/docs
```

For the notification service (separate repo):

```bash
# In notification-service/
cp .env.example .env
pip install -r requirements-dev.txt
pytest
docker compose up --build   # http://localhost:8004/docs
```

---

## 2. End-to-end manual test

1. Register: `POST http://localhost:8001/api/v1/auth/register`
   `{"email":"me@example.com","password":"password123","full_name":"Me"}`
2. Login: `POST http://localhost:8001/api/v1/auth/login` → copy `access_token`
3. Initiate upload: `POST http://localhost:8002/api/v1/files/upload` with
   `Authorization: Bearer <token>` and a JSON body describing the file.
4. PUT the file bytes to the returned `upload_url`.
5. Confirm: `POST http://localhost:8002/api/v1/files/confirm` `{"file_id":"..."}`
   (this triggers a notification if the notification service is running).
6. Search: `GET http://localhost:8003/api/v1/search?name=...`.

---

## 3. 7-Day Plan (3 hrs/day)

| Day | Focus | What to do | Skills |
|-----|-------|-----------|--------|
| 1 | FastAPI + auth | Read + run auth; understand router→service→repo | Python, FastAPI, JWT, SQLAlchemy |
| 2 | Files + S3 | Run files with LocalStack; do the upload flow | boto3, S3 presigned URLs, async |
| 3 | Search + Lambda | Run search; read the processor Lambda | pagination, serverless, events |
| 4 | Wire it together | Run both repos; watch a notification fire | inter-service HTTP, polyrepo |
| 5 | Kubernetes | Deploy to minikube (infra/k8s) | Deployments, Services, Ingress, HPA |
| 6 | CI/CD | Push to GitHub; watch Actions run tests | GitHub Actions, Docker build |
| 7 | AWS + destroy | `terraform apply`, test, `terraform destroy` | Terraform, ECS/ECR/RDS/Lambda, cost control |

---

## 4. Deploy to Kubernetes (minikube, free)

See `infra/k8s/README.md`. Summary:

```bash
minikube start --cpus=4 --memory=6g
minikube addons enable ingress metrics-server
eval $(minikube docker-env)
docker build -t cloudfile-auth:latest   -f services/auth/Dockerfile   .
docker build -t cloudfile-files:latest  -f services/files/Dockerfile  .
docker build -t cloudfile-search:latest -f services/search/Dockerfile .
kubectl apply -f infra/k8s/namespace.yaml
kubectl apply -f infra/k8s/configmap.yaml
cp infra/k8s/secrets.example.yaml infra/k8s/secrets.yaml && kubectl apply -f infra/k8s/secrets.yaml
kubectl apply -f infra/k8s/postgres.yaml
kubectl apply -f infra/k8s/auth.yaml -f infra/k8s/files.yaml -f infra/k8s/search.yaml
kubectl apply -f infra/k8s/ingress.yaml -f infra/k8s/hpa.yaml
```

---

## 5. Deploy to AWS (free-tier-first) — then DESTROY

See `infra/terraform/README.md`.

```bash
cd infra/terraform
terraform init
export TF_VAR_db_password=$(openssl rand -hex 16)
terraform apply
# Build + push images to the ECR repos shown in outputs, then the ECS services
# pick them up. Test. THEN:
terraform destroy
```

> Always destroy when done. Leaving RDS/NAT/EKS running will consume credits.

---

## 6. Interview talking points

- **Why microservices?** Independent deploy/scale; bounded contexts; failure
  isolation (notification can be down without breaking uploads).
- **Monorepo vs polyrepo?** Monorepo for shared code + unified CI; polyrepo for
  an independently-owned service. It's a code-management choice, not an
  architecture one — the runtime is identical.
- **Why presigned URLs?** Clients upload straight to S3; services stay
  stateless and don't proxy large payloads.
- **How do services authenticate each other?** Shared-secret JWT, forwarded on
  inter-service calls.
- **How do you scale?** Stateless services + HPA on CPU; S3 and Lambda scale
  on their own; RDS read replicas if needed.
- **How do you control cost?** Fargate over EKS for the cheap path; destroy
  infra after testing; `db.t3.micro`; avoid NAT Gateway by using public
  subnets for the demo.
- **What would you improve for real production?** Separate DBs per service with
  an event bus (SNS/SQS) for the read model; secrets in AWS Secrets Manager;
  per-service observability (traces/metrics); blue-green deploys.

---

## 7. Skills checklist (for your resume)

Backend: FastAPI, async Python, Pydantic, SQLAlchemy 2.0, Alembic, JWT auth,
layered architecture, structured logging, testing with pytest.

Cloud: S3 (presigned URLs), Lambda (event-driven), RDS, ECS Fargate, ECR, IAM,
(optional) EKS, SES.

DevOps: Docker multi-stage builds, Docker Compose, LocalStack, Kubernetes
(Deployments/Services/Ingress/HPA/ConfigMaps/Secrets), Terraform, GitHub
Actions CI/CD, cost management.
