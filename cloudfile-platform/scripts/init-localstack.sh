#!/bin/bash
# Initialize LocalStack resources for local development.
# Creates the S3 bucket used by the files service.
set -euo pipefail

BUCKET="${S3_BUCKET_NAME:-cloudfile-uploads}"
ENDPOINT="${S3_ENDPOINT_URL:-http://localhost:4566}"

echo "Creating S3 bucket '$BUCKET' at $ENDPOINT"

# awslocal is available inside the LocalStack container; fall back to aws CLI.
if command -v awslocal >/dev/null 2>&1; then
	awslocal s3 mb "s3://$BUCKET" || true
else
	aws --endpoint-url "$ENDPOINT" s3 mb "s3://$BUCKET" || true
fi

echo "LocalStack init complete"
