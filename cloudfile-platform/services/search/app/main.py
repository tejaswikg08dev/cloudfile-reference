"""Search service FastAPI application entry point."""
from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI

from shared.db_init import create_all_safe
from shared.exceptions import install_exception_handlers
from shared.logging_config import configure_logging, get_logger

from .config import get_settings
from .database import Base, engine
from .router import router

settings = get_settings()
configure_logging(settings.log_level)
logger = get_logger("search.main")


@asynccontextmanager
async def lifespan(_: FastAPI):
    # Search READS the `files` table owned by the files service. In local/dev,
    # whichever service starts first creates the shared table; create_all_safe
    # is idempotent and race-safe, so it's fine for search to ensure it too.
    # In production, Alembic (run for the files service) owns this schema and
    # DB_AUTO_CREATE should be false.
    await create_all_safe(engine, Base.metadata)
    logger.info("search_service_started")
    yield
    await engine.dispose()
    logger.info("search_service_stopped")


app = FastAPI(title="CloudFile Search Service", version="1.0.0", lifespan=lifespan)

install_exception_handlers(app)
app.include_router(router)


@app.get("/health", tags=["health"])
async def health() -> dict[str, str]:
    return {"status": "ok", "service": settings.service_name}
