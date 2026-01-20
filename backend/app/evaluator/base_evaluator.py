"""
Clase base para todos los evaluadores
Define la interfaz común y utilidades compartidas
"""
from typing import Dict, List, Optional, Union, Any
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
    Clase base para todos los evaluadores.

    Cada evaluador hereda de esta clase y tiene acceso a métodos
    utilitarios para extraer datos y calcular status.
    """

    # Umbrales por defecto para determinar status
    DEFAULT_PASS_THRESHOLD = 90.0
    DEFAULT_PARTIAL_THRESHOLD = 70.0

    def __init__(self, dimension: str):
        self.dimension = dimension
        self.results: List[CriteriaEvaluation] = []

    def evaluate(self, extracted_content: Dict) -> List[CriteriaEvaluation]:
        """
        Método principal que debe implementar cada evaluador.

        Recibe ExtractedContent como dict y retorna lista de evaluaciones.
        """
        raise NotImplementedError("Subclasses must implement evaluate()")

    def add_result(self, result: CriteriaEvaluation):
        """Agrega un resultado de evaluación."""
        self.results.append(result)

    def get_dimension_score(self) -> Dict:
        """Calcula el score total de la dimensión."""
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
        """Limpia los resultados."""
        self.results = []

    # ========================================================================
    # MÉTODOS UTILITARIOS COMPARTIDOS
    # ========================================================================

    @staticmethod
    def extract_count(data: Union[int, Dict[str, Any], None], default: int = 0) -> int:
        """
        Extrae el valor 'count' de una estructura flexible.

        Args:
            data: Puede ser int, dict con 'count', o None
            default: Valor por defecto si no se encuentra

        Returns:
            int: El count extraído o el default

        Examples:
            >>> extract_count(5)
            5
            >>> extract_count({'count': 10, 'present': True})
            10
            >>> extract_count(None)
            0
        """
        if data is None:
            return default
        if isinstance(data, int):
            return data
        if isinstance(data, dict):
            return data.get('count', default)
        return default

    @staticmethod
    def extract_present(data: Union[bool, Dict[str, Any], None], default: bool = False) -> bool:
        """
        Extrae el valor 'present' de una estructura flexible.

        Args:
            data: Puede ser bool, dict con 'present', o None
            default: Valor por defecto si no se encuentra

        Returns:
            bool: El present extraído o el default

        Examples:
            >>> extract_present(True)
            True
            >>> extract_present({'count': 10, 'present': True})
            True
            >>> extract_present(None)
            False
        """
        if data is None:
            return default
        if isinstance(data, bool):
            return data
        if isinstance(data, dict):
            return data.get('present', default)
        return default

    @staticmethod
    def calculate_status(
        percentage: float,
        pass_threshold: float = DEFAULT_PASS_THRESHOLD,
        partial_threshold: float = DEFAULT_PARTIAL_THRESHOLD
    ) -> str:
        """
        Calcula el status basado en porcentaje.

        Args:
            percentage: Porcentaje obtenido (0-100)
            pass_threshold: Umbral para "pass" (default: 90%)
            partial_threshold: Umbral para "partial" (default: 70%)

        Returns:
            str: "pass", "partial" o "fail"

        Examples:
            >>> calculate_status(95)
            'pass'
            >>> calculate_status(75)
            'partial'
            >>> calculate_status(50)
            'fail'
        """
        if percentage >= pass_threshold:
            return "pass"
        elif percentage >= partial_threshold:
            return "partial"
        else:
            return "fail"

    @staticmethod
    def safe_divide(numerator: float, denominator: float, default: float = 0.0) -> float:
        """
        División segura que evita división por cero.

        Args:
            numerator: Numerador
            denominator: Denominador
            default: Valor a retornar si denominator es 0

        Returns:
            float: Resultado de la división o default
        """
        if denominator == 0:
            return default
        return numerator / denominator
