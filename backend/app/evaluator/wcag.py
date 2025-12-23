"""
Evaluador de accesibilidad WCAG 2.0.

Implementa verificaciones de criterios de accesibilidad web según
las pautas WCAG 2.0 nivel A y AA.
"""

from typing import Dict, List, Optional
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class WCAGCriteria:
    """
    Criterio WCAG 2.0.

    Attributes:
        code: Código del criterio (ej: WCAG-1.1.1)
        name: Nombre del criterio
        description: Descripción detallada
        level: Nivel (A, AA, AAA)
        principle: Principio (Percibible, Operable, Comprensible, Robusto)
        weight: Peso del criterio
    """
    code: str
    name: str
    description: str
    level: str
    principle: str
    weight: float = 1.0


class WCAGEvaluator:
    """
    Evaluador de accesibilidad WCAG 2.0.

    Verifica cumplimiento de criterios de accesibilidad web
    según WCAG 2.0 niveles A y AA.
    """

    # Criterios WCAG 2.0 principales
    CRITERIA = [
        # Principio 1: Percibible
        WCAGCriteria(
            code="WCAG-1.1.1",
            name="Contenido no textual",
            description="Todo contenido no textual debe tener alternativa textual",
            level="A",
            principle="Percibible",
            weight=2.0
        ),
        WCAGCriteria(
            code="WCAG-1.3.1",
            name="Información y relaciones",
            description="Estructura y relaciones deben estar programáticamente determinadas",
            level="A",
            principle="Percibible",
            weight=1.5
        ),
        WCAGCriteria(
            code="WCAG-1.4.1",
            name="Uso del color",
            description="El color no debe ser el único medio visual de transmitir información",
            level="A",
            principle="Percibible",
            weight=1.0
        ),
        WCAGCriteria(
            code="WCAG-1.4.3",
            name="Contraste mínimo",
            description="Relación de contraste mínima de 4.5:1",
            level="AA",
            principle="Percibible",
            weight=1.5
        ),

        # Principio 2: Operable
        WCAGCriteria(
            code="WCAG-2.1.1",
            name="Teclado",
            description="Toda funcionalidad debe ser operable por teclado",
            level="A",
            principle="Operable",
            weight=2.0
        ),
        WCAGCriteria(
            code="WCAG-2.4.1",
            name="Evitar bloques",
            description="Mecanismo para evitar bloques de contenido repetidos",
            level="A",
            principle="Operable",
            weight=1.0
        ),
        WCAGCriteria(
            code="WCAG-2.4.2",
            name="Página titulada",
            description="Las páginas web deben tener títulos descriptivos",
            level="A",
            principle="Operable",
            weight=2.0
        ),
        WCAGCriteria(
            code="WCAG-2.4.4",
            name="Propósito de los enlaces",
            description="El propósito de cada enlace debe determinarse desde el texto del enlace",
            level="A",
            principle="Operable",
            weight=1.5
        ),

        # Principio 3: Comprensible
        WCAGCriteria(
            code="WCAG-3.1.1",
            name="Idioma de la página",
            description="El idioma predeterminado debe estar programáticamente determinado",
            level="A",
            principle="Comprensible",
            weight=1.5
        ),
        WCAGCriteria(
            code="WCAG-3.2.3",
            name="Navegación consistente",
            description="Mecanismos de navegación repetidos deben ocurrir en el mismo orden",
            level="AA",
            principle="Comprensible",
            weight=1.0
        ),

        # Principio 4: Robusto
        WCAGCriteria(
            code="WCAG-4.1.1",
            name="Procesamiento",
            description="Elementos deben tener etiquetas de inicio y fin completas",
            level="A",
            principle="Robusto",
            weight=1.5
        ),
        WCAGCriteria(
            code="WCAG-4.1.2",
            name="Nombre, función, valor",
            description="Componentes de interfaz deben tener nombre y función determinables",
            level="A",
            principle="Robusto",
            weight=1.5
        ),
    ]

    def __init__(self):
        """Inicializa el evaluador WCAG."""
        self.criteria_dict = {c.code: c for c in self.CRITERIA}
        logger.info("Evaluador WCAG 2.0 inicializado")

    def evaluate(self, page_data: Dict) -> Dict[str, any]:
        """
        Evalúa una página según criterios WCAG 2.0.

        Args:
            page_data: Datos extraídos de la página web

        Returns:
            dict: Resultados de la evaluación por criterio
        """
        results = {}

        # Evaluar cada criterio
        results["WCAG-1.1.1"] = self._check_alt_text(page_data)
        results["WCAG-1.3.1"] = self._check_semantic_structure(page_data)
        results["WCAG-1.4.1"] = self._check_color_usage(page_data)
        results["WCAG-1.4.3"] = self._check_contrast(page_data)
        results["WCAG-2.1.1"] = self._check_keyboard_accessible(page_data)
        results["WCAG-2.4.1"] = self._check_skip_links(page_data)
        results["WCAG-2.4.2"] = self._check_page_title(page_data)
        results["WCAG-2.4.4"] = self._check_link_purpose(page_data)
        results["WCAG-3.1.1"] = self._check_language(page_data)
        results["WCAG-3.2.3"] = self._check_consistent_navigation(page_data)
        results["WCAG-4.1.1"] = self._check_valid_html(page_data)
        results["WCAG-4.1.2"] = self._check_aria_labels(page_data)

        return results

    def _check_alt_text(self, data: Dict) -> Dict:
        """Verifica que las imágenes tengan texto alternativo"""
        images = data.get('images', [])

        if not images:
            return {
                'status': 'na',
                'score': None,
                'details': {'message': 'No hay imágenes para evaluar'}
            }

        total_images = len(images)
        images_with_alt = len([img for img in images if img.get('alt')])
        percentage = (images_with_alt / total_images * 100) if total_images > 0 else 0

        passed = percentage >= 90  # 90% de imágenes deben tener alt

        return {
            'status': 'pass' if passed else 'fail',
            'score': percentage,
            'details': {
                'total_images': total_images,
                'images_with_alt': images_with_alt,
                'percentage': round(percentage, 2)
            }
        }

    def _check_semantic_structure(self, data: Dict) -> Dict:
        """Verifica uso de estructura semántica"""
        headings = data.get('headings', {})
        has_h1 = bool(headings.get('h1', []))

        # Verificar jerarquía de headings
        h1_count = len(headings.get('h1', []))
        proper_hierarchy = h1_count == 1  # Debe haber exactamente un H1

        passed = has_h1 and proper_hierarchy

        return {
            'status': 'pass' if passed else 'fail',
            'score': 100 if passed else 50,
            'details': {
                'has_h1': has_h1,
                'h1_count': h1_count,
                'message': 'Estructura semántica correcta' if passed
                          else 'Problemas en jerarquía de headings'
            }
        }

    def _check_color_usage(self, data: Dict) -> Dict:
        """Verifica que no se use solo color para transmitir información"""
        # TODO: Requiere análisis de CSS y estilos
        return {
            'status': 'na',
            'score': None,
            'details': {
                'message': 'Requiere análisis de CSS y estilos'
            }
        }

    def _check_contrast(self, data: Dict) -> Dict:
        """Verifica contraste de colores"""
        # TODO: Requiere análisis de colores y contraste
        return {
            'status': 'na',
            'score': None,
            'details': {
                'message': 'Requiere análisis de contraste de colores'
            }
        }

    def _check_keyboard_accessible(self, data: Dict) -> Dict:
        """Verifica accesibilidad por teclado"""
        # TODO: Requiere pruebas interactivas
        return {
            'status': 'na',
            'score': None,
            'details': {
                'message': 'Requiere pruebas de navegación por teclado'
            }
        }

    def _check_skip_links(self, data: Dict) -> Dict:
        """Verifica presencia de enlaces de salto"""
        links = data.get('links', [])
        skip_link_keywords = ['skip', 'saltar', 'ir al contenido', 'skip to content']

        has_skip_link = any(
            any(keyword in link.lower() for keyword in skip_link_keywords)
            for link in [l.get('text', '') for l in links]
        )

        return {
            'status': 'pass' if has_skip_link else 'fail',
            'score': 100 if has_skip_link else 0,
            'details': {
                'message': 'Enlaces de salto presentes' if has_skip_link
                          else 'No se encontraron enlaces de salto'
            }
        }

    def _check_page_title(self, data: Dict) -> Dict:
        """Verifica que la página tenga título"""
        title = data.get('title', '')
        has_title = bool(title.strip())
        is_descriptive = len(title.strip()) > 5

        passed = has_title and is_descriptive

        return {
            'status': 'pass' if passed else 'fail',
            'score': 100 if passed else 0,
            'details': {
                'title': title,
                'length': len(title),
                'message': 'Título descriptivo presente' if passed
                          else 'Título ausente o no descriptivo'
            }
        }

    def _check_link_purpose(self, data: Dict) -> Dict:
        """Verifica que los enlaces tengan propósito claro"""
        links = data.get('links', [])

        if not links:
            return {
                'status': 'na',
                'score': None,
                'details': {'message': 'No hay enlaces para evaluar'}
            }

        vague_text = ['clic aquí', 'click here', 'más', 'more', 'ver más', 'read more']
        total_links = len(links)
        vague_links = len([
            l for l in links
            if any(vague in l.get('text', '').lower() for vague in vague_text)
        ])

        percentage = ((total_links - vague_links) / total_links * 100) if total_links > 0 else 0
        passed = percentage >= 80

        return {
            'status': 'pass' if passed else 'fail',
            'score': percentage,
            'details': {
                'total_links': total_links,
                'vague_links': vague_links,
                'percentage': round(percentage, 2)
            }
        }

    def _check_language(self, data: Dict) -> Dict:
        """Verifica que el idioma esté declarado"""
        language = data.get('language', '')
        has_lang = language and language != 'unknown'

        return {
            'status': 'pass' if has_lang else 'fail',
            'score': 100 if has_lang else 0,
            'details': {
                'language': language,
                'message': f'Idioma declarado: {language}' if has_lang
                          else 'Idioma no declarado en HTML'
            }
        }

    def _check_consistent_navigation(self, data: Dict) -> Dict:
        """Verifica navegación consistente"""
        # TODO: Requiere análisis de múltiples páginas
        return {
            'status': 'na',
            'score': None,
            'details': {
                'message': 'Requiere análisis de múltiples páginas'
            }
        }

    def _check_valid_html(self, data: Dict) -> Dict:
        """Verifica validez del HTML"""
        # TODO: Requiere validación con W3C validator
        return {
            'status': 'na',
            'score': None,
            'details': {
                'message': 'Requiere validación con W3C validator'
            }
        }

    def _check_aria_labels(self, data: Dict) -> Dict:
        """Verifica uso de atributos ARIA"""
        # TODO: Implementar verificación de ARIA
        return {
            'status': 'na',
            'score': None,
            'details': {
                'message': 'Requiere análisis de atributos ARIA'
            }
        }

    def get_criteria_by_level(self, level: str) -> List[WCAGCriteria]:
        """
        Obtiene criterios por nivel.

        Args:
            level: Nivel WCAG (A, AA, AAA)

        Returns:
            list: Lista de criterios del nivel
        """
        return [c for c in self.CRITERIA if c.level == level]

    def get_criteria_by_principle(self, principle: str) -> List[WCAGCriteria]:
        """
        Obtiene criterios por principio.

        Args:
            principle: Principio WCAG

        Returns:
            list: Lista de criterios del principio
        """
        return [c for c in self.CRITERIA if c.principle == principle]
