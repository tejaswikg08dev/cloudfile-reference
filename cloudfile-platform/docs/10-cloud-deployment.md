# 10 — Cloud Deployment

Two tracks:
- **Track 1: Kubernetes on minikube** (free, where you learn K8s)
- **Track 2: AWS** (ECS Fargate cheap path + optional short EKS demo)

> 💸 Golden rule: on AWS, run `terraform destroy` the moment you finish testing.
> Never leave RDS, NAT, or EKS running overnight.

---

## Track 1 — Kubernetes on minikube (free)

### Step 1 — Start the cluster
```bash
minikube start --cpus=4 --memory=6g
minikube addons enable ingress
minikube addons enable metrics-server
```

### Step 2 — Build images into minikube's Docker
```bash
cd cloudfile-platform
eval $(minikube docker-env)          # Git Bash/WSL; see note for PowerShell
docker build -t cloudfile-auth:latest   -f services/auth/Dockerfile   .
docker build -t cloudfile-files:latest  -f services/files/Dockerfile  .
docker build -t cloudfile-search:latest -f services/search/Dockerfile .
```
(PowerShell: `& minikube -p minikube docker-env --shell powershell | Invoke-Expression`)

### Step 3 — Apply manifests
```bash
kubectl apply -f infra/k8s/namespace.yaml
kubectl apply -f infra/k8s/configmap.yaml
cp infra/k8s/secrets.example.yaml infra/k8s/secrets.yaml   # edit values
kubectl apply -f infra/k8s/secrets.yaml
kubectl apply -f infra/k8s/postgres.yaml        # local DB (not for AWS)
kubectl apply -f infra/k8s/auth.yaml
kubectl apply -f infra/k8s/files.yaml
kubectl apply -f infra/k8s/search.yaml
kubectl apply -f infra/k8s/ingress.yaml
kubectl apply -f infra/k8s/hpa.yaml
```

### Step 4 — Access
```bash
kubectl -n cloudfile get pods          # wait for Running/Ready
echo "127.0.0.1 cloudfile.local" | sudo tee -a /etc/hosts
minikube tunnel                        # separate terminal, keep running
# Test:
curl http://cloudfile.local/auth/health
```
Routing (ingress strips the prefix):
- `/auth/api/v1/auth/login` → auth
- `/files/api/v1/files/upload` → files
- `/search/api/v1/search` → search

### Step 5 — Observe autoscaling
```bash
kubectl -n cloudfile get hpa
kubectl -n cloudfile describe hpa auth-hpa
```

### Step 6 — Tear down
```bash
kubectl delete namespace cloudfile
minikube stop        # or: minikube delete
```

---

## Track 2 — AWS with Terraform (free-tier-first)

### Prerequisites
```bash
aws configure         # set your access key, secret, region (us-east-1)
aws sts get-caller-identity    # confirm you're authenticated
```

### Step 1 — Provision infrastructure
```bash
cd cloudfile-platform/infra/terraform
terraform init
export TF_VAR_db_password=$(openssl rand -hex 16)
export TF_VAR_jwt_secret_key=$(openssl rand -hex 32)
terraform plan
terraform apply       # type "yes"
terraform output      # note ECR URLs, bucket, RDS endpoint
```
This creates: VPC, ECR repos, S3 bucket (+ Lambda trigger), processor Lambda,
RDS Postgres (db.t3.micro), ECS Fargate cluster + services, IAM roles.

### Step 2 — Build & push images to ECR
```bash
ACCOUNT=$(aws sts get-caller-identity --query Account --output text)
REGION=us-east-1
aws ecr get-login-password --region $REGION | \
  docker login --username AWS --password-stdin $ACCOUNT.dkr.ecr.$REGION.amazonaws.com

for s in auth files search; do
  docker build -t $ACCOUNT.dkr.ecr.$REGION.amazonaws.com/cloudfile-$s:latest \
    -f services/$s/Dockerfile .
  docker push $ACCOUNT.dkr.ecr.$REGION.amazonaws.com/cloudfile-$s:latest
done
```

### Step 3 — Create the databases on RDS
RDS creates one database (`cloudfile_files`). Create `cloudfile_auth` too:
```bash
# From a machine that can reach RDS (or temporarily make it publicly
# accessible / use a bastion). Using psql:
psql "postgres://cloudfile:$TF_VAR_db_password@<rds-endpoint>:5432/postgres" \
  -c "CREATE DATABASE cloudfile_auth;"
```
Then run migrations (point the env vars at RDS and run `alembic upgrade head`
for auth and files), or rely on the services' startup `create_all` for a demo.

### Step 4 — Roll ECS to pick up images
```bash
for s in auth files search; do
  aws ecs update-service --cluster cloudfile-cluster \
    --service cloudfile-$s --force-new-deployment --region $REGION
done
```
Find the public IP/DNS of a task to test:
```bash
aws ecs list-tasks --cluster cloudfile-cluster --service-name cloudfile-auth
# describe the task to get its ENI, then its public IP
```

### Step 5 — Verify
```bash
curl http://<task-public-ip>:8001/health
```

### Step 6 — DESTROY (do not skip)
```bash
terraform destroy      # type "yes"
```
Double-check in the console that RDS, ECS, NAT (if any), and the bucket are gone.

### Optional — short EKS demo
```bash
terraform apply -var="enable_eks=true"
aws eks update-kubeconfig --name cloudfile-eks --region us-east-1
kubectl apply -f ../k8s/   # (use ECR image URIs; skip postgres.yaml, use RDS)
# ... demo, screenshot ...
terraform destroy -var="enable_eks=true"
```

---

## CI/CD (GitHub Actions) does steps 2 + 4 for you

Once images and ECS exist, pushing to `main` triggers `.github/workflows/cd.yml`
which builds each service, pushes to ECR, and forces a new ECS deployment.
Set repo secrets: `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_REGION`.

---

## Cost cheat sheet

| Resource | Free-tier friendly? | Note |
|----------|--------------------|------|
| S3 | mostly | 5 GB free; tiny demo cost |
| Lambda | yes | 1M requests/mo free |
| RDS db.t3.micro | yes-ish | within limits; still destroy after |
| ECS Fargate | low | pay per task-second; stop when idle |
| ECR | low | pay per GB stored |
| NAT Gateway | NO | avoided by using public subnets |
| EKS control plane | NO | ~$0.10/hr; only for brief demos |
