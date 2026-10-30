# ---- Build stage ----
FROM python:3.11-slim AS builder

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./requirements.txt
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# ---- Runtime stage ----
FROM python:3.11-slim AS runtime

RUN useradd --create-home --uid 1000 appuser

WORKDIR /app

COPY --from=builder /install /usr/local

COPY app /app/app
COPY alembic /app/alembic
COPY alembic.ini /app/alembic.ini

ENV PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    PORT=8004

USER appuser

EXPOSE 8004

# 1 worker for local/dev so startup table creation never races. Scale workers
# (or replicas in Kubernetes) in production, where Alembic owns the schema.
CMD ["gunicorn", "app.main:app", \
     "--worker-class", "uvicorn.workers.UvicornWorker", \
     "--workers", "1", \
     "--bind", "0.0.0.0:8004", \
     "--timeout", "60"]
