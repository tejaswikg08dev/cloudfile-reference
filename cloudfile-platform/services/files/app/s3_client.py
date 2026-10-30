"""Thin wrapper around boto3 S3 for presigned URLs.

boto3 is synchronous. We keep the surface tiny and call it from async code
via run_in_threadpool in the service layer to avoid blocking the event loop.

LocalStack note:
- The service reaches S3 at `s3_endpoint_url` (inside Docker: localstack:4566).
- A browser can't resolve `localstack`, so presigned URLs must point at a
  host-reachable address (localhost:4566). We sign presigned URLs with a
  SEPARATE client bound to `s3_public_endpoint_url`. Generating a presigned URL
  does not make a network call, so signing against the public endpoint is fine
  and yields a URL the browser can actually use. For real AWS, leave
  `s3_public_endpoint_url` unset and both clients are identical.
"""
from __future__ import annotations

import boto3
from botocore.config import Config

from .config import get_settings


def _build_client(endpoint_url: str | None):
    settings = get_settings()
    return boto3.client(
        "s3",
        region_name=settings.aws_region,
        endpoint_url=endpoint_url,
        aws_access_key_id=settings.aws_access_key_id,
        aws_secret_access_key=settings.aws_secret_access_key,
        config=Config(signature_version="s3v4"),
    )


class S3Client:
    def __init__(self) -> None:
        self._settings = get_settings()
        # Operational client (bucket create/delete, head) uses the internal
        # endpoint the service can actually reach.
        self._client = _build_client(self._settings.s3_endpoint_url)
        # Signing client for presigned URLs uses the public endpoint if set,
        # so the returned URL is reachable from the client's browser.
        public = self._settings.s3_public_endpoint_url or self._settings.s3_endpoint_url
        self._sign_client = _build_client(public)

    @property
    def bucket(self) -> str:
        return self._settings.s3_bucket_name

    def generate_upload_url(self, key: str, content_type: str) -> str:
        return self._sign_client.generate_presigned_url(
            "put_object",
            Params={
                "Bucket": self.bucket,
                "Key": key,
                "ContentType": content_type,
            },
            ExpiresIn=self._settings.presigned_url_expire_seconds,
        )

    def generate_download_url(self, key: str) -> str:
        return self._sign_client.generate_presigned_url(
            "get_object",
            Params={"Bucket": self.bucket, "Key": key},
            ExpiresIn=self._settings.presigned_url_expire_seconds,
        )

    def delete_object(self, key: str) -> None:
        self._client.delete_object(Bucket=self.bucket, Key=key)

    def ensure_bucket(self) -> None:
        """Create the bucket if it does not exist (used for LocalStack/dev)."""
        try:
            self._client.head_bucket(Bucket=self.bucket)
        except Exception:
            self._client.create_bucket(Bucket=self.bucket)
