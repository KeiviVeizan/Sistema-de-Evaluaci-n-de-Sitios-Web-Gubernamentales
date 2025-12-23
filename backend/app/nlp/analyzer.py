"""
Analizador de texto usando BETO (BERT en español).

Proporciona análisis de calidad del contenido textual de sitios web,
incluyendo claridad, ambigüedad y detección de problemas.
"""

from typing import Dict, List, Optional
import logging
import re

# TODO: Descomentar cuando se instalen las dependencias
# from transformers import AutoTokenizer, AutoModel
# import torch

from app.config import settings

logger = logging.getLogger(__name__)


class TextAnalyzer:
    """
    Analizador de texto usando BETO.

    Analiza calidad del contenido textual usando el modelo BERT
    preentrenado en español (BETO).
    """

    def __init__(self):
        """Inicializa el analizador de texto."""
        self.model_name = settings.nlp_model_name
        self.cache_dir = settings.nlp_cache_dir

        # TODO: Descomentar cuando se cargue el modelo
        # self.tokenizer = None
        # self.model = None
        # self._load_model()

        logger.info(f"Analizador de texto inicializado (modelo: {self.model_name})")

    def _load_model(self):
        """
        Carga el modelo BETO.

        Este método debe ser llamado cuando se instalen las dependencias.
        """
        try:
            # TODO: Descomentar cuando se instalen las dependencias
            # logger.info(f"Cargando modelo {self.model_name}...")
            # self.tokenizer = AutoTokenizer.from_pretrained(
            #     self.model_name,
            #     cache_dir=self.cache_dir
            # )
            # self.model = AutoModel.from_pretrained(
            #     self.model_name,
            #     cache_dir=self.cache_dir
            # )
            # logger.info("Modelo cargado exitosamente")
            pass
        except Exception as e:
            logger.error(f"Error cargando modelo: {e}")
            raise

    def analyze_text(self, text: str) -> Dict[str, any]:
        """
        Analiza un texto para evaluar su calidad.

        Args:
            text: Texto a analizar

        Returns:
            dict: Resultados del análisis incluyendo puntajes y problemas detectados
        """
        if not text or len(text.strip()) < 50:
            return {
                'error': 'Texto muy corto para análisis',
                'ambiguity_score': None,
                'clarity_score': None,
                'issues_detected': []
            }

        # Análisis básico de texto (sin ML por ahora)
        results = {
            'ambiguity_score': self._calculate_ambiguity_score(text),
            'clarity_score': self._calculate_clarity_score(text),
            'issues_detected': self._detect_issues(text),
            'readability_metrics': self._calculate_readability(text),
            'text_length': len(text),
            'word_count': len(text.split())
        }

        # TODO: Agregar análisis con BETO cuando se cargue el modelo
        # results['sentiment'] = self._analyze_sentiment(text)
        # results['entities'] = self._extract_entities(text)

        return results

    def _calculate_ambiguity_score(self, text: str) -> float:
        """
        Calcula el puntaje de ambigüedad del texto.

        Un puntaje más bajo indica menos ambigüedad.

        Args:
            text: Texto a analizar

        Returns:
            float: Puntaje de 0 a 100
        """
        score = 0.0

        # Palabras ambiguas comunes
        ambiguous_words = [
            'podría', 'tal vez', 'quizás', 'probablemente', 'posiblemente',
            'aproximadamente', 'cerca de', 'algunos', 'varios', 'muchos'
        ]

        text_lower = text.lower()
        words = text_lower.split()

        # Contar palabras ambiguas
        ambiguous_count = sum(1 for word in ambiguous_words if word in text_lower)

        # Calcular porcentaje
        if len(words) > 0:
            score = (ambiguous_count / len(words)) * 1000  # Escalar a 0-100

        return min(round(score, 2), 100)

    def _calculate_clarity_score(self, text: str) -> float:
        """
        Calcula el puntaje de claridad del texto.

        Un puntaje más alto indica mayor claridad.

        Args:
            text: Texto a analizar

        Returns:
            float: Puntaje de 0 a 100
        """
        score = 100.0

        # Factores que reducen claridad
        penalties = 0

        # Oraciones muy largas (>40 palabras)
        sentences = self._split_sentences(text)
        for sentence in sentences:
            words_in_sentence = len(sentence.split())
            if words_in_sentence > 40:
                penalties += 5

        # Uso excesivo de tecnicismos (palabras muy largas)
        words = text.split()
        long_words = [w for w in words if len(w) > 15]
        if len(words) > 0:
            long_word_ratio = len(long_words) / len(words)
            if long_word_ratio > 0.15:
                penalties += 10

        # Falta de puntuación
        punctuation_marks = text.count('.') + text.count(',') + text.count(';')
        if len(words) > 50 and punctuation_marks < 3:
            penalties += 15

        score -= penalties
        return max(round(score, 2), 0)

    def _detect_issues(self, text: str) -> List[Dict[str, str]]:
        """
        Detecta problemas comunes en el texto.

        Args:
            text: Texto a analizar

        Returns:
            list: Lista de problemas detectados
        """
        issues = []

        # Texto demasiado corto
        if len(text) < 100:
            issues.append({
                'type': 'length',
                'severity': 'warning',
                'message': 'El contenido textual es muy breve'
            })

        # Oraciones muy largas
        sentences = self._split_sentences(text)
        long_sentences = [s for s in sentences if len(s.split()) > 40]
        if long_sentences:
            issues.append({
                'type': 'readability',
                'severity': 'warning',
                'message': f'Se encontraron {len(long_sentences)} oraciones muy largas'
            })

        # Falta de mayúsculas al inicio
        if sentences and sentences[0] and not sentences[0][0].isupper():
            issues.append({
                'type': 'formatting',
                'severity': 'info',
                'message': 'El texto no comienza con mayúscula'
            })

        # Uso excesivo de mayúsculas
        uppercase_ratio = sum(1 for c in text if c.isupper()) / len(text) if text else 0
        if uppercase_ratio > 0.3:
            issues.append({
                'type': 'formatting',
                'severity': 'warning',
                'message': 'Uso excesivo de mayúsculas'
            })

        # Palabras repetidas consecutivamente
        words = text.lower().split()
        for i in range(len(words) - 1):
            if words[i] == words[i + 1] and len(words[i]) > 3:
                issues.append({
                    'type': 'grammar',
                    'severity': 'warning',
                    'message': f'Palabra repetida: "{words[i]}"'
                })
                break

        return issues

    def _calculate_readability(self, text: str) -> Dict[str, float]:
        """
        Calcula métricas de legibilidad.

        Args:
            text: Texto a analizar

        Returns:
            dict: Métricas de legibilidad
        """
        sentences = self._split_sentences(text)
        words = text.split()

        # Promedio de palabras por oración
        avg_words_per_sentence = len(words) / len(sentences) if sentences else 0

        # Promedio de caracteres por palabra
        avg_chars_per_word = sum(len(w) for w in words) / len(words) if words else 0

        # Índice de legibilidad simplificado (similar a Flesch)
        # Fórmula simplificada: 206.835 - 1.015 * (palabras/oraciones) - 84.6 * (sílabas/palabras)
        # Aquí usamos caracteres/palabra como aproximación
        readability_index = 206.835 - 1.015 * avg_words_per_sentence - 84.6 * (avg_chars_per_word / 5)
        readability_index = max(0, min(100, readability_index))

        return {
            'avg_words_per_sentence': round(avg_words_per_sentence, 2),
            'avg_chars_per_word': round(avg_chars_per_word, 2),
            'readability_index': round(readability_index, 2),
            'total_sentences': len(sentences)
        }

    def _split_sentences(self, text: str) -> List[str]:
        """
        Divide el texto en oraciones.

        Args:
            text: Texto a dividir

        Returns:
            list: Lista de oraciones
        """
        # Patrón simple para dividir oraciones
        sentences = re.split(r'[.!?]+', text)
        return [s.strip() for s in sentences if s.strip()]

    def analyze_sentiment(self, text: str) -> Dict[str, float]:
        """
        Analiza el sentimiento del texto.

        TODO: Implementar con BETO cuando se cargue el modelo.

        Args:
            text: Texto a analizar

        Returns:
            dict: Scores de sentimiento (positivo, negativo, neutral)
        """
        # Placeholder - implementar con BETO
        return {
            'positive': 0.5,
            'negative': 0.3,
            'neutral': 0.2,
            'note': 'Análisis de sentimiento requiere modelo BETO cargado'
        }

    def extract_keywords(self, text: str, top_n: int = 10) -> List[str]:
        """
        Extrae palabras clave del texto.

        Args:
            text: Texto a analizar
            top_n: Número de palabras clave a extraer

        Returns:
            list: Lista de palabras clave
        """
        # Palabras vacías en español
        stopwords = {
            'el', 'la', 'de', 'que', 'y', 'a', 'en', 'un', 'ser', 'se',
            'no', 'haber', 'por', 'con', 'su', 'para', 'como', 'estar',
            'tener', 'le', 'lo', 'todo', 'pero', 'más', 'hacer', 'o',
            'poder', 'decir', 'este', 'ir', 'otro', 'ese', 'la', 'si',
            'me', 'ya', 'ver', 'porque', 'dar', 'cuando', 'él', 'muy',
            'sin', 'vez', 'mucho', 'saber', 'qué', 'sobre', 'mi', 'alguno',
            'mismo', 'yo', 'también', 'hasta', 'año', 'dos', 'querer'
        }

        # Limpiar y tokenizar
        words = re.findall(r'\b[a-záéíóúñü]{4,}\b', text.lower())

        # Filtrar stopwords
        words = [w for w in words if w not in stopwords]

        # Contar frecuencias
        word_freq = {}
        for word in words:
            word_freq[word] = word_freq.get(word, 0) + 1

        # Obtener top N
        top_keywords = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:top_n]

        return [word for word, freq in top_keywords]
