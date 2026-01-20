"""
Punto de entrada principal de la aplicación FastAPI.

Configura la aplicación, middleware, CORS y registra las rutas de la API.
"""

from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import logging
from pathlib import Path
from sqlalchemy.orm import Session

from app.config import settings
from app.database import init_db, get_db
from app.api.routes import router as api_router
from app.api.crawler_routes import router as crawler_router
from app.api.evaluation_routes import router as evaluation_router
from app import __version__, __description__


# Configurar logging
log_path = Path(settings.log_file)
log_path.parent.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=settings.log_level,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(settings.log_file, encoding='utf-8'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """
    Gestor de ciclo de vida de la aplicación.

    Ejecuta tareas al iniciar y cerrar la aplicación.
    """
    # Startup
    logger.info("Iniciando aplicación...")
    try:
        init_db()
        logger.info("Base de datos inicializada correctamente")
    except Exception as e:
        logger.error(f"Error al inicializar base de datos: {e}")
        raise

    yield

    # Shutdown
    logger.info("Cerrando aplicación...")


# Crear aplicación FastAPI
app = FastAPI(
    title="Evaluador de Sitios Web Gubernamentales Bolivianos",
    description=__description__,
    version=__version__,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan
)


# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Registrar rutas
app.include_router(api_router, prefix=settings.api_v1_prefix)
app.include_router(crawler_router, prefix=settings.api_v1_prefix)
app.include_router(evaluation_router, prefix=settings.api_v1_prefix)


# Health check endpoint (fuera del prefijo API)
@app.get("/health", tags=["Health"])
async def health_check(db: Session = Depends(get_db)):
    """
    Endpoint de health check para verificar el estado del servicio.

    Verifica:
    - Conexión a base de datos PostgreSQL
    - Conexión a Redis
    - Estado general del servicio

    Returns:
        dict: Estado del servicio, base de datos y Redis
    """
    from app.schemas import HealthResponse
    from datetime import datetime
    from sqlalchemy import text

    # Verificar PostgreSQL
    db_status = "connected"
    try:
        db.execute(text("SELECT 1"))
        db.commit()
    except Exception as e:
        db_status = f"error: {str(e)[:100]}"
        logger.error(f"Database health check failed: {e}")

    # Verificar Redis
    redis_status = "connected"
    try:
        import redis
        r = redis.Redis.from_url(settings.redis_url, socket_connect_timeout=2, socket_timeout=2)
        r.ping()
        r.close()
    except Exception as e:
        redis_status = f"error: {str(e)[:100]}"
        logger.error(f"Redis health check failed: {e}")

    # Status general
    overall_status = "healthy" if (db_status == "connected" and redis_status == "connected") else "unhealthy"

    return HealthResponse(
        status=overall_status,
        database=db_status,
        redis=redis_status,
        version=__version__,
        timestamp=datetime.utcnow()
    )


# Root endpoint
@app.get("/", tags=["Root"])
async def root():
    """
    Endpoint raíz que proporciona información básica de la API.

    Returns:
        dict: Información de la API y enlaces útiles
    """
    return {
        "name": "Evaluador de Sitios Web Gubernamentales Bolivianos",
        "version": __version__,
        "description": __description__,
        "docs": "/docs",
        "health": "/health",
        "api": settings.api_v1_prefix
    }


# Manejador de excepciones global
@app.exception_handler(Exception)
async def global_exception_handler(_request, exc):
    """
    Manejador global de excepciones.

    Args:
        request: Request de FastAPI
        exc: Excepción capturada

    Returns:
        JSONResponse: Respuesta JSON con el error
    """
    logger.error(f"Error no manejado: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Error interno del servidor",
            "error_code": "INTERNAL_SERVER_ERROR"
        }
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
        log_level=settings.log_level.lower()
    )
