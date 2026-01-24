"""
Detección de Ambigüedades en textos web.

Detecta textos problemáticos según WCAG 2.0:
- ACC-07: Labels ambiguos
- ACC-08: Enlaces no descriptivos
- ACC-09: Headings vagos

Categorías:
1. TEXTO_GENERICO: "Ver más", "Haga clic aquí"
2. TEXTO_AMBIGUO: "Nombre", "Fecha"
3. TEXTO_NO_DESCRIPTIVO: "Información", "Datos"
4. TEXTO_DEMASIADO_CORTO: < 3 caracteres
5. TEXTO_EXCESIVAMENTE_TECNICO: Siglas sin explicar

References:
    WCAG 2.0 Level AA - Web Content Accessibility Guidelines
"""

import logging
import re
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class AmbiguityCategory(Enum):
    """Categorías de ambigüedad según WCAG 2.0."""
    TEXTO_GENERICO = "genérico"
    TEXTO_AMBIGUO = "ambiguo"
    TEXTO_NO_DESCRIPTIVO = "no descriptivo"
    TEXTO_DEMASIADO_CORTO = "demasiado corto"
    TEXTO_EXCESIVAMENTE_TECNICO = "excesivamente técnico"
    TEXTO_CLARO = "claro"


@dataclass
class AmbiguityResult:
    """
    Resultado de análisis de ambigüedad.

    Attributes:
        text: Texto analizado
        element_type: 'link', 'label', 'heading', 'button'
        category: Categoría detectada
        is_problematic: True si es problemático
        confidence: Confianza [0-1]
        recommendation: Recomendación de mejora
        wcag_criterion: Criterio WCAG relacionado
    """
    text: str
    element_type: str
    category: AmbiguityCategory
    is_problematic: bool
    confidence: float
    recommendation: Optional[str] = None
    wcag_criterion: Optional[str] = None


