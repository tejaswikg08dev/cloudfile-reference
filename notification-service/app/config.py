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

    # Which provider to use: "console" (local/dev), "smtp" (Mailtrap/any SMTP),
    # or "ses" (AWS SES).
    notification_provider: str = "console"

    # AWS SES (production)
    aws_region: str = "us-east-1"
    ses_sender: str = "no-reply@cloudfile.example.com"

    # SMTP (Mailtrap or any SMTP server) — for seeing real emails locally.
    smtp_host: str = "sandbox.smtp.mailtrap.io"
    smtp_port: int = 2525
    smtp_username: str = ""
    smtp_password: str = ""
    smtp_sender: str = "no-reply@cloudfile.example.com"
    smtp_use_tls: bool = True


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
        smtp_host=os.getenv("SMTP_HOST", defaults.smtp_host),
        smtp_port=int(os.getenv("SMTP_PORT", str(defaults.smtp_port))),
        smtp_username=os.getenv("SMTP_USERNAME", defaults.smtp_username),
        smtp_password=os.getenv("SMTP_PASSWORD", defaults.smtp_password),
        smtp_sender=os.getenv("SMTP_SENDER", defaults.smtp_sender),
        smtp_use_tls=os.getenv("SMTP_USE_TLS", "true").lower()
        in ("1", "true", "yes"),
        log_level=os.getenv("LOG_LEVEL", defaults.log_level),
    )
