"""Standard API response envelopes shared across services."""
from __future__ import annotations

from typing import Any, Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class SuccessResponse(BaseModel, Generic[T]):
    """Envelope for successful responses."""

    success: bool = True
    data: T


class ErrorDetail(BaseModel):
    """Machine-readable error information."""

    code: str
    message: str
    details: Any | None = None


class ErrorResponse(BaseModel):
    """Envelope for error responses."""

    success: bool = False
    error: ErrorDetail


def ok(data: Any) -> dict[str, Any]:
    """Build a success response body."""
    return {"success": True, "data": data}


def err(code: str, message: str, details: Any | None = None) -> dict[str, Any]:
    """Build an error response body."""
    return {
        "success": False,
        "error": {"code": code, "message": message, "details": details},
    }
