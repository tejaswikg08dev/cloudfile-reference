#!/usr/bin/env bash
# Hard reset the local stack: stop + wipe volumes, rebuild images from scratch,
# and start fresh. Use this after pulling code or Dockerfile changes so you are
# NEVER running stale cached code.
set -euo pipefail

echo "==> Stopping stack and removing volumes + orphans..."
docker compose down -v --remove-orphans

echo "==> Rebuilding images with no cache..."
docker compose build --no-cache

echo "==> Starting fresh..."
docker compose up
