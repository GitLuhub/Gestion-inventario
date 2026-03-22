# Sistema de Gestión de Inventario Avanzado

Sistema de gestión de inventario construido con Odoo 16.0 LTS, ETL en Python, API Gateway FastAPI y Frontend Next.js.

## Arquitectura

```
┌─────────────┐     ┌──────────────┐     ┌──────────────┐
│   Nginx     │────▶│   Frontend   │────▶│  API Gateway │
│  (Reverse   │     │  (Next.js)   │     │  (FastAPI)   │
│   Proxy)    │     └──────────────┘     └──────┬───────┘
└─────────────┘                                 │
                                                 ▼
┌─────────────┐     ┌──────────────┐     ┌──────────────┐
│ Prometheus  │◀────│   Odoo       │◀────│    ETL       │
│   +         │     │   16.0       │     │   Service    │
│  Grafana    │     │  + Inventory │     │  (Python)    │
└─────────────┘     └──────┬───────┘     └──────────────┘
                           │
                           ▼
                    ┌──────────────┐
                    │  PostgreSQL   │
                    │     15       │
                    └──────────────┘
```

## Servicios

| Servicio | Descripción | Puerto |
|----------|-------------|--------|
| Nginx | Reverse Proxy / Load Balancer | 80, 443 |
| Odoo | ERP con módulo de inventario | 8069 |
| PostgreSQL | Base de datos principal | 5432 |
| ETL Service | Pipeline de sincronización | - |
| API Gateway | API REST con JWT | 8000 |
| Frontend | Aplicación web Next.js | 3000 |
| Prometheus | Métricas | 9090 |
| Grafana | Dashboards | 3001 |

## Requisitos

- Docker Engine 24.0+
- Docker Compose 2.20+
- 8GB RAM mínimo recomendado
- 50GB espacio en disco

## Instalación Rápida

### 1. Clonar el repositorio

```bash
git clone <repo-url>
cd Gestion-inventario
```

### 2. Configurar secretos

```bash
# Ejecutar script de configuración
bash secrets/setup_secrets.sh

# O manualmente:
mkdir -p secrets/certs
openssl rand -base64 32 > secrets/db_password.txt
openssl rand -base64 32 > secrets/odoo_master_password.txt
openssl rand -hex 64 > secrets/jwt_secret_key.txt
chmod 600 secrets/*.txt
```

### 3. Iniciar servicios

```bash
# Construir e iniciar todos los servicios
docker compose up -d --build

# Ver logs
docker compose logs -f
```

### 4. Acceder a los servicios

| Servicio | URL |
|----------|-----|
| Odoo | http://localhost:8069 |
| Frontend | http://localhost:3000 |
| API Gateway | http://localhost:8000 |
| Swagger UI | http://localhost:8000/docs |
| Grafana | http://localhost:3001 |
| Prometheus | http://localhost:9090 |

## Desarrollo

### Estructura del proyecto

```
.
├── docker/               # Configuración Docker
│   ├── nginx/           # Configuración Nginx
│   ├── odoo/            # Dockerfile Odoo
│   ├── prometheus/      # Configuración Prometheus
│   └── grafana/         # Dashboards de Grafana
├── odoo_custom_module/  # Módulo personalizado Odoo
├── etl_service/         # Servicio ETL Python
├── api_gateway_service/ # API Gateway FastAPI
├── frontend/            # Aplicación Next.js
├── secrets/             # Secretos (no commitear)
├── docker compose.yml   # Orquestación de servicios
└── .env.example        # Variables de entorno ejemplo
```

### Comandos útiles

```bash
# Reconstruir un servicio específico
docker compose up -d --build odoo_app

# Ver logs de un servicio
docker compose logs -f odoo_app

# Reiniciar un servicio
docker compose restart etl_service

# Acceder a PostgreSQL
docker exec -it inventory_pg_db psql -U odoo -d odoo_db

# Acceder al shell de Odoo
docker exec -it inventory_odoo_app bash

# Ver uso de recursos
docker stats
```

## ETL - Sincronización de Datos

