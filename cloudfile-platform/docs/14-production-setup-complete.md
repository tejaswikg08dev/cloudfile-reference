# 14 — Complete Production Setup (AWS, step by step)

A full teaching walkthrough for deploying to AWS with Terraform + ECS Fargate,
then verifying, then destroying. Free-tier-first.

> 💸 **Cost rule:** run `terraform destroy` as soon as you finish testing. RDS,
> ECS tasks, and (if enabled) EKS accrue cost. This guide avoids NAT Gateway
> and uses `db.t3.micro` to stay cheap.

---

## 0. Prerequisites

| Tool | Check |
|------|-------|
| AWS account (2026 free plan is fine) | — |
| AWS CLI | `aws --version` |
| Terraform ≥ 1.5 | `terraform --version` |
| Docker (running) | `docker --version` |

Configure credentials:
```bash
aws configure            # access key, secret, region = us-east-1
aws sts get-caller-identity    # should print your account id
```

---

## 1. Understand what gets created

Terraform (`infra/terraform/`) provisions:
- VPC with two public subnets (no NAT Gateway → cheaper)
- 3 ECR repositories (auth, files, search images)
- S3 bucket (+ event notification that triggers the processor Lambda)
- processor Lambda
- RDS PostgreSQL (`db.t3.micro`, one database `cloudfile_files`)
- ECS Fargate cluster + one service per app
- IAM roles

> All services share the single RDS database. Table names (`users`, `files`)
> don't collide, so one database is enough and avoids multi-DB provisioning.

---

## 2. Provision the infrastructure

```bash
cd cloudfile-platform/infra/terraform
terraform init

# Secrets passed as variables (never hard-code):
export TF_VAR_db_password=$(openssl rand -hex 16)
export TF_VAR_jwt_secret_key=$(openssl rand -hex 32)

terraform plan        # review what will be created
terraform apply       # type "yes"
```

When it finishes, capture outputs:
```bash
terraform output
# ecr_repository_urls = { auth = "...", files = "...", search = "..." }
# s3_bucket_name      = "cloudfile-uploads-xxxx"
# rds_endpoint        = "cloudfile-db.xxxx.us-east-1.rds.amazonaws.com"
# ecs_cluster_name    = "cloudfile-cluster"
```

---

## 3. Build and push images to ECR

```bash
cd cloudfile-platform          # back to repo root
ACCOUNT=$(aws sts get-caller-identity --query Account --output text)
REGION=us-east-1

# Authenticate Docker to ECR
aws ecr get-login-password --region $REGION | \
  docker login --username AWS --password-stdin $ACCOUNT.dkr.ecr.$REGION.amazonaws.com

# Build + push each service (build context is the repo root so `shared/` is included)
for s in auth files search; do
  IMG=$ACCOUNT.dkr.ecr.$REGION.amazonaws.com/cloudfile-$s:latest
  docker build -t $IMG -f services/$s/Dockerfile .
  docker push $IMG
done
```

---

## 4. Roll the ECS services to pick up the images

```bash
REGION=us-east-1
for s in auth files search; do
  aws ecs update-service --cluster cloudfile-cluster \
    --service cloudfile-$s --force-new-deployment --region $REGION
done
```

Watch them become healthy:
```bash
aws ecs describe-services --cluster cloudfile-cluster \
  --services cloudfile-auth cloudfile-files cloudfile-search \
  --query 'services[].{name:serviceName,running:runningCount,desired:desiredCount}'
```
You want `running == desired` for each.

---

## 5. Find a service's public address and test

```bash
# List tasks for auth
TASK=$(aws ecs list-tasks --cluster cloudfile-cluster \
  --service-name cloudfile-auth --query 'taskArns[0]' --output text)

# Get the ENI, then its public IP
ENI=$(aws ecs describe-tasks --cluster cloudfile-cluster --tasks $TASK \
  --query 'tasks[0].attachments[0].details[?name==`networkInterfaceId`].value' --output text)
IP=$(aws ec2 describe-network-interfaces --network-interface-ids $ENI \
  --query 'NetworkInterfaces[0].Association.PublicIp' --output text)
echo "auth is at http://$IP:8001"

curl http://$IP:8001/health      # {"status":"ok","service":"auth"}
```

Repeat for files (8002) and search (8003) by listing their tasks.

> In a real setup you'd put an Application Load Balancer in front and use one
> DNS name. For a learning demo, hitting task public IPs is fine.

---

## 6. Database schema on AWS

The services run with `DB_AUTO_CREATE=true` by default, so on first start each
service creates its tables (idempotent + advisory-locked). For a production-grade
setup, switch to migrations:

```bash
# Set DB_AUTO_CREATE=false in the ECS task env, then run migrations once from a
# machine that can reach RDS (bastion or temporarily public), pointing the env
# vars at the RDS endpoint:
export AUTH_DATABASE_URL="postgresql+asyncpg://cloudfile:${TF_VAR_db_password}@<rds-endpoint>:5432/cloudfile_files"
cd services/auth  && alembic upgrade head
export FILES_DATABASE_URL="postgresql+asyncpg://cloudfile:${TF_VAR_db_password}@<rds-endpoint>:5432/cloudfile_files"
cd ../files       && alembic upgrade head
```

---

## 7. CI/CD does steps 3–4 automatically

Once ECR + ECS exist, pushing to `main` triggers `.github/workflows/cd.yml`:
build → push to ECR → force ECS redeploy. Set repo secrets:
`AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_REGION`.

---

## 8. Known limitations (be honest in interviews)

- **Processor Lambda deps:** the zip contains only source. Pillow/psycopg2 are
  not bundled, so thumbnails + DB updates are skipped unless you add a Lambda
  layer (documented in `services/processor/README.md`). The handler degrades
  gracefully — it never crashes.
- **Lambda ↔ RDS networking:** the Lambda isn't VPC-attached, so it can't reach
  RDS by default. Add VPC config + an SG rule to enable DB updates from Lambda.
- **No load balancer:** demo hits task IPs directly. Add an ALB for production.
- **One shared RDS database:** fine here (unique table names); split per service
  with an event bus for a stricter microservices setup.

---

## 9. DESTROY everything (do not skip)

```bash
cd cloudfile-platform/infra/terraform
terraform destroy       # type "yes"
```
Then confirm in the AWS console that RDS, ECS, ECR, S3, and the Lambda are gone.
Leaving RDS running is the most common surprise charge.

---

## 10. Kubernetes alternative (minikube, free)

If you want the Kubernetes experience without AWS cost, use minikube locally —
see [10-cloud-deployment.md](10-cloud-deployment.md) (Track 1). You deploy the
same images with the manifests in `infra/k8s/` (platform) and the
`notification-service/infra/k8s/` manifests (including its `postgres.yaml`).
