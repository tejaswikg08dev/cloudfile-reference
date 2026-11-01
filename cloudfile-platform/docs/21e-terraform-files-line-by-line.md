# 21e — Our Terraform Files, Line by Line

A guided tour of every file in `infra/terraform/`. Terraform reads ALL `.tf`
files in the folder together (file names are just for humans), so splitting by
topic is purely for readability.

```
infra/terraform/
├── providers.tf     # which cloud + plugins + region
├── variables.tf     # inputs (password, region, counts)
├── vpc.tf           # the private network
├── ecr.tf           # image registries
├── iam.tf           # permission roles
├── rds.tf           # the database
├── s3.tf            # file storage + event trigger
├── lambda.tf        # the processor function
├── ecs_fargate.tf   # the running containers
├── eks.tf           # optional Kubernetes (off by default)
└── outputs.tf       # values printed after apply
```

---

## providers.tf — the foundation

```hcl
terraform {
  required_version = ">= 1.5.0"       # need Terraform 1.5+
  required_providers {
    aws     = { source = "hashicorp/aws",     version = "~> 5.0" }
    random  = { source = "hashicorp/random",  version = "~> 3.5" }
    archive = { source = "hashicorp/archive", version = "~> 2.4" }
  }
}
provider "aws" {
  region = var.aws_region
  default_tags { tags = { Project = "cloudfile", ManagedBy = "terraform" } }
}
```
- Declares the 3 plugins `init` will download.
- `default_tags` stamps every resource with tags — handy to find/clean up
  everything ("show me all Project=cloudfile resources").

---

## variables.tf — the inputs

```hcl
variable "aws_region"  { default = "us-east-1" }
variable "project_name"{ default = "cloudfile" }      # name prefix for resources
variable "db_name"     { default = "cloudfile_files" }
variable "db_username" { default = "cloudfile" }
variable "db_password" { type = string, sensitive = true }   # no default → must provide
variable "db_engine_version" { default = "15" }
variable "jwt_secret_key" { sensitive = true, default = "..." }
variable "enable_eks"  { default = false }            # keep EKS off (costs money)
variable "service_desired_count" { default = 0 }      # 0 first, then 1 (2-phase)
```
- `sensitive = true` hides the value in `plan`/`apply` output.
- `db_password` has **no default** on purpose — you MUST supply it
  (`export TF_VAR_db_password=...`), so no password is ever committed.
- `service_desired_count` is the trick that solves the ECR/ECS chicken-and-egg
  (see [21f](21f-how-resources-connect.md)).

---

## vpc.tf — the network

(Covered in detail in [21d](21d-networking-deep-dive.md).) In short:
- `aws_vpc.main` — the `10.0.0.0/16` private network.
- `aws_internet_gateway.main` — the door to the internet.
- `aws_subnet.public[0,1]` — two public subnets in two AZs.
- `aws_route_table.public` + associations — "internet traffic → IGW," applied to
  both subnets.

---

## ecr.tf — image registries

```hcl
locals { services = ["auth", "files", "search"] }

resource "aws_ecr_repository" "service" {
  for_each     = toset(local.services)       # make one per service
  name         = "${var.project_name}-${each.key}"   # cloudfile-auth, etc.
  force_delete = true                         # allow destroy even with images
  image_scanning_configuration { scan_on_push = true }
}
```
- `locals` defines the list of service names (reused across files).
- `for_each` creates 3 repositories from that list (`cloudfile-auth`,
  `cloudfile-files`, `cloudfile-search`).
- `force_delete = true` lets `terraform destroy` remove the repo even though it
  contains images (otherwise destroy would fail).

---

## iam.tf — permissions (the badges)

Three roles:

1. **Lambda role** — lets the processor run + read/write S3:
```hcl
resource "aws_iam_role" "lambda" { assume_role_policy = <lambda can assume this> }
resource "aws_iam_role_policy_attachment" "lambda_basic" {
  policy_arn = ".../AWSLambdaBasicExecutionRole"   # write logs
}
resource "aws_iam_role_policy" "lambda_s3" { ... s3:GetObject, s3:PutObject ... }
```

2. **ECS execution role** — lets ECS itself pull images + write logs:
```hcl
resource "aws_iam_role_policy_attachment" "ecs_execution" {
  policy_arn = ".../AmazonECSTaskExecutionRolePolicy"
}
```

3. **ECS task role** — what the app code is allowed to do (access S3):
```hcl
resource "aws_iam_role_policy" "ecs_task_s3" {
  # object actions on items in the bucket + bucket-level list/location
  actions = ["s3:GetObject","s3:PutObject","s3:DeleteObject", "s3:ListBucket", ...]
}
```

> **Execution role vs task role** (important):
> - *Execution role* = permissions for the ECS **platform** to start your
>   container (pull image, write logs). Used before your code runs.
> - *Task role* = permissions for **your running code** (boto3 calling S3).
> This separation is why the app needs no AWS keys — it inherits the task role.

---

## rds.tf — the database

