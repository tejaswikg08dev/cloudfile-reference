# 21j — In-Depth Production Testing & Verification

Doc 20 covers the happy-path test. This goes deeper: verify every layer actually
works — networking, IAM, the database, S3, the Lambda, and negative cases.

Assumes you've set `AUTH_IP`, `FILES_IP`, `SEARCH_IP`, and `TOKEN` as in doc 20.

---

## Layer 1 — Networking & health

```bash
# Every service reachable through the IGW + its SG port
curl -i http://$AUTH_IP:8001/health
curl -i http://$FILES_IP:8002/health
curl -i http://$SEARCH_IP:8003/health
```
Expect `HTTP/1.1 200 OK` + `{"status":"ok",...}` on each. If one hangs → the
task isn't RUNNING or the SG port is wrong.

**Negative test (prove the DB is NOT public):**
```bash
RDS=$(cd infra/terraform && terraform output -raw rds_endpoint && cd - >/dev/null)
# Try to reach Postgres from your laptop — should TIME OUT (good: it's locked down)
nc -vz -w 5 $RDS 5432 || echo "correctly unreachable from the internet"
```

---

## Layer 2 — Auth & JWT

```bash
# register duplicate -> 409
curl -s -o /dev/null -w "%{http_code}\n" -X POST http://$AUTH_IP:8001/api/v1/auth/register \
  -H 'Content-Type: application/json' \
  -d '{"email":"me@example.com","password":"password123","full_name":"Me"}'
# expect 409 (already exists)

# wrong password -> 401
curl -s -o /dev/null -w "%{http_code}\n" -X POST http://$AUTH_IP:8001/api/v1/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"email":"me@example.com","password":"WRONG"}'
# expect 401

# /me without token -> 401
curl -s -o /dev/null -w "%{http_code}\n" http://$AUTH_IP:8001/api/v1/auth/me
# expect 401

# /me with token -> 200
curl -s http://$AUTH_IP:8001/api/v1/auth/me -H "Authorization: Bearer $TOKEN"
```

---

## Layer 3 — Files + S3 + IAM (the important one)

Upload (see doc 20 steps 3–6), then **verify at the AWS level** that IAM + S3
actually worked:

```bash
BUCKET=$(cd infra/terraform && terraform output -raw s3_bucket_name && cd - >/dev/null)

# The object really exists in S3 (proves the task role could PUT via presign)
aws s3 ls "s3://$BUCKET/uploads/" --recursive

# Inspect object metadata (content-type stored correctly)
KEY=$(aws s3 ls "s3://$BUCKET/uploads/" --recursive | awk '{print $4}' | head -1)
aws s3api head-object --bucket "$BUCKET" --key "$KEY"
# look for "ContentType": "image/jpeg" and the correct "ContentLength"
```

**Negative test — cross-user isolation (403):**
```bash
# second user
curl -s -X POST http://$AUTH_IP:8001/api/v1/auth/register -H 'Content-Type: application/json' \
  -d '{"email":"other@example.com","password":"password123","full_name":"Other"}'
OTHER=$(curl -s -X POST http://$AUTH_IP:8001/api/v1/auth/login -H 'Content-Type: application/json' \
  -d '{"email":"other@example.com","password":"password123"}' \
  | grep -o '"access_token":"[^"]*"' | sed 's/"access_token":"//; s/"//')

# other user tries to download YOUR file -> 403
curl -s -o /dev/null -w "%{http_code}\n" \
  "http://$FILES_IP:8002/api/v1/files/$FILE_ID/download" -H "Authorization: Bearer $OTHER"
# expect 403
```

---

## Layer 4 — Database (RDS actually has the data)

The services talk to RDS; confirm the row landed. Easiest without opening the DB
port: check via the API (the list endpoint reads from RDS):
```bash
curl -s http://$FILES_IP:8002/api/v1/files -H "Authorization: Bearer $TOKEN"
# your file appears with status "ready" -> RDS write+read works
```

To inspect RDS directly you'd need network access (it's private). Options:
- temporarily add your IP to the RDS SG (remember to remove it), or
- run a one-off query from an ECS task. For a demo, the API check above is enough
  proof the DB works.

---

## Layer 5 — Lambda fired (async processing)

```bash
# did the Lambda get invoked when you uploaded?
aws logs tail /aws/lambda/cloudfile-processor --since 10m --region us-east-1
```
Expect log lines like `processing s3://.../uploads/...`. (It may log that Pillow
isn't available and skip the thumbnail — that's expected in the free setup; the
point is the trigger fired.)

Also:
```bash
aws lambda get-function --function-name cloudfile-processor --region us-east-1 \
  --query 'Configuration.[FunctionName,Runtime,LastModified]'
```

---

## Layer 6 — Logs & observability

```bash
# tail each service
aws logs tail /ecs/cloudfile-auth   --follow --region us-east-1
aws logs tail /ecs/cloudfile-files  --follow --region us-east-1
aws logs tail /ecs/cloudfile-search --follow --region us-east-1
```
You should see structured JSON logs: startup lines, and a log per request. This
is what you'd use to debug a real incident.

---

## Layer 7 — Search correctness

```bash
# filter by name
curl -s "http://$SEARCH_IP:8003/api/v1/search?name=cat" -H "Authorization: Bearer $TOKEN"
# filter by type
curl -s "http://$SEARCH_IP:8003/api/v1/search?content_type=image/jpeg" -H "Authorization: Bearer $TOKEN"
# pagination
curl -s "http://$SEARCH_IP:8003/api/v1/search?page=1&page_size=1" -H "Authorization: Bearer $TOKEN"
# verify total / total_pages in the response
```

---

## Full verification checklist

| # | Check | Pass = |
|---|-------|--------|
| 1 | All 3 `/health` return 200 | networking + SGs + tasks OK |
| 2 | RDS port times out from laptop | DB correctly private |
| 3 | register dup → 409, bad login → 401 | auth logic OK |
| 4 | object appears in `aws s3 ls` | IAM task role + presign + S3 OK |
| 5 | head-object shows right content-type/size | upload integrity OK |
| 6 | other user download → 403 | authorization/isolation OK |
| 7 | `/files` lists the file | RDS write+read OK |
| 8 | Lambda logs show invocation | S3→Lambda trigger OK |
| 9 | search filters + pagination correct | query layer OK |
| 10 | ECS logs show requests | observability OK |

If all 10 pass, your production system is genuinely working end to end — and
you've verified it at the infrastructure level, not just the API level.

---

## Then: destroy

```bash
cd infra/terraform && terraform destroy
```
Don't leave it running. See runbook Phase 6 for the verify-nothing-left checks.

Next: [21k — Decisions, cost, security & interview →](21k-decisions-cost-security-interview.md)
