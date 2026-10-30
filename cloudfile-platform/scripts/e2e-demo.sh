#!/usr/bin/env bash
# End-to-end demo: register -> login -> upload -> (PUT to S3) -> confirm ->
# search -> list notifications. Runs against the locally running stack.
#
# Prerequisites:
#   - cloudfile-platform stack running:   docker compose up --build
#   - notification-service running:        (in its repo) docker compose up --build
#   - `curl` installed. `jq` is optional (a built-in fallback is used if absent).
#
# Usage:
#   bash scripts/e2e-demo.sh
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
warn() { printf "\033[1;33m    ! %s\033[0m\n" "$1"; }
fail() { printf "\033[1;31m    ✗ %s\033[0m\n" "$1"; exit 1; }

command -v curl >/dev/null || fail "curl is required"

HAVE_JQ=0
if command -v jq >/dev/null; then HAVE_JQ=1; fi

# Extract a top-level JSON string/number field by key. Uses jq if available,
# otherwise a regex fallback (good enough for these simple, flat responses).
json_field() {
  local key="$1" body="$2"
  if [ "$HAVE_JQ" -eq 1 ]; then
    printf '%s' "$body" | jq -r ".${key} // empty"
  else
    # Match "key": "value"  OR  "key": value  (strings or bare tokens/numbers)
    printf '%s' "$body" \
      | grep -o "\"${key}\"[[:space:]]*:[[:space:]]*\(\"[^\"]*\"\|[^,}]*\)" \
      | head -n1 \
      | sed -E "s/\"${key}\"[[:space:]]*:[[:space:]]*//; s/^\"//; s/\"$//"
  fi
}

if [ "$HAVE_JQ" -eq 0 ]; then
  warn "jq not found — using a built-in JSON fallback (install jq for nicer parsing)"
fi

# ---------------------------------------------------------------------------
say "1. Health checks"
for pair in "auth:$AUTH" "files:$FILES" "search:$SEARCH"; do
  name="${pair%%:*}"; url="${pair#*:}"
  if curl -sf "$url/health" >/dev/null; then ok "$name healthy"; else fail "$name not reachable at $url"; fi
done
NOTIFY_UP=0
if curl -sf "$NOTIFY/health" >/dev/null; then ok "notification healthy"; NOTIFY_UP=1; else
  warn "notification service not running; notify step will be skipped"
fi

# ---------------------------------------------------------------------------
say "2. Register user ($EMAIL)"
curl -sf -X POST "$AUTH/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"$EMAIL\",\"password\":\"$PASSWORD\",\"full_name\":\"$FULL_NAME\"}" >/dev/null \
  && ok "registered" || fail "register failed"

# ---------------------------------------------------------------------------
say "3. Login"
LOGIN_BODY=$(curl -sf -X POST "$AUTH/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"$EMAIL\",\"password\":\"$PASSWORD\"}")
TOKEN=$(json_field access_token "$LOGIN_BODY")
[ -n "$TOKEN" ] && ok "got token" || fail "login failed (no token in: $LOGIN_BODY)"
AUTHH="Authorization: Bearer $TOKEN"

# ---------------------------------------------------------------------------
say "4. Initiate upload"
UPLOAD_JSON=$(curl -sf -X POST "$FILES/api/v1/files/upload" \
  -H "$AUTHH" -H "Content-Type: application/json" \
  -d '{"filename":"demo.txt","content_type":"text/plain","size_bytes":12}')
FILE_ID=$(json_field file_id "$UPLOAD_JSON")
UPLOAD_URL=$(json_field upload_url "$UPLOAD_JSON")
[ -n "$FILE_ID" ] && ok "file_id=$FILE_ID" || fail "upload initiation failed (got: $UPLOAD_JSON)"

# ---------------------------------------------------------------------------
say "5. PUT bytes to presigned URL"
echo "hello world!" > /tmp/cloudfile-demo.txt
if [ -n "$UPLOAD_URL" ] && curl -sf -X PUT "$UPLOAD_URL" -H "Content-Type: text/plain" \
     --data-binary @/tmp/cloudfile-demo.txt >/dev/null; then
  ok "uploaded bytes to S3/LocalStack"
else
  warn "direct S3 PUT failed (LocalStack signing can be strict); continuing"
fi

# ---------------------------------------------------------------------------
say "6. Confirm upload (fires notification)"
CONFIRM_JSON=$(curl -sf -X POST "$FILES/api/v1/files/confirm" \
  -H "$AUTHH" -H "Content-Type: application/json" \
  -d "{\"file_id\":\"$FILE_ID\"}")
STATUS=$(json_field status "$CONFIRM_JSON")
[ "$STATUS" = "ready" ] && ok "confirmed (status=ready)" || fail "confirm failed (got: $CONFIRM_JSON)"

# ---------------------------------------------------------------------------
say "7. List files"
LIST_JSON=$(curl -sf "$FILES/api/v1/files" -H "$AUTHH")
if [ "$HAVE_JQ" -eq 1 ]; then
  COUNT=$(printf '%s' "$LIST_JSON" | jq 'length')
else
  COUNT=$(printf '%s' "$LIST_JSON" | grep -o '"id"' | wc -l | tr -d ' ')
fi
ok "user has $COUNT file(s)"

# ---------------------------------------------------------------------------
say "8. Search"
SEARCH_JSON=$(curl -sf "$SEARCH/api/v1/search?name=demo" -H "$AUTHH")
TOTAL=$(json_field total "$SEARCH_JSON")
ok "search total=${TOTAL:-?} for name=demo"

# ---------------------------------------------------------------------------
say "9. List notifications (recipient = my email)"
if [ "$NOTIFY_UP" -eq 1 ]; then
  NOTE_JSON=$(curl -sf "$NOTIFY/api/v1/notifications" -H "$AUTHH")
  if [ "$HAVE_JQ" -eq 1 ]; then
    NOTES=$(printf '%s' "$NOTE_JSON" | jq 'length')
  else
    NOTES=$(printf '%s' "$NOTE_JSON" | grep -o '"id"' | wc -l | tr -d ' ')
  fi
  ok "notification service has $NOTES notification(s) for $EMAIL"
else
  warn "skipped (notification service not running)"
fi

say "Demo complete ✅"
