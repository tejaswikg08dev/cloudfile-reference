"""Search service FastAPI application entry point."""
from __future__ import annotations

from fastapi import FastAPI

from shared.exceptions import install_exception_handlers
from shared.logging_config import configure_logging

from .config import get_settings
from .router import router

settings = get_settings()
configure_logging(settings.log_level)

app = FastAPI(title="CloudFile Search Service", version="1.0.0")

install_exception_handlers(app)
app.include_router(router)


@app.get("/health", tags=["health"])
async def health() -> dict[str, str]:
    return {"status": "ok", "service": settings.service_name}
