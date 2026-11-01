# 21h — A Request's Journey Through Live AWS

Now that it's deployed, let's follow a real **image upload** across the AWS
infrastructure, packet by packet (conceptually).

---

## The cast (who's involved)

- **You** (curl/browser) on the public internet
- **IGW** — the VPC's internet gateway
- **ECS SG** — firewall allowing 8001–8003
- **files task** — the running container (Fargate), with a public IP + the task
  IAM role
- **RDS** — Postgres, reachable only from the ECS SG
- **S3** — the uploads bucket
- **Lambda** — the processor, triggered by S3
- **CloudWatch** — collecting logs the whole time

---

## Step-by-step journey

### 1. Login (get a token)
```
curl POST http://<auth-ip>:8001/api/v1/auth/login
```
```
You ──internet──▶ IGW ──▶ [ECS SG: port 8001 allowed] ──▶ auth task
auth task ──▶ RDS (SELECT user; check bcrypt password)      (via RDS SG)
auth task ──▶ signs a JWT ──▶ returns { access_token }
```
You now hold a JWT (your pass).

### 2. Initiate upload
```
curl POST http://<files-ip>:8002/api/v1/files/upload  (Authorization: Bearer <token>)
```
```
You ──▶ IGW ──▶ [ECS SG: 8002] ──▶ files task
files task ── verifies the JWT locally (shared secret, no network hop)
files task ──▶ RDS: INSERT files row (status=pending)        (via RDS SG)
files task ── asks S3 (via boto3 + TASK ROLE) to presign a PUT URL
            (no network call; it just cryptographically signs a URL)
files task ──▶ returns { file_id, upload_url }
```
Key detail: boto3 uses the **task IAM role** to sign — no AWS keys in the app.

### 3. Upload the bytes (straight to S3, bypassing the service!)
```
curl PUT "<upload_url>"  --data-binary @cat.jpg
```
```
You ──internet──▶ S3 directly (the presigned URL points at s3.amazonaws.com)
S3 verifies the signature (valid, signed by the task role) ──▶ stores the object
```
Notice: the file bytes **never touch the files service**. The service only
handed you a signed link; you upload directly to S3. This is why the service
stays small, fast, and stateless.

### 4. Confirm
```
curl POST http://<files-ip>:8002/api/v1/files/confirm  (Bearer <token>)
```
```
You ──▶ IGW ──▶ files task
files task ──▶ RDS: UPDATE files SET status='ready'          (via RDS SG)
files task ── (would call notification service, but it's not deployed on AWS →
              logs "notification_skipped_no_url", no error)
files task ──▶ returns { status: "ready" }
```

### 5. S3 triggers the Lambda (asynchronous, behind the scenes)
```
S3 (object created under uploads/) ──event──▶ Lambda (processor)
   (allowed by aws_lambda_permission.allow_s3)
Lambda ── reads the object (via its IAM role) ── tries to make a thumbnail
   (skips if Pillow not bundled — degrades gracefully, no crash)
Lambda ── would UPDATE RDS, but it's not VPC-attached → skips DB update
```
This happens on its own, in parallel, without you waiting.

### 6. Search
```
curl GET http://<search-ip>:8003/api/v1/search?name=cat  (Bearer <token>)
```
```
You ──▶ IGW ──▶ [ECS SG: 8003] ──▶ search task
search task ──▶ RDS: SELECT ... WHERE owner_id=? AND filename ILIKE '%cat%'
search task ──▶ returns the paginated results
```

### 7. Download
```
curl GET http://<files-ip>:8002/api/v1/files/<id>/download  (Bearer <token>)
```
```
files task ── presigns a GET URL (task role) ──▶ returns { download_url }
You ──internet──▶ S3 directly ──▶ receive the file bytes
```

---

## The full picture (one diagram)

```
                    ┌──────────── VPC (10.0.0.0/16) ────────────┐
                    │                                           │
 You ──(1,2,4,6,7)──┼─▶ IGW ─▶[ECS SG]─▶ auth/files/search tasks │
     (HTTP + JWT)   │                         │  │               │
                    │                         │  └──▶ RDS (5432, via RDS SG)
                    │                         │                  │
                    └─────────────────────────┼──────────────────┘
                                              │
 You ──(3 upload, 7 download)──────────────▶  S3  (presigned URL, direct)
                                              │
                                   (5) ObjectCreated event
                                              ▼
                                           Lambda (processor)

 (logs from every task) ───────────────▶ CloudWatch
```

---

## Why this design is good (talking points)

- **Stateless services:** no files stored on the task; restart/scale freely.
- **Direct-to-S3:** heavy bytes bypass the app → cheap, fast, scalable.
- **IAM role, no keys:** the app proves its identity via the task role; no
  secrets in code.
- **DB locked down:** only the app's security group can reach Postgres.
- **Async processing:** Lambda does slow work off the request path.

---

## Check your understanding

- *Q: Do file bytes pass through the files service?* → No — straight to S3 via a
  presigned URL.
- *Q: How does the app authenticate to S3?* → The ECS task IAM role (no keys).
- *Q: Can the public reach RDS?* → No — only the ECS security group can.
- *Q: Is the Lambda part of the request?* → No — it fires asynchronously after
  S3 stores the object.

Next: [21i — Terraform → AWS Console map →](21i-terraform-to-console-map.md)
