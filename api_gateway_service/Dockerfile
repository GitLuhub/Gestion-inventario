# =============================================================================
# API Gateway FastAPI — Multi-stage build (H1)
# Stage 1 (builder): instala dependencias Python en directorio aislado
# Stage 2 (runtime): imagen mínima sin pip ni herramientas de compilación
# Resultado: imagen ~60% más pequeña que el Dockerfile single-stage original.
# =============================================================================

# ---------------------------------------------------------------------------
# Stage 1: builder — instala deps en /deps para copiarlos en runtime
# ---------------------------------------------------------------------------
FROM python:3.10-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_TIMEOUT=600

WORKDIR /build

COPY requirements.txt .

RUN pip install --upgrade pip && \
    pip install --target=/deps -r requirements.txt


# ---------------------------------------------------------------------------
# Stage 2: runtime — solo el código y las deps instaladas
# ---------------------------------------------------------------------------
FROM python:3.10-slim AS runtime

ARG BUILD_DATE
ARG VERSION=1.0.0

LABEL maintainer="Luis Brito" \
      org.label-schema.build-date="${BUILD_DATE}" \
      org.label-schema.description="API Gateway FastAPI — Gestión de Inventario" \
      org.label-schema.name="inventory-api-gateway" \
      org.label-schema.version="${VERSION}"

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONFAULTHANDLER=1 \
    PYTHONPATH=/deps:/app \
    TZ=America/Bogota

# Solo curl para el HEALTHCHECK
RUN apt-get update && apt-get install -y --no-install-recommends curl && \
    rm -rf /var/lib/apt/lists/*

RUN groupadd -r api && useradd -r -g api --home /app api

WORKDIR /app

# Dependencias del builder
COPY --from=builder /deps /deps

# Código fuente
COPY --chown=api:api src/ ./src/

USER api

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -sf http://localhost:8000/health || exit 1

CMD ["python", "-m", "uvicorn", "src.main:app", \
     "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
