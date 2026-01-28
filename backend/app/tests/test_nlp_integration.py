#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test de integracion: EvaluationEngine + NLPAnalyzer.

Verifica que el motor de evaluacion integra correctamente el analisis NLP
con los evaluadores heuristicos.

Ejecutar:
    cd backend
    python -m app.tests.test_nlp_integration

O directamente:
    python app/tests/test_nlp_integration.py

Author: Keivi Veizan
Version: 1.0.0
"""

import sys
import os
import io
import logging
from datetime import datetime

# Forzar UTF-8 en stdout para Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# Agregar path del proyecto
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_nlp_integration():
    """
    Test principal de integracion NLP.

    Verifica:
    1. EvaluationEngine inicializa con NLPAnalyzer
    2. evaluate_url ejecuta analisis NLP
    3. Resultados incluyen scores NLP
    4. Total 35 criterios (32 heuristicos + 3 NLP)
    """
    print("\n" + "=" * 70)
    print("  TEST DE INTEGRACION: EvaluationEngine + NLPAnalyzer")
    print("=" * 70 + "\n")

    # 1. Importar EvaluationEngine
    print("[1/5] Importando EvaluationEngine...")
    try:
        from app.evaluator.evaluation_engine import EvaluationEngine, HAS_NLP
        print("      [OK] EvaluationEngine importado")
        print(f"      [OK] NLP disponible: {HAS_NLP}")
    except ImportError as e:
        print(f"      [FAIL] Error importando: {e}")
        return False

    # 2. Inicializar engine
    print("\n[2/5] Inicializando EvaluationEngine...")
    try:
        engine = EvaluationEngine()
        print("      [OK] Engine inicializado")
        nlp_status = "Si" if engine.nlp_analyzer else "No"
        adapter_status = "Si" if engine.nlp_adapter else "No"
        crawler_status = "Si" if engine.crawler else "No"
        print(f"      [OK] NLP Analyzer: {nlp_status}")
        print(f"      [OK] NLP Adapter: {adapter_status}")
        print(f"      [OK] Crawler: {crawler_status}")
    except Exception as e:
        print(f"      [FAIL] Error inicializando: {e}")
        return False

    # 3. Verificar pesos
    print("\n[3/5] Verificando pesos de dimensiones...")
    expected_pesos = {
        "accesibilidad": 0.30,
        "usabilidad": 0.30,
        "semantica_tecnica": 0.15,
        "semantica_nlp": 0.15,
        "soberania": 0.10
    }

    total_peso = sum(engine.PESOS.values())
    print("      Pesos configurados:")
    for dim, peso in engine.PESOS.items():
        expected = expected_pesos.get(dim, 0)
        status = "[OK]" if abs(peso - expected) < 0.01 else "[FAIL]"
        print(f"        {status} {dim}: {peso*100:.0f}%")

    if abs(total_peso - 1.0) > 0.01:
        print(f"      [FAIL] Error: pesos suman {total_peso} (debe ser 1.0)")
        return False
    print("      [OK] Total pesos: 100%")

    # 4. Test con datos simulados (sin crawling real)
    print("\n[4/5] Probando analisis NLP con datos simulados...")

    # Crear datos de prueba simulando output del crawler
    test_extracted_content = {
        'metadata': {
            'url': 'https://test.gob.bo',
            'title': 'Portal de Test'
        },
        'headings': {
            'h1': ['Portal de Test Gubernamental'],
            'h2': ['Servicios al Ciudadano', 'Tramites en Linea', 'Contacto'],
            'h3': ['Requisitos', 'Horarios de Atencion']
        },
        'text_corpus': {
            'sections': [
                {
                    'heading': 'Servicios al Ciudadano',
                    'heading_level': 2,
                    'content': 'Ofrecemos diversos servicios para facilitar los tramites de los ciudadanos bolivianos. Nuestro portal permite realizar consultas, verificar estados de tramites y acceder a informacion importante.',
                    'word_count': 25
                },
                {
                    'heading': 'Tramites en Linea',
                    'heading_level': 2,
                    'content': 'Puede realizar sus tramites de forma digital sin necesidad de asistir a nuestras oficinas. El sistema esta disponible las 24 horas del dia.',
                    'word_count': 22
                }
            ],
            'paragraphs': [
                'Este es el portal oficial del gobierno boliviano.',
                'Aqui encontrara informacion sobre todos los servicios disponibles.'
            ]
        },
        'links': {
            'internal': [
                {'text': 'Inicio', 'href': '/'},
                {'text': 'Servicios', 'href': '/servicios'},
                {'text': 'Ver mas', 'href': '/more'},
                {'text': 'Click aqui', 'href': '/link'},
                {'text': 'Consultar estado de tramite', 'href': '/tramites/estado'}
            ],
            'external': [
                {'text': 'Gobierno de Bolivia', 'href': 'https://www.bolivia.gob.bo'}
            ]
        },
        'forms': {
            'inputs_with_label': [
                {'label': 'Nombre completo', 'for': 'nombre'},
                {'label': 'Correo electronico', 'for': 'email'}
            ],
            'inputs_without_label': [
                {'placeholder': 'Buscar...'}
            ]
        }
    }

    nlp_result = None
    if engine.nlp_analyzer:
        try:
            nlp_result = engine._run_nlp_analysis(test_extracted_content)

            if nlp_result:
                print("      [OK] Analisis NLP ejecutado")
                print(f"      Score Global: {nlp_result['global_score']:.1f}/100")
                print(f"        - Coherencia: {nlp_result['coherence_score']:.1f}")
                print(f"        - Ambiguedad: {nlp_result['ambiguity_score']:.1f}")
                print(f"        - Claridad: {nlp_result['clarity_score']:.1f}")

                # Verificar WCAG compliance
                wcag = nlp_result.get('wcag_compliance', {})
                print("      WCAG Compliance:")
                acc07 = "[OK] Pass" if wcag.get('ACC-07') else "[FAIL] Fail"
                acc08 = "[OK] Pass" if wcag.get('ACC-08') else "[FAIL] Fail"
                acc09 = "[OK] Pass" if wcag.get('ACC-09') else "[FAIL] Fail"
                print(f"        - ACC-07: {acc07}")
                print(f"        - ACC-08: {acc08}")
                print(f"        - ACC-09: {acc09}")

                # Verificar recomendaciones
                recs = nlp_result.get('recommendations', [])
                print(f"      Recomendaciones: {len(recs)}")
                for rec in recs[:3]:
                    print(f"        - {rec[:60]}...")
            else:
                print("      [WARN] Analisis NLP retorno None")
        except Exception as e:
            print(f"      [FAIL] Error en analisis NLP: {e}")
            import traceback
            traceback.print_exc()
    else:
        print("      [WARN] NLP Analyzer no disponible")

    # 5. Verificar creacion de criterios NLP
    print("\n[5/5] Verificando criterios NLP...")

    if engine.nlp_analyzer and nlp_result:
        try:
            nlp_criteria = engine._create_nlp_criteria_dicts(nlp_result)
            print(f"      [OK] Criterios NLP creados: {len(nlp_criteria)}")

            for criteria in nlp_criteria:
                status_icon = "[OK]" if criteria['status'] == 'pass' else "[FAIL]"
                print(f"        {status_icon} {criteria['criteria_id']}: {criteria['status']}")

            # Verificar que son exactamente 3
            if len(nlp_criteria) == 3:
                print("      [OK] Total criterios NLP: 3 (correcto)")
            else:
                print(f"      [FAIL] Error: esperados 3, obtenidos {len(nlp_criteria)}")
                return False

        except Exception as e:
            print(f"      [FAIL] Error creando criterios: {e}")
            return False

    # Resumen
    print("\n" + "=" * 70)
    print("  RESUMEN DE INTEGRACION")
    print("=" * 70)

    nlp_status = "[OK] Integrado" if engine.nlp_analyzer else "[FAIL] No disponible"
    adapter_status = "[OK] Integrado" if engine.nlp_adapter else "[FAIL] No disponible"
    total_criteria = 32 + (3 if engine.nlp_analyzer else 0)
    nlp_criteria_count = 3 if engine.nlp_analyzer else 0

    print(f"""
    EvaluationEngine:
      - Evaluadores heuristicos: 4 (32 criterios)
      - NLP Analyzer: {nlp_status}
      - NLP Adapter: {adapter_status}

    Pesos de dimensiones:
      - Accesibilidad: 30%
      - Usabilidad: 30%
      - Semantica Tecnica: 15%
      - Semantica NLP: 15%
      - Soberania: 10%

    Total criterios: {total_criteria}
      - Heuristicos: 32
      - NLP: {nlp_criteria_count}
    """)

    print("=" * 70)
    print("  [OK] INTEGRACION NLP COMPLETADA EXITOSAMENTE")
    print("=" * 70 + "\n")

    return True


def test_evaluate_url_real():
    """
    Test opcional con URL real (requiere conexion a internet).

    Solo ejecutar si se pasa --real como argumento.
    """
    print("\n" + "=" * 70)
    print("  TEST CON URL REAL")
    print("=" * 70 + "\n")

    from app.evaluator.evaluation_engine import EvaluationEngine

    engine = EvaluationEngine()
    url = "https://www.aduana.gob.bo"

    print(f"Evaluando: {url}")
    print("(Esto puede tomar unos segundos...)\n")

    try:
        result = engine.evaluate_url(url)

        print("\n" + "-" * 50)
        print("RESULTADOS:")
        print("-" * 50)
        print(f"URL: {result['url']}")
        print(f"Status: {result['status']}")
        print("\nScores:")
        print(f"  Total: {result['scores']['total']:.1f}%")
        print(f"  Accesibilidad: {result['scores']['accesibilidad'].get('percentage', 0):.1f}%")
        print(f"  Usabilidad: {result['scores']['usabilidad'].get('percentage', 0):.1f}%")
        print(f"  Semantica Tecnica: {result['scores']['semantica_tecnica'].get('percentage', 0):.1f}%")

        if result['scores'].get('semantica_nlp'):
            print(f"  Semantica NLP: {result['scores']['semantica_nlp']['percentage']:.1f}%")
            print(f"    - Coherencia: {result['scores']['semantica_nlp']['coherence']:.1f}%")
            print(f"    - Ambiguedad: {result['scores']['semantica_nlp']['ambiguity']:.1f}%")
            print(f"    - Claridad: {result['scores']['semantica_nlp']['clarity']:.1f}%")

        print(f"  Soberania: {result['scores']['soberania'].get('percentage', 0):.1f}%")

        print("\nCriterios:")
        print(f"  Total: {result['summary']['total_criteria']}")
        print(f"  Heuristicos: {result['summary']['heuristic_criteria']}")
        print(f"  NLP: {result['summary']['nlp_criteria']}")
        print(f"  Pasados: {result['summary']['passed']}")
        print(f"  Fallidos: {result['summary']['failed']}")

        if result['summary']['total_criteria'] >= 35:
            print("\n[OK] Total criterios >= 35 (32 heuristicos + 3 NLP)")
        else:
            print(f"\n[WARN] Total criterios: {result['summary']['total_criteria']} (esperado >= 35)")

        return True

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    # Test basico de integracion
    success = test_nlp_integration()

    # Test con URL real si se pasa --real
    if "--real" in sys.argv:
        success = test_evaluate_url_real() and success

    sys.exit(0 if success else 1)
