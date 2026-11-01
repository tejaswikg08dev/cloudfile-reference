# 21 — Terraform & AWS Deep Dive (zero to understanding)

A mini-course that explains **exactly how** your AWS deployment works — every
term from scratch, using YOUR actual project files. No prior AWS or Terraform
knowledge assumed.

Read the parts in order. Each builds on the previous one.

| Part | Title | You'll understand |
|------|-------|-------------------|
| [21a](21a-cloud-and-aws-basics.md) | Cloud & AWS basics from zero | What the cloud/AWS/regions/free-tier actually are |
| [21b](21b-what-is-terraform.md) | What is Terraform & how it thinks | Desired state, plan/apply/destroy, the state file |
| [21c](21c-aws-building-blocks.md) | The AWS building blocks we use | VPC, ECR, ECS, RDS, S3, Lambda, IAM — in plain English |
| [21d](21d-networking-deep-dive.md) | Networking deep dive | How traffic flows; subnets, gateways, firewalls |
| [21e](21e-terraform-files-line-by-line.md) | Our Terraform files, line by line | What every `.tf` file in the project does |
| [21f](21f-how-resources-connect.md) | How resources connect | The dependency graph + the 2-phase apply |
| [21g](21g-inside-each-phase.md) | Inside each runbook phase | What `init/plan/apply/destroy` do under the hood |
| [21h](21h-request-journey.md) | A request's journey through live AWS | Trace an upload end-to-end across AWS |
| [21i](21i-terraform-to-console-map.md) | Terraform → AWS Console map | Find each resource in the console |
| [21j](21j-production-testing-indepth.md) | In-depth production testing | Verify everything works, including internals |
| [21k](21k-decisions-cost-security-interview.md) | Decisions, cost, security, interview | Why each choice + how to explain it |

---

## How to use this

1. If you're brand new: read **21a → 21b → 21c → 21d** first (the foundations).
2. Then **21e → 21f → 21g** to understand the actual files and what happens.
3. Then **21h → 21i** to see it running and find things in the console.
4. Then **21j → 21k** to test deeply and prepare to explain it.

There's also an **interactive animated page** that shows Terraform building AWS
and a request flowing through it:
`visual-docs/12-aws-deploy-internals.html` (open in a browser).

---

## One-screen glossary (skim now, revisit anytime)

| Term | One-line meaning (analogy) |
|------|----------------------------|
| **Cloud** | Renting computers/storage over the internet instead of owning them |
| **AWS** | Amazon's cloud — a city of rentable utilities (compute, storage, DB...) |
| **Region** | A geographic cluster of AWS data centers (e.g. `us-east-1` = N. Virginia) |
| **AZ (Availability Zone)** | One data center within a region; regions have several |
| **Terraform** | A tool where you describe infrastructure in files; it builds it for you |
| **Provider** | Terraform's plugin that talks to a specific cloud (we use the AWS provider) |
| **State file** | Terraform's memory of what it created (`terraform.tfstate`) |
| **Resource** | One thing Terraform manages (a database, a bucket, a role...) |
| **VPC** | Your own private network inside AWS (your plot of land) |
| **Subnet** | A fenced section of your VPC (a floor in your building) |
| **Internet Gateway (IGW)** | The door between your VPC and the internet |
| **Security Group (SG)** | A firewall around a resource (a door lock with rules) |
| **ECR** | Elastic Container Registry — storage for your Docker images |
| **ECS** | Elastic Container Service — runs your containers |
| **Fargate** | "Serverless" mode for ECS — AWS runs the containers, you don't manage servers |
| **Task / Task Definition** | A running container / its blueprint |
| **RDS** | Relational Database Service — managed PostgreSQL |
| **S3** | Simple Storage Service — file/object storage |
| **Lambda** | Run a function on-demand without a server |
| **IAM** | Identity & Access Management — who is allowed to do what |
| **Role** | An identity a service assumes to get permissions (an ID badge) |
| **ARN** | Amazon Resource Name — a unique ID for any AWS thing |
| **CloudWatch** | AWS's logging + monitoring service |

Start with [21a →](21a-cloud-and-aws-basics.md)
