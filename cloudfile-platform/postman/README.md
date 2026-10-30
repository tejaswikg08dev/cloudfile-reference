# Postman Collection

Test the entire CloudFile system from Postman.

## Files

- `CloudFile.postman_collection.json` — all requests for auth, files, search,
  and the notification service.
- `CloudFile.local.postman_environment.json` — local URLs + variables.
- `CloudFile.production.postman_environment.json` — edit with your deployed URLs.

## Import

1. Open Postman → **Import** → select the collection + the environment(s).
2. Top-right environment dropdown → choose **CloudFile — Local** (or
   **CloudFile — Production** after editing its URLs).

## Run the full flow (in order)

The collection is ordered so you can run it top to bottom:

1. **0. Health checks** — confirm all four services are up.
2. **1. Auth → Register** then **Login** — login auto-saves the JWT to `{{token}}`.
3. **2. Files → Initiate upload** — auto-saves `{{file_id}}`, `{{upload_url}}`.
4. **PUT bytes to presigned URL** — uploads the content to S3 (LocalStack).
5. **Confirm upload** — marks the file ready and fires a notification.
6. **List / Download / Delete** — manage the file.
7. **3. Search** — query your files.
8. **4. Notification** — send + list notifications.

Tip: use Postman's **Collection Runner** to execute the whole thing at once.

## Notes

- Requests that need auth already include `Authorization: Bearer {{token}}`.
  Just run **Login** first and the token is captured automatically.
- The presigned URL (`{{upload_url}}`) points at `localhost:4566` (LocalStack),
  so the **PUT bytes** request works from your machine.
- For a deployed environment, duplicate the local environment and replace the
  `*_url` values with your deployed addresses.
