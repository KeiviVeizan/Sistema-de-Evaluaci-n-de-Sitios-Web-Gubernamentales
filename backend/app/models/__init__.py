"""
Módulo de modelos de base de datos.

Expone todos los modelos SQLAlchemy para facilitar su importación.
"""

from app.models.database_models import (
    Website,
    Evaluation,
    CriteriaResult,
    NLPAnalysis
)

__all__ = [
    "Website",
    "Evaluation",
    "CriteriaResult",
    "NLPAnalysis"
]
