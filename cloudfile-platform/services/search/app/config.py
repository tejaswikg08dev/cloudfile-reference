"""Search service configuration."""
from __future__ import annotations

import os
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    service_name: str = "search"
    log_level: str = "INFO"

    database_url: str = (
        "postgresql+asyncpg://cloudfile:cloudfile@localhost:5432/cloudfile_files"
    )

    jwt_secret_key: str = "change-me-in-production-use-a-long-random-string"
    jwt_algorithm: str = "HS256"


@lru_cache
def get_settings() -> Settings:
    defaults = Settings()
    return Settings(
        database_url=os.getenv("SEARCH_DATABASE_URL", defaults.database_url),
        jwt_secret_key=os.getenv("JWT_SECRET_KEY", defaults.jwt_secret_key),
        jwt_algorithm=os.getenv("JWT_ALGORITHM", defaults.jwt_algorithm),
        log_level=os.getenv("LOG_LEVEL", defaults.log_level),
    )
