# 21b — What is Terraform & How It Thinks

---

## The core idea: "desired state"

Most tools are **imperative**: you give step-by-step commands ("create this,
then that"). Terraform is **declarative**: you describe the **end result you
want**, and Terraform figures out the steps to get there.

> Analogy: Imperative = giving turn-by-turn driving directions. Declarative =
> telling a GPS your destination and letting it compute the route. If you move
> the destination slightly, the GPS recomputes only what changed.

You write files like "I want a VPC, a database, and 3 container services."
Terraform compares that to what currently exists and makes AWS match it.

---

## The three commands you'll use

```
terraform init      # set up (download the AWS plugin)      — once per project
terraform plan      # preview: what WILL change             — read before apply
terraform apply     # make AWS match your files             — creates/updates
terraform destroy   # remove everything your files created  — cleanup
```

---

## How Terraform works internally (the cycle)

Every `plan`/`apply` does this:

```
   ┌─────────────┐     ┌──────────────┐     ┌─────────────┐
   │ 1. READ     │     │ 2. COMPARE   │     │ 3. ACT      │
   │ your .tf    │ --> │ desired vs.  │ --> │ call AWS    │
   │ files       │     │ the state    │     │ APIs to fix │
   │ (desired)   │     │ file (actual)│     │ the diff    │
   └─────────────┘     └──────────────┘     └─────────────┘
```

1. **Read** — parse all `.tf` files to learn the desired state.
2. **Compare** — look at the **state file** (what Terraform believes exists) and
   optionally refresh it against real AWS. Compute the difference.
3. **Act** — call AWS APIs to create/update/delete so reality matches desired.

On the FIRST apply, the state is empty → everything is "to add" → it creates
everything. On a SECOND apply with one change → only that one thing changes.

---

## The state file (`terraform.tfstate`)

This is Terraform's **memory**. After it creates a resource, it records the
resource's real AWS ID in `terraform.tfstate` (a JSON file in your terraform
folder).

Why it matters:
- It's how Terraform knows "I already created the VPC with id `vpc-123`" so next
  time it doesn't create a duplicate.
- It's how `destroy` knows exactly what to delete.

> Rule: never hand-edit or delete the state file. If you lose it, Terraform
> forgets what it made (and can't clean it up automatically).

> In a team you'd store state remotely (e.g. in an S3 bucket) so everyone shares
> it. For our solo demo, the local file is fine.

---

## Providers (how Terraform talks to AWS)

Terraform itself knows nothing about AWS. A **provider** is a plugin that
translates Terraform's instructions into AWS API calls.

From our `providers.tf`:
```hcl
terraform {
  required_providers {
    aws     = { source = "hashicorp/aws",     version = "~> 5.0" }
    random  = { source = "hashicorp/random",  version = "~> 3.5" }
    archive = { source = "hashicorp/archive", version = "~> 2.4" }
  }
}

provider "aws" {
  region = var.aws_region       # which region to build in
}
```

- `aws` provider → creates VPC, RDS, S3, ECS, etc.
- `random` provider → generates a random suffix for the S3 bucket name (bucket
  names must be globally unique).
- `archive` provider → zips the Lambda code.

`terraform init` is what downloads these plugins.

---

## The language: HCL

Terraform files are written in **HCL (HashiCorp Configuration Language)**. The
two things you'll see most:

**Resource** — "create this thing":
```hcl
resource "aws_s3_bucket" "uploads" {
  bucket = "cloudfile-uploads-abcd"
}
```
- `aws_s3_bucket` = the type (an S3 bucket)
- `uploads` = a local nickname you choose (to refer to it elsewhere)
- the `{ }` = its settings

**Variable** — "an input you can change":
```hcl
variable "aws_region" {
  default = "us-east-1"
}
```
Used elsewhere as `var.aws_region`.

**Referencing** — how resources connect (this is the magic):
```hcl
# RDS security group allows traffic FROM the ECS security group:
security_groups = [aws_security_group.ecs.id]
```
By writing `aws_security_group.ecs.id`, Terraform learns "RDS depends on the
ECS security group" and automatically creates the ECS SG first. (More on this
in [21f](21f-how-resources-connect.md).)

---

## Variables, outputs, locals (quick)

- **variable** = input (you can override with `-var` or `TF_VAR_...` env vars).
  Our `db_password` is a variable so it's never hard-coded.
- **output** = a value printed after apply (e.g. the RDS endpoint, ECR URLs).
- **local** = a computed helper value reused in the file (e.g. our list of
  service names `["auth","files","search"]`).

---

## Why Terraform is great for our "deploy then destroy" goal

- **One command up, one command down.** `apply` builds ~25 resources;
  `destroy` removes all ~25. No clicking, nothing forgotten.
- **Safe preview.** `plan` shows exactly what will happen before it happens.
- **Repeatable.** Delete everything, run `apply`, get an identical environment.

---

## Check your understanding

- *Q: Declarative vs imperative?* → You describe the result; Terraform finds the
  steps.
- *Q: What's the state file for?* → Terraform's memory of what it created; powers
  updates and clean destroy.
- *Q: What's a provider?* → The plugin that turns Terraform instructions into
  AWS API calls.
- *Q: What does `init` do?* → Downloads the providers/plugins.

Next: [21c — The AWS building blocks we use →](21c-aws-building-blocks.md)
