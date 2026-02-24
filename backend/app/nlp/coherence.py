"""
Análisis de Coherencia Semántica para evaluación de sitios web.

Evalúa coherencia entre encabezados (h1-h6) y contenido asociado usando
embeddings BETO y similitud coseno.

Criterios WCAG:
- ACC-09 (WCAG 2.4.6): Headings and Labels - Level AA

References:
    Cañete, J., et al. (2020). Spanish Pre-Trained BERT Model.
    Reimers & Gurevych (2019). Sentence-BERT.

Umbral Calibrado:
    Umbral óptimo de 0.80 obtenido mediante calibración experimental
    con 1,068 ejemplos de sitios gubernamentales bolivianos.
    Métricas: Precisión=85.39%, Recall=83.36%, F1-Score=84.37%
"""

import logging
from typing import Dict, Optional, Any
from dataclasses import dataclass
import numpy as np
import json
import os
from pathlib import Path

from .models import beto_manager

logger = logging.getLogger(__name__)

# Constante global del umbral calibrado
UMBRAL_OPTIMO_CALIBRADO = 0.80


def cargar_umbral_calibrado() -> float:
    """
    Carga el umbral óptimo desde el archivo JSON de calibración.

    Returns:
        float: Umbral calibrado (default: 0.80 si no se encuentra el archivo)

    Note:
        El archivo umbral_optimo.json se genera mediante calibracion_umbral.py
        con métricas validadas en 1,068 ejemplos reales.
    """
    try:
        # Buscar umbral_optimo.json en el directorio nlp
        json_path = Path(__file__).parent / 'umbral_optimo.json'

        if json_path.exists():
            with open(json_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
                umbral = config.get('umbral_optimo', UMBRAL_OPTIMO_CALIBRADO)
                precision = config.get('precision', 0)
                recall = config.get('recall', 0)
                f1 = config.get('f1_score', 0)

                logger.info(
                    f"Umbral calibrado cargado: {umbral:.2f} "
                    f"(P={precision:.3f}, R={recall:.3f}, F1={f1:.3f})"
                )
                return float(umbral)
        else:
            logger.warning(
                f"Archivo {json_path} no encontrado. "
                f"Usando umbral calibrado por defecto: {UMBRAL_OPTIMO_CALIBRADO}"
            )
            return UMBRAL_OPTIMO_CALIBRADO

    except Exception as e:
        logger.error(f"Error al cargar umbral calibrado: {str(e)}")
        logger.info(f"Usando umbral por defecto: {UMBRAL_OPTIMO_CALIBRADO}")
        return UMBRAL_OPTIMO_CALIBRADO


@dataclass
class SectionCoherence:
    """
    Resultado de análisis de coherencia para una sección.

    Attributes:
        heading: Texto del encabezado
        heading_level: Nivel (1-6)
        content: Contenido de la sección
        word_count: Palabras en contenido
        similarity_score: Similitud coseno [0, 1]
        is_coherent: True si >= threshold
        recommendation: Recomendación si no es coherente
    """
    heading: str
    heading_level: int
    content: str
    word_count: int
    similarity_score: float
    is_coherent: bool
    recommendation: Optional[str] = None


class CoherenceAnalyzer:
    """
    Analizador de coherencia semántica entre encabezados y contenido.

    Implementa similitud coseno entre embeddings BETO con umbral calibrable.

    Attributes:
        coherence_threshold: Umbral [0.5-0.9], default 0.7
        min_content_words: Palabras mínimas, default 10
        max_content_chars: Caracteres máximos, default 2000

    Example:
        >>> analyzer = CoherenceAnalyzer(coherence_threshold=0.7)
        >>> result = analyzer.analyze_section(
        ...     heading="Servicios de Salud",
        ...     content="El ministerio ofrece atención médica..."
        ... )
        >>> result.is_coherent
        True
    """

    def __init__(
        self,
        coherence_threshold: Optional[float] = None,
        min_content_words: int = 10,
        max_content_chars: int = 2000
    ):
        """
        Inicializa el analizador con umbral calibrado.

        Args:
            coherence_threshold: Umbral de similitud [0.5-0.9].
                                Si es None, carga el umbral calibrado (0.80)
            min_content_words: Palabras mínimas para análisis
            max_content_chars: Máximo de caracteres (trunca)

        Raises:
            ValueError: Si threshold fuera de rango

        Note:
            El umbral por defecto (0.80) fue calibrado experimentalmente
            con 1,068 ejemplos y ofrece F1-Score de 84.37%.
        """
        # Cargar umbral calibrado si no se especifica
        if coherence_threshold is None:
            coherence_threshold = cargar_umbral_calibrado()
            logger.info(
                f"Usando umbral calibrado óptimo: {coherence_threshold:.2f} "
                f"(Precisión=85.39%, Recall=83.36%, F1=84.37%)"
            )

        if not 0.5 <= coherence_threshold <= 0.9:
            raise ValueError("Threshold debe estar entre 0.5 y 0.9")

        self.coherence_threshold = coherence_threshold
        self.min_content_words = min_content_words
        self.max_content_chars = max_content_chars

        logger.info(
            f"CoherenceAnalyzer inicializado con threshold={coherence_threshold:.2f}"
        )

    def _validate_text_corpus(self, text_corpus: Dict[str, Any]) -> None:
        """
        Valida estructura del text_corpus.

        Args:
            text_corpus: Diccionario con 'sections'

        Raises:
            ValueError: Si estructura inválida
        """
        if not isinstance(text_corpus, dict):
            raise ValueError("text_corpus debe ser un diccionario")

        if 'sections' not in text_corpus:
            raise ValueError("text_corpus debe contener 'sections'")

        if not isinstance(text_corpus['sections'], list):
            raise ValueError("'sections' debe ser una lista")

    def _truncate_content(self, content: str) -> str:
        """Trunca contenido largo."""
        if len(content) <= self.max_content_chars:
            return content
        return content[:self.max_content_chars]

    def _generate_recommendation(self, heading: str, similarity: float) -> str:
        """
        Genera recomendación según nivel de coherencia.

        Args:
            heading: Texto del encabezado
            similarity: Score obtenido

        Returns:
            Recomendación en español
        """
        if similarity < 0.5:
            return (
                f"El contenido bajo '{heading}' no está relacionado con el título. "
                f"Recomendación: Revisar que el contenido corresponda al tema "
                f"indicado o cambiar el título para reflejar mejor el contenido."
            )
        elif similarity < 0.7:
            return (
                f"El contenido bajo '{heading}' está parcialmente relacionado. "
                f"Recomendación: Mejorar la alineación entre título y contenido, "
                f"asegurando que los primeros párrafos traten directamente el tema "
                f"indicado en el encabezado."
            )
        return None

    def analyze_section(
        self,
        heading: str,
        content: str,
        heading_level: int = 2
    ) -> SectionCoherence:
        """
        Analiza coherencia de una sección individual.

        Args:
            heading: Texto del encabezado
            content: Contenido de la sección
            heading_level: Nivel del heading (1-6)

        Returns:
            SectionCoherence con resultados

        Example:
            >>> result = analyzer.analyze_section(
            ...     heading="Trámites",
            ...     content="Información sobre documentos requeridos..."
            ... )
            >>> result.similarity_score
            0.823
        """
        # Validar heading
        if not heading or not heading.strip():
            logger.warning("Heading vacío")
            return SectionCoherence(
                heading="[VACÍO]",
                heading_level=heading_level,
                content=content,
                word_count=len(content.split()),
                similarity_score=0.0,
                is_coherent=False,
                recommendation="El encabezado está vacío."
            )

        # Validar content
        if not content or not content.strip():
            logger.warning("Content vacío")
            return SectionCoherence(
                heading=heading,
                heading_level=heading_level,
                content="[VACÍO]",
                word_count=0,
                similarity_score=0.0,
                is_coherent=False,
                recommendation=f"La sección '{heading}' no tiene contenido."
            )

        # Contar palabras
        word_count = len(content.split())

        # Si muy corto, asumir coherente
        if word_count < self.min_content_words:
            logger.debug(f"Contenido muy corto ({word_count} palabras)")
            return SectionCoherence(
                heading=heading,
                heading_level=heading_level,
                content=content,
                word_count=word_count,
                similarity_score=1.0,
                is_coherent=True,
                recommendation=None
            )

        try:
            # Truncar contenido
            content_truncated = self._truncate_content(content)

            # Calcular similitud con BETO
            similarity = beto_manager.compute_similarity(
                text1=heading,
                text2=content_truncated,
                metric='cosine'
            )

            # Determinar coherencia
            is_coherent = similarity >= self.coherence_threshold

            # Generar recomendación
            recommendation = None if is_coherent else self._generate_recommendation(
                heading, similarity
            )

            logger.debug(
                f"'{heading[:50]}...': similarity={similarity:.3f}, "
                f"coherent={is_coherent}"
            )

            return SectionCoherence(
                heading=heading,
                heading_level=heading_level,
                content=content,
                word_count=word_count,
                similarity_score=float(similarity),
                is_coherent=is_coherent,
                recommendation=recommendation
            )

        except Exception as e:
            logger.error(f"Error al analizar '{heading}': {str(e)}")
            return SectionCoherence(
                heading=heading,
                heading_level=heading_level,
                content=content,
                word_count=word_count,
                similarity_score=0.0,
                is_coherent=False,
                recommendation=f"Error en análisis: {str(e)}"
            )

    def analyze_coherence(self, text_corpus: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analiza coherencia de todas las secciones de un sitio.

        Args:
            text_corpus: {
                'url': str,
                'sections': [
                    {
                        'heading': str,
                        'heading_level': int,
                        'content': str,
                        'word_count': int
                    }
                ]
            }

        Returns:
            {
                'coherence_score': float (0-100),
                'sections_analyzed': int,
                'coherent_sections': int,
                'incoherent_sections': int,
                'average_similarity': float (0-1),
                'threshold_used': float,
                'details': List[Dict],
                'recommendations': List[str]
            }

        Example:
            >>> result = analyzer.analyze_coherence(text_corpus)
            >>> result['coherence_score']
            78.5
        """
        # Validar entrada
        self._validate_text_corpus(text_corpus)

        sections = text_corpus['sections']

        if not sections:
            logger.warning("No hay secciones para analizar")
            return {
                'coherence_score': 0.0,
                'sections_analyzed': 0,
                'coherent_sections': 0,
                'incoherent_sections': 0,
                'average_similarity': 0.0,
                'threshold_used': self.coherence_threshold,
                'details': [],
                'recommendations': ["No se encontraron secciones."]
            }

        logger.info(f"Analizando {len(sections)} secciones")

        # Analizar cada sección
        section_results = []
        for section in sections:
            result = self.analyze_section(
                heading=section['heading'],
                content=section['content'],
                heading_level=section.get('heading_level', 2)
            )
            section_results.append(result)

        # Calcular estadísticas
        coherent_count = sum(1 for r in section_results if r.is_coherent)
        incoherent_count = len(section_results) - coherent_count

        coherence_score = (coherent_count / len(section_results)) * 100
        avg_similarity = np.mean([r.similarity_score for r in section_results])

        # Recomendaciones
        recommendations = [
            r.recommendation for r in section_results
            if r.recommendation is not None
        ]

        # Detalles
        details = [
            {
                'heading': r.heading,
                'heading_level': r.heading_level,
                'word_count': r.word_count,
                'similarity_score': round(r.similarity_score, 3),
                'is_coherent': r.is_coherent,
                'recommendation': r.recommendation
            }
            for r in section_results
        ]

        result = {
            'coherence_score': round(coherence_score, 2),
            'sections_analyzed': len(section_results),
            'coherent_sections': coherent_count,
            'incoherent_sections': incoherent_count,
            'average_similarity': round(float(avg_similarity), 3),
            'threshold_used': self.coherence_threshold,
            'details': details,
            'recommendations': recommendations
        }

        logger.info(
            f"Coherencia: {coherence_score:.1f}% "
            f"({coherent_count}/{len(section_results)} coherentes)"
        )

        return result
