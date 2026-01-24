"""
Orquestador del Módulo NLP.

Integra los 3 analizadores principales:
- CoherenceAnalyzer: Coherencia semántica heading-content
- AmbiguityDetector: Detección de textos problemáticos
- ClarityAnalyzer: Análisis de claridad y legibilidad

Proporciona interfaz unificada para el EvaluationEngine.

Author: Keivi Veizan
Version: 1.0.0
"""

import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

from app.nlp.coherence import CoherenceAnalyzer
from app.nlp.ambiguity import AmbiguityDetector, AmbiguityCategory
from app.nlp.clarity import ClarityAnalyzer

logger = logging.getLogger(__name__)


@dataclass
class NLPReport:
    """
    Reporte consolidado de análisis NLP.

    Attributes:
        global_score: Score global ponderado [0-100]
        coherence_score: Score de coherencia [0-100]
        ambiguity_score: Score de claridad en textos [0-100]
        clarity_score: Score de legibilidad [0-100]
        wcag_compliance: Estado de cumplimiento WCAG
        total_sections_analyzed: Secciones analizadas
        total_texts_analyzed: Textos (links/labels) analizados
        recommendations: Recomendaciones priorizadas
        details: Detalles por categoría
    """
    global_score: float
    coherence_score: float
    ambiguity_score: float
    clarity_score: float
    wcag_compliance: Dict[str, bool]
    total_sections_analyzed: int
    total_texts_analyzed: int
    recommendations: List[str]
    details: Dict[str, Any]


