# 06 — Environment Setup

Do this once on your personal machine. Allow ~20–30 minutes.

## 1. Install the tools

| Tool | Version | Link | Verify |
|------|---------|------|--------|
| Python | 3.11+ | https://www.python.org/downloads/ | `python --version` |
| Docker Desktop | latest | https://www.docker.com/products/docker-desktop/ | `docker --version` |
| Git | latest | https://git-scm.com/downloads | `git --version` |
| jq | latest | https://jqlang.github.io/jq/ | `jq --version` |

For cloud/K8s days (install later when needed):

| Tool | Link |
|------|------|
| minikube | https://minikube.sigs.k8s.io/docs/start/ |
| kubectl | https://kubernetes.io/docs/tasks/tools/ |
| Terraform | https://developer.hashicorp.com/terraform/downloads |
| AWS CLI | https://aws.amazon.com/cli/ |

### Windows notes
- During Python install, CHECK "Add Python to PATH".
- Install Docker Desktop with the WSL2 backend (recommended).
- Use Git Bash (or WSL) to run the `.sh` scripts.
- Restart your terminal after installing so PATH updates apply.

## 2. Verify Docker is running
```bash
docker run --rm hello-world
```
You should see "Hello from Docker!". If not, start Docker Desktop first.

## 3. Get the code

This project is two separate repositories. On your personal machine:
```bash
# After you push them to your GitHub:
git clone https://github.com/<you>/cloudfile-platform.git
git clone https://github.com/<you>/notification-service.git
```

## 4. Configure environment variables
```bash
# cloudfile-platform
cd cloudfile-platform
cp .env.example .env

# notification-service
cd ../notification-service
cp .env.example .env
```
For local dev the defaults work as-is. The only value you'd change for real
use is `JWT_SECRET_KEY` — and it MUST be identical across all services so they
can verify each other's tokens.

## 5. (Optional) Create Python virtual environments

Only needed if you want to run tests outside Docker.
```bash
cd cloudfile-platform
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate
```

## Troubleshooting

| Symptom | Cause | Fix |
|---------|-------|-----|
| `python: command not found` | not on PATH | reinstall with "Add to PATH"; restart terminal |
| `docker: command not found` | Docker not installed/running | install Docker Desktop, start it |
| `Cannot connect to the Docker daemon` | Docker Desktop not running | start Docker Desktop |
| port 5432/8001 already in use | another service bound the port | stop it, or change the published port in compose |
| `.sh` won't run on Windows | using CMD/PowerShell | run via Git Bash or WSL |
| JWT errors between services | mismatched `JWT_SECRET_KEY` | make it identical everywhere |
