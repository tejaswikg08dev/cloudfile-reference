"""Exceptions + handlers (standalone copy for this repo)."""
from __future__ import annotations

from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from .logging_config import get_logger

logger = get_logger(__name__)


def _err(code: str, message: str, details: Any | None = None) -> dict[str, Any]:
    return {"success": False, "error": {"code": code, "message": message, "details": details}}


class AppError(Exception):
    status_code: int = 400
    code: str = "app_error"

    def __init__(
        self,
        message: str,
        *,
        status_code: int | None = None,
        code: str | None = None,
        details: Any | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        if status_code is not None:
            self.status_code = status_code
        if code is not None:
            self.code = code
        self.details = details


class UnauthorizedError(AppError):
    status_code = 401
    code = "unauthorized"


def install_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def _handle_app_error(_: Request, exc: AppError) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content=_err(exc.code, exc.message, exc.details),
        )

    @app.exception_handler(RequestValidationError)
    async def _handle_validation(_: Request, exc: RequestValidationError) -> JSONResponse:
        return JSONResponse(
            status_code=422, content=_err("validation_error", "Request validation failed", exc.errors())
        )

    @app.exception_handler(StarletteHTTPException)
    async def _handle_http(_: Request, exc: StarletteHTTPException) -> JSONResponse:
        return JSONResponse(status_code=exc.status_code, content=_err("http_error", str(exc.detail)))

    @app.exception_handler(Exception)
    async def _handle_unexpected(_: Request, exc: Exception) -> JSONResponse:
        logger.exception("unexpected_error", exc_info=exc)
        return JSONResponse(status_code=500, content=_err("internal_error", "An unexpected error occurred"))
