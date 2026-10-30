#!/usr/bin/env bash
# Hard reset the notification service stack. Use after pulling changes so you
# never run stale cached code.
set -euo pipefail

echo "==> Stopping stack and removing volumes + orphans..."
docker compose down -v --remove-orphans

echo "==> Rebuilding image with no cache..."
docker compose build --no-cache

echo "==> Starting fresh..."
docker compose up
