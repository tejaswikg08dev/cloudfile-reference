"""Image helper utilities for the processor Lambda.

Separated from handler.py so the logic is unit-testable without S3.
"""
from __future__ import annotations

import io

THUMBNAIL_SIZE = (256, 256)


def generate_thumbnail(data: bytes, size: tuple[int, int] = THUMBNAIL_SIZE) -> bytes | None:
    """Return thumbnail bytes for the given image, or None on failure."""
    try:
        from PIL import Image
    except ImportError:
        return None

    try:
        img = Image.open(io.BytesIO(data))
        img.thumbnail(size)
        out = io.BytesIO()
        fmt = img.format or "PNG"
        img.save(out, format=fmt)
        return out.getvalue()
    except Exception:
        return None
