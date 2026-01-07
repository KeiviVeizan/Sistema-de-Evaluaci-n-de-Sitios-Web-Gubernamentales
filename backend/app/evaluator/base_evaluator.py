"""
Clase base para todos los evaluadores
Define la interfaz común y utilidades compartidas
"""
from typing import Dict, List, Optional
from datetime import datetime


class CriteriaEvaluation:
    """Resultado de evaluación de un criterio individual"""

    def __init__(
        self,
        criteria_id: str,
        criteria_name: str,
        dimension: str,
        lineamiento: str,
        status: str,  # "pass", "fail", "partial", "na"
        score: float,
        max_score: float,
        details: Dict,
        evidence: Dict
    ):
        self.criteria_id = criteria_id
        self.criteria_name = criteria_name
        self.dimension = dimension
        self.lineamiento = lineamiento
        self.status = status
        self.score = score
        self.max_score = max_score
        self.details = details
        self.evidence = evidence

    def to_dict(self) -> Dict:
        return {
            "criteria_id": self.criteria_id,
            "criteria_name": self.criteria_name,
            "dimension": self.dimension,
            "lineamiento": self.lineamiento,
            "status": self.status,
            "score": self.score,
            "max_score": self.max_score,
            "score_percentage": (self.score / self.max_score * 100) if self.max_score > 0 else 0,
            "details": self.details,
            "evidence": self.evidence
        }


class BaseEvaluator:
    """
    Clase base para todos los evaluadores
    Cada evaluador hereda de esta clase
    """

    def __init__(self, dimension: str):
        self.dimension = dimension
        self.results: List[CriteriaEvaluation] = []

    def evaluate(self, extracted_content: Dict) -> List[CriteriaEvaluation]:
        """
        Método principal que debe implementar cada evaluador
        Recibe ExtractedContent como dict y retorna lista de evaluaciones
        """
        raise NotImplementedError("Subclasses must implement evaluate()")

    def add_result(self, result: CriteriaEvaluation):
        """Agrega un resultado de evaluación"""
        self.results.append(result)

    def get_dimension_score(self) -> Dict:
        """Calcula el score total de la dimensión"""
        total_score = sum(r.score for r in self.results)
        max_score = sum(r.max_score for r in self.results)

        return {
            "dimension": self.dimension,
            "total_score": total_score,
            "max_score": max_score,
            "percentage": (total_score / max_score * 100) if max_score > 0 else 0,
            "criteria_count": len(self.results),
            "passed": len([r for r in self.results if r.status == "pass"]),
            "failed": len([r for r in self.results if r.status == "fail"]),
            "partial": len([r for r in self.results if r.status == "partial"])
        }

    def clear_results(self):
        """Limpia los resultados"""
        self.results = []
