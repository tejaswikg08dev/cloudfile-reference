# 09 — Development Guide

## Project conventions

- Layered architecture: `router → service → repository → model`.
- Routers do no business logic; services do no HTTP/SQL-framework specifics.
- Raise domain errors from services (`NotFoundError`, etc.); let the shared
  handlers map them to HTTP.
- All config comes from environment variables via `config.py`.
- Type hints everywhere; run `ruff` and `mypy` before committing.

## Add a new endpoint to an existing service

Example: add `GET /api/v1/files/{id}` to return one file's metadata.

1. **schema** (if needed) — reuse `FileOut`.
2. **repository** — `get_by_id` already exists.
3. **service** — add a method:
   ```python
   async def get_file(self, file_id: str, owner_id: str) -> FileMetadata:
       return await self._get_owned(file_id, owner_id)
   ```
4. **router** — add the route:
   ```python
   @router.get("/{file_id}", response_model=FileOut)
   async def get_file(file_id: str,
                      token: TokenData = Depends(get_current_token),
                      service: FileService = Depends(get_file_service)) -> FileOut:
       return FileOut.model_validate(await service.get_file(file_id, token.user_id))
   ```
5. **test** — add a case in `tests/test_files.py`.
6. Run `PYTHONPATH=.:../.. pytest` and `ruff check`.

## Add a new migration (auth or files)

```bash
cd services/files
# after editing models.py:
alembic revision --autogenerate -m "add column x"
# review the generated file in alembic/versions/, then:
alembic upgrade head
```
Set the DB URL env var first (e.g. `FILES_DATABASE_URL=...`).

## Add a brand-new microservice (monorepo)

1. `services/<name>/app/` with `main.py, config.py, database.py, models.py,
   schemas.py, repository.py, service.py, router.py, dependencies.py`.
2. `requirements.txt`, `requirements-dev.txt`, `Dockerfile`, `.dockerignore`.
3. `conftest.py` at the service root (copy from an existing service) + `tests/`.
4. Add a service block to `docker-compose.yml` (build context `.`,
   dockerfile `services/<name>/Dockerfile`, a unique port).
5. Add K8s `infra/k8s/<name>.yaml` (Deployment + Service).
6. Add the service to the CI matrix in `.github/workflows/ci.yml`.
7. If it needs AWS, add an ECR repo + ECS task/service in Terraform.

## Local inner loop

```bash
# Run just Postgres + LocalStack:
docker compose up -d postgres localstack

# Run one service with autoreload:
cd services/auth
PYTHONPATH=.:../.. uvicorn app.main:app --reload --port 8001
```

## Code style

```bash
ruff format services shared     # format
ruff check --fix services shared # autofix lint
mypy services shared            # type check
```

## Git workflow (when you move to your GitHub)

- Branch off `main`: `git checkout -b feat/<thing>`.
- Commit small, descriptive changes.
- Open a PR → CI runs lint + tests.
- Merge to `main` → CD builds images and deploys.
- Never commit `.env` or `secrets.yaml` (already in `.gitignore`).
