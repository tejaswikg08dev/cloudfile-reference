"""Notification service FastAPI application entry point."""
from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI

from .config import get_settings
from .database import Base, engine
from .exceptions import install_exception_handlers
from .logging_config import configure_logging, get_logger
from .router import router

settings = get_settings()
configure_logging(settings.log_level)
logger = get_logger("notification.main")


@asynccontextmanager
async def lifespan(_: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("notification_service_started")
    yield
    await engine.dispose()
    logger.info("notification_service_stopped")


app = FastAPI(
    title="CloudFile Notification Service",
    version="1.0.0",
    lifespan=lifespan,
)

install_exception_handlers(app)
app.include_router(router)


@app.get("/health", tags=["health"])
async def health() -> dict[str, str]:
    return {"status": "ok", "service": settings.service_name}
