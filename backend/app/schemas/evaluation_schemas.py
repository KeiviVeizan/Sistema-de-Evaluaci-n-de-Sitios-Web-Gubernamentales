"""
Schemas Pydantic para evaluaciones.

Define los esquemas de entrada y salida para la API de evaluaciones.
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, HttpUrl, field_validator
from enum import Enum


class EvaluationStatusEnum(str, Enum):
    """Estados posibles de una evaluacion."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class CriteriaStatusEnum(str, Enum):
    """Estados de cumplimiento de criterios."""
    PASS = "pass"
    FAIL = "fail"
    PARTIAL = "partial"
    NOT_APPLICABLE = "na"


# ============================================================================
# REQUEST SCHEMAS
# ============================================================================

class EvaluateURLRequest(BaseModel):
    """Request para evaluar una URL directamente."""
    url: str = Field(
        ...,
        description="URL del sitio web gubernamental a evaluar",
        example="https://www.aduana.gob.bo"
    )
    institution_name: Optional[str] = Field(
        None,
        description="Nombre de la institucion (opcional)",
        example="Aduana Nacional de Bolivia"
    )
    force_recrawl: bool = Field(
        default=False,
        description="Forzar re-crawling aunque exista evaluacion reciente"
    )

    @field_validator('url')
    @classmethod
    def validate_gob_bo_domain(cls, v):
        """Validar que sea dominio .gob.bo."""
        url_str = str(v).lower()
        if not ('.gob.bo' in url_str):
            raise ValueError('La URL debe ser un dominio .gob.bo valido')
        if not url_str.startswith(('http://', 'https://')):
            raise ValueError('La URL debe comenzar con http:// o https://')
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "url": "https://www.aduana.gob.bo",
                "institution_name": "Aduana Nacional de Bolivia",
                "force_recrawl": False
            }
        }


# ============================================================================
# RESPONSE SCHEMAS
# ============================================================================

class ScoresByDimension(BaseModel):
    """Scores por cada dimension."""
    percentage: float = Field(..., ge=0, le=100)
    total_score: float = Field(default=0)
    max_score: float = Field(default=0)
    passed: int = Field(default=0)
    failed: int = Field(default=0)
    partial: int = Field(default=0)


class NLPScores(BaseModel):
    """Scores del analisis NLP."""
    percentage: float = Field(..., ge=0, le=100, description="Score global NLP")
    coherence: float = Field(..., ge=0, le=100, description="Coherencia semantica")
    ambiguity: float = Field(..., ge=0, le=100, description="Deteccion de ambiguedades")
    clarity: float = Field(..., ge=0, le=100, description="Claridad y legibilidad")
    wcag_compliance: Optional[Dict[str, bool]] = Field(
        default=None,
        description="Cumplimiento WCAG por criterio"
    )


class CriteriaResultItem(BaseModel):
    """Resultado individual de un criterio evaluado."""
    criteria_id: str = Field(..., example="ACC-01")
    criteria_name: str = Field(..., example="Texto alternativo en imagenes")
    dimension: str = Field(..., example="accesibilidad")
    lineamiento: str = Field(..., example="WCAG 2.0 - 1.1.1")
    status: str = Field(..., example="pass")
    score: float = Field(..., ge=0, example=1.0)
    max_score: float = Field(..., ge=0, example=1.0)
    details: Optional[Dict[str, Any]] = None
    evidence: Optional[Dict[str, Any]] = None


class NLPAnalysisDetail(BaseModel):
    """Detalles del analisis NLP."""
    global_score: float = Field(..., ge=0, le=100)
    coherence_score: float = Field(..., ge=0, le=100)
    ambiguity_score: float = Field(..., ge=0, le=100)
    clarity_score: float = Field(..., ge=0, le=100)
    wcag_compliance: Dict[str, bool] = Field(default_factory=dict)
    total_sections_analyzed: int = Field(default=0)
    total_texts_analyzed: int = Field(default=0)
    recommendations: List[str] = Field(default_factory=list)
    details: Optional[Dict[str, Any]] = None


class EvaluationSummary(BaseModel):
    """Resumen estadistico de la evaluacion."""
    total_criteria: int = Field(..., example=35)
    heuristic_criteria: int = Field(..., example=32)
    nlp_criteria: int = Field(..., example=3)
    passed: int = Field(..., example=20)
    failed: int = Field(..., example=10)
    partial: int = Field(..., example=4)
    not_applicable: int = Field(..., example=1)


class EvaluateURLResponse(BaseModel):
    """Respuesta completa de evaluacion de URL."""
    # Informacion basica
    url: str = Field(..., description="URL evaluada")
    status: str = Field(..., description="Estado de la evaluacion")
    timestamp: str = Field(..., description="Fecha/hora de la evaluacion")

    # Scores por dimension
    scores: Dict[str, Any] = Field(
        ...,
        description="Scores por dimension y total"
    )

    # Analisis NLP detallado
    nlp_analysis: Optional[NLPAnalysisDetail] = Field(
        None,
        description="Resultados detallados del analisis NLP"
    )

    # Resultados de criterios
    criteria_results: List[CriteriaResultItem] = Field(
        default_factory=list,
        description="Resultados de cada criterio evaluado"
    )

    # Resumen
    summary: EvaluationSummary = Field(
        ...,
        description="Resumen estadistico"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "url": "https://www.aduana.gob.bo",
                "status": "completed",
                "timestamp": "2025-01-28T10:30:00",
                "scores": {
                    "accesibilidad": {"percentage": 86.1},
                    "usabilidad": {"percentage": 67.8},
                    "semantica_tecnica": {"percentage": 56.2},
                    "semantica_nlp": {"percentage": 97.1},
                    "soberania": {"percentage": 85.0},
                    "total": 77.7
                },
                "summary": {
                    "total_criteria": 35,
                    "heuristic_criteria": 32,
                    "nlp_criteria": 3,
                    "passed": 20,
                    "failed": 10,
                    "partial": 4,
                    "not_applicable": 1
                }
            }
        }


class EvaluationListItem(BaseModel):
    """Item para listado de evaluaciones."""
    id: int
    website_id: int
    website_url: str
    institution_name: Optional[str] = None
    score_total: Optional[float] = None
    status: str
    started_at: datetime
    completed_at: Optional[datetime] = None


class EvaluationListResponse(BaseModel):
    """Respuesta paginada de listado de evaluaciones."""
    total: int = Field(..., description="Total de evaluaciones")
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=10, ge=1, le=100)
    evaluations: List[EvaluationListItem]


# ============================================================================
# API STATUS SCHEMAS
# ============================================================================

class APIStatusResponse(BaseModel):
    """Estado de la API."""
    message: str
    version: str
    status: str
    docs: str
    endpoints: Dict[str, str]


class HealthCheckResponse(BaseModel):
    """Respuesta de health check."""
    status: str
    timestamp: str
    database: str
    version: str
