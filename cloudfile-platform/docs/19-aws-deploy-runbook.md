# 19 — AWS Deployment Runbook (baby steps, Terraform + CLI)

A copy-paste, step-by-step guide to deploy CloudFile to AWS, test it, and
**destroy it the same day** so you stay near $0.

> 💸 Golden rule: finish with **Phase 6 (destroy)**. Don't leave it running.
> The only real cost is ECS Fargate while tasks run; a few hours ≈ a few cents.

Run everything in **Git Bash** from:
```
cloudfile-reference/cloudfile-platform/infra/terraform
```

---

## Phase 0 — Pre-flight checklist (5 min)

Run these and confirm each works:

```bash
aws --version                      # AWS CLI present
terraform --version                # Terraform present (install if missing)
aws sts get-caller-identity        # prints your account id = you're logged in
docker --version                   # Docker running (needed to build images)
```

- If `terraform` is missing: `winget install HashiCorp.Terraform`, restart Git Bash.
- If `aws sts get-caller-identity` errors: run `aws configure` and enter your
  Access Key, Secret, region `us-east-1`.

Set two secrets as environment variables (used by Terraform):
```bash
export TF_VAR_db_password="$(openssl rand -hex 16)"
export TF_VAR_jwt_secret_key="$(openssl rand -hex 32)"
echo "db_password=$TF_VAR_db_password"       # save these somewhere for the session
echo "jwt_secret_key=$TF_VAR_jwt_secret_key"
```
> Keep this terminal open for the whole session — these vars live only here.

---

## Phase 1 — Create the infrastructure (ECR + RDS + S3 + Lambda + ECS, services OFF)

```bash
cd cloudfile-reference/cloudfile-platform/infra/terraform

terraform init          # downloads the AWS provider (first time only)
terraform plan          # preview — read the summary, should say "X to add"
terraform apply         # type: yes
```

This creates everything but starts ECS services at **0 tasks** (because images
don't exist yet — this avoids crash loops). Takes ~5–10 min (RDS is the slow part).

When done, capture the outputs:
```bash
terraform output
```
You'll see something like:
```
ecr_repository_urls = {
  "auth"   = "1234.dkr.ecr.us-east-1.amazonaws.com/cloudfile-auth"
  "files"  = "1234.dkr.ecr.us-east-1.amazonaws.com/cloudfile-files"
  "search" = "1234.dkr.ecr.us-east-1.amazonaws.com/cloudfile-search"
}
rds_endpoint     = "cloudfile-db.xxxx.us-east-1.rds.amazonaws.com"
s3_bucket_name   = "cloudfile-uploads-abcd1234"
ecs_cluster_name = "cloudfile-cluster"
```

---

## Phase 2 — Build and push the Docker images to ECR

```bash
cd cloudfile-reference/cloudfile-platform     # back to repo root (has shared/)

ACCOUNT=$(aws sts get-caller-identity --query Account --output text)
REGION=us-east-1
REGISTRY=$ACCOUNT.dkr.ecr.$REGION.amazonaws.com

# 1. Log Docker in to ECR
aws ecr get-login-password --region $REGION \
  | docker login --username AWS --password-stdin $REGISTRY

# 2. Build + push each service (build context is the repo root)
for s in auth files search; do
  echo "=== building $s ==="
  docker build -t $REGISTRY/cloudfile-$s:latest -f services/$s/Dockerfile .
  docker push $REGISTRY/cloudfile-$s:latest
done
```

Verify the images are in ECR:
```bash
aws ecr list-images --repository-name cloudfile-auth --region $REGION
```

---

## Phase 3 — Start the services (scale ECS to 1)

Now that images exist, tell Terraform to run 1 task per service:
```bash
cd infra/terraform
terraform apply -var="service_desired_count=1"     # type: yes
```

Watch them start:
```bash
aws ecs describe-services \
  --cluster cloudfile-cluster \
  --services cloudfile-auth cloudfile-files cloudfile-search \
  --region us-east-1 \
  --query 'services[].{name:serviceName,running:runningCount,desired:desiredCount}'
```
Re-run until each shows `running: 1, desired: 1` (give it 1–3 min).

---

## Phase 4 — Find the public address and test

Get the public IP of the auth task:
```bash
REGION=us-east-1
TASK=$(aws ecs list-tasks --cluster cloudfile-cluster \
  --service-name cloudfile-auth --region $REGION \
  --query 'taskArns[0]' --output text)

ENI=$(aws ecs describe-tasks --cluster cloudfile-cluster --tasks $TASK --region $REGION \
  --query 'tasks[0].attachments[0].details[?name==`networkInterfaceId`].value' --output text)

AUTH_IP=$(aws ec2 describe-network-interfaces --network-interface-ids $ENI --region $REGION \
  --query 'NetworkInterfaces[0].Association.PublicIp' --output text)

echo "AUTH is at: http://$AUTH_IP:8001"
curl http://$AUTH_IP:8001/health
```
Expected: `{"status":"ok","service":"auth"}`

Repeat for files (port 8002) and search (8003) by changing
`--service-name cloudfile-files` / `cloudfile-search`.

### Quick end-to-end test on AWS
```bash
# register + login against the auth public IP
curl -s -X POST http://$AUTH_IP:8001/api/v1/auth/register \
  -H 'Content-Type: application/json' \
  -d '{"email":"me@example.com","password":"password123","full_name":"Me"}'

TOKEN=$(curl -s -X POST http://$AUTH_IP:8001/api/v1/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"email":"me@example.com","password":"password123"}' \
  | grep -o '"access_token":"[^"]*"' | sed 's/"access_token":"//; s/"//')
echo "$TOKEN"
```
Take screenshots now — this is your "deployed to AWS" proof for interviews.

> Note: tables are auto-created on first start (DB_AUTO_CREATE=true). The Lambda
> thumbnail step is best-effort (see known limitations in doc 14).

---

## Phase 5 — (Optional) look around in the AWS Console

While it's running, open the AWS Console and VIEW (don't edit):
- **ECS** → Clusters → cloudfile-cluster → see 3 running services
- **ECR** → your 3 repositories with images
- **RDS** → cloudfile-db instance
- **S3** → your uploads bucket
- **CloudWatch** → Log groups → `/ecs/cloudfile-*` → live logs