class NLPAnalyzer:
    """
    Orquestador del módulo NLP.

    Integra los 3 analizadores en una interfaz unificada:
    1. CoherenceAnalyzer: Coherencia semántica
    2. AmbiguityDetector: Detección de ambigüedades
    3. ClarityAnalyzer: Análisis de claridad

    Attributes:
        coherence_weight: Peso de coherencia (default: 0.40)
        ambiguity_weight: Peso de ambigüedad (default: 0.40)
        clarity_weight: Peso de claridad (default: 0.20)
        max_recommendations: Máximo de recomendaciones (default: 20)

    Example:
        >>> analyzer = NLPAnalyzer()
        >>> report = analyzer.analyze_website(text_corpus)
        >>> report.global_score
        78.5
        >>> report.wcag_compliance['ACC-07']
        True
    """

    def __init__(
        self,
        coherence_weight: float = 0.40,
        ambiguity_weight: float = 0.40,
        clarity_weight: float = 0.20,
        max_recommendations: int = 20,
        coherence_threshold: float = 0.7,
        clarity_target_min: float = 60.0,
        clarity_target_max: float = 80.0
    ):
        """
        Inicializa el orquestador NLP.

        Args:
            coherence_weight: Peso para coherencia (0-1)
            ambiguity_weight: Peso para ambigüedad (0-1)
            clarity_weight: Peso para claridad (0-1)
            max_recommendations: Máximo de recomendaciones
            coherence_threshold: Umbral de coherencia
            clarity_target_min: Score mínimo de claridad
            clarity_target_max: Score máximo de claridad
        """
        # Validar pesos
        total_weight = coherence_weight + ambiguity_weight + clarity_weight
        if abs(total_weight - 1.0) > 0.01:
            raise ValueError(
                f"Los pesos deben sumar 1.0, suman {total_weight:.2f}"
            )

        self.coherence_weight = coherence_weight
        self.ambiguity_weight = ambiguity_weight
        self.clarity_weight = clarity_weight
        self.max_recommendations = max_recommendations

        # Inicializar analizadores
        self.coherence_analyzer = CoherenceAnalyzer(
            coherence_threshold=coherence_threshold
        )
        self.ambiguity_detector = AmbiguityDetector()
        self.clarity_analyzer = ClarityAnalyzer(
            target_score_min=clarity_target_min,
            target_score_max=clarity_target_max
        )

        logger.info(
            f"NLPAnalyzer inicializado "
            f"(pesos: {coherence_weight}/{ambiguity_weight}/{clarity_weight})"
        )

    def analyze_website(self, text_corpus: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analiza un sitio web completo.

        Args:
            text_corpus: {
                'url': str,
                'sections': [
                    {
                        'heading': str,
                        'heading_level': int,
                        'content': str,
                        'word_count': int
                    },
                    ...
                ],
                'links': [
                    {'text': str, 'url': str},
                    ...
                ],
                'labels': [
                    {'text': str, 'for': str},
                    ...
                ]
            }

        Returns:
            {
                'global_score': float,
                'coherence_score': float,
                'ambiguity_score': float,
                'clarity_score': float,
                'wcag_compliance': {
                    'ACC-07': bool,
                    'ACC-08': bool,
                    'ACC-09': bool
                },
                'total_sections_analyzed': int,
                'total_texts_analyzed': int,
                'recommendations': List[str],
                'details': {
                    'coherence': {...},
                    'ambiguity': {...},
                    'clarity': {...}
                }
            }
        """
        logger.info(f"Analizando sitio: {text_corpus.get('url', 'N/A')}")

        # Análisis 1: Coherencia semántica
        coherence_result = self._analyze_coherence(text_corpus)

        # Análisis 2: Ambigüedades en textos
        ambiguity_result = self._analyze_ambiguity(text_corpus)

        # Análisis 3: Claridad y legibilidad
        clarity_result = self._analyze_clarity(text_corpus)

        # Calcular score global ponderado
        global_score = self._calculate_global_score(
            coherence_result['coherence_score'],
            ambiguity_result['clarity_score'],
            clarity_result['avg_score']
        )

        # Evaluar cumplimiento WCAG
        wcag_compliance = self._evaluate_wcag_compliance(
            ambiguity_result
        )

        # Combinar recomendaciones
        recommendations = self._combine_recommendations(
            coherence_result,
            ambiguity_result,
            clarity_result
        )

        # Construir reporte consolidado
        report = {
            'global_score': round(global_score, 2),
            'coherence_score': coherence_result['coherence_score'],
            'ambiguity_score': ambiguity_result['clarity_score'],
            'clarity_score': clarity_result['avg_score'],
            'wcag_compliance': wcag_compliance,
            'total_sections_analyzed': coherence_result['sections_analyzed'],
            'total_texts_analyzed': ambiguity_result['total_analyzed'],
            'recommendations': recommendations,
            'details': {
                'coherence': coherence_result,
                'ambiguity': ambiguity_result,
                'clarity': clarity_result
            }
        }

        logger.info(
            f"Análisis completado - Score global: {global_score:.1f}/100"
        )

        return report

    def _analyze_coherence(self, text_corpus: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analiza coherencia semántica de las secciones.

        Args:
            text_corpus: Corpus con secciones

        Returns:
            Resultado del análisis de coherencia
        """
        sections = text_corpus.get('sections', [])

        if not sections:
            logger.warning("No hay secciones para analizar coherencia")
            return {
                'coherence_score': 0.0,
                'sections_analyzed': 0,
                'coherent_sections': 0,
                'incoherent_sections': 0,
                'average_similarity': 0.0,
                'threshold_used': self.coherence_analyzer.coherence_threshold,
                'recommendations': ['No se encontraron secciones para analizar coherencia.'],
                'details': []
            }

        # Analizar con CoherenceAnalyzer
        result = self.coherence_analyzer.analyze_coherence(text_corpus)

        logger.debug(
            f"Coherencia: {result['coherence_score']}/100 "
            f"({result['coherent_sections']}/{result['sections_analyzed']} coherentes)"
        )

        return result

    def _analyze_ambiguity(self, text_corpus: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analiza ambigüedades en enlaces y labels.

        Args:
            text_corpus: Corpus con links y labels

        Returns:
            Resultado del análisis de ambigüedades
        """
        # Extraer enlaces
        links = text_corpus.get('links', [])
        labels = text_corpus.get('labels', [])

        # Preparar textos para análisis
        texts_to_analyze = []

        for link in links:
            texts_to_analyze.append({
                'text': link.get('text', ''),
                'element_type': 'link'
            })

        for label in labels:
            texts_to_analyze.append({
                'text': label.get('text', ''),
                'element_type': 'label'
            })

        # También analizar headings de secciones
        sections = text_corpus.get('sections', [])
        for section in sections:
            texts_to_analyze.append({
                'text': section.get('heading', ''),
                'element_type': 'heading'
            })

        if not texts_to_analyze:
            logger.warning("No hay textos para analizar ambigüedad")
            return {
                'total_analyzed': 0,
                'problematic_count': 0,
                'clear_count': 0,
                'clarity_score': 100.0,
                'by_category': {},
                'by_element_type': {},
                'details': [],
                'recommendations': []
            }

        # Analizar con AmbiguityDetector
        result = self.ambiguity_detector.analyze_multiple(texts_to_analyze)

        # Calcular clarity_score (inverso de problematic_count)
        if result['total_analyzed'] > 0:
            clarity_percentage = (result['clear_count'] / result['total_analyzed']) * 100
            result['clarity_score'] = round(clarity_percentage, 2)
        else:
            result['clarity_score'] = 100.0

        logger.debug(
            f"Ambigüedad: {result['clarity_score']}/100 "
            f"({result['clear_count']}/{result['total_analyzed']} claros)"
        )

        return result

    def _analyze_clarity(self, text_corpus: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analiza claridad y legibilidad del contenido.

        Args:
            text_corpus: Corpus con secciones

        Returns:
            Resultado del análisis de claridad
        """
        sections = text_corpus.get('sections', [])

        if not sections:
            logger.warning("No hay secciones para analizar claridad")
            return {
                'total_analyzed': 0,
                'clear_count': 0,
                'unclear_count': 0,
                'avg_score': 0.0,
                'details': [],
                'recommendations': []
            }

        # Extraer contenido de cada sección
        texts_to_analyze = []
        for section in sections:
            content = section.get('content', '')
            if content and content.strip():
                texts_to_analyze.append(content)

        if not texts_to_analyze:
            return {
                'total_analyzed': 0,
                'clear_count': 0,
                'unclear_count': 0,
                'avg_score': 0.0,
                'details': [],
                'recommendations': []
            }

        # Analizar con ClarityAnalyzer
        result = self.clarity_analyzer.analyze_multiple(texts_to_analyze)

        logger.debug(
            f"Claridad: {result['avg_score']}/100 "
            f"(Fernández Huerta promedio)"
        )

        return result

    def _calculate_global_score(
        self,
        coherence_score: float,
        ambiguity_score: float,
        clarity_score: float
    ) -> float:
        """
        Calcula score global ponderado.

        Args:
            coherence_score: Score de coherencia [0-100]
            ambiguity_score: Score de claridad en textos [0-100]
            clarity_score: Score de legibilidad [0-100]

        Returns:
            Score global [0-100]
        """
        global_score = (
            (coherence_score * self.coherence_weight) +
            (ambiguity_score * self.ambiguity_weight) +
            (clarity_score * self.clarity_weight)
        )

        logger.debug(
            f"Score global: {global_score:.1f} = "
            f"{coherence_score:.1f}*{self.coherence_weight} + "
            f"{ambiguity_score:.1f}*{self.ambiguity_weight} + "
            f"{clarity_score:.1f}*{self.clarity_weight}"
        )

        return round(global_score, 2)

    def _evaluate_wcag_compliance(
        self,
        ambiguity_result: Dict[str, Any]
    ) -> Dict[str, bool]:
        """
        Evalúa cumplimiento de criterios WCAG.

        Args:
            ambiguity_result: Resultado del análisis de ambigüedades

        Returns:
            {
                'ACC-07': bool,  # Labels or Instructions (WCAG 3.3.2 - Level A)
                'ACC-08': bool,  # Link Purpose (WCAG 2.4.4 - Level A)
                'ACC-09': bool   # Headings and Labels (WCAG 2.4.6 - Level AA)
            }
        """
        by_category = ambiguity_result.get('by_category', {})

        # ACC-07: WCAG 3.3.2 Labels or Instructions - Level A
        # Cumple si NO hay textos ambiguos
        acc_07 = by_category.get(AmbiguityCategory.TEXTO_AMBIGUO.value, 0) == 0

        # ACC-08: WCAG 2.4.4 Link Purpose - Level A
        # Cumple si NO hay textos genéricos ni muy cortos
        acc_08 = (
            by_category.get(AmbiguityCategory.TEXTO_GENERICO.value, 0) == 0 and
            by_category.get(AmbiguityCategory.TEXTO_DEMASIADO_CORTO.value, 0) == 0
        )

        # ACC-09: WCAG 2.4.6 Headings and Labels - Level AA
        # Cumple si NO hay textos no descriptivos ni excesivamente técnicos
        acc_09 = (
            by_category.get(AmbiguityCategory.TEXTO_NO_DESCRIPTIVO.value, 0) == 0 and
            by_category.get(AmbiguityCategory.TEXTO_EXCESIVAMENTE_TECNICO.value, 0) == 0
        )

        compliance = {
            'ACC-07': acc_07,
            'ACC-08': acc_08,
            'ACC-09': acc_09
        }

        logger.debug(
            f"WCAG Compliance: ACC-07={acc_07}, ACC-08={acc_08}, ACC-09={acc_09}"
        )

        return compliance

    def _combine_recommendations(
        self,
        coherence_result: Dict[str, Any],
        ambiguity_result: Dict[str, Any],
        clarity_result: Dict[str, Any]
    ) -> List[str]:
        """
        Combina y prioriza recomendaciones de todos los analizadores.

        Prioridad:
        1. Ambigüedades (afectan WCAG directamente)
        2. Coherencia (afecta usabilidad)
        3. Claridad (afecta legibilidad)

        Args:
            coherence_result: Resultado de coherencia
            ambiguity_result: Resultado de ambigüedades
            clarity_result: Resultado de claridad

        Returns:
            Lista de recomendaciones priorizadas (max: self.max_recommendations)
        """
        all_recommendations = []

        # Prioridad 1: Ambigüedades (WCAG crítico)
        ambiguity_recs = ambiguity_result.get('recommendations', [])
        for rec in ambiguity_recs:
            all_recommendations.append({
                'priority': 1,
                'category': 'Ambigüedad (WCAG)',
                'text': rec
            })

        # Prioridad 2: Coherencia (Usabilidad)
        coherence_recs = coherence_result.get('recommendations', [])
        for rec in coherence_recs:
            all_recommendations.append({
                'priority': 2,
                'category': 'Coherencia',
                'text': rec
            })

        # Prioridad 3: Claridad (Legibilidad)
        clarity_recs = clarity_result.get('recommendations', [])
        for rec in clarity_recs:
            all_recommendations.append({
                'priority': 3,
                'category': 'Claridad',
                'text': rec
            })

        # Ordenar por prioridad
        all_recommendations.sort(key=lambda x: x['priority'])

        # Limitar al máximo configurado
        top_recommendations = all_recommendations[:self.max_recommendations]

        # Formatear para salida
        formatted_recs = [
            f"[{rec['category']}] {rec['text']}"
            for rec in top_recommendations
        ]

        logger.debug(
            f"Recomendaciones combinadas: {len(formatted_recs)} "
            f"(de {len(all_recommendations)} totales)"
        )

        return formatted_recs


# ============================================================================
# LEGACY CODE - Preserved for compatibility
# ============================================================================

# Renamed from TextAnalyzer to TextAnalyzerOld
# This class is kept for reference but should not be used in new code
# Use NLPAnalyzer instead

from typing import Dict, List
import re
from app.config import settings


class TextAnalyzerOld:
    """
    DEPRECATED: Use NLPAnalyzer instead.

    Analizador de texto básico (legacy).
    Conservado por compatibilidad.
    """

    def __init__(self):
        """Inicializa el analizador de texto (legacy)."""
        self.model_name = settings.nlp_model_name
        self.cache_dir = settings.nlp_cache_dir
        logger.info(f"TextAnalyzerOld inicializado (DEPRECATED - usar NLPAnalyzer)")

    def analyze_text(self, text: str) -> Dict[str, any]:
        """Analiza un texto (legacy)."""
        if not text or len(text.strip()) < 50:
            return {
                'error': 'Texto muy corto para análisis',
                'ambiguity_score': None,
                'clarity_score': None,
                'issues_detected': []
            }

        results = {
            'ambiguity_score': self._calculate_ambiguity_score(text),
            'clarity_score': self._calculate_clarity_score(text),
            'issues_detected': self._detect_issues(text),
            'readability_metrics': self._calculate_readability(text),
            'text_length': len(text),
            'word_count': len(text.split())
        }

        return results

    def _calculate_ambiguity_score(self, text: str) -> float:
        """Calcula puntaje de ambigüedad (legacy)."""
        score = 0.0
        ambiguous_words = [
            'podría', 'tal vez', 'quizás', 'probablemente', 'posiblemente',
            'aproximadamente', 'cerca de', 'algunos', 'varios', 'muchos'
        ]

        text_lower = text.lower()
        words = text_lower.split()
        ambiguous_count = sum(1 for word in ambiguous_words if word in text_lower)

        if len(words) > 0:
            score = (ambiguous_count / len(words)) * 1000

        return min(round(score, 2), 100)

    def _calculate_clarity_score(self, text: str) -> float:
        """Calcula puntaje de claridad (legacy)."""
        score = 100.0
        penalties = 0

        sentences = self._split_sentences(text)
        for sentence in sentences:
            words_in_sentence = len(sentence.split())
            if words_in_sentence > 40:
                penalties += 5

        words = text.split()
        long_words = [w for w in words if len(w) > 15]
        if len(words) > 0:
            long_word_ratio = len(long_words) / len(words)
            if long_word_ratio > 0.15:
                penalties += 10

        punctuation_marks = text.count('.') + text.count(',') + text.count(';')
        if len(words) > 50 and punctuation_marks < 3:
            penalties += 15

        score -= penalties
        return max(round(score, 2), 0)

    def _detect_issues(self, text: str) -> List[Dict[str, str]]:
        """Detecta problemas comunes (legacy)."""
        issues = []

        if len(text) < 100:
            issues.append({
                'type': 'length',
                'severity': 'warning',
                'message': 'El contenido textual es muy breve'
            })

        sentences = self._split_sentences(text)
        long_sentences = [s for s in sentences if len(s.split()) > 40]
        if long_sentences:
            issues.append({
                'type': 'readability',
                'severity': 'warning',
                'message': f'Se encontraron {len(long_sentences)} oraciones muy largas'
            })

        return issues

    def _calculate_readability(self, text: str) -> Dict[str, float]:
        """Calcula métricas de legibilidad (legacy)."""
        sentences = self._split_sentences(text)
        words = text.split()

        avg_words_per_sentence = len(words) / len(sentences) if sentences else 0
        avg_chars_per_word = sum(len(w) for w in words) / len(words) if words else 0

        readability_index = 206.835 - 1.015 * avg_words_per_sentence - 84.6 * (avg_chars_per_word / 5)
        readability_index = max(0, min(100, readability_index))

        return {
            'avg_words_per_sentence': round(avg_words_per_sentence, 2),
            'avg_chars_per_word': round(avg_chars_per_word, 2),
            'readability_index': round(readability_index, 2),
            'total_sentences': len(sentences)
        }

    def _split_sentences(self, text: str) -> List[str]:
        """Divide texto en oraciones (legacy)."""
        sentences = re.split(r'[.!?]+', text)
        return [s.strip() for s in sentences if s.strip()]
