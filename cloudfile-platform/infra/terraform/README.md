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
terraform init
terraform plan  -var="db_password=$(openssl rand -hex 16)"
terraform apply -var="db_password=..."

# ... test ...

terraform destroy -var="db_password=..."   # ALWAYS do this when finished
```

## Free-tier guidance

- Keep RDS at `db.t3.micro`, single-AZ.
- Avoid leaving NAT Gateway running; for a pure demo you can place ECS tasks in
  public subnets with `assign_public_ip = true` (as configured) to skip NAT.
- Delete the S3 bucket contents before destroy if versioning retains objects.
