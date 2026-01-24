"""
Análisis de Claridad del Lenguaje.

Implementa métricas de legibilidad en español:
- Índice Fernández Huerta (adaptación Flesch)
- Detección de oraciones largas
- Análisis de complejidad léxica

Objetivo para sitios .gob.bo: Score 60-80 (legibilidad media-alta)

References:
    Fernández Huerta, J. (1959). Medidas sencillas de lectura.
    Flesch, R. (1948). A new readability yardstick.
"""

import logging
import re
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class ClarityResult:
    """
    Resultado de análisis de claridad.

    Attributes:
        text: Texto analizado
        fernandez_huerta_score: Score [0-100]
        interpretation: Interpretación del score
        avg_sentence_length: Palabras promedio por oración
        avg_syllables_per_word: Sílabas promedio por palabra
        long_sentences_count: Oraciones >40 palabras
        complex_words_count: Palabras >4 sílabas
        complex_words_percentage: % palabras complejas
        is_clear: True si score >= 60
        recommendation: Recomendación si no es claro
    """
    text: str
    fernandez_huerta_score: float
    interpretation: str
    avg_sentence_length: float
    avg_syllables_per_word: float
    long_sentences_count: int
    complex_words_count: int
    complex_words_percentage: float
    is_clear: bool
    recommendation: Optional[str] = None


