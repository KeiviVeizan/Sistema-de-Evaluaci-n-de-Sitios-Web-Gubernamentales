"""
Módulo de schemas Pydantic.

Expone todos los schemas para validación y serialización de datos.
"""

from app.schemas.pydantic_schemas import (
    # Website schemas
    WebsiteBase,
    WebsiteCreate,
    WebsiteUpdate,
    WebsiteResponse,
    WebsiteList,

    # Evaluation schemas
    EvaluationBase,
    EvaluationCreate,
    EvaluationResponse,
    EvaluationList,

    # Criteria Result schemas
    CriteriaResultResponse,

    # NLP Analysis schemas
    NLPAnalysisResponse,

    # Health check
    HealthResponse
)

__all__ = [
    # Website
    "WebsiteBase",
    "WebsiteCreate",
    "WebsiteUpdate",
    "WebsiteResponse",
    "WebsiteList",

    # Evaluation
    "EvaluationBase",
    "EvaluationCreate",
    "EvaluationResponse",
    "EvaluationList",

    # Criteria Result
    "CriteriaResultResponse",

    # NLP Analysis
    "NLPAnalysisResponse",

    # Health
    "HealthResponse"
]
