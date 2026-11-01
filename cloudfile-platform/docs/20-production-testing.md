# 20 — Production Testing (after AWS deployment)

You've deployed to AWS with `docs/19-aws-deploy-runbook.md`. This guide tests
the live system — upload a real image/file, verify it in real S3, search, and
download — then reminds you to destroy.

Run everything in **Git Bash** from `cloudfile-reference/cloudfile-platform`.

> 💸 When finished, run **Phase 8 (destroy)**. Leaving ECS Fargate running bills
> by the second.

---

## Step 1 — Get the public IPs of your services

```bash
REGION=us-east-1

get_ip() {
  local svc=$1 task eni
  task=$(aws ecs list-tasks --cluster cloudfile-cluster --service-name cloudfile-$svc \
    --region $REGION --query 'taskArns[0]' --output text)
  eni=$(aws ecs describe-tasks --cluster cloudfile-cluster --tasks $task --region $REGION \
    --query 'tasks[0].attachments[0].details[?name==`networkInterfaceId`].value' --output text)
  aws ec2 describe-network-interfaces --network-interface-ids $eni --region $REGION \
    --query 'NetworkInterfaces[0].Association.PublicIp' --output text
}

AUTH_IP=$(get_ip auth)
FILES_IP=$(get_ip files)
SEARCH_IP=$(get_ip search)

echo "AUTH:   http://$AUTH_IP:8001"
echo "FILES:  http://$FILES_IP:8002"
echo "SEARCH: http://$SEARCH_IP:8003"
```

Sanity check:
```bash
curl http://$AUTH_IP:8001/health
curl http://$FILES_IP:8002/health
curl http://$SEARCH_IP:8003/health
```
Each returns `{"status":"ok","service":"..."}`.

---

## Step 2 — Register + login (get your token)

```bash
curl -s -X POST http://$AUTH_IP:8001/api/v1/auth/register \
  -H 'Content-Type: application/json' \
  -d '{"email":"me@example.com","password":"password123","full_name":"Me"}'

TOKEN=$(curl -s -X POST http://$AUTH_IP:8001/api/v1/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"email":"me@example.com","password":"password123"}' \
  | grep -o '"access_token":"[^"]*"' | sed 's/"access_token":"//; s/"//')
echo "$TOKEN"
```

---

## Step 3 — Prepare a file/image and get its EXACT size

```bash
cp /c/Users/<you>/Pictures/cat.jpg ./cat.jpg     # use any real file
SIZE=$(stat -c %s cat.jpg)
echo "size: $SIZE"
```

> On real AWS, `size_bytes` should be the EXACT byte size (AWS is strict, unlike
> LocalStack). Any file type works: `image/jpeg`, `image/png`, `video/mp4`,
> `text/plain`, `application/pdf`. Max 100 MB.

---

## Step 4 — Initiate the upload

```bash
RESP=$(curl -s -X POST http://$FILES_IP:8002/api/v1/files/upload \
  -H "Authorization: Bearer $TOKEN" -H 'Content-Type: application/json' \
  -d "{\"filename\":\"cat.jpg\",\"content_type\":\"image/jpeg\",\"size_bytes\":$SIZE}")
echo "$RESP"

FILE_ID=$(echo "$RESP" | grep -o '"file_id":"[^"]*"' | sed 's/"file_id":"//; s/"//')
UPLOAD_URL=$(echo "$RESP" | grep -o '"upload_url":"[^"]*"' | sed 's/"upload_url":"//; s/"//')
echo "file_id:    $FILE_ID"
echo "upload_url: $UPLOAD_URL"
```

The `upload_url` is now a REAL S3 URL (`https://cloudfile-uploads-xxxx.s3.amazonaws.com/...`).

---

## Step 5 — Upload the bytes to real S3

```bash
curl -X PUT "$UPLOAD_URL" -H "Content-Type: image/jpeg" --data-binary @cat.jpg
```
No error = stored in real AWS S3.

> The `Content-Type` here MUST match Step 4 exactly, or S3 rejects the signature.

---

## Step 6 — Confirm the upload

