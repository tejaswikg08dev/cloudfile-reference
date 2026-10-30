# ---- Build stage ----
FROM python:3.11-slim AS builder

WORKDIR /app

# Install build deps only in this stage.
RUN apt-get update && apt-get install -y --no-install-recommends gcc \
    && rm -rf /var/lib/apt/lists/*

COPY services/auth/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# ---- Runtime stage ----
FROM python:3.11-slim AS runtime

# Create a non-root user for security.
RUN useradd --create-home --uid 1000 appuser

WORKDIR /app

# Copy installed packages from the builder.
COPY --from=builder /install /usr/local

# Copy shared library and the service code.
COPY shared /app/shared
COPY services/auth/app /app/app
COPY services/auth/alembic /app/alembic
COPY services/auth/alembic.ini /app/alembic.ini

ENV PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    PORT=8001

USER appuser

EXPOSE 8001

# Gunicorn with uvicorn workers for production serving.
CMD ["gunicorn", "app.main:app", \
     "--worker-class", "uvicorn.workers.UvicornWorker", \
     "--workers", "2", \
     "--bind", "0.0.0.0:8001", \
     "--timeout", "60"]
