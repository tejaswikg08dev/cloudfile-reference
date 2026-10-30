"""Structured JSON logging configuration shared across services."""
from __future__ import annotations

import json
import logging
import sys
from datetime import datetime, timezone


class JsonFormatter(logging.Formatter):
    """Render log records as single-line JSON."""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, object] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        standard = set(logging.LogRecord("", 0, "", 0, "", None, None).__dict__)
        standard.update({"message", "asctime"})
        for key, value in record.__dict__.items():
            if key not in standard and not key.startswith("_"):
                payload[key] = value

        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)

        return json.dumps(payload, default=str)


_configured = False


def configure_logging(level: str = "INFO") -> None:
    """Configure root logging once with JSON output to stdout."""
    global _configured
    if _configured:
        return

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())

    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(level.upper())

    _configured = True


def get_logger(name: str) -> logging.Logger:
    """Return a logger, ensuring logging is configured."""
    if not _configured:
        configure_logging()
    return logging.getLogger(name)
