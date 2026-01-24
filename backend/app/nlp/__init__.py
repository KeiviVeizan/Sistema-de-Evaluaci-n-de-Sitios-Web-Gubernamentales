"""
Módulo de Procesamiento de Lenguaje Natural (NLP).

Análisis de coherencia, claridad y ambigüedades con BETO.

Componentes principales:
- NLPAnalyzer: Orquestador principal (punto de entrada)
- CoherenceAnalyzer: Análisis de coherencia semántica
- AmbiguityDetector: Detección de textos problemáticos
- ClarityAnalyzer: Análisis de claridad y legibilidad
- BETOModelManager: Gestor del modelo BETO (singleton)

Uso recomendado:
    >>> from app.nlp import NLPAnalyzer
    >>> analyzer = NLPAnalyzer()
    >>> report = analyzer.analyze_website(text_corpus)
    >>> print(report['global_score'])

Author: Keivi Veizan
"""

__version__ = '1.0.0'
__author__ = 'Keivi Veizan'

# Exportar clases principales
from app.nlp.analyzer import NLPAnalyzer, NLPReport
from app.nlp.coherence import CoherenceAnalyzer, SectionCoherence
from app.nlp.ambiguity import AmbiguityDetector, AmbiguityResult, AmbiguityCategory
from app.nlp.clarity import ClarityAnalyzer, ClarityResult
from app.nlp.models import BETOModelManager

__all__ = [
    # Orquestador (punto de entrada principal)
    'NLPAnalyzer',
    'NLPReport',

    # Analizadores individuales
    'CoherenceAnalyzer',
    'AmbiguityDetector',
    'ClarityAnalyzer',

    # Modelo BETO
    'BETOModelManager',

    # Resultados
    'SectionCoherence',
    'AmbiguityResult',
    'ClarityResult',

    # Enumeraciones
    'AmbiguityCategory',
]
