"""Files service FastAPI application entry point."""
from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI

from shared.db_init import create_all_safe
from shared.exceptions import install_exception_handlers
from shared.logging_config import configure_logging, get_logger

from .config import get_settings
from .database import Base, engine
from .dependencies import get_s3_client
from .router import router

settings = get_settings()
configure_logging(settings.log_level)
logger = get_logger("files.main")


@asynccontextmanager
async def lifespan(_: FastAPI):
    await create_all_safe(engine, Base.metadata)
    # Ensure the bucket exists (useful for LocalStack/dev).
    try:
        get_s3_client().ensure_bucket()
    except Exception as exc:  # noqa: BLE001
        logger.warning("bucket_ensure_failed", extra={"error": str(exc)})
    logger.info("files_service_started")
    yield
    await engine.dispose()
    logger.info("files_service_stopped")


app = FastAPI(title="CloudFile Files Service", version="1.0.0", lifespan=lifespan)

install_exception_handlers(app)
app.include_router(router)


@app.get("/health", tags=["health"])
async def health() -> dict[str, str]:
    return {"status": "ok", "service": settings.service_name}
