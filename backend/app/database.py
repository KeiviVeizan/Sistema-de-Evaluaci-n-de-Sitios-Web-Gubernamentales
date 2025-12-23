"""
Configuración de SQLAlchemy y gestión de sesiones de base de datos.

Este módulo configura el engine de SQLAlchemy, la sesión y proporciona
utilidades para la inicialización de la base de datos.
"""

from typing import Generator
from sqlalchemy import create_engine, event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import Pool

from app.config import settings

# Crear engine de SQLAlchemy con configuración de pool
engine = create_engine(
    settings.database_url,
    pool_size=settings.db_pool_size,
    max_overflow=settings.db_max_overflow,
    pool_pre_ping=True,  # Verifica conexiones antes de usarlas
    echo=settings.debug,  # Log de queries SQL en modo debug
)


# Event listener para habilitar foreign keys en SQLite (si se usa)
@event.listens_for(Pool, "connect")
def set_sqlite_pragma(dbapi_conn, connection_record):
    """
    Habilita foreign keys en SQLite.

    Args:
        dbapi_conn: Conexión de la base de datos
        connection_record: Registro de la conexión
    """
    if "sqlite" in settings.database_url:
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


# Factory de sesiones
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# Base declarativa para modelos
Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """
    Dependency para obtener una sesión de base de datos.

    Crea una nueva sesión para cada request y la cierra automáticamente
    al finalizar, incluso si ocurre una excepción.

    Yields:
        Session: Sesión de SQLAlchemy

    Example:
        ```python
        @app.get("/items")
        def get_items(db: Session = Depends(get_db)):
            return db.query(Item).all()
        ```
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """
    Inicializa la base de datos creando todas las tablas.

    Esta función debe ser llamada al iniciar la aplicación para asegurar
    que todas las tablas definidas en los modelos existan.

    Note:
        En producción, se recomienda usar Alembic para migraciones en lugar
        de crear tablas directamente.
    """
    # Importar todos los modelos antes de crear las tablas
    from app.models import database_models  # noqa: F401

    Base.metadata.create_all(bind=engine)
    print("✓ Base de datos inicializada correctamente")


def drop_db() -> None:
    """
    Elimina todas las tablas de la base de datos.

    ADVERTENCIA: Esta función elimina todos los datos. Solo debe usarse
    en desarrollo o testing.
    """
    Base.metadata.drop_all(bind=engine)
    print("✓ Todas las tablas eliminadas")


def reset_db() -> None:
    """
    Reinicia la base de datos eliminando y recreando todas las tablas.

    ADVERTENCIA: Esta función elimina todos los datos. Solo debe usarse
    en desarrollo o testing.
    """
    drop_db()
    init_db()
    print("✓ Base de datos reiniciada")
