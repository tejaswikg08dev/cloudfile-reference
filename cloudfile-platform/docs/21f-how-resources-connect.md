# 21f — How Resources Connect (the dependency graph)

Terraform figures out the **order** to build things automatically. You never say
"build the VPC first." Here's how it knows.

---

## Implicit dependencies (the magic of references)

Whenever one resource **references** another, Terraform learns a dependency.

Example from `rds.tf`:
```hcl
resource "aws_db_instance" "main" {
  db_subnet_group_name   = aws_db_subnet_group.main.name   # ← depends on subnet group
  vpc_security_group_ids = [aws_security_group.rds.id]     # ← depends on RDS SG
}
```
Because the DB mentions `aws_db_subnet_group.main` and `aws_security_group.rds`,
Terraform knows: **create the subnet group and the SG BEFORE the database.**

It does this for everything, building a **dependency graph**, then creates
resources in the correct order (and in parallel where there's no dependency).

---

## The full dependency graph (our project)

```
                         aws_vpc.main
                        /     |      \
         aws_internet_gateway  aws_subnet.public[0,1]
                  |                 |           \
         aws_route_table.public     |            aws_db_subnet_group.main
                  |                 |                     |
         route_table_association    |                     |
                                     |                     |
            aws_security_group.ecs ──┼──────────────┐      |
                     ▲               |              ▼      ▼
                     │               |   aws_security_group.rds
                     │               |              |
                     │               |              ▼
                     │               |     aws_db_instance.main (RDS)
                     │               |              │
   aws_ecr_repository.service[*]     |              │
                     │               |              │
   aws_iam_role.ecs_execution        |              │
   aws_iam_role.ecs_task ────────────┤              │
                     │               ▼              │
                     └──▶ aws_ecs_task_definition ◀──┘ (needs image URL + env w/ RDS endpoint)
                                     │
                                     ▼
                            aws_ecs_service (needs cluster + task def + subnets + SG)

   aws_s3_bucket.uploads ──▶ aws_lambda_function.processor ──▶ aws_lambda_permission.allow_s3
            ▲                          ▲                                  │
            └────── aws_s3_bucket_notification ◀───────────────────────-─┘
```

Reading it:
- **VPC** is the root — almost everything needs it.
- **Subnets** need the VPC; **route table** needs the IGW; **DB subnet group**
  needs the subnets.
- **RDS SG** needs the **ECS SG** (it references it to allow traffic from it).
- **RDS** needs its subnet group + SG.
- **ECS task definition** needs: the **ECR repo URL** (for the image) + the **IAM
  roles** + the **RDS endpoint** (baked into the DB URL env var).
- **ECS service** needs the cluster + task definition + subnets + ECS SG.
- **S3 → Lambda → permission → notification** form their own little chain.

Terraform computes all this from the references and builds bottom-up.

---

## Why the task definition depends on RDS

Look at `ecs_fargate.tf`:
```hcl
environment = [
  { name = "FILES_DATABASE_URL",
    value = "postgresql+asyncpg://.../@${aws_db_instance.main.address}:5432/..." }
]
```
The DB URL embeds `aws_db_instance.main.address` (the RDS endpoint). Terraform
can't write that env var until RDS exists and its address is known — so it
creates **RDS before the ECS task definition**. That's why apply spends several
minutes on RDS before ECS appears.

---

## The chicken-and-egg problem (and our fix)

Here's a dependency Terraform CANNOT solve on its own:

- The **ECS service** wants to run a task using the image
  `cloudfile-auth:latest` from ECR.
- But on the **first** apply, **no image has been pushed yet** — the ECR repo
  exists but is empty.
- If `desired_count = 1`, ECS immediately tries to pull a non-existent image →
  the task fails → ECS retries forever (`CannotPullContainerError`).

This is a **runtime** ordering problem (build image → then run it) that
Terraform's graph doesn't cover, because pushing images is a separate step you
do with Docker, not Terraform.

### Our fix: the `service_desired_count` variable

```hcl
desired_count = var.service_desired_count   # default 0
```

- **First apply** (`service_desired_count = 0`): creates ECR + everything, but
  the ECS services run **0 tasks** — nothing tries to pull a missing image.
- **You push images** to ECR with Docker.
- **Second apply** (`-var="service_desired_count=1"`): now scales to 1 task per
  service, which pulls the (now-existing) images and starts cleanly.

> This is a very common real-world pattern: create the registry, push images,
> then start the workloads.

---

## `depends_on` — the manual override

Usually references are enough. Occasionally there's a dependency with no
reference between the resources. Then you state it explicitly. Example in `s3.tf`:
```hcl
resource "aws_s3_bucket_notification" "uploads" {
  depends_on = [aws_lambda_permission.allow_s3]
}
```
The notification doesn't *reference* the permission, but S3 must be *allowed* to
invoke the Lambda before the notification is wired — so we force the order with
`depends_on`.

---

## How `for_each` creates multiple connected resources

```hcl
locals { services = ["auth", "files", "search"] }

resource "aws_ecr_repository" "service" {
  for_each = toset(local.services)      # 3 repos
}
resource "aws_ecs_task_definition" "service" {
  for_each = toset(local.services)      # 3 task defs
  image    = aws_ecr_repository.service[each.key].repository_url  # each links to its repo
}
```
`for_each` makes a set of resources keyed by name. `aws_ecr_repository.service["auth"]`
is the auth repo; the auth task definition references exactly that one. Terraform
tracks each pairing as its own dependency.

---

## Mental model summary

> You never order anything manually. You just **reference** resources by their
> attributes (`.id`, `.arn`, `.address`). Each reference is a dependency.
> Terraform turns all references into a graph and builds in the right order,
> in parallel where safe. The ONE thing it can't know — "push images before
> running them" — we handle with the 2-phase `service_desired_count`.

Next: [21g — Inside each runbook phase →](21g-inside-each-phase.md)
