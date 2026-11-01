# 21c — The AWS Building Blocks We Use

Plain-English intro to each AWS service in CloudFile. Each has: an analogy, what
it does, and how WE use it.

---

## The whole thing on one picture

```
                         ┌──────────────────────────────────────────┐
                         │                 AWS (us-east-1)           │
                         │                                           │
  You (curl/browser)     │   ┌──────────────── VPC ───────────────┐  │
        │                │   │  (your private network)            │  │
        │   internet     │   │                                    │  │
        └────────────────┼──▶│  [IGW]  ──▶  ECS Fargate tasks     │  │
                         │   │               (auth/files/search)  │  │
                         │   │                 │        │         │  │
                         │   │                 ▼        ▼         │  │
                         │   │               RDS      (calls S3)  │  │
                         │   │              Postgres              │  │
                         │   └────────────────────────────────────┘  │
                         │                                 │          │
                         │   ECR (images)   S3 (files) ◀───┘          │
                         │                    │                       │
                         │                    ▼ (ObjectCreated event) │
                         │                  Lambda (thumbnail)        │
                         │                                           │
                         │   IAM (permissions)   CloudWatch (logs)    │
                         └──────────────────────────────────────────┘
```

---

## 1. VPC — Virtual Private Cloud

**What:** your own private, isolated network inside AWS. Nothing else in AWS can
see into it unless you allow it.

> Analogy: AWS is a huge city. A VPC is **your own fenced plot of land** in that
> city. You decide the internal roads and who can enter.

**Our use:** everything (ECS tasks, RDS) lives inside one VPC so they can talk to
each other privately.

---

## 2. Subnet

**What:** a subdivision of your VPC's network. Can be "public" (reachable from
the internet) or "private" (internal only).

> Analogy: if the VPC is your plot, subnets are **fenced sections** of it. A
> public subnet has a gate to the street; a private one doesn't.

**Our use:** 2 **public** subnets (in 2 AZs). We use public subnets on purpose
to avoid paying for a NAT Gateway (explained in [21d](21d-networking-deep-dive.md)).

---

## 3. Internet Gateway (IGW)

**What:** the component that connects your VPC to the internet.

> Analogy: the **main gate** between your plot and the public road.

**Our use:** lets your curl/browser reach the ECS tasks, and lets tasks pull
images from ECR.

---

## 4. Security Group (SG)

**What:** a virtual firewall attached to a resource. It has rules like "allow
incoming traffic on port 8001" or "allow Postgres only from the app."

> Analogy: a **door lock with a guest list** on each resource. Only traffic
> matching a rule gets through.

**Our use:**
- ECS SG: allows inbound 8001–8003 (so you can reach the services).
- RDS SG: allows inbound 5432 **only from the ECS SG** (so only our app can
  reach the database — not the public internet).

---

## 5. ECR — Elastic Container Registry

**What:** a private storage service for Docker images (like a private Docker Hub).

> Analogy: a **warehouse** where you store the shipping containers (images)
> before they're deployed.

**Our use:** we build 3 Docker images (auth, files, search) and push them to 3
ECR repositories. ECS pulls from here to run them.

---

## 6. ECS + Fargate — running your containers

**ECS (Elastic Container Service):** AWS's system for running Docker containers.

**Fargate:** a mode of ECS where **AWS runs the containers for you** — you never
manage or even see the underlying servers. "Serverless containers."

> Analogy: ECS is a **container ship operator**. Normally you'd rent the ship
> (EC2 servers) and load it yourself. Fargate = you just hand over your
> containers and AWS runs them; no ship to manage.

**Key terms:**
- **Task Definition** = the blueprint for a container (which image, how much
  CPU/memory, env vars, which port). Like a recipe.
- **Task** = one actual running container from that blueprint. Like a cooked dish.
- **Service** = keeps N tasks running (restarts them if they die).

**Our use:** 3 ECS services (auth/files/search), each running 1 Fargate task.

---

## 7. RDS — Relational Database Service

**What:** managed PostgreSQL (or MySQL, etc.). AWS handles backups, patching,
the OS — you just get a database endpoint.

> Analogy: renting a **fully-serviced apartment** vs building a house. You just
> move in (connect); maintenance is handled.

**Our use:** one `db.t3.micro` PostgreSQL instance (free-tier size) holding the
`users` and `files` tables.

---

## 8. S3 — Simple Storage Service

**What:** store files ("objects") in "buckets." Virtually unlimited, cheap,
durable. Not a filesystem — it's key→file storage.

> Analogy: an **infinite warehouse of labeled boxes**. You put a box (file) with
> a label (key like `uploads/user1/cat.jpg`) and retrieve it by that label.

**Our use:** the bucket where uploaded files live. Users upload directly to S3
via presigned URLs (the service never handles the bytes).

---

## 9. Lambda — serverless functions

**What:** run a piece of code on-demand without any server. It wakes up when
triggered, runs, then sleeps. You pay only per execution.

> Analogy: a **motion-sensor light**. It's off (costs nothing) until someone
> walks by (an event), then it turns on just for that moment.

**Our use:** the "processor" — when a file lands in S3, S3 triggers the Lambda to
make a thumbnail. (In our free setup it runs but skips thumbnails without the
image library — documented; it never crashes.)

---

## 10. IAM — Identity and Access Management

**What:** controls **who can do what** in AWS. Nothing is allowed by default;
you grant specific permissions.

**Key terms:**
- **Policy** = a document listing allowed actions (e.g. "can read/write this S3
  bucket").
- **Role** = an identity a *service* assumes to get those permissions — without
  any password or key.

> Analogy: **ID badges**. A role is a badge; a policy is what doors that badge
> opens. The ECS task wears the "files task" badge, which opens the S3 bucket
> door — no password needed.

**Our use:**
- ECS task role → allows the files service to read/write the S3 bucket.
- ECS execution role → lets ECS pull images from ECR and write logs.
- Lambda role → lets the Lambda read/write S3 + write logs.

This is why the app needs **no AWS passwords in its code** — the role provides
access automatically.

---

## 11. CloudWatch — logs & monitoring

**What:** collects logs and metrics from AWS services.

> Analogy: the **CCTV + logbook** of your deployment.

**Our use:** each ECS service writes its logs to a CloudWatch "log group"
(`/ecs/cloudfile-auth`, etc.) so you can debug.

---

## How they work together (one sentence)

> Your request enters through the **IGW** into the **VPC**, hits an **ECS
> Fargate** task (permitted by an **IAM role**), which reads/writes **RDS** and
> **S3** (allowed by **security groups** and the role), while **Lambda**
> processes new S3 files and everything logs to **CloudWatch** — all built from
> images stored in **ECR**.

Next: [21d — Networking deep dive →](21d-networking-deep-dive.md)