This is a great way to connect "what Terraform made" to "what it looks like".

---

## Phase 6 — DESTROY everything (do this when done!)

```bash
cd cloudfile-reference/cloudfile-platform/infra/terraform
terraform destroy          # type: yes
```
This removes ECS, RDS, S3, Lambda, ECR, VPC — everything — in one go.

### Verify nothing is left (cost safety)
```bash
REGION=us-east-1
aws ecs list-clusters --region $REGION                 # no cloudfile-cluster
aws rds describe-db-instances --region $REGION          # no cloudfile-db
aws s3 ls | grep cloudfile || echo "no cloudfile buckets"
aws ecr describe-repositories --region $REGION 2>/dev/null | grep cloudfile || echo "no cloudfile repos"
```
Also glance at the Console → **Billing → Free Tier** the next day to confirm
usage is tiny.

> If `destroy` ever fails on the S3 bucket "not empty", empty it then retry:
> `aws s3 rm s3://<bucket-name> --recursive` then `terraform destroy` again.

---

## Cost recap

| Resource | While running | After destroy |
|----------|---------------|---------------|
| ECS Fargate (3 tasks) | a few cents/hour | $0 |
| RDS db.t3.micro | free tier | $0 |
| S3 / Lambda / ECR | ~free | $0 |
| VPC / IGW | free | $0 |

A 1–2 hour deploy-test-destroy session costs **a few cents**, well within your
$100 credits.

---

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| `terraform apply` asks for `db_password` | you didn't `export TF_VAR_db_password=...` in this terminal |
| ECS task `CannotPullContainerError` | images not pushed yet — do Phase 2, then Phase 3 |
| service stuck `running: 0` | check CloudWatch logs `/ecs/cloudfile-auth`; usually DB URL/secret |
| can't curl the public IP | security group allows 8001–8003; make sure you used the right port |
| `destroy` fails on bucket | `aws s3 rm s3://<bucket> --recursive`, then destroy again |
| surprise this costs money | you left it running — run Phase 6 |

---

## Next: CI/CD

Once you've seen this work, wire up GitHub Actions so `git push` builds + pushes
images and redeploys ECS automatically. See `docs/20-cicd-setup.md` (added when
you're ready).
