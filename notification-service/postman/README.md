# Postman — Notification Service

Standalone collection for testing the notification service on its own.

## Files
- `Notification.postman_collection.json` — health, get-token, notify, list.
- `Notification.local.postman_environment.json` — local URLs.
- `Notification.production.postman_environment.json` — edit with your deployed URLs.

## Import
1. Postman → **Import** → select the collection + an environment.
2. Pick the environment in the top-right dropdown.

## Run
1. **Health** — confirm the service is up on 8004.
2. **Get token (via auth)** — logs into the platform's auth service (8001) and
   saves `{{token}}`. (Register that user in auth first if it doesn't exist.)
   - If you're running notification WITHOUT the platform, skip this and paste a
     JWT signed with the same `JWT_SECRET_KEY` into the `token` variable.
3. **Send notification** — posts a notification (expects 201, status `sent`).
4. **List my notifications** — lists notifications for your email.

> Why a token is needed: `/notify` is authenticated so only trusted callers
> (like the files service) can send notifications. It verifies the JWT with the
> shared `JWT_SECRET_KEY`.
