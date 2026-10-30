# 02 — Local Deployment

## A. Docker Compose (recommended)

```bash
cd notification-service
cp .env.example .env          # first time only
docker compose up --build
```
Starts `notify-db` (Postgres on host port 5433) and `notification` (port 8004).

Open the API docs: http://localhost:8004/docs

### Quick test
```bash
# This service requires a JWT. Generate one using the SAME secret as the
# service config (JWT_SECRET_KEY). If running the full platform, just use a
# token from the auth service's /login. For a standalone quick test, any JWT
# signed with the configured secret and containing sub + email works.

TOKEN="<paste a JWT signed with JWT_SECRET_KEY, claims: sub, email>"

curl -X POST http://localhost:8004/api/v1/notifications/notify \
  -H "Authorization: Bearer $TOKEN" -H 'Content-Type: application/json' \
  -d '{"recipient":"user@example.com","subject":"Hi","message":"Hello","channel":"email"}'

curl http://localhost:8004/api/v1/notifications -H "Authorization: Bearer $TOKEN"
```
With the default `NOTIFICATION_PROVIDER=console`, the "delivery" is just a log
line in the container output — perfect for free local testing.

## B. Bare Python (fast iteration)

Run just the DB via Docker, then the app locally:
```bash
cd notification-service
docker compose up -d notify-db

python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # macOS/Linux
pip install -r requirements-dev.txt

export NOTIFICATION_DATABASE_URL="postgresql+asyncpg://notify:notify@localhost:5433/notifications"
export JWT_SECRET_KEY="local-dev-secret-change-me-0123456789"
export NOTIFICATION_PROVIDER="console"

uvicorn app.main:app --reload --port 8004
```

## Connecting to the platform

When running together with `cloudfile-platform`, the files service calls this
service at `NOTIFICATION_SERVICE_URL` (default
`http://host.docker.internal:8004`). Because this service publishes port 8004
on the host, the platform's containers can reach it even though the two stacks
are separate Docker Compose projects.

The shared `JWT_SECRET_KEY` MUST match the platform's so tokens verify.

## Stop
```bash
docker compose down        # add -v to also wipe the database volume
```

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| 401 on /notify | token missing/invalid, or `JWT_SECRET_KEY` mismatch |
| port 5433 in use | change the left side of the `ports:` mapping |
| files can't reach this service | ensure it's up on 8004; check `NOTIFICATION_SERVICE_URL` |
