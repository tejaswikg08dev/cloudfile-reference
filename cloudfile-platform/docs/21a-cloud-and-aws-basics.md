# 21a — Cloud & AWS Basics (from zero)

Before any Terraform, let's understand the ground we're standing on.

---

## What is "the cloud"?

Normally, to run a website or app, you'd buy physical computers (servers), put
them in a room, power them, cool them, fix them when they break. Expensive and
slow.

**The cloud** means: instead of owning computers, you **rent** them from a
company over the internet. You pay only for what you use, turn them on/off in
minutes, and someone else handles the hardware.

> Analogy: Owning servers = buying a car (big upfront cost, you maintain it).
> The cloud = Uber (pay per ride, no maintenance, scale up anytime).

---

## What is AWS?

**AWS (Amazon Web Services)** is Amazon's cloud. It's not one product — it's
~200 separate **services**, each doing one job:
- need to run code? → EC2 or ECS or Lambda
- need to store files? → S3
- need a database? → RDS
- need permissions? → IAM

> Analogy: AWS is a **city of utilities you can rent**. Need water? Turn on the
> water service. Need electricity? Turn on the power service. You only pay for
> what you switch on, and you can switch it off anytime.

Our project uses about 8 of these services together to run CloudFile.

---

## Regions and Availability Zones

AWS has data centers all over the world, grouped into **Regions**.

- **Region** = a geographic area, e.g. `us-east-1` (Northern Virginia, USA),
  `ap-south-1` (Mumbai, India). You pick one; your stuff lives there.
- **Availability Zone (AZ)** = one physical data center inside a region. Each
  region has several AZs (e.g. `us-east-1a`, `us-east-1b`). Having multiple AZs
  lets you survive one data center failing.

> Analogy: Region = a city. AZ = a specific building in that city. If one
> building loses power, another in the same city keeps running.

Our project uses **`us-east-1`** and spreads the database subnets across **2
AZs** (AWS requires at least 2 for a database).

> Why us-east-1? It's the cheapest and has every service. For a demo it's ideal.

---

## How you pay (and the free tier)

AWS charges per-use: per hour a server runs, per GB stored, per million
requests, etc. Tiny amounts individually, but they add up if you leave things
running.

**Free tier** (for newer accounts, like yours in 2026):
- You got ~$100 in credits, valid for a few months.
- Some services have an "always free" allowance (e.g. 1M Lambda calls/month).
- Some services (like a small RDS database) are free for the first 12 months.

> This is why our whole strategy is **deploy → test → `terraform destroy`**:
> we turn the city's utilities ON, use them for an hour, then turn them OFF so
> the meter stops. Cost ≈ a few cents.

---

## What is a "service" vs a "resource"?

- A **service** is a category of capability (e.g. "S3" is the storage service).
- A **resource** is one specific thing you create within a service (e.g. "the
  `cloudfile-uploads-abcd` bucket" is one S3 resource).

Terraform creates and manages **resources**. Our project creates ~25 resources
across 8 services.

---

## How do you control AWS? (3 ways)

1. **Console (website)** — click around in a browser. Good for looking, bad for
   repeating or cleaning up (easy to forget a resource → surprise bill).
2. **CLI (`aws ...` commands)** — type commands in a terminal. Scriptable.
3. **Infrastructure as Code (Terraform)** — describe everything in files; one
   command builds it, one command destroys it. **This is what we use**, because
   it's repeatable and `terraform destroy` removes everything cleanly.

We use Terraform for infrastructure + the AWS CLI for pushing Docker images.

---

## The specific AWS services CloudFile uses

| Service | What it gives us | Our use |
|---------|------------------|---------|
| **VPC** | A private network | isolates our app's networking |
| **ECR** | Docker image storage | holds our 3 service images |
| **ECS + Fargate** | Runs containers | runs auth/files/search |
| **RDS** | Managed PostgreSQL | our database |
| **S3** | File storage | stores uploaded files |
| **Lambda** | Serverless functions | the thumbnail processor |
| **IAM** | Permissions | lets services talk safely |
| **CloudWatch** | Logs | our service logs |

Each gets its own plain-English explanation in [21c](21c-aws-building-blocks.md).

---

## Check your understanding

- *Q: Why don't we own servers?* → Cloud = rent, cheaper + instant + no upkeep.
- *Q: What's a region?* → A geographic group of AWS data centers; we use us-east-1.
- *Q: Why destroy after testing?* → AWS bills per-use; destroying stops the meter.
- *Q: Why Terraform over clicking?* → Repeatable + clean teardown (no forgotten
  resources = no surprise bill).

Next: [21b — What is Terraform & how it thinks →](21b-what-is-terraform.md)
