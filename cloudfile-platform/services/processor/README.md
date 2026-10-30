# Processor Lambda

S3-triggered function that generates thumbnails for images and updates file
metadata in PostgreSQL.

## Trigger

Configured via S3 bucket notification on `s3:ObjectCreated:*` (see
`infra/terraform/lambda.tf` and `s3.tf`). Objects under the `thumbnails/`
prefix are ignored to prevent recursive invocations.

## Environment variables

| Name | Purpose |
|------|---------|
| `S3_ENDPOINT_URL` | Optional; set for LocalStack testing |
| `PROCESSOR_DATABASE_URL` | psycopg2 DSN for the files DB (optional locally) |

## Packaging

The deployment package is built by Terraform (`archive_file`) or can be zipped
manually:

```bash
pip install -r requirements.txt -t build/
cp handler.py image_utils.py build/
cd build && zip -r ../processor.zip .
```

## Local testing

Use LocalStack. See `scripts/init-localstack.sh` in the repo root, which can
register the bucket and (optionally) the Lambda.
