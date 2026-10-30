"""Thin wrapper around boto3 S3 for presigned URLs.

boto3 is synchronous. We keep the surface tiny and call it from async code
via run_in_threadpool in the service layer to avoid blocking the event loop.
"""
from __future__ import annotations

import boto3
from botocore.config import Config

from .config import get_settings


def _build_client():
    settings = get_settings()
    return boto3.client(
        "s3",
        region_name=settings.aws_region,
        endpoint_url=settings.s3_endpoint_url,
        aws_access_key_id=settings.aws_access_key_id,
        aws_secret_access_key=settings.aws_secret_access_key,
        config=Config(signature_version="s3v4"),
    )


class S3Client:
    def __init__(self) -> None:
        self._settings = get_settings()
        self._client = _build_client()

    @property
    def bucket(self) -> str:
        return self._settings.s3_bucket_name

    def generate_upload_url(self, key: str, content_type: str) -> str:
        return self._client.generate_presigned_url(
            "put_object",
            Params={
                "Bucket": self.bucket,
                "Key": key,
                "ContentType": content_type,
            },
            ExpiresIn=self._settings.presigned_url_expire_seconds,
        )

    def generate_download_url(self, key: str) -> str:
        return self._client.generate_presigned_url(
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
