# Convenience commands for local development.
# Usage: make <target>

.PHONY: help up down logs build test lint typecheck fmt migrate clean

help:
	@echo "Targets:"
	@echo "  up         Start the full local stack (docker compose)"
	@echo "  down       Stop the stack"
	@echo "  logs       Tail logs"
	@echo "  build      Build all images"
	@echo "  test       Run all service test suites"
	@echo "  lint       Run ruff on all code"
	@echo "  typecheck  Run mypy"
	@echo "  fmt        Format code with ruff"
	@echo "  migrate    Run Alembic migrations for auth + files"
	@echo "  clean      Remove volumes and caches"

up:
	docker compose up --build

down:
	docker compose down

logs:
	docker compose logs -f

build:
	docker compose build

# Run each service's tests from its own directory so imports resolve.
# "." puts the service root on the path (so `app` and `tests` import), and
# "../.." adds the repo root (so `shared` imports).
test:
	cd services/auth   && PYTHONPATH=.:../.. pytest
	cd services/files  && PYTHONPATH=.:../.. pytest
	cd services/search && PYTHONPATH=.:../.. pytest

lint:
	ruff check services shared

typecheck:
	mypy services shared

fmt:
	ruff check --fix services shared
	ruff format services shared

migrate:
	cd services/auth  && alembic upgrade head
	cd services/files && alembic upgrade head

clean:
	docker compose down -v
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	rm -rf .pytest_cache .mypy_cache .ruff_cache
