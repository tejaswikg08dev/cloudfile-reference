# 21k — Design Decisions, Cost, Security & Interview Prep

The "why" behind every choice, plus ready-to-say answers.

---

## Design decisions (and the trade-offs)

> **D1 — Fargate instead of EKS (Kubernetes on AWS).**
> Why: EKS charges ~$0.10/hour (~$73/mo) just for the control plane, plus worker
> nodes. Fargate has no control-plane fee — you pay only per running task.
> Trade-off: less "K8s on cloud" experience → we cover that free on minikube
> locally (doc 18).

> **D2 — Public subnets, no NAT Gateway.**
> Why: a NAT Gateway is ~$32/mo and not free tier. Public subnets + public IPs
> let tasks reach ECR/S3 through the free Internet Gateway.
> Trade-off: tasks are internet-exposed (mitigated by security groups). A real
> prod setup uses private subnets + NAT + a load balancer.

> **D3 — One shared RDS database for all services.**
> Why: RDS provisions one database; creating more needs extra tooling. Our table
> names (`users`, `files`) don't collide, so one DB is safe and simple.
> Trade-off: not strict per-service data isolation. The upgrade path is a DB per
> service + an event bus (SNS/SQS) for the search read model.

> **D4 — IAM task role instead of access keys.**
> Why: the container inherits temporary credentials from its role — no secrets
> in code or env. More secure and the AWS-recommended way.
> Trade-off: none meaningful; this is best practice.

> **D5 — `DB_AUTO_CREATE` tables on startup (not migrations) for the demo.**
> Why: simplest path to a working demo. Trade-off: production should run Alembic
> migrations (set `DB_AUTO_CREATE=false`); the code supports both.

> **D6 — Deploy → test → destroy (not always-on).**
> Why: keeps cost near $0 and demonstrates cost-awareness.
> Trade-off: not a persistent public demo; re-deploy when needed (it's one
> command).

> **D7 — Lambda not VPC-attached.**
> Why: attaching Lambda to the VPC to reach RDS adds complexity (ENIs, subnets).
> For the demo the thumbnail/DB-update step degrades gracefully.
> Trade-off: Lambda can't update the DB; fixable with VPC config + an SG rule.

---

## Cost breakdown (us-east-1, approximate)

| Resource | While running | Free-tier note |
|----------|---------------|----------------|
| ECS Fargate × 3 tasks (256 CPU/512 MB) | ~$0.012/hour each ≈ $0.04/hr total | NOT free; the main cost |
| RDS db.t3.micro single-AZ | ~free | 750 hrs/mo free for 12 months |
| S3 | ~$0 | 5 GB free |
| Lambda | ~$0 | 1M requests/mo free |
| ECR | ~$0 | 500 MB free |
| Data transfer | tiny | small for a test |
| NAT Gateway | **$0** | avoided by design |
| EKS | **$0** | disabled |

**A 1–2 hour deploy-test-destroy session ≈ a few cents.** The ~$100 credits
cover hundreds of such sessions.

> Biggest "gotcha": forgetting to `terraform destroy`. Three tasks + RDS left on
> 24/7 ≈ $30–40/month. Always destroy.

---

## Security model (how it's protected)

| Layer | Control |
|-------|---------|
| Passwords | bcrypt hashing (never plaintext) |
| Sessions | JWT with expiry; verified per request |
| Inter-service | shared-secret JWT forwarded on calls |
| Database | SG allows 5432 only from the ECS SG (not the internet) |
| S3 | public access blocked; access via time-limited presigned URLs only |
| App → AWS | IAM task role (no keys in code) |
| Secrets | `db_password`/`jwt_secret_key` passed as Terraform vars, never committed |
| Containers | run as non-root user |

**Honest gaps for a real prod** (good to mention): no HTTPS/TLS termination
(would add an ALB + ACM cert), tasks are in public subnets, secrets would move
to AWS Secrets Manager, and you'd scope IAM policies even tighter.

---

## Interview answers (ready to say)

**"Walk me through your AWS deployment."**
> "Infrastructure is defined in Terraform — VPC, ECR, RDS, S3, Lambda, IAM, and
> ECS Fargate. I deploy in two phases: first create the registry and infra with
> services scaled to zero, then push Docker images to ECR and scale the services
> to one task. Services run on Fargate in public subnets with security groups;
> the database only accepts traffic from the app's security group. The app uses
> an IAM task role to access S3, so there are no credentials in code. Uploads go
> directly to S3 via presigned URLs, and an S3 event triggers a Lambda for
> processing. When I'm done I run `terraform destroy` — one command tears it all
> down, which keeps it near-free and shows cost discipline."

**"Why Fargate over EKS?"**
> "Cost. EKS bills a control-plane fee (~$73/mo); Fargate is pay-per-task with no
> control plane. I still demonstrate Kubernetes locally on minikube, so I get the
> skill without the cost."

**"How do your services authenticate to AWS?"**
> "ECS task IAM roles. The container assumes a role that grants exactly the S3
> actions it needs. boto3 picks up the temporary role credentials automatically —
> no access keys anywhere."

**"How is the database secured?"**
> "It's in the VPC, not publicly accessible, and its security group only allows
> port 5432 from the ECS security group. So only the application can reach it;
> the open internet cannot."

**"How would you make this production-grade?"**
> "Add an Application Load Balancer with HTTPS, move tasks to private subnets with
> a NAT Gateway, use AWS Secrets Manager for secrets, run Alembic migrations
> instead of auto-create, split the database per service with an event bus for
> the search read model, and add autoscaling, alarms, and tracing."

**"How do you control cost?"**
> "Fargate over EKS, public subnets to avoid NAT, db.t3.micro single-AZ,
> deploy-test-destroy with Terraform, and `default_tags` so I can find and remove
> every resource. A test session costs a few cents."

---

## What you can now confidently claim

- Designed and deployed a microservices system on AWS with Terraform (IaC).
- Used ECS Fargate, RDS, S3, Lambda, ECR, IAM, VPC, CloudWatch.
- Implemented secure networking (security groups, private DB) and IAM roles.
- Practiced cost management (free-tier shaping, destroy-after-use).
- Can explain the full request path and every design trade-off.

---

That's the deep dive. Revisit [21 (hub)](21-terraform-aws-deep-dive.md) anytime,
and use the interactive page `visual-docs/12-aws-deploy-internals.html` to *watch*
it build and flow.
