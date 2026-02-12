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
from app.database import init_db, get_db, SessionLocal
from app.api.routes import router as api_router
from app.api.crawler_routes import router as crawler_router
from app.api.evaluation_routes import router as evaluation_router
from app.api.auth_routes import router as auth_router
from app.api.admin_routes import router as admin_router
from app.api.followup_routes import router as followup_router
from app.api.notification_routes import router as notification_router
from app.auth.seed import seed_users
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

        # Crear usuarios seed (solo si no existen)
        db = SessionLocal()
        try:
            seed_users(db)
        finally:
            db.close()
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
logger.info(f"CORS allowed_origins: {settings.allowed_origins}")
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
app.include_router(auth_router, prefix=settings.api_v1_prefix)
app.include_router(admin_router, prefix=settings.api_v1_prefix)
app.include_router(followup_router, prefix=settings.api_v1_prefix)
app.include_router(notification_router, prefix=settings.api_v1_prefix)


# Health check endpoint (fuera del prefijo API)
@app.get(
    "/health",
    tags=["Health"],
    summary="Health check",
    description="Verifica el estado del servicio y sus dependencias"
)
async def health_check(db: Session = Depends(get_db)):
    """
    Endpoint de health check con verificacion de dependencias.

    - database: CRITICO - sistema no funciona sin BD
    - redis: OPCIONAL - sistema funciona sin cache (degraded mode)
    """
    from datetime import datetime
    from sqlalchemy import text
    from app.cache import cache_manager

    # Verificar PostgreSQL (CRITICO)
    db_status = "connected"
    db_healthy = True
    try:
        db.execute(text("SELECT 1"))
        db.commit()
    except Exception as e:
        db_status = f"error: {str(e)[:100]}"
        db_healthy = False
        logger.error(f"Database health check failed: {e}")

    # Verificar Redis (OPCIONAL)
    redis_stats = cache_manager.get_stats()
    redis_healthy = redis_stats.get("available", False)

    # El sistema esta healthy si la BD funciona (Redis es opcional)
    overall_status = "healthy" if db_healthy else "critical"

    # Si Redis no esta pero BD si, es "degraded" pero operativo
    if db_healthy and not redis_healthy:
        overall_status = "degraded"

    return {
        "status": overall_status,
        "timestamp": datetime.now().isoformat(),
        "components": {
            "database": {
                "status": db_status,
                "healthy": db_healthy,
                "critical": True
            },
            "redis": {
                "status": redis_stats.get("status", "unknown"),
                "healthy": redis_healthy,
                "critical": False,
                "stats": redis_stats if redis_healthy else None
            }
        },
        "version": __version__,
        "message": (
            "Sistema operativo" if overall_status == "healthy" else
            "Sistema operativo sin cache (Redis no disponible)" if overall_status == "degraded" else
            "Sistema no operativo - BD desconectada"
        )
    }


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
