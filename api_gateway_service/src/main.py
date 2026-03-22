from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import time
import logging
from datetime import datetime
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST

from .config import settings
from .routers import auth_router, products_router, inventory_router
from .schemas import HealthResponse
from .utils.odoo_client import get_odoo_client

logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

REQUEST_COUNT = Counter(
    'api_gateway_requests_total',
    'Total de peticiones',
    ['method', 'endpoint', 'status']
)

REQUEST_LATENCY = Histogram(
    'api_gateway_request_duration_seconds',
    'Duración de peticiones',
    ['method', 'endpoint']
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Iniciando API Gateway...")
    
    try:
        odoo = get_odoo_client()
        if odoo.test_connection():
            logger.info("Conexión a Odoo establecida")
        else:
            logger.warning("No se pudo conectar a Odoo")
    except Exception as e:
        logger.error(f"Error al conectar a Odoo: {e}")
    
    yield
    
    logger.info("API Gateway detenido")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.VERSION,
    description="API Gateway para Gestión de Inventario con Odoo",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    
    logger.debug(f"Petición: {request.method} {request.url.path}")
    
    response = await call_next(request)
    
    process_time = time.time() - start_time
    
    REQUEST_COUNT.labels(
        method=request.method,
        endpoint=request.url.path,
        status=response.status_code
    ).inc()
    
    REQUEST_LATENCY.labels(
        method=request.method,
        endpoint=request.url.path
    ).observe(process_time)
    
    logger.info(
        f"{request.method} {request.url.path} - "
        f"Status: {response.status_code} - "
        f"Duration: {process_time:.3f}s"
    )
    
    response.headers["X-Process-Time"] = str(process_time)
    
    return response


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.exception(f"Error no manejado: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Error interno del servidor",
            "path": str(request.url),
        },
    )


@app.get("/")
async def root():
    return {
        "name": settings.APP_NAME,
        "version": settings.VERSION,
        "status": "running",
    }


@app.get("/health", response_model=HealthResponse)
async def health_check():
    odoo = get_odoo_client()
    odoo_connected = odoo.test_connection()
    
    return HealthResponse(
        status="healthy" if odoo_connected else "degraded",
        version=settings.VERSION,
        odoo_connected=odoo_connected,
        timestamp=datetime.now(),
    )


@app.get("/metrics")
async def metrics():
    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST
    )


app.include_router(auth_router, prefix=settings.API_V1_PREFIX)
app.include_router(products_router, prefix=settings.API_V1_PREFIX)
app.include_router(inventory_router, prefix=settings.API_V1_PREFIX)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "src.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=True,
    )
