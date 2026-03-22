# Dockerfile para API Gateway FastAPI
FROM python:3.10-slim

# Argumentos de build
ARG BUILD_DATE
ARG VERSION=1.0.0

# Metadatos
LABEL maintainer="Inventory Team" \
      org.label-schema.build-date=$BUILD_DATE \
      org.label-schema.description="API Gateway FastAPI for Inventory Management" \
      org.label-schema.name="inventory-api-gateway" \
      org.label-schema.version=$VERSION

# Configurar timezone
ENV TZ=America/Bogota
RUN ln -snf /usr/share/zoneinfo/${TZ} /etc/localtime || true

# Configurar Python
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONFAULTHANDLER=1 \
    PIP_TIMEOUT=600

# Crear usuario no root
RUN groupadd -r api && useradd -r -g api api

# Establecer directorio de trabajo
WORKDIR /app

# Copiar requirements primero
COPY requirements.txt .

# Instalar dependencias base primero
RUN pip install --upgrade pip setuptools wheel

# Instalar fastapi y uvicorn
RUN pip install fastapi uvicorn

# Instalar dependencias de autenticación
RUN pip install python-jose[cryptography] passlib[bcrypt] python-multipart

# Instalar pydantic y settings
RUN pip install pydantic pydantic-settings

# Instalar otras dependencias
RUN pip install requests tenacity prometheus-client

# Copiar código fuente
COPY src/ ./src/

# Dar permisos al usuario api
RUN chown -R api:api /app

# Cambiar a usuario no root
USER api

# Exponer puerto
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Comando por defecto con uvicorn
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