```bash
curl -s -X POST http://$FILES_IP:8002/api/v1/files/confirm \
  -H "Authorization: Bearer $TOKEN" -H 'Content-Type: application/json' \
  -d "{\"file_id\":\"$FILE_ID\"}"
# expect "status":"ready"
```

---

## Step 7 — Verify it's really in S3 (the proof)

```bash
BUCKET=$(cd infra/terraform && terraform output -raw s3_bucket_name && cd - >/dev/null)
aws s3 ls "s3://$BUCKET/uploads/" --recursive
```
You'll see your `cat.jpg` object. Also visible in AWS Console → S3 → your bucket
→ `uploads/`. Take a screenshot — great interview evidence.

---

## Step 8 — List, search, download

```bash
# List
curl -s http://$FILES_IP:8002/api/v1/files -H "Authorization: Bearer $TOKEN"

# Search
curl -s "http://$SEARCH_IP:8003/api/v1/search?name=cat" -H "Authorization: Bearer $TOKEN"

# Download round-trip
DL=$(curl -s "http://$FILES_IP:8002/api/v1/files/$FILE_ID/download" \
  -H "Authorization: Bearer $TOKEN" \
  | grep -o '"download_url":"[^"]*"' | sed 's/"download_url":"//; s/"//')
curl -s "$DL" --output downloaded-cat.jpg
ls -la downloaded-cat.jpg      # same size as cat.jpg = success
```
Open the `download_url` in a browser → the image displays, served from S3.

---

## Testing with Postman (production)

1. Import the collection + **CloudFile — Production** environment from
   `postman/` (if not already).
2. Edit the production environment URLs:
   - `auth_url`   = `http://<AUTH_IP>:8001`
   - `files_url`  = `http://<FILES_IP>:8002`
   - `search_url` = `http://<SEARCH_IP>:8003`
3. Run folders in order: **Login** → **Initiate upload** →
   **PUT bytes** (Body → **binary** → Select File; Header `Content-Type:
   image/jpeg`) → **Confirm** → **List** → **Search**.

---

## Local vs Production differences

| Thing | Local | Production |
|-------|-------|------------|
| Storage | LocalStack (fake S3) | Real AWS S3 |
| Presigned URL host | localhost:4566 | real s3.amazonaws.com |
| `size_bytes` | lenient | must be exact |
| `Content-Type` on PUT | lenient | must match exactly |
| Verify object | n/a | `aws s3 ls` / S3 Console |
| Notification | Mailtrap/console | skipped (notification not deployed on AWS) |
| Thumbnail | none | Lambda runs but skips without Pillow layer; file still fine |

---

## Viewing logs in production

```bash
# tail a service's logs
aws logs tail /ecs/cloudfile-files --follow --region us-east-1
aws logs tail /ecs/cloudfile-auth  --follow --region us-east-1
```
Or AWS Console → CloudWatch → Log groups → `/ecs/cloudfile-*`.

---

## Troubleshooting (production specifics)

| Symptom | Fix |
|---------|-----|
| S3 PUT `SignatureDoesNotMatch` | `Content-Type` in PUT must equal the `content_type` from Step 4 |
| S3 PUT `EntityTooLarge` / size error | `size_bytes` must equal the real file size (`stat -c %s file`) |
| `InvalidAccessKeyId` in files logs | ensure you pushed the latest `files` image (uses IAM role, not dummy keys) |
| download link 403 / expired | links expire (default 1h); request a fresh one via /download |
| can't reach the IP | task must be RUNNING; security group opens 8001–8003 |

---

## Step 9 — DESTROY when done (don't skip!)

```bash
cd cloudfile-reference/cloudfile-platform/infra/terraform
terraform destroy          # type: yes
```
Verify nothing remains (see runbook Phase 6). This stops all billing.

---

## What you proved

- A real microservices app deployed on AWS (ECS Fargate + RDS + S3 + Lambda).
- End-to-end file/image upload to **real S3** via presigned URLs.
- Auth, search, and download all working against the live system.
- Clean teardown with a single command (cost control).

Screenshots to keep: `terraform output`, the S3 Console with your object, a
successful upload+confirm response, and CloudWatch logs.
