"""
Módulo de evaluación de sitios web.

Implementa evaluadores heurísticos para D.S. 3925, WCAG 2.0 y cálculo de puntajes.
"""

from .evaluation_engine import EvaluationEngine
from .base_evaluator import BaseEvaluator, CriteriaEvaluation
from .accesibilidad_evaluator import EvaluadorAccesibilidad
from .usabilidad_evaluator import EvaluadorUsabilidad
from .semantica_evaluator import EvaluadorSemanticaTecnica
from .soberania_evaluator import EvaluadorSoberania

__all__ = [
    'EvaluationEngine',
    'BaseEvaluator',
    'CriteriaEvaluation',
    'EvaluadorAccesibilidad',
    'EvaluadorUsabilidad',
    'EvaluadorSemanticaTecnica',
    'EvaluadorSoberania'
]
