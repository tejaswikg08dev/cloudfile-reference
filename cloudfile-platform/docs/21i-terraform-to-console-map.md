# 21i — Terraform Block → AWS Console Map

Connect the code to reality. After `terraform apply`, open the AWS Console
(https://console.aws.amazon.com, region = **N. Virginia / us-east-1** top-right)
and find each thing your Terraform created.

> Tip: use the search bar at the top of the Console to jump to any service.

---

## The mapping table

| Terraform block | Console service → where to look | What you'll see |
|-----------------|--------------------------------|-----------------|
| `aws_vpc.main` | **VPC** → Your VPCs | `cloudfile-vpc`, CIDR 10.0.0.0/16 |
| `aws_subnet.public[*]` | **VPC** → Subnets | `cloudfile-public-0`, `-1` in 2 AZs |
| `aws_internet_gateway.main` | **VPC** → Internet gateways | `cloudfile-igw`, attached to the VPC |
| `aws_route_table.public` | **VPC** → Route tables | route `0.0.0.0/0 → igw` |
| `aws_security_group.ecs` | **VPC** → Security groups | inbound 8001–8003 from 0.0.0.0/0 |
| `aws_security_group.rds` | **VPC** → Security groups | inbound 5432 from the ECS SG |
| `aws_ecr_repository.service[*]` | **ECR** → Repositories | `cloudfile-auth/files/search` + image tags |
| `aws_iam_role.ecs_execution` | **IAM** → Roles | `cloudfile-ecs-execution` |
| `aws_iam_role.ecs_task` | **IAM** → Roles | `cloudfile-ecs-task` (has the S3 policy) |
| `aws_iam_role.lambda` | **IAM** → Roles | `cloudfile-lambda-role` |
| `aws_db_instance.main` | **RDS** → Databases | `cloudfile-db`, engine Postgres, t3.micro |
| `aws_db_subnet_group.main` | **RDS** → Subnet groups | `cloudfile-db-subnets` |
| `aws_s3_bucket.uploads` | **S3** → Buckets | `cloudfile-uploads-xxxx` |
| `aws_s3_bucket_notification` | **S3** → bucket → Properties → Event notifications | the Lambda trigger on ObjectCreated |
| `aws_lambda_function.processor` | **Lambda** → Functions | `cloudfile-processor` |
| `aws_lambda_permission.allow_s3` | **Lambda** → function → Configuration → Permissions | S3 allowed to invoke |
| `aws_ecs_cluster.main` | **ECS** → Clusters | `cloudfile-cluster` |
| `aws_ecs_task_definition.service[*]` | **ECS** → Task definitions | `cloudfile-auth/files/search` |
| `aws_ecs_service.service[*]` | **ECS** → cluster → Services | 3 services, running count |
| `aws_cloudwatch_log_group.services[*]` | **CloudWatch** → Log groups | `/ecs/cloudfile-auth` etc. |

---

## A guided 10-minute console tour (do this while deployed)

### 1. See your network — VPC
- Console → **VPC** → **Your VPCs** → click `cloudfile-vpc`.
- Left menu → **Subnets** → filter by the VPC → see 2 public subnets in 2 AZs.
- **Internet gateways** → `cloudfile-igw` (state: Attached).
- **Security groups** → open the RDS one → Inbound rules → notice the source is
  the ECS security group (not an IP range). That's the "allow from the app only."

### 2. See your images — ECR
- Console → **ECR** → **Repositories** → `cloudfile-files` → see the `latest`
  image tag and its push time. (Empty before Phase 2, populated after.)

### 3. See your running app — ECS
- Console → **ECS** → **Clusters** → `cloudfile-cluster`.
- **Services** tab → 3 services; each shows Desired=1, Running=1 after Phase 3.
- Click `cloudfile-files` → **Tasks** → click the task → see:
  - its **public IP** (what you curl),
  - **Configuration** → the image + env vars,
  - **Logs** tab → live CloudWatch logs.

### 4. See your database — RDS
- Console → **RDS** → **Databases** → `cloudfile-db`.
- Status: Available. Note the **Endpoint** (matches `terraform output rds_endpoint`).
- Connectivity & security → the VPC + the RDS security group.

### 5. See your storage — S3
- Console → **S3** → `cloudfile-uploads-xxxx`.
- After you upload a file: open `uploads/` → see your object.
- **Properties** tab → **Event notifications** → the Lambda trigger.

### 6. See the processor — Lambda
- Console → **Lambda** → **Functions** → `cloudfile-processor`.
- **Monitor** tab → invocations spike when you upload a file.
- **Configuration → Triggers** → the S3 bucket trigger.

### 7. See the permissions — IAM
- Console → **IAM** → **Roles** → `cloudfile-ecs-task`.
- **Permissions** → the inline S3 policy (Get/Put/Delete/List on your bucket).
- This is the "badge" the files container wears to access S3.

### 8. See the logs — CloudWatch
- Console → **CloudWatch** → **Log groups** → `/ecs/cloudfile-files`.
- Click the latest log stream → your service's JSON logs (startup, requests).

---

## Reading tags to find everything

Every resource is tagged `Project=cloudfile` (from `default_tags` in
`providers.tf`). Use **Resource Groups & Tag Editor** → search tag
`Project = cloudfile` to list EVERYTHING in one view — great for confirming
`destroy` removed it all.

---

## After destroy — confirm it's gone

Revisit:
- ECS → Clusters → (no cloudfile-cluster)
- RDS → Databases → (no cloudfile-db)
- S3 → Buckets → (no cloudfile-uploads-xxxx)
- VPC → Your VPCs → (no cloudfile-vpc)

Plus **Billing → Free Tier** the next day to confirm near-zero usage.

Next: [21j — In-depth production testing →](21j-production-testing-indepth.md)
