# Terraform — AWS Infrastructure

> ⚠️ COST WARNING
> Some resources here (NAT Gateway, EKS control plane, RDS) cost money and are
> NOT fully covered by the free tier. ALWAYS run `terraform destroy` when done.
> The cheap path (ECS Fargate + Lambda + S3 + RDS db.t3.micro) is the default.

## What this creates

- VPC with public + private subnets
- ECR repositories for the three services
- S3 bucket for uploads (triggers the processor Lambda)
- Lambda processor function
- RDS PostgreSQL (db.t3.micro — free-tier eligible)
- ECS Fargate cluster + services (cheap deployment path)
- Optional EKS cluster (commented by default; enable only for a short demo)

## Usage

```bash
cd infra/terraform
export TF_VAR_db_password="$(openssl rand -hex 16)"
export TF_VAR_jwt_secret_key="$(openssl rand -hex 32)"

terraform init
terraform apply                              # phase 1: infra + ECR, services at 0

# ... push images to ECR (see docs/19-aws-deploy-runbook.md Phase 2) ...

terraform apply -var="service_desired_count=1"   # phase 2: start the services

# ... test ...

terraform destroy                            # ALWAYS do this when finished
```

> Two-phase apply avoids a chicken-and-egg problem: ECS can't pull images that
> don't exist yet. First apply creates ECR with services at 0 tasks; after you
> push images, the second apply scales them to 1.
> Full baby-steps guide: `docs/19-aws-deploy-runbook.md`.

## Free-tier guidance

- Keep RDS at `db.t3.micro`, single-AZ.
- Avoid leaving NAT Gateway running; for a pure demo you can place ECS tasks in
  public subnets with `assign_public_ip = true` (as configured) to skip NAT.
- Delete the S3 bucket contents before destroy if versioning retains objects.
