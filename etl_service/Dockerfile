# =============================================================================
# ETL Service — Multi-stage build (H1)
# Stage 1 (builder): instala dependencias Python
# Stage 2 (runtime): imagen mínima con cron + solo los deps necesarios
# =============================================================================

# ---------------------------------------------------------------------------
# Stage 1: builder
# ---------------------------------------------------------------------------
FROM python:3.10-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_TIMEOUT=300

WORKDIR /build

COPY requirements.txt .

RUN pip install --upgrade pip && \
    pip install --target=/deps -r requirements.txt


# ---------------------------------------------------------------------------
# Stage 2: runtime
# ---------------------------------------------------------------------------
FROM python:3.10-slim AS runtime

ARG BUILD_DATE
ARG VERSION=1.0.0

LABEL maintainer="Luis Brito" \
      org.label-schema.build-date="${BUILD_DATE}" \
      org.label-schema.description="ETL Service — Gestión de Inventario" \
      org.label-schema.name="inventory-etl" \
      org.label-schema.version="${VERSION}"

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONFAULTHANDLER=1 \
    PYTHONPATH=/deps:/app/src \
    TZ=America/Bogota

# cron es el único binario de sistema necesario en runtime
RUN apt-get update && \
    apt-get install -y --no-install-recommends cron && \
    rm -rf /var/lib/apt/lists/*

RUN groupadd -r etl && useradd -r -g etl etl

RUN mkdir -p /app/data /app/logs /var/log/cron && \
    touch /var/log/cron.log && \
    chown -R etl:etl /app /var/log/cron /var/log/cron.log

WORKDIR /app

# Dependencias del builder
COPY --from=builder /deps /deps

# Código fuente, Alembic y configuración de cron
COPY --chown=etl:etl src/ ./src/
COPY --chown=etl:etl alembic/ ./alembic/
COPY --chown=etl:etl alembic.ini .
COPY cronjob /etc/cron.d/etl-cron
RUN chmod 0644 /etc/cron.d/etl-cron && crontab /etc/cron.d/etl-cron || true

# cron necesita root para escribir /var/run/crond.pid — no se puede ejecutar
# como usuario no privilegiado en contenedores estándar de Linux.
# Los scripts Python del cron corren en el contexto del usuario etl vía PYTHONPATH.

HEALTHCHECK --interval=60s --timeout=10s --start-period=60s --retries=3 \
    CMD pgrep -x cron || pgrep -x crond || exit 1

CMD ["cron", "-f"]
