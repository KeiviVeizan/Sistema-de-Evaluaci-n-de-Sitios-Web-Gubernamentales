"""
Calculador de puntajes de evaluación.

Calcula puntajes finales basándose en los resultados de evaluación
de D.S. 3925 y WCAG 2.0.
"""

from typing import Dict, List
import logging

logger = logging.getLogger(__name__)


class ScoreCalculator:
    """
    Calculador de puntajes de evaluación.

    Combina y pondera resultados de diferentes evaluadores para
    generar puntajes finales.
    """

    # Pesos para cada categoría en el puntaje total
    CATEGORY_WEIGHTS = {
        'digital_sovereignty': 0.30,  # D.S. 3925 - Soberanía Digital
        'accessibility': 0.30,         # WCAG 2.0
        'usability': 0.20,             # Usabilidad general
        'semantic_web': 0.20           # Web semántica y estándares
    }

    def __init__(self):
        """Inicializa el calculador de puntajes."""
        logger.info("Calculador de puntajes inicializado")

    def calculate_ds3925_score(self, results: Dict[str, Dict]) -> float:
        """
        Calcula el puntaje de D.S. 3925.

        Args:
            results: Resultados de evaluación D.S. 3925

        Returns:
            float: Puntaje de 0 a 100
        """
        if not results:
            return 0.0

        total_weight = 0.0
        weighted_score = 0.0

        for code, result in results.items():
            if result['status'] == 'na':
                continue

            # Obtener peso del criterio (por defecto 1.0)
            weight = 1.0  # TODO: Obtener peso real del criterio

            score = result.get('score', 0) or 0
            weighted_score += score * weight
            total_weight += weight

        final_score = (weighted_score / total_weight) if total_weight > 0 else 0.0
        return round(final_score, 2)

    def calculate_wcag_score(self, results: Dict[str, Dict]) -> float:
        """
        Calcula el puntaje WCAG.

        Args:
            results: Resultados de evaluación WCAG

        Returns:
            float: Puntaje de 0 a 100
        """
        if not results:
            return 0.0

        total_weight = 0.0
        weighted_score = 0.0

        for code, result in results.items():
            if result['status'] == 'na':
                continue

            # Criterios nivel A tienen más peso que AA
            weight = 2.0 if 'A' in code else 1.0

            score = result.get('score', 0) or 0
            weighted_score += score * weight
            total_weight += weight

        final_score = (weighted_score / total_weight) if total_weight > 0 else 0.0
        return round(final_score, 2)

    def calculate_usability_score(self, page_data: Dict) -> float:
        """
        Calcula el puntaje de usabilidad.

        Args:
            page_data: Datos de la página web

        Returns:
            float: Puntaje de 0 a 100
        """
        score = 0.0
        max_score = 0.0

        # Tiene título descriptivo (20 puntos)
        max_score += 20
        title = page_data.get('title', '')
        if title and len(title) > 10:
            score += 20

        # Tiene meta descripción (15 puntos)
        max_score += 15
        meta_desc = page_data.get('meta_description', '')
        if meta_desc and len(meta_desc) > 20:
            score += 15

        # Tiene estructura de headings (20 puntos)
        max_score += 20
        headings = page_data.get('headings', {})
        if headings.get('h1') and headings.get('h2'):
            score += 20

        # Tiene formularios (15 puntos)
        max_score += 15
        if page_data.get('has_forms', False):
            score += 15

        # Navegación clara (15 puntos)
        max_score += 15
        links = page_data.get('links', [])
        if len(links) >= 5:
            score += 15

        # Tiempo de carga aceptable (15 puntos)
        max_score += 15
        # TODO: Implementar medición de tiempo de carga
        score += 10  # Puntaje parcial por defecto

        final_score = (score / max_score * 100) if max_score > 0 else 0.0
        return round(final_score, 2)

    def calculate_semantic_web_score(self, page_data: Dict) -> float:
        """
        Calcula el puntaje de web semántica.

        Args:
            page_data: Datos de la página web

        Returns:
            float: Puntaje de 0 a 100
        """
        score = 0.0
        max_score = 0.0

        # Usa HTML5 semántico (30 puntos)
        max_score += 30
        # TODO: Verificar uso de etiquetas semánticas HTML5
        score += 15  # Puntaje parcial por defecto

        # Usa microdatos/schema.org (25 puntos)
        max_score += 25
        # TODO: Verificar presencia de microdatos
        score += 0

        # Estructura de datos clara (20 puntos)
        max_score += 20
        headings = page_data.get('headings', {})
        if headings.get('h1') and len(headings.get('h2', [])) > 0:
            score += 20

        # Tiene idioma declarado (15 puntos)
        max_score += 15
        language = page_data.get('language', '')
        if language and language != 'unknown':
            score += 15

        # URLs semánticas (10 puntos)
        max_score += 10
        url = page_data.get('url', '')
        if self._is_semantic_url(url):
            score += 10

        final_score = (score / max_score * 100) if max_score > 0 else 0.0
        return round(final_score, 2)

    def calculate_total_score(self, scores: Dict[str, float]) -> float:
        """
        Calcula el puntaje total ponderado.

        Args:
            scores: Diccionario con puntajes por categoría

        Returns:
            float: Puntaje total de 0 a 100
        """
        total = 0.0

        total += scores.get('digital_sovereignty', 0) * self.CATEGORY_WEIGHTS['digital_sovereignty']
        total += scores.get('accessibility', 0) * self.CATEGORY_WEIGHTS['accessibility']
        total += scores.get('usability', 0) * self.CATEGORY_WEIGHTS['usability']
        total += scores.get('semantic_web', 0) * self.CATEGORY_WEIGHTS['semantic_web']

        return round(total, 2)

    def get_score_classification(self, score: float) -> str:
        """
        Clasifica un puntaje.

        Args:
            score: Puntaje de 0 a 100

        Returns:
            str: Clasificación del puntaje
        """
        if score >= 90:
            return "Excelente"
        elif score >= 75:
            return "Bueno"
        elif score >= 60:
            return "Regular"
        elif score >= 40:
            return "Deficiente"
        else:
            return "Muy deficiente"

    def generate_summary(
        self,
        ds3925_results: Dict,
        wcag_results: Dict,
        page_data: Dict
    ) -> Dict:
        """
        Genera un resumen completo de la evaluación.

        Args:
            ds3925_results: Resultados D.S. 3925
            wcag_results: Resultados WCAG
            page_data: Datos de la página

        Returns:
            dict: Resumen completo con todos los puntajes
        """
        # Calcular puntajes individuales
        ds_score = self.calculate_ds3925_score(ds3925_results)
        wcag_score = self.calculate_wcag_score(wcag_results)
        usability_score = self.calculate_usability_score(page_data)
        semantic_score = self.calculate_semantic_web_score(page_data)

        scores = {
            'digital_sovereignty': ds_score,
            'accessibility': wcag_score,
            'usability': usability_score,
            'semantic_web': semantic_score
        }

        # Calcular puntaje total
        total_score = self.calculate_total_score(scores)

        return {
            'scores': scores,
            'total_score': total_score,
            'classification': self.get_score_classification(total_score),
            'details': {
                'ds3925_passed': self._count_passed(ds3925_results),
                'ds3925_failed': self._count_failed(ds3925_results),
                'wcag_passed': self._count_passed(wcag_results),
                'wcag_failed': self._count_failed(wcag_results),
            }
        }

    def _is_semantic_url(self, url: str) -> bool:
        """Verifica si una URL es semántica."""
        # URLs semánticas usan palabras en lugar de IDs numéricos
        return not any(char.isdigit() for char in url.split('/')[-1])

    def _count_passed(self, results: Dict) -> int:
        """Cuenta criterios aprobados."""
        return len([r for r in results.values() if r['status'] == 'pass'])

    def _count_failed(self, results: Dict) -> int:
        """Cuenta criterios fallados."""
        return len([r for r in results.values() if r['status'] == 'fail'])
