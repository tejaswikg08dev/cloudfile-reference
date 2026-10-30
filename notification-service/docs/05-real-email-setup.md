# 05 — Real Email Setup (Mailtrap for local, SES for production)

By default the notification service uses the **console** provider — it only
logs + records notifications (no real email). This guide turns on REAL email.

You pick the provider with the `NOTIFICATION_PROVIDER` env var:
- `console` — logs only (default)
- `smtp` — sends via any SMTP server, e.g. **Mailtrap** (best for local)
- `ses` — sends via **AWS SES** (for production)

---

## Option A — Mailtrap (local, free, see emails instantly)

Mailtrap is a free "fake inbox" for testing. Emails you send land in a web
inbox you can view — nothing goes to real people. Perfect for local dev.

### 1. Create a free Mailtrap sandbox
1. Sign up at https://mailtrap.io (free).
2. Go to **Email Testing → Inboxes → My Inbox**.
3. Open **SMTP Settings** and choose **SMTP** (not the API). You'll see:
   ```
   Host:     sandbox.smtp.mailtrap.io
   Port:     2525
   Username: <your mailtrap username>
   Password: <your mailtrap password>
   ```

### 2. Put the creds in your environment
From the `notification-service` folder, export them in the shell you'll run
Docker Compose in (Git Bash):
```bash
export NOTIFICATION_PROVIDER=smtp
export SMTP_HOST=sandbox.smtp.mailtrap.io
export SMTP_PORT=2525
export SMTP_USERNAME=<your mailtrap username>
export SMTP_PASSWORD=<your mailtrap password>
export SMTP_SENDER=no-reply@cloudfile.example.com
export SMTP_USE_TLS=true
```
(These are read by `docker-compose.yml` via `${VAR}` substitution. You can also
put them in a `.env` file in the `notification-service` folder.)

### 3. Restart the notification service
```bash
docker compose down
docker compose up --build
```

### 4. Test it
Send a notification (needs a JWT — get one from the auth service login):
```bash
curl -X POST http://localhost:8004/api/v1/notifications/notify \
  -H "Authorization: Bearer <token>" -H 'Content-Type: application/json' \
  -d '{"recipient":"anyone@example.com","subject":"Hi","message":"Hello from CloudFile","channel":"email"}'
```
Now open your **Mailtrap inbox in the browser** — the email appears there.
The service logs show `notification_smtp_sent`.

> Mailtrap sandbox captures ALL mail, so `recipient` can be anything — it won't
> actually email that person; it lands in your Mailtrap inbox.

---

## Option B — AWS SES (production, free tier)

SES is AWS's email service. Free tier: ~3,000 messages/month for 12 months.
New accounts start in **sandbox mode**, where you can only send to/from
**verified** addresses (fine for a demo).

### 1. Verify a sender (and recipient, in sandbox)
1. AWS Console → **SES** → **Verified identities** → **Create identity**.
2. Verify an email you own as the **sender** (e.g. `you@gmail.com`). Click the
   confirmation link AWS emails you.
3. In sandbox, also verify any **recipient** address you'll send to.

### 2. Give the service permission
The ECS task role needs `ses:SendEmail`. The project's Terraform IAM can be
extended with:
```hcl
statement {
  actions   = ["ses:SendEmail", "ses:SendRawEmail"]
  resources = ["*"]
}
```
(Add to the ECS task role policy in `infra/terraform/iam.tf`.)

### 3. Configure the service
Set env on the deployed notification service:
```
NOTIFICATION_PROVIDER=ses
AWS_REGION=us-east-1
SES_SENDER=you@gmail.com        # a VERIFIED sender
```

### 4. Test
```bash
curl -X POST https://<your-notify-url>/api/v1/notifications/notify \
  -H "Authorization: Bearer <token>" -H 'Content-Type: application/json' \
  -d '{"recipient":"verified@you.com","subject":"Hi","message":"Hello","channel":"email"}'
```
A real email arrives at the verified recipient. Logs show `notification_ses_sent`.

> To send to ANY address (not just verified), request **production access** in
> the SES console (removes the sandbox). Not needed for a demo.

---

## How the provider is chosen (code)

`app/providers/factory.py` reads `NOTIFICATION_PROVIDER`:
```
console -> ConsoleProvider  (logs + DB record)
smtp    -> SMTPProvider     (Mailtrap / any SMTP)
ses     -> SESProvider      (AWS SES)
```
All three implement the same `NotificationProvider.send(...)` interface
(strategy pattern), and every notification is still recorded in the database
regardless of provider.

---

## Cost summary

| Provider | Cost | Use for |
|----------|------|---------|
| console | free | default local, no real email |
| smtp (Mailtrap) | free | local — see emails in a web inbox |
| ses | free tier ~3k/mo for 12 months | production real email |
| SMS | NOT free (per-message) | not implemented; skip |
