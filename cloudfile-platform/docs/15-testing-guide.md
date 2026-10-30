# 15 — Testing Guide (Postman, e2e script, automated tests)

Three ways to test CloudFile, from easiest to most thorough.

---

## A. Postman (manual / exploratory)

### Platform collection (auth + files + search + notification)
Location: `cloudfile-platform/postman/`
- `CloudFile.postman_collection.json`
- `CloudFile.local.postman_environment.json`
- `CloudFile.production.postman_environment.json`

Steps:
1. Postman → Import → select the collection + an environment.
2. Choose **CloudFile — Local** in the environment dropdown.
3. Run folders in order:
   - **0. Health checks** → all four services `ok`
   - **1. Auth** → Register, then Login (auto-saves `{{token}}`)
   - **2. Files** → Initiate upload (auto-saves `{{file_id}}`, `{{upload_url}}`)
     → PUT bytes → Confirm → List → Download → Delete
   - **3. Search** → by name / all
   - **4. Notification** → send + list
4. Or use the **Collection Runner** to run everything at once.

### Notification-only collection (standalone)
Location: `notification-service/postman/`
Use when testing that service in isolation. Run **Get token (via auth)** first
(needs the platform's auth on 8001), then **Send / List**.

### Production
Duplicate the production environment, replace the `*_url` values with your
deployed addresses, select it, and run the same requests.

---

## B. End-to-end script (one command)

Location: `cloudfile-platform/scripts/e2e-demo.sh`

```bash
cd cloudfile-platform
bash scripts/e2e-demo.sh
```

Runs: health → register → login → upload → PUT to S3 → confirm → list →
search → list notifications, printing ✓ for each step.

- `jq` is **optional** — the script has a built-in JSON fallback. Installing
  `jq` just gives nicer parsing (`winget install jqlang.jq`, then restart the
  terminal).
- Override targets with env vars if needed:
  ```bash
  AUTH_URL=http://localhost:8001 NOTIFY_URL=http://localhost:8004 bash scripts/e2e-demo.sh
  ```

---

## C. Automated unit/API tests (pytest)

Fast, no Docker needed (in-memory SQLite + fakes).

Platform (run each service from its own dir):
```bash
cd cloudfile-platform/services/auth   && pip install -r requirements-dev.txt && PYTHONPATH=.:../.. pytest && cd -
cd cloudfile-platform/services/files  && pip install -r requirements-dev.txt && PYTHONPATH=.:../.. pytest && cd -
cd cloudfile-platform/services/search && pip install -r requirements-dev.txt && PYTHONPATH=.:../.. pytest && cd -
```
Notification:
```bash
cd notification-service && pip install -r requirements-dev.txt && pytest
```

What's covered: health, auth (register/login/me + error cases), files
(full upload→confirm→list→download→delete, size cap, cross-user 403), search
(owner-only, filters, pagination), notification (notify + list, invalid channel).

See [08-testing.md](08-testing.md) for details and how to add tests.

---

## Which should I use?

| Goal | Use |
|------|-----|
| Click around, see requests/responses | Postman |
| Prove the whole flow works in 10 seconds | e2e script |
| Catch regressions in logic (CI) | pytest |

In CI, pytest runs automatically on every push (see `.github/workflows/ci.yml`).
