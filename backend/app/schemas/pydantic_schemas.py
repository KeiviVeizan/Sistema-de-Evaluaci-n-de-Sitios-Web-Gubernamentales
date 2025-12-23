"""
Schemas Pydantic para validación y serialización de datos.

Define los esquemas de entrada y salida para la API REST.
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, HttpUrl, field_validator
import validators


# ============================================================================
# Website Schemas
# ============================================================================

class WebsiteBase(BaseModel):
    """Schema base para sitios web."""
    url: str = Field(..., description="URL del sitio web")
    institution_name: str = Field(..., min_length=3, description="Nombre de la institución")

    @field_validator("url")
    @classmethod
    def validate_url(cls, v: str) -> str:
        """Valida que la URL sea válida y termine en .gob.bo"""
        if not validators.url(v):
            raise ValueError("URL no válida")
        if not v.lower().endswith(".gob.bo") and ".gob.bo/" not in v.lower():
            raise ValueError("La URL debe ser de un sitio gubernamental boliviano (.gob.bo)")
        return v


class WebsiteCreate(WebsiteBase):
    """Schema para crear un nuevo sitio web."""
    pass


class WebsiteUpdate(BaseModel):
    """Schema para actualizar un sitio web."""
    institution_name: Optional[str] = Field(None, min_length=3)
    is_active: Optional[bool] = None


class WebsiteResponse(WebsiteBase):
    """Schema de respuesta para sitios web."""
    id: int
    domain: str
    created_at: datetime
    updated_at: datetime
    last_crawled_at: Optional[datetime] = None
    is_active: bool
    crawl_status: str

    class Config:
        from_attributes = True


class WebsiteList(BaseModel):
    """Schema para lista de sitios web."""
    total: int
    items: List[WebsiteResponse]


# ============================================================================
# Evaluation Schemas
# ============================================================================

class EvaluationBase(BaseModel):
    """Schema base para evaluaciones."""
    website_id: int = Field(..., gt=0, description="ID del sitio web a evaluar")


class EvaluationCreate(EvaluationBase):
    """Schema para crear una nueva evaluación."""
    pass


class EvaluationResponse(BaseModel):
    """Schema de respuesta para evaluaciones."""
    id: int
    website_id: int
    started_at: datetime
    completed_at: Optional[datetime] = None
    score_digital_sovereignty: Optional[float] = None
    score_accessibility: Optional[float] = None
    score_usability: Optional[float] = None
    score_semantic_web: Optional[float] = None
    score_total: Optional[float] = None
    status: str
    error_message: Optional[str] = None

    class Config:
        from_attributes = True


class EvaluationList(BaseModel):
    """Schema para lista de evaluaciones."""
    total: int
    items: List[EvaluationResponse]


# ============================================================================
# Criteria Result Schemas
# ============================================================================

class CriteriaResultResponse(BaseModel):
    """Schema de respuesta para resultados de criterios."""
    id: int
    evaluation_id: int
    criteria_type: str
    criteria_code: str
    criteria_name: str
    status: str
    score: Optional[float] = None
    details: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True


# ============================================================================
# NLP Analysis Schemas
# ============================================================================

class NLPAnalysisResponse(BaseModel):
    """Schema de respuesta para análisis NLP."""
    id: int
    evaluation_id: int
    text_sample: str
    ambiguity_score: Optional[float] = None
    clarity_score: Optional[float] = None
    issues_detected: Optional[Dict[str, Any]] = None
    created_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# Evaluation Detail Schema (con relaciones)
# ============================================================================

class EvaluationDetailResponse(EvaluationResponse):
    """Schema detallado de evaluación con todos sus resultados."""
    criteria_results: List[CriteriaResultResponse] = []
    nlp_analyses: List[NLPAnalysisResponse] = []
    website: WebsiteResponse

    class Config:
        from_attributes = True


# ============================================================================
# Health Check Schema
# ============================================================================

class HealthResponse(BaseModel):
    """Schema para health check."""
    status: str = Field(..., description="Estado del servicio")
    database: str = Field(..., description="Estado de la base de datos")
    redis: str = Field(..., description="Estado de Redis")
    version: str = Field(..., description="Versión de la API")
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# ============================================================================
# Error Schema
# ============================================================================

class ErrorResponse(BaseModel):
    """Schema para respuestas de error."""
    detail: str = Field(..., description="Detalle del error")
    error_code: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
