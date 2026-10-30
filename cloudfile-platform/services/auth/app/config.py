"""Auth service configuration via Pydantic settings (twelve-factor).

Configuration is read from environment variables so the same image can run
in any environment. We use service-specific env var names (AUTH_DATABASE_URL)
so one shared .env file can configure every microservice.
"""
from __future__ import annotations

import os
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    service_name: str = "auth"
    log_level: str = "INFO"

    database_url: str = (
        "postgresql+asyncpg://cloudfile:cloudfile@localhost:5432/cloudfile_auth"
    )

    jwt_secret_key: str = "change-me-in-production-use-a-long-random-string"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 60


@lru_cache
def get_settings() -> Settings:
    """Cached settings accessor resolving service-specific env vars."""
    defaults = Settings()
    return Settings(
        database_url=os.getenv("AUTH_DATABASE_URL", defaults.database_url),
        jwt_secret_key=os.getenv("JWT_SECRET_KEY", defaults.jwt_secret_key),
        jwt_algorithm=os.getenv("JWT_ALGORITHM", defaults.jwt_algorithm),
        jwt_access_token_expire_minutes=int(
            os.getenv(
                "JWT_ACCESS_TOKEN_EXPIRE_MINUTES",
                str(defaults.jwt_access_token_expire_minutes),
            )
        ),
        log_level=os.getenv("LOG_LEVEL", defaults.log_level),
    )
