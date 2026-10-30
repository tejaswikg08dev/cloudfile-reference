# 04 — Cloud Deployment

> 💸 On AWS, destroy resources when done. This service is cheap, but RDS/SES and
> any always-on compute still accrue cost.

## Kubernetes (minikube or EKS)

Manifests live in `infra/k8s/`.

```bash
# Build the image (into minikube's Docker for local):
eval $(minikube docker-env)
docker build -t notification-service:latest .

# Namespace is shared with the platform ("cloudfile").
kubectl apply -f infra/k8s/service.yaml
cp infra/k8s/secrets.example.yaml infra/k8s/secrets.yaml   # edit values
kubectl apply -f infra/k8s/secrets.yaml
kubectl apply -f infra/k8s/deployment.yaml
```

The deployment reads `NOTIFICATION_DATABASE_URL` and `JWT_SECRET_KEY` from a
`notification-secrets` Secret. The `JWT_SECRET_KEY` must match the platform's.

In-cluster, the platform's files service reaches this service at:
```
http://notification-service.cloudfile.svc.cluster.local:8004
```
(This is already set in the platform's ConfigMap.)

## AWS (as a container)

Being a standalone repo, this service deploys on its own. The simplest path:

1. Create an ECR repository (console or CLI).
2. Build and push the image:
   ```bash
   ACCOUNT=$(aws sts get-caller-identity --query Account --output text)
   REGION=us-east-1
   aws ecr get-login-password --region $REGION | \
     docker login --username AWS --password-stdin $ACCOUNT.dkr.ecr.$REGION.amazonaws.com
   docker build -t $ACCOUNT.dkr.ecr.$REGION.amazonaws.com/notification-service:latest .
   docker push $ACCOUNT.dkr.ecr.$REGION.amazonaws.com/notification-service:latest
   ```
3. Run it on ECS Fargate (an extra task/service alongside the platform's
   cluster) or on the EKS cluster using the manifests above.
4. Provide env vars: `NOTIFICATION_DATABASE_URL` (RDS), `JWT_SECRET_KEY`,
   and (for real email) `NOTIFICATION_PROVIDER=ses` + SES setup.

## Using AWS SES for real email

1. Verify the sender (and, in sandbox, the recipient) in SES.
2. Grant the task role `ses:SendEmail`.
3. Set env: `NOTIFICATION_PROVIDER=ses`, `SES_SENDER=you@verified-domain`.
4. The `SESProvider` sends via boto3 (offloaded to a thread).

## CI/CD

`.github/workflows/ci-cd.yml` is this service's own independent pipeline:
test → (on main) build → push to ECR. Set repo secrets `AWS_ACCESS_KEY_ID`,
`AWS_SECRET_ACCESS_KEY`, `AWS_REGION`.
