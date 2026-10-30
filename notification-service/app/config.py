"""Notification service configuration.

This is a standalone repository, so it does NOT depend on the monorepo's
`shared/` package. It carries its own small helpers.
"""
from __future__ import annotations

import os
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    service_name: str = "notification"
    log_level: str = "INFO"

    database_url: str = (
        "postgresql+asyncpg://notify:notify@localhost:5432/notifications"
    )

    jwt_secret_key: str = "change-me-use-a-long-random-string"
    jwt_algorithm: str = "HS256"

    # Which provider to use: "console" (local/dev) or "ses" (AWS).
    notification_provider: str = "console"
    aws_region: str = "us-east-1"
    ses_sender: str = "no-reply@cloudfile.example.com"


@lru_cache
def get_settings() -> Settings:
    defaults = Settings()
    return Settings(
        database_url=os.getenv("NOTIFICATION_DATABASE_URL", defaults.database_url),
        jwt_secret_key=os.getenv("JWT_SECRET_KEY", defaults.jwt_secret_key),
        jwt_algorithm=os.getenv("JWT_ALGORITHM", defaults.jwt_algorithm),
        notification_provider=os.getenv(
            "NOTIFICATION_PROVIDER", defaults.notification_provider
        ),
        aws_region=os.getenv("AWS_REGION", defaults.aws_region),
        ses_sender=os.getenv("SES_SENDER", defaults.ses_sender),
        log_level=os.getenv("LOG_LEVEL", defaults.log_level),
    )
