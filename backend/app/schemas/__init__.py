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

# Nuevos schemas para API de evaluación
from app.schemas.evaluation_schemas import (
    # Enums
    EvaluationStatusEnum,
    CriteriaStatusEnum,

    # Request schemas
    EvaluateURLRequest,

    # Response schemas
    ScoresByDimension,
    NLPScores,
    CriteriaResultItem,
    NLPAnalysisDetail,
    EvaluationSummary,
    EvaluateURLResponse,
    EvaluationListItem,
    EvaluationListResponse,

    # API Status
    APIStatusResponse,
    HealthCheckResponse,
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
    "HealthResponse",

    # === Nuevos schemas API Evaluación ===
    # Enums
    "EvaluationStatusEnum",
    "CriteriaStatusEnum",

    # Request
    "EvaluateURLRequest",

    # Response
    "ScoresByDimension",
    "NLPScores",
    "CriteriaResultItem",
    "NLPAnalysisDetail",
    "EvaluationSummary",
    "EvaluateURLResponse",
    "EvaluationListItem",
    "EvaluationListResponse",

    # API Status
    "APIStatusResponse",
    "HealthCheckResponse",
]
