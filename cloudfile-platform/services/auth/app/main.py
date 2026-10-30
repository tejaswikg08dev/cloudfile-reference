"""Auth service FastAPI application entry point."""
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
logger = get_logger("auth.main")


@asynccontextmanager
async def lifespan(_: FastAPI):
    # In local/dev we create tables on startup (idempotent + race-safe across
    # gunicorn workers). In production, Alembic owns the schema; disable this
    # with DB_AUTO_CREATE=false and run `alembic upgrade head` instead.
    await create_all_safe(engine, Base.metadata)
    logger.info("auth_service_started")
    yield
    await engine.dispose()
    logger.info("auth_service_stopped")


app = FastAPI(
    title="CloudFile Auth Service",
    version="1.0.0",
    lifespan=lifespan,
)

install_exception_handlers(app)
app.include_router(router)


@app.get("/health", tags=["health"])
async def health() -> dict[str, str]:
    """Liveness/readiness probe endpoint."""
    return {"status": "ok", "service": settings.service_name}