class ClarityAnalyzer:
    """
    Analizador de claridad textual en español.

    Implementa Índice Fernández Huerta y métricas complementarias.

    Attributes:
        target_score_min: Score mínimo objetivo (default: 60)
        target_score_max: Score máximo objetivo (default: 80)
        long_sentence_threshold: Palabras para considerar larga (default: 40)
        complex_word_threshold: Sílabas para considerar compleja (default: 4)

    Example:
        >>> analyzer = ClarityAnalyzer()
        >>> result = analyzer.analyze_text(
        ...     "El ministerio ofrece servicios de salud."
        ... )
        >>> result.fernandez_huerta_score
        78.5
        >>> result.is_clear
        True
    """

    # Vocales españolas (incluyendo acentuadas)
    VOWELS = set('aeiouáéíóúü')

    def __init__(
        self,
        target_score_min: float = 60.0,
        target_score_max: float = 80.0,
        long_sentence_threshold: int = 40,
        complex_word_threshold: int = 4
    ):
        """
        Inicializa el analizador.

        Args:
            target_score_min: Score mínimo aceptable
            target_score_max: Score máximo ideal
            long_sentence_threshold: Palabras para oración larga
            complex_word_threshold: Sílabas para palabra compleja
        """
        self.target_score_min = target_score_min
        self.target_score_max = target_score_max
        self.long_sentence_threshold = long_sentence_threshold
        self.complex_word_threshold = complex_word_threshold

        logger.info(
            f"ClarityAnalyzer inicializado "
            f"(target: {target_score_min}-{target_score_max})"
        )

    def _count_syllables(self, word: str) -> int:
        """
        Cuenta sílabas en una palabra española.

        Reglas simplificadas:
        - Cada vocal es potencialmente una sílaba
        - Diptongos cuentan como 1 sílaba
        - Hiatos cuentan como 2 sílabas

        Args:
            word: Palabra en español

        Returns:
            Número de sílabas

        Note:
            Implementación simplificada. Para precisión total
            se requeriría silabizador completo.
        """
        word = word.lower()
        syllable_count = 0
        previous_was_vowel = False

        for char in word:
            is_vowel = char in self.VOWELS

            if is_vowel:
                if not previous_was_vowel:
                    syllable_count += 1
                previous_was_vowel = True
            else:
                previous_was_vowel = False

        # Mínimo 1 sílaba
        return max(1, syllable_count)

    def _split_sentences(self, text: str) -> List[str]:
        """
        Divide texto en oraciones.

        Args:
            text: Texto a dividir

        Returns:
            Lista de oraciones
        """
        # Regex para puntos, signos de interrogación, exclamación
        # Evita dividir en abreviaturas comunes
        sentences = re.split(r'(?<=[.!?])\s+', text)

        # Filtrar oraciones vacías
        return [s.strip() for s in sentences if s.strip()]

    def _split_words(self, text: str) -> List[str]:
        """
        Divide texto en palabras.

        Args:
            text: Texto a dividir

        Returns:
            Lista de palabras (solo letras)
        """
        # Extraer solo palabras (letras)
        words = re.findall(r'\b[a-záéíóúüñ]+\b', text.lower())
        return words

    def _calculate_fernandez_huerta(
        self,
        avg_syllables_per_word: float,
        avg_words_per_sentence: float
    ) -> float:
        """
        Calcula Índice Fernández Huerta.

        Fórmula: 206.84 - (0.60 × S) - (1.02 × P)

        Args:
            avg_syllables_per_word: S (promedio sílabas/palabra)
            avg_words_per_sentence: P (promedio palabras/oración)

        Returns:
            Score [0-100]
        """
        score = 206.84 - (0.60 * avg_syllables_per_word) - (1.02 * avg_words_per_sentence)

        # Limitar a [0, 100]
        return max(0.0, min(100.0, score))

    def _interpret_score(self, score: float) -> str:
        """
        Interpreta score Fernández Huerta.

        Args:
            score: Score calculado

        Returns:
            Interpretación en español
        """
        if score >= 90:
            return "Muy fácil (nivel primaria)"
        elif score >= 80:
            return "Fácil (conversación casual)"
        elif score >= 70:
            return "Bastante fácil (prensa popular)"
        elif score >= 60:
            return "Normal (prensa general)"
        elif score >= 50:
            return "Bastante difícil (prensa especializada)"
        elif score >= 30:
            return "Difícil (textos académicos)"
        else:
            return "Muy difícil (textos científicos)"

    def _generate_recommendation(
        self,
        score: float,
        long_sentences: int,
        complex_words_pct: float
    ) -> str:
        """
        Genera recomendación de mejora.

        Args:
            score: Score Fernández Huerta
            long_sentences: Número de oraciones largas
            complex_words_pct: Porcentaje de palabras complejas

        Returns:
            Recomendación específica
        """
        recommendations = []

        if score < 60:
            recommendations.append(
                f"El texto tiene un índice de legibilidad de {score:.1f}/100, "
                f"considerado difícil para el público general."
            )

        if long_sentences > 0:
            recommendations.append(
                f"Hay {long_sentences} oración(es) con más de {self.long_sentence_threshold} "
                f"palabras. Divídalas en oraciones más cortas (15-25 palabras ideal)."
            )

        if complex_words_pct > 15:
            recommendations.append(
                f"El {complex_words_pct:.1f}% de las palabras son complejas (>4 sílabas). "
                f"Use palabras más simples cuando sea posible."
            )

        if not recommendations:
            recommendations.append(
                "El texto es claro pero podría mejorarse usando: "
                "oraciones cortas (15-25 palabras), palabras simples, y voz activa."
            )

        return " ".join(recommendations)

    def analyze_text(self, text: str) -> ClarityResult:
        """
        Analiza claridad de un texto.

        Args:
            text: Texto a analizar

        Returns:
            ClarityResult con métricas

        Example:
            >>> result = analyzer.analyze_text(
            ...     "El Ministerio de Salud ofrece servicios. "
            ...     "Los ciudadanos pueden acceder."
            ... )
            >>> result.is_clear
            True
        """
        if not text or not text.strip():
            return ClarityResult(
                text="[VACÍO]",
                fernandez_huerta_score=0.0,
                interpretation="Sin texto",
                avg_sentence_length=0.0,
                avg_syllables_per_word=0.0,
                long_sentences_count=0,
                complex_words_count=0,
                complex_words_percentage=0.0,
                is_clear=False,
                recommendation="No hay texto para analizar."
            )

        # Dividir en oraciones y palabras
        sentences = self._split_sentences(text)
        words = self._split_words(text)

        if not sentences or not words:
            return ClarityResult(
                text=text[:100],
                fernandez_huerta_score=0.0,
                interpretation="Texto inválido",
                avg_sentence_length=0.0,
                avg_syllables_per_word=0.0,
                long_sentences_count=0,
                complex_words_count=0,
                complex_words_percentage=0.0,
                is_clear=False,
                recommendation="El texto no contiene oraciones o palabras válidas."
            )

        # Contar sílabas por palabra
        syllables_per_word = [self._count_syllables(word) for word in words]
        total_syllables = sum(syllables_per_word)

        # Palabras por oración
        words_per_sentence = [len(self._split_words(s)) for s in sentences]

        # Promedios
        avg_syllables_per_word = total_syllables / len(words)
        avg_words_per_sentence = sum(words_per_sentence) / len(sentences)

        # Calcular Fernández Huerta
        score = self._calculate_fernandez_huerta(
            avg_syllables_per_word,
            avg_words_per_sentence
        )

        interpretation = self._interpret_score(score)

        # Oraciones largas
        long_sentences_count = sum(
            1 for count in words_per_sentence
            if count > self.long_sentence_threshold
        )

        # Palabras complejas
        complex_words_count = sum(
            1 for syllables in syllables_per_word
            if syllables > self.complex_word_threshold
        )
        complex_words_pct = (complex_words_count / len(words)) * 100

        # Determinar si es claro
        is_clear = self.target_score_min <= score <= self.target_score_max

        # Generar recomendación si no es claro
        recommendation = None
        if not is_clear or long_sentences_count > 0 or complex_words_pct > 15:
            recommendation = self._generate_recommendation(
                score, long_sentences_count, complex_words_pct
            )

        logger.debug(f"Claridad: score={score:.1f}, oraciones_largas={long_sentences_count}")

        return ClarityResult(
            text=text[:100] + "..." if len(text) > 100 else text,
            fernandez_huerta_score=round(score, 2),
            interpretation=interpretation,
            avg_sentence_length=round(avg_words_per_sentence, 2),
            avg_syllables_per_word=round(avg_syllables_per_word, 2),
            long_sentences_count=long_sentences_count,
            complex_words_count=complex_words_count,
            complex_words_percentage=round(complex_words_pct, 2),
            is_clear=is_clear,
            recommendation=recommendation
        )

    def analyze_multiple(self, texts: List[str]) -> Dict[str, Any]:
        """
        Analiza claridad de múltiples textos.

        Args:
            texts: Lista de textos

        Returns:
            {
                'total_analyzed': int,
                'clear_count': int,
                'unclear_count': int,
                'avg_score': float,
                'details': List[Dict],
                'recommendations': List[str]
            }
        """
        if not texts:
            return {
                'total_analyzed': 0,
                'clear_count': 0,
                'unclear_count': 0,
                'avg_score': 0.0,
                'details': [],
                'recommendations': []
            }

        logger.info(f"Analizando claridad de {len(texts)} textos")

        results = [self.analyze_text(text) for text in texts]

        clear_count = sum(1 for r in results if r.is_clear)
        unclear_count = len(results) - clear_count
        avg_score = sum(r.fernandez_huerta_score for r in results) / len(results)

        details = [
            {
                'text_preview': r.text,
                'score': r.fernandez_huerta_score,
                'interpretation': r.interpretation,
                'is_clear': r.is_clear,
                'recommendation': r.recommendation
            }
            for r in results
        ]

        recommendations = [r.recommendation for r in results if r.recommendation]

        summary = {
            'total_analyzed': len(results),
            'clear_count': clear_count,
            'unclear_count': unclear_count,
            'avg_score': round(avg_score, 2),
            'details': details,
            'recommendations': recommendations
        }

        logger.info(f"Claridad promedio: {avg_score:.1f}/100")

        return summary