class AmbiguityDetector:
    """
    Detector de ambigüedades mediante reglas heurísticas.

    Estrategia híbrida:
    1. Reglas heurísticas (diccionarios de patrones)
    2. BETO clasificación (fallback, actualmente deshabilitado)

    Attributes:
        min_text_length: Longitud mínima (default: 3)
        max_acronym_length: Máximo para sigla (default: 6)

    Example:
        >>> detector = AmbiguityDetector()
        >>> result = detector.analyze_text("Ver más", "link")
        >>> result.category
        AmbiguityCategory.TEXTO_GENERICO
        >>> result.is_problematic
        True
    """

    # Diccionarios de patrones problemáticos
    GENERIC_PATTERNS = {
        # Español común en .gob.bo
        "ver más", "ver mas", "leer más", "leer mas",
        "más", "mas", "ver", "leer",
        "haga clic aquí", "haga clic aqui", "clic aquí", "clic aqui",
        "click aquí", "click aqui", "haga click aquí", "haga click aqui",
        "clic", "click", "aquí", "aqui", "acá", "aca",
        "descargar", "download",
        "más información", "mas informacion", "información adicional",
        "ver detalles", "detalles", "ver detalle", "detalle",
        "continuar", "siguiente", "anterior", "volver",
        "ir", "ir a", "ir hacia",
        # Inglés común
        "read more", "see more", "more", "click here", "here",
        "details", "continue", "next", "back", "go",
        # Variaciones con símbolos
        "[+]", "(+)", "+ ver más", "+ ver mas",
        ">>", ">>>", "→", "=>",
        # Genéricos cortos
        "info", "datos", "doc", "arch"
    }

    AMBIGUOUS_PATTERNS = {
        # Campos de formulario sin contexto
        "nombre", "apellido", "apellidos",
        "fecha", "hora", "tiempo",
        "documento", "archivo", "file",
        "número", "numero", "nro", "n°", "nro.",
        "código", "codigo", "cod", "cod.",
        "tipo", "categoría", "categoria", "cat",
        "estado", "status", "situación", "situacion",
        "datos", "data", "información", "informacion",
        "valor", "value", "cantidad",
        "texto", "text", "descripción", "descripcion",
        "campo", "field", "input"
    }

    NON_DESCRIPTIVE_PATTERNS = {
        "información", "informacion", "info",
        "datos", "data",
        "sección", "seccion", "section",
        "contenido", "content",
        "detalles", "details", "detalle",
        "otros", "other", "otro", "otra",
        "adicional", "additional",
        "general", "varios", "varias",
        "elementos", "items", "cosas"
    }

    # Patrón para siglas (2-6 letras mayúsculas)
    ACRONYM_PATTERN = re.compile(r'\b[A-ZÁÉÍÓÚÑ]{2,6}\b')

    def __init__(
        self,
        min_text_length: int = 3,
        max_acronym_length: int = 6
    ):
        """
        Inicializa el detector.

        Args:
            min_text_length: Mínimo de caracteres
            max_acronym_length: Máximo para considerar sigla
        """
        self.min_text_length = min_text_length
        self.max_acronym_length = max_acronym_length

        logger.info(f"AmbiguityDetector inicializado (min_length={min_text_length})")

    def _normalize_text(self, text: str) -> str:
        """Normaliza texto para comparación."""
        return text.strip().lower()

    def _is_too_short(self, text: str) -> bool:
        """Verifica si el texto es demasiado corto."""
        return len(text.strip()) < self.min_text_length

    def _is_acronym(self, text: str) -> bool:
        """
        Verifica si es una sigla sin explicar.

        Criterios:
        - Todo mayúsculas
        - 2-6 caracteres
        - Sin palabras adicionales
        """
        text_clean = text.strip()

        # Solo letras y longitud correcta
        if not text_clean.isalpha():
            return False

        if not (2 <= len(text_clean) <= self.max_acronym_length):
            return False

        # Todo en mayúsculas
        return text_clean.isupper()

    def _classify_with_rules(self, text: str) -> Optional[AmbiguityCategory]:
        """
        Clasifica usando reglas heurísticas.

        Args:
            text: Texto a clasificar

        Returns:
            Categoría o None si no coincide
        """
        normalized = self._normalize_text(text)

        # Regla 1: Muy corto
        if self._is_too_short(text):
            return AmbiguityCategory.TEXTO_DEMASIADO_CORTO

        # Regla 2: Sigla
        if self._is_acronym(text):
            return AmbiguityCategory.TEXTO_EXCESIVAMENTE_TECNICO

        # Regla 3: Genérico
        if normalized in self.GENERIC_PATTERNS:
            return AmbiguityCategory.TEXTO_GENERICO

        # Regla 4: Ambiguo
        if normalized in self.AMBIGUOUS_PATTERNS:
            return AmbiguityCategory.TEXTO_AMBIGUO

        # Regla 5: No descriptivo
        if normalized in self.NON_DESCRIPTIVE_PATTERNS:
            return AmbiguityCategory.TEXTO_NO_DESCRIPTIVO

        return None

    def _generate_recommendation(
        self,
        text: str,
        category: AmbiguityCategory,
        element_type: str
    ) -> str:
        """
        Genera recomendación específica.

        Args:
            text: Texto problemático
            category: Categoría detectada
            element_type: Tipo de elemento

        Returns:
            Recomendación en español
        """
        recommendations = {
            AmbiguityCategory.TEXTO_GENERICO: {
                'link': f"El enlace '{text}' no describe su destino. Use texto descriptivo como 'Descargar informe anual 2024' o 'Ver requisitos para trámite de pasaporte'.",
                'button': f"El botón '{text}' no describe su acción. Use texto específico como 'Buscar documentos' o 'Enviar solicitud'.",
                'heading': f"El encabezado '{text}' es genérico. Use títulos descriptivos que indiquen claramente el contenido de la sección."
            },
            AmbiguityCategory.TEXTO_AMBIGUO: {
                'label': f"El label '{text}' es ambiguo. Agregue contexto: 'Nombre completo', 'Fecha de nacimiento', 'Número de documento de identidad'.",
                'link': f"El enlace '{text}' necesita más contexto. Especifique qué tipo de documento o información se descargará.",
                'heading': f"El encabezado '{text}' es muy vago. Especifique de qué trata la sección."
            },
            AmbiguityCategory.TEXTO_NO_DESCRIPTIVO: {
                'heading': f"El encabezado '{text}' no describe el contenido. Use títulos específicos como 'Requisitos para inscripción' o 'Horarios de atención'.",
                'link': f"El enlace '{text}' no indica su propósito. Describa qué información o acción proporciona.",
                'button': f"El botón '{text}' no es claro. Indique específicamente qué acción realizará."
            },
            AmbiguityCategory.TEXTO_DEMASIADO_CORTO: {
                'link': f"El enlace '{text}' es demasiado corto. Amplíe a al menos 5-10 caracteres con texto descriptivo.",
                'label': f"El label '{text}' es demasiado corto. Proporcione una descripción clara del campo.",
                'button': f"El botón '{text}' es demasiado corto. Use al menos 5 caracteres descriptivos."
            },
            AmbiguityCategory.TEXTO_EXCESIVAMENTE_TECNICO: {
                'link': f"La sigla '{text}' no es comprensible para todos los usuarios. Agregue el significado completo: '{text} (Nombre Completo de la Sigla)'.",
                'label': f"La sigla '{text}' necesita explicación. Use '{text} (significado completo)' o expanda totalmente.",
                'heading': f"La sigla '{text}' como encabezado no es accesible. Expanda el significado completo."
            }
        }

        # Obtener recomendación por categoría y tipo
        category_recs = recommendations.get(category, {})
        rec = category_recs.get(element_type)

        # Fallback genérico
        if not rec:
            rec = f"El texto '{text}' presenta problemas de claridad. Reemplace con texto más descriptivo y específico."

        return rec

    def _get_wcag_criterion(self, category: AmbiguityCategory) -> str:
        """Obtiene criterio WCAG relacionado."""
        mapping = {
            AmbiguityCategory.TEXTO_GENERICO: "ACC-08 (WCAG 2.4.4 Link Purpose - Level A)",
            AmbiguityCategory.TEXTO_AMBIGUO: "ACC-07 (WCAG 3.3.2 Labels or Instructions - Level A)",
            AmbiguityCategory.TEXTO_NO_DESCRIPTIVO: "ACC-09 (WCAG 2.4.6 Headings and Labels - Level AA)",
            AmbiguityCategory.TEXTO_DEMASIADO_CORTO: "ACC-08 (WCAG 2.4.4 Link Purpose - Level A)",
            AmbiguityCategory.TEXTO_EXCESIVAMENTE_TECNICO: "ACC-09 (WCAG 2.4.6 Headings and Labels - Level AA)"
        }
        return mapping.get(category, "WCAG 2.0 Accessibility")

    def analyze_text(
        self,
        text: str,
        element_type: str = 'link'
    ) -> AmbiguityResult:
        """
        Analiza un texto individual.

        Args:
            text: Texto a analizar
            element_type: 'link', 'label', 'heading', 'button'

        Returns:
            AmbiguityResult con clasificación

        Example:
            >>> detector = AmbiguityDetector()
            >>> result = detector.analyze_text("Ver más", "link")
            >>> result.is_problematic
            True
            >>> result.category
            AmbiguityCategory.TEXTO_GENERICO
        """
        if not text or not text.strip():
            return AmbiguityResult(
                text="[VACÍO]",
                element_type=element_type,
                category=AmbiguityCategory.TEXTO_DEMASIADO_CORTO,
                is_problematic=True,
                confidence=1.0,
                recommendation="El texto está vacío. Proporcione texto descriptivo.",
                wcag_criterion="WCAG 2.0 Multiple criteria"
            )

        # Clasificar con reglas
        category = self._classify_with_rules(text)

        # Si no se detectó problema, asumir claro
        if category is None:
            return AmbiguityResult(
                text=text,
                element_type=element_type,
                category=AmbiguityCategory.TEXTO_CLARO,
                is_problematic=False,
                confidence=0.8,  # Confianza moderada (no usamos BETO)
                recommendation=None,
                wcag_criterion=None
            )

        # Generar recomendación
        recommendation = self._generate_recommendation(text, category, element_type)
        wcag_criterion = self._get_wcag_criterion(category)

        logger.debug(f"'{text}' ({element_type}): {category.value}")

        return AmbiguityResult(
            text=text,
            element_type=element_type,
            category=category,
            is_problematic=True,
            confidence=1.0,  # Alta confianza en reglas
            recommendation=recommendation,
            wcag_criterion=wcag_criterion
        )

    def analyze_multiple(
        self,
        texts: List[Dict[str, str]]
    ) -> Dict[str, Any]:
        """
        Analiza múltiples textos.

        Args:
            texts: [
                {'text': 'Ver más', 'element_type': 'link'},
                {'text': 'Nombre', 'element_type': 'label'},
                ...
            ]

        Returns:
            {
                'total_analyzed': int,
                'problematic_count': int,
                'clear_count': int,
                'by_category': Dict[str, int],
                'by_element_type': Dict[str, int],
                'details': List[Dict],
                'recommendations': List[str]
            }
        """
        if not texts:
            return {
                'total_analyzed': 0,
                'problematic_count': 0,
                'clear_count': 0,
                'by_category': {},
                'by_element_type': {},
                'details': [],
                'recommendations': []
            }

        logger.info(f"Analizando {len(texts)} textos")

        results = []
        for item in texts:
            result = self.analyze_text(
                text=item['text'],
                element_type=item.get('element_type', 'link')
            )
            results.append(result)

        # Estadísticas
        problematic_count = sum(1 for r in results if r.is_problematic)
        clear_count = len(results) - problematic_count

        # Por categoría
        by_category = {}
        for r in results:
            cat = r.category.value
            by_category[cat] = by_category.get(cat, 0) + 1

        # Por tipo de elemento
        by_element_type = {}
        for r in results:
            et = r.element_type
            by_element_type[et] = by_element_type.get(et, 0) + 1

        # Recomendaciones
        recommendations = [r.recommendation for r in results if r.recommendation]

        # Detalles
        details = [
            {
                'text': r.text,
                'element_type': r.element_type,
                'category': r.category.value,
                'is_problematic': r.is_problematic,
                'confidence': r.confidence,
                'recommendation': r.recommendation,
                'wcag_criterion': r.wcag_criterion
            }
            for r in results
        ]

        summary = {
            'total_analyzed': len(results),
            'problematic_count': problematic_count,
            'clear_count': clear_count,
            'by_category': by_category,
            'by_element_type': by_element_type,
            'details': details,
            'recommendations': recommendations
        }

        logger.info(
            f"Ambigüedades: {problematic_count}/{len(results)} problemáticos"
        )

        return summary
