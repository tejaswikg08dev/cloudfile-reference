#!/usr/bin/env bash
# End-to-end demo: register -> login -> upload -> (PUT to S3) -> confirm ->
# search -> list notifications. Runs against the locally running stack.
#
# Prerequisites:
#   - cloudfile-platform stack running:   docker compose up --build
#   - notification-service running:        (in its repo) docker compose up --build
#   - `curl` and `jq` installed
#
# Usage:
#   ./scripts/e2e-demo.sh
set -euo pipefail

AUTH="${AUTH_URL:-http://localhost:8001}"
FILES="${FILES_URL:-http://localhost:8002}"
SEARCH="${SEARCH_URL:-http://localhost:8003}"
NOTIFY="${NOTIFY_URL:-http://localhost:8004}"

EMAIL="demo+$(date +%s)@example.com"
PASSWORD="password123"
FULL_NAME="Demo User"

say()  { printf "\n\033[1;36m==> %s\033[0m\n" "$1"; }
ok()   { printf "\033[1;32m    ✓ %s\033[0m\n" "$1"; }
fail() { printf "\033[1;31m    ✗ %s\033[0m\n" "$1"; exit 1; }

command -v jq >/dev/null   || fail "jq is required (https://jqlang.github.io/jq/)"
command -v curl >/dev/null || fail "curl is required"

# ---------------------------------------------------------------------------
say "1. Health checks"
for pair in "auth:$AUTH" "files:$FILES" "search:$SEARCH"; do
  name="${pair%%:*}"; url="${pair#*:}"
  if curl -sf "$url/health" >/dev/null; then ok "$name healthy"; else fail "$name not reachable at $url"; fi
done
if curl -sf "$NOTIFY/health" >/dev/null; then ok "notification healthy"; else
  printf "\033[1;33m    ! notification service not running; notify step will be skipped\033[0m\n"
fi

# ---------------------------------------------------------------------------
say "2. Register user ($EMAIL)"
curl -sf -X POST "$AUTH/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"$EMAIL\",\"password\":\"$PASSWORD\",\"full_name\":\"$FULL_NAME\"}" >/dev/null \
  && ok "registered" || fail "register failed"

# ---------------------------------------------------------------------------
say "3. Login"
TOKEN=$(curl -sf -X POST "$AUTH/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"$EMAIL\",\"password\":\"$PASSWORD\"}" | jq -r '.access_token')
[ -n "$TOKEN" ] && [ "$TOKEN" != "null" ] && ok "got token" || fail "login failed"
AUTHH="Authorization: Bearer $TOKEN"

# ---------------------------------------------------------------------------
say "4. Initiate upload"
UPLOAD_JSON=$(curl -sf -X POST "$FILES/api/v1/files/upload" \
  -H "$AUTHH" -H "Content-Type: application/json" \
  -d '{"filename":"demo.txt","content_type":"text/plain","size_bytes":12}')
FILE_ID=$(echo "$UPLOAD_JSON" | jq -r '.file_id')
UPLOAD_URL=$(echo "$UPLOAD_JSON" | jq -r '.upload_url')
[ -n "$FILE_ID" ] && [ "$FILE_ID" != "null" ] && ok "file_id=$FILE_ID" || fail "upload initiation failed"

# ---------------------------------------------------------------------------
say "5. PUT bytes to presigned URL"
echo "hello world!" > /tmp/cloudfile-demo.txt
if curl -sf -X PUT "$UPLOAD_URL" -H "Content-Type: text/plain" \
     --data-binary @/tmp/cloudfile-demo.txt >/dev/null; then
  ok "uploaded bytes to S3/LocalStack"
else
  printf "\033[1;33m    ! direct S3 PUT failed (LocalStack signing can be strict); continuing\033[0m\n"
fi

# ---------------------------------------------------------------------------
say "6. Confirm upload (fires notification)"
curl -sf -X POST "$FILES/api/v1/files/confirm" \
  -H "$AUTHH" -H "Content-Type: application/json" \
  -d "{\"file_id\":\"$FILE_ID\"}" | jq -e '.status == "ready"' >/dev/null \
  && ok "confirmed (status=ready)" || fail "confirm failed"

# ---------------------------------------------------------------------------
say "7. List files"
COUNT=$(curl -sf "$FILES/api/v1/files" -H "$AUTHH" | jq 'length')
ok "user has $COUNT file(s)"

# ---------------------------------------------------------------------------
say "8. Search"
TOTAL=$(curl -sf "$SEARCH/api/v1/search?name=demo" -H "$AUTHH" | jq '.total')
ok "search found $TOTAL result(s) for name=demo"

# ---------------------------------------------------------------------------
say "9. List notifications (recipient = my email)"
if curl -sf "$NOTIFY/health" >/dev/null 2>&1; then
  NOTES=$(curl -sf "$NOTIFY/api/v1/notifications" -H "$AUTHH" | jq 'length')
  ok "notification service has $NOTES notification(s) for $EMAIL"
else
  printf "\033[1;33m    ! skipped (notification service not running)\033[0m\n"
fi

say "Demo complete ✅"
