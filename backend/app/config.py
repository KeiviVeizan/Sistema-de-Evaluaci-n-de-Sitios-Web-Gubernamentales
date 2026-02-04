"""
Configuración de la aplicación usando Pydantic Settings.

Este módulo centraliza toda la configuración de la aplicación,
cargando variables de entorno y proporcionando valores por defecto.
"""

from typing import List
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Configuración principal de la aplicación.

    Carga variables desde el archivo .env y proporciona
    valores por defecto para desarrollo.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"  # Ignora variables extra en .env
    )

    # Database Configuration
    database_url: str = Field(
        default="postgresql://localhost:5432/gob_evaluator",
        description="URL de conexión a PostgreSQL (configurar con usuario/contraseña en .env)"
    )
    db_pool_size: int = Field(default=10, description="Tamaño del pool de conexiones")
    db_max_overflow: int = Field(default=20, description="Máximo de conexiones adicionales")

    # Redis Configuration
    redis_url: str = Field(
        default="redis://localhost:6379/0",
        description="URL de conexión a Redis"
    )

    # Application Configuration
    app_name: str = Field(
        default="GOB.BO Evaluator",
        description="Nombre de la aplicación"
    )
    app_version: str = Field(
        default="1.0.0",
        description="Versión de la aplicación"
    )
    environment: str = Field(
        default="development",
        description="Entorno de ejecución (development, production)"
    )
    secret_key: str = Field(
        default="dev-secret-key-change-in-production-min-32-characters",
        description="Clave secreta para JWT y encriptación"
    )
    debug: bool = Field(default=True, description="Modo debug")
    allowed_origins: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:5173", "http://localhost:8000"],
        description="Orígenes permitidos para CORS"
    )

    # API Configuration
    api_v1_prefix: str = Field(default="/api/v1", description="Prefijo para API v1")
    max_concurrent_evaluations: int = Field(
        default=5,
        description="Máximo de evaluaciones concurrentes"
    )

    # Crawler Configuration
    crawler_user_agent: str = Field(
        default="GobBoEvaluator/1.0 (+https://evaluador.gob.bo)",
        description="User agent para el crawler"
    )
    crawler_delay: int = Field(
        default=2,
        description="Delay entre requests en segundos"
    )
    crawler_max_depth: int = Field(
        default=3,
        description="Profundidad máxima de crawling"
    )
    crawler_timeout: int = Field(
        default=30,
        description="Timeout para requests en segundos"
    )
    crawler_max_pages: int = Field(
        default=100,
        description="Máximo de páginas a crawlear por sitio"
    )

    # NLP Configuration
    nlp_model_name: str = Field(
        default="dccuchile/bert-base-spanish-wwm-cased",
        description="Modelo BERT en español para análisis NLP"
    )
    nlp_cache_dir: str = Field(
        default="./models_cache",
        description="Directorio para cache de modelos NLP"
    )

    # Logging Configuration
    log_level: str = Field(default="INFO", description="Nivel de logging")
    log_file: str = Field(default="logs/app.log", description="Archivo de logs")

    # Evaluation Configuration
    wcag_min_score: float = Field(
        default=70.0,
        description="Puntaje mínimo WCAG para considerarse aceptable"
    )
    ds3925_min_score: float = Field(
        default=70.0,
        description="Puntaje mínimo D.S. 3925 para considerarse aceptable"
    )

    @field_validator("allowed_origins", mode="before")
    @classmethod
    def parse_allowed_origins(cls, v):
        """Parsea los orígenes permitidos desde string o lista."""
        if isinstance(v, str):
            v = v.strip()
            if v.startswith('[') and v.endswith(']'):
                v = v[1:-1]
            origins = []
            for origin in v.split(","):
                origin = origin.strip().strip('"').strip("'")
                if origin:
                    origins.append(origin)
            return origins
        return v

    @field_validator("secret_key")
    @classmethod
    def validate_secret_key(cls, v):
        """Valida que la clave secreta tenga mínimo 32 caracteres."""
        if len(v) < 32:
            raise ValueError("La clave secreta debe tener al menos 32 caracteres")
        return v


# Instancia global de configuración
settings = Settings()
