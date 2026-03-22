# Dockerfile para el Servicio ETL
FROM python:3.10-slim

# Argumentos de build
ARG BUILD_DATE
ARG VERSION=1.0.0

# Metadatos
LABEL maintainer="Inventory Team" \
      org.label-schema.build-date=$BUILD_DATE \
      org.label-schema.description="ETL Service for Inventory Management" \
      org.label-schema.name="inventory-etl" \
      org.label-schema.version=$VERSION

# Configurar timezone e instalar cron
RUN apt-get update && \
    apt-get install -y --no-install-recommends cron && \
    rm -rf /var/lib/apt/lists/*

ENV TZ=America/Bogota
RUN ln -snf /usr/share/zoneinfo/${TZ} /etc/localtime || true

# Configurar Python
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONFAULTHANDLER=1 \
    PIP_TIMEOUT=300 \
    PIP_NO_CACHE_DIR=1

# Crear usuario no root para seguridad
RUN groupadd -r etl && useradd -r -g etl etl

# Crear estructura de directorios
RUN mkdir -p /app/data /app/logs /var/log/cron
RUN chown -R etl:etl /app /var/log/cron

# Establecer directorio de trabajo
WORKDIR /app

# Copiar requirements primero para cachear dependencias
COPY requirements.txt .

# Instalar dependencias en partes para mejor manejo de errores
RUN pip install --upgrade pip setuptools wheel && \
    pip install requests python-dotenv schedule tenacity pydantic

# Instalar dependencias de datos
RUN pip install pandas openpyxl psycopg2-binary

# Instalar herramientas de BD (opcional para MVP)
RUN pip install alembic sqlalchemy || true

# Copiar código fuente
COPY --chown=etl:etl src/ ./src/

# Configurar cron
COPY cronjob /etc/cron.d/etl-cron
RUN chmod 0644 /etc/cron.d/etl-cron
RUN crontab /etc/cron.d/etl-cron || true

# Crear archivo de log
RUN touch /var/log/cron.log && chown etl:etl /var/log/cron.log

# Cambiar a usuario no root
USER etl

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD python -c "import sys; sys.path.insert(0, '/app/src'); from config import Config; print('ETL OK')" || exit 1

# Comando por defecto: iniciar cron y mantener contenedor activo
CMD ["cron", "-f"]
