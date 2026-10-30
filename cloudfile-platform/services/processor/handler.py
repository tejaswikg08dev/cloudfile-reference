"""AWS Lambda: process files after they land in S3.

Triggered by S3 ObjectCreated events. For images it generates a thumbnail and
uploads it back to S3 under a `thumbnails/` prefix. It then updates the file's
status/metadata in the database.

Kept dependency-light so the deployment package stays small.
"""
from __future__ import annotations

import io
import json
import logging
import os
import urllib.parse

import boto3

logger = logging.getLogger()
logger.setLevel(logging.INFO)

THUMBNAIL_SIZE = (256, 256)
IMAGE_TYPES = {"image/jpeg", "image/png", "image/gif", "image/webp"}

_s3 = boto3.client("s3", endpoint_url=os.getenv("S3_ENDPOINT_URL") or None)


def _make_thumbnail(data: bytes) -> bytes | None:
    """Generate a thumbnail; returns None if Pillow/processing is unavailable."""
    try:
        from PIL import Image  # imported lazily so non-image events are cheap
    except ImportError:
        logger.warning("Pillow not available; skipping thumbnail")
        return None

    try:
        img = Image.open(io.BytesIO(data))
        img.thumbnail(THUMBNAIL_SIZE)
        out = io.BytesIO()
        fmt = img.format or "PNG"
        img.save(out, format=fmt)
        return out.getvalue()
    except Exception as exc:  # noqa: BLE001
        logger.warning("thumbnail generation failed: %s", exc)
        return None


def _thumbnail_key(key: str) -> str:
    return f"thumbnails/{key}"


def handler(event: dict, _context: object) -> dict:
    """Lambda entry point."""
    records = event.get("Records", [])
    processed = 0

    for record in records:
        bucket = record["s3"]["bucket"]["name"]
        raw_key = record["s3"]["object"]["key"]
        key = urllib.parse.unquote_plus(raw_key)

        # Avoid recursive triggers on thumbnails we create.
        if key.startswith("thumbnails/"):
            continue

        logger.info("processing s3://%s/%s", bucket, key)

        head = _s3.head_object(Bucket=bucket, Key=key)
        content_type = head.get("ContentType", "application/octet-stream")

        thumb_key: str | None = None
        if content_type in IMAGE_TYPES:
            obj = _s3.get_object(Bucket=bucket, Key=key)
            data = obj["Body"].read()
            thumb = _make_thumbnail(data)
            if thumb is not None:
                thumb_key = _thumbnail_key(key)
                _s3.put_object(
                    Bucket=bucket,
                    Key=thumb_key,
                    Body=thumb,
                    ContentType=content_type,
                )
                logger.info("thumbnail written to %s", thumb_key)

        _update_database(key, content_type, head.get("ContentLength", 0), thumb_key)
        processed += 1

    return {"statusCode": 200, "body": json.dumps({"processed": processed})}


def _update_database(
    s3_key: str, content_type: str, size_bytes: int, thumbnail_key: str | None
) -> None:
    """Update file metadata in PostgreSQL using a synchronous driver.

    Uses psycopg2 if available. In local LocalStack testing the DB update may
    be skipped if no connection string is configured.
    """
    dsn = os.getenv("PROCESSOR_DATABASE_URL")
    if not dsn:
        logger.info("no PROCESSOR_DATABASE_URL set; skipping DB update")
        return

    try:
        import psycopg2
    except ImportError:
        logger.warning("psycopg2 not available; skipping DB update")
        return

    conn = psycopg2.connect(dsn)
    try:
        with conn, conn.cursor() as cur:
            cur.execute(
                """
                UPDATE files
                SET status = 'processed',
                    content_type = %s,
                    size_bytes = %s,
                    thumbnail_key = COALESCE(%s, thumbnail_key)
                WHERE s3_key = %s
                """,
                (content_type, size_bytes, thumbnail_key, s3_key),
            )
        logger.info("db updated for %s", s3_key)
    finally:
        conn.close()
