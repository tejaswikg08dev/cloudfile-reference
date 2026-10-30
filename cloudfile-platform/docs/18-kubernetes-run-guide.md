# 18 — How to Run on Kubernetes (step by step)

You've been running CloudFile with **Docker Compose**. Kubernetes (K8s) is a
different way to run the SAME containers — the way production systems run them,
with scaling and self-healing. This guide runs it locally on **minikube** (free).

---

## What is Kubernetes (quick)

- **Pod** = one running container (your service).
- **Deployment** = keeps N copies (replicas) of a pod alive; restarts crashes.
- **Service** = a stable internal address + load balancer for a set of pods.
- **Ingress** = routes outside traffic to services by URL path.
- **ConfigMap / Secret** = config and secrets injected as env vars.
- **HPA** = Horizontal Pod Autoscaler — adds pods when CPU is high.

minikube runs a small Kubernetes cluster on your laptop. Free.

---

## 1. Install the tools

| Tool | Install | Verify |
|------|---------|--------|
| minikube | https://minikube.sigs.k8s.io/docs/start/ | `minikube version` |
| kubectl | https://kubernetes.io/docs/tasks/tools/ | `kubectl version --client` |

Docker Desktop must be running (minikube uses it as the driver).

---

## 2. Start the cluster

```bash
minikube start --cpus=4 --memory=6g
minikube addons enable ingress
minikube addons enable metrics-server     # needed for autoscaling (HPA)
kubectl get nodes                          # should show one "Ready" node
```

---

## 3. Build the images INTO minikube

minikube has its own Docker. Point your shell at it, then build so the cluster
can find the images locally (no registry needed).

```bash
cd cloudfile-reference/cloudfile-platform

# Git Bash:
eval $(minikube docker-env)
# (PowerShell instead: & minikube -p minikube docker-env --shell powershell | Invoke-Expression)

docker build -t cloudfile-auth:latest   -f services/auth/Dockerfile   .
docker build -t cloudfile-files:latest  -f services/files/Dockerfile  .
docker build -t cloudfile-search:latest -f services/search/Dockerfile .
```

The manifests use `image: cloudfile-auth:latest` with `imagePullPolicy:
IfNotPresent`, so they pick up these local images.

---

## 4. Deploy the platform

```bash
kubectl apply -f infra/k8s/namespace.yaml
kubectl apply -f infra/k8s/configmap.yaml

# secrets: copy the example and apply it
cp infra/k8s/secrets.example.yaml infra/k8s/secrets.yaml
kubectl apply -f infra/k8s/secrets.yaml

# in-cluster Postgres (local only; prod uses RDS)
kubectl apply -f infra/k8s/postgres.yaml

# the three services
kubectl apply -f infra/k8s/auth.yaml
kubectl apply -f infra/k8s/files.yaml
kubectl apply -f infra/k8s/search.yaml

# routing + autoscaling
kubectl apply -f infra/k8s/ingress.yaml
kubectl apply -f infra/k8s/hpa.yaml
```

### Deploy the notification service too (separate repo)
```bash
cd ../notification-service
kubectl apply -f infra/k8s/postgres.yaml          # its own DB
cp infra/k8s/secrets.example.yaml infra/k8s/secrets.yaml
kubectl apply -f infra/k8s/secrets.yaml
kubectl apply -f infra/k8s/service.yaml
# build its image into minikube first:
eval $(minikube docker-env)
docker build -t notification-service:latest .
kubectl apply -f infra/k8s/deployment.yaml
cd ../cloudfile-platform
```

---

## 5. Watch it come up

```bash
kubectl -n cloudfile get pods -w
```
Wait until every pod is `Running` and `READY 1/1`. Press Ctrl+C to stop watching.

Useful checks:
```bash
kubectl -n cloudfile get all
kubectl -n cloudfile logs deploy/auth          # view a service's logs
kubectl -n cloudfile describe pod <pod-name>   # troubleshoot a pending/crash pod
```

---

## 6. Access the services

```bash
# add a hosts entry so the ingress hostname resolves
echo "127.0.0.1 cloudfile.local" | sudo tee -a /etc/hosts
# (Windows: edit C:\Windows\System32\drivers\etc\hosts as admin, add the line)

# open a tunnel (keep this running in its own terminal)
minikube tunnel
```

Now test (the ingress strips the `/auth` `/files` `/search` prefixes):
```bash
curl http://cloudfile.local/auth/health
curl http://cloudfile.local/files/health
curl http://cloudfile.local/search/health
```

Full API paths through the ingress:
- `http://cloudfile.local/auth/api/v1/auth/login`
- `http://cloudfile.local/files/api/v1/files/upload`
- `http://cloudfile.local/search/api/v1/search`

> Simpler alternative to ingress+tunnel — port-forward a single service:
> ```bash
> kubectl -n cloudfile port-forward svc/auth 8001:8001
> # then: curl http://localhost:8001/health
> ```

---

## 7. See Kubernetes do its thing

**Self-healing** — delete a pod; K8s recreates it:
```bash
kubectl -n cloudfile delete pod -l app=auth
kubectl -n cloudfile get pods -w        # a new auth pod appears
```

**Scaling** — manually scale, or let the HPA do it:
```bash
kubectl -n cloudfile scale deploy/files --replicas=3
kubectl -n cloudfile get pods -l app=files
kubectl -n cloudfile get hpa            # shows CPU target + current replicas
```

---

## 8. Tear down (free up your laptop)

```bash
kubectl delete namespace cloudfile      # removes everything in the namespace
minikube stop                           # stop the cluster (keep it)
# or
minikube delete                         # remove the cluster entirely
```

---

## Production: AWS EKS (not free — do briefly, then destroy)

The same manifests run on EKS. Differences:
- Build + push images to **ECR**, and set the Deployments' `image:` to the ECR
  URIs (CI/CD does this).
- Do NOT deploy `postgres.yaml` — point the ConfigMap DB URLs at **RDS**.
- Create the EKS cluster with Terraform: `terraform apply -var="enable_eks=true"`,
  then `aws eks update-kubeconfig --name cloudfile-eks`.
- **`terraform destroy` immediately after testing** — the EKS control plane
  bills ~$0.10/hour.

See `docs/14-production-setup-complete.md` and `docs/10-cloud-deployment.md`.

---

## Common issues

| Symptom | Cause / fix |
|---------|-------------|
| pod `ImagePullBackOff` | you didn't `eval $(minikube docker-env)` before building; rebuild into minikube |
| pod `CrashLoopBackOff` | check `kubectl logs <pod>`; usually a DB URL or secret mismatch |
| `cloudfile.local` not resolving | add the hosts entry; run `minikube tunnel` |
| HPA shows `<unknown>` CPU | enable `metrics-server` addon |
| pods `Pending` | not enough CPU/memory — start minikube with more (`--cpus --memory`) |
