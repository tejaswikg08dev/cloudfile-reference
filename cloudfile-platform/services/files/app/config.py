"""Files service configuration."""
from __future__ import annotations

import os
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    service_name: str = "files"
    log_level: str = "INFO"

    database_url: str = (
        "postgresql+asyncpg://cloudfile:cloudfile@localhost:5432/cloudfile_files"
    )

    jwt_secret_key: str = "change-me-in-production-use-a-long-random-string"
    jwt_algorithm: str = "HS256"

    # S3 / object storage
    s3_bucket_name: str = "cloudfile-uploads"
    s3_endpoint_url: str | None = None  # LocalStack in dev; None uses real AWS
    aws_region: str = "us-east-1"
    aws_access_key_id: str = "test"
    aws_secret_access_key: str = "test"
    presigned_url_expire_seconds: int = 3600

    # Inter-service
    notification_service_url: str | None = None


@lru_cache
def get_settings() -> Settings:
    defaults = Settings()
    return Settings(
        database_url=os.getenv("FILES_DATABASE_URL", defaults.database_url),
        jwt_secret_key=os.getenv("JWT_SECRET_KEY", defaults.jwt_secret_key),
        jwt_algorithm=os.getenv("JWT_ALGORITHM", defaults.jwt_algorithm),
        s3_bucket_name=os.getenv("S3_BUCKET_NAME", defaults.s3_bucket_name),
        s3_endpoint_url=os.getenv("S3_ENDPOINT_URL") or None,
        aws_region=os.getenv("AWS_REGION", defaults.aws_region),
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID", defaults.aws_access_key_id),
        aws_secret_access_key=os.getenv(
            "AWS_SECRET_ACCESS_KEY", defaults.aws_secret_access_key
        ),
        presigned_url_expire_seconds=int(
            os.getenv(
                "PRESIGNED_URL_EXPIRE_SECONDS",
                str(defaults.presigned_url_expire_seconds),
            )
        ),
        notification_service_url=os.getenv("NOTIFICATION_SERVICE_URL") or None,
        log_level=os.getenv("LOG_LEVEL", defaults.log_level),
    )