El servicio ETL sincroniza datos de fuentes externas hacia Odoo:

### Fuentes de datos soportadas

- Archivos CSV/Excel
- APIs REST externas
- Bases de datos SQL

### Configuración

```bash
# Editar configuración del ETL
vi etl_service/src/config.py

# Los datos CSV van en:
etl_service/data/products.csv
etl_service/data/inventory.csv
```

### Ejecución manual

```bash
# Ejecutar ETL manualmente
docker exec -it inventory_etl_service python /app/src/main.py
```

## API Gateway

### Autenticación

```bash
# Obtener token JWT
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin"}'
```

### Endpoints principales

- `POST /api/v1/auth/login` - Iniciar sesión
- `GET /api/v1/products` - Listar productos
- `POST /api/v1/products` - Crear producto
- `GET /api/v1/inventory` - Ver inventario
- `POST /api/v1/inventory/adjust` - Ajustar stock

## Monitoreo

### Prometheus

Accede a http://localhost:9090 para ver métricas.

### Grafana

Accede a http://localhost:3001 (admin/admin).

Dashboards disponibles:
- Infrastructure Overview
- Odoo Performance
- ETL Status
- PostgreSQL Stats

## Testing

### Unit Tests

```bash
# ETL Service tests
cd etl_service
pip install -r requirements.txt
pytest tests/ -v

# API Gateway tests
cd api_gateway_service
pip install -r requirements.txt
pytest tests/ -v

# Frontend tests
cd frontend
npm install
npm test
```

### E2E Tests

```bash
# Run Playwright E2E tests (when configured)
npm run test:e2e
```

## CI/CD

### GitHub Actions

El proyecto incluye pipelines de CI/CD automatizados:

#### CI Pipeline (`.github/workflows/ci.yml`)
- Linting y type checking
- Tests unitarios para ETL, API y Frontend
- Build de imágenes Docker
- Se ejecuta en cada push y PR

#### CD Pipeline (`.github/workflows/cd.yml`)
- Deploy automático a staging (rama develop)
- Deploy a producción (rama main)
- Requiere configurar secrets en GitHub:
  - `STAGING_HOST`, `STAGING_USER`, `STAGING_SSH_KEY`
  - `PRODUCTION_HOST`, `PRODUCTION_USER`, `PRODUCTION_SSH_KEY`

### Configurar Secrets para Deploy

```bash
# En GitHub > Settings > Secrets > Actions:
STAGING_HOST=staging.example.com
STAGING_USER=deploy
STAGING_SSH_KEY=<private_key>
PRODUCTION_HOST=prod.example.com
PRODUCTION_USER=deploy
PRODUCTION_SSH_KEY=<private_key>
```

## Producción

### Requisitos del Servidor

- Ubuntu 22.04 LTS (recomendado)
- 16GB RAM mínimo
- 100GB SSD
- Docker Engine 24.0+
- Docker Compose 2.20+

### Pasos de Despliegue

```bash
# 1. Clonar en el servidor
git clone <repo-url> /opt/inventory
cd /opt/inventory

# 2. Configurar producción
cp .env.example .env
# Editar .env con valores de producción

# 3. Crear secretos
mkdir -p secrets
openssl rand -base64 32 > secrets/db_password.txt
openssl rand -base64 64 > secrets/odoo_master_password.txt
openssl rand -hex 64 > secrets/jwt_secret_key.txt
chmod 600 secrets/*.txt

# 4. Deploy
 docker compose -f docker compose.yml -f docker compose.dev.yml up

# 5. Verificar
docker compose ps
docker compose logs -f
```

### Backup

```bash
# Backup de PostgreSQL
docker exec inventory_pg_db pg_dump -U odoo odoo_db > backup_$(date +%Y%m%d).sql

# Backup de volúmenes
docker run --rm -v inventory_pg_data:/data -v $(pwd):/backup alpine tar czf /backup/pg_backup.tar.gz -C /data .
```

### Actualización

```bash
cd /opt/inventory
git pull
docker compose pull
docker compose up -d --build
```

## Licencia

MIT License