```hcl
resource "aws_db_subnet_group" "main" {
  subnet_ids = aws_subnet.public[*].id    # DB spans both subnets (2 AZs required)
}
resource "aws_security_group" "rds" { ingress 5432 from ECS SG only }
resource "aws_db_instance" "main" {
  engine         = "postgres"
  engine_version = var.db_engine_version
  instance_class = "db.t3.micro"           # free-tier size
  allocated_storage = 20
  multi_az          = false                # single-AZ = free
  db_name  = var.db_name
  username = var.db_username
  password = var.db_password
  skip_final_snapshot     = true           # don't snapshot on destroy (faster/cheaper)
  deletion_protection     = false          # allow terraform destroy
  backup_retention_period = 0              # no backups (demo)
}
```
- `db.t3.micro` + single-AZ + 20 GB = free-tier shape.
- `skip_final_snapshot` + `deletion_protection = false` = clean, fast destroy.

---

## s3.tf — storage + event trigger

```hcl
resource "random_id" "bucket_suffix" { byte_length = 4 }   # random uniqueness
resource "aws_s3_bucket" "uploads" {
  bucket        = "cloudfile-uploads-${random_id.bucket_suffix.hex}"  # globally unique
  force_destroy = true                                     # destroy even if not empty
}
resource "aws_s3_bucket_public_access_block" "uploads" { ...block all public... }
resource "aws_s3_bucket_cors_configuration" "uploads" { allow GET/PUT from browsers }
resource "aws_s3_bucket_notification" "uploads" {
  lambda_function {
    lambda_function_arn = aws_lambda_function.processor.arn
    events              = ["s3:ObjectCreated:*"]   # when any object is created
    filter_prefix       = "uploads/"               # only under uploads/
  }
  depends_on = [aws_lambda_permission.allow_s3]
}
```
- Bucket names are **globally unique across all AWS** → the random suffix.
- `public_access_block` → the bucket is private; access only via presigned URLs.
- The `notification` wires S3 → Lambda: "when a file is created under
  `uploads/`, invoke the processor."

---

## lambda.tf — the processor function

```hcl
data "archive_file" "processor" {               # zip the code
  source_dir  = "${path.module}/../../services/processor"
  output_path = "${path.module}/processor.zip"
}
resource "aws_lambda_function" "processor" {
  handler = "handler.handler"                    # file.function to run
  runtime = "python3.11"
  filename = data.archive_file.processor.output_path
  environment { variables = { PROCESSOR_DATABASE_URL = "..." } }
}
resource "aws_lambda_permission" "allow_s3" {    # let S3 invoke this Lambda
  action        = "lambda:InvokeFunction"
  principal     = "s3.amazonaws.com"
  source_arn    = aws_s3_bucket.uploads.arn
}
```
- `archive_file` is a **data source** (not a resource) — it zips your Python code
  at plan time.
- `aws_lambda_permission` is required so S3 is *allowed* to trigger the Lambda.

---

## ecs_fargate.tf — the running containers

The biggest file. Three resource types, one per service via `for_each`:

```hcl
resource "aws_ecs_cluster" "main" { name = "cloudfile-cluster" }  # the "group"

resource "aws_ecs_task_definition" "service" {   # the blueprint (x3)
  for_each = toset(local.services)
  cpu = "256"  memory = "512"                     # valid Fargate combo
  execution_role_arn = aws_iam_role.ecs_execution.arn
  task_role_arn      = aws_iam_role.ecs_task.arn
  container_definitions = jsonencode([{
    image = "${aws_ecr_repository.service[each.key].repository_url}:latest"
    portMappings = [{ containerPort = local.service_ports[each.key] }]
    environment  = local.service_env[each.key]    # DB URL, JWT, S3 bucket...
    logConfiguration = { ... awslogs to CloudWatch ... }
  }])
}

resource "aws_ecs_service" "service" {            # keeps tasks running (x3)
  for_each        = toset(local.services)
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.service[each.key].arn
  desired_count   = var.service_desired_count     # 0 first apply, then 1
  launch_type     = "FARGATE"
  network_configuration {
    subnets          = aws_subnet.public[*].id
    security_groups  = [aws_security_group.ecs.id]
    assign_public_ip = true                        # so we can reach it (no NAT)
  }
}
```
- **cluster** = a logical group for your services.
- **task definition** = the recipe (image + CPU/mem + env + logging).
- **service** = runs & maintains `desired_count` copies of the task.
- `local.service_env` sets each service's DB URL, JWT secret, S3 bucket, etc.

---

## eks.tf — optional Kubernetes (off)

Everything here is wrapped in `count = var.enable_eks ? 1 : 0`, meaning: create
these resources only if `enable_eks = true`. Default is `false`, so **nothing**
in this file is created normally (EKS costs money). It's there if you ever want
a short EKS demo.

---

## outputs.tf — what prints after apply

```hcl
output "ecr_repository_urls" { value = {for k,r in aws_ecr_repository.service : k => r.repository_url} }
output "s3_bucket_name"      { value = aws_s3_bucket.uploads.bucket }
output "rds_endpoint"        { value = aws_db_instance.main.address }
output "ecs_cluster_name"    { value = aws_ecs_cluster.main.name }
```
After `apply`, `terraform output` prints these — the ECR URLs (to push images),
the bucket name, and the RDS endpoint.

Next: [21f — How resources connect →](21f-how-resources-connect.md)
