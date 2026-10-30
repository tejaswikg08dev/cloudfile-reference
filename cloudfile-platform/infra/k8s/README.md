# Kubernetes Deployment (minikube + EKS)

## Local with minikube (free)

```bash
minikube start --cpus=4 --memory=6g
minikube addons enable ingress
minikube addons enable metrics-server

# Build images directly into minikube's Docker daemon:
eval $(minikube docker-env)
docker build -t cloudfile-auth:latest   -f services/auth/Dockerfile   .
docker build -t cloudfile-files:latest  -f services/files/Dockerfile  .
docker build -t cloudfile-search:latest -f services/search/Dockerfile .

# Create namespace + config + secrets
kubectl apply -f infra/k8s/namespace.yaml
kubectl apply -f infra/k8s/configmap.yaml
cp infra/k8s/secrets.example.yaml infra/k8s/secrets.yaml   # edit values
kubectl apply -f infra/k8s/secrets.yaml

# Local Postgres (skip on AWS; use RDS there)
kubectl apply -f infra/k8s/postgres.yaml

# Services
kubectl apply -f infra/k8s/auth.yaml
kubectl apply -f infra/k8s/files.yaml
kubectl apply -f infra/k8s/search.yaml
kubectl apply -f infra/k8s/ingress.yaml
kubectl apply -f infra/k8s/hpa.yaml

# Access
echo "127.0.0.1 cloudfile.local" | sudo tee -a /etc/hosts
minikube tunnel   # in a separate terminal
# Then: http://cloudfile.local/auth/health
```

## Routing

The ingress strips the service prefix, so:

- `http://cloudfile.local/auth/api/v1/auth/login`   -> auth
- `http://cloudfile.local/files/api/v1/files/upload` -> files
- `http://cloudfile.local/search/api/v1/search`      -> search
- `http://cloudfile.local/auth/health`               -> auth health

## EKS

Same manifests apply to EKS. Differences:
- Use ECR image URIs in the Deployments.
- Do NOT deploy `postgres.yaml`; point the ConfigMap DB URLs at RDS.
- Use the AWS Load Balancer Controller instead of the NGINX ingress, or
  install NGINX ingress on EKS.

Remember: `terraform destroy` after testing to avoid charges.
