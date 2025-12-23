"""
Módulo de evaluación de sitios web.

Implementa evaluadores para D.S. 3925, WCAG 2.0 y cálculo de puntajes.
"""

from app.evaluator.ds3925 import DS3925Evaluator
from app.evaluator.wcag import WCAGEvaluator
from app.evaluator.scorer import ScoreCalculator

__all__ = ["DS3925Evaluator", "WCAGEvaluator", "ScoreCalculator"]
