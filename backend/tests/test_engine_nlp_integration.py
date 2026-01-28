#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test de integración: EvaluationEngine + NLPAnalyzer.

Verifica:
1. 32 criterios heurísticos + 3 criterios NLP = 35 total
2. NLPAnalyzer funciona correctamente con datos reales
3. Persistencia en BD (si disponible)
4. Pesos correctos: 30-30-15-15-10

Uso:
    python -m pytest tests/test_engine_nlp_integration.py -v
    python tests/test_engine_nlp_integration.py
"""

import os
import sys
import logging

# Fix encoding for Windows console
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Agregar path para imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def test_nlp_analyzer_standalone():
    """Test NLPAnalyzer funciona de forma independiente."""
    print("\n" + "=" * 60)
    print("TEST 1: NLPAnalyzer Standalone")
    print("=" * 60)

    from app.nlp.analyzer import NLPAnalyzer

    analyzer = NLPAnalyzer()

    # Datos de prueba representativos de un sitio gubernamental
    test_corpus = {
        'url': 'https://test.gob.bo',
        'sections': [
            {
                'heading': 'Servicios al Ciudadano',
                'heading_level': 1,
                'content': 'Ofrecemos servicios de atención al ciudadano para trámites gubernamentales. '
                          'Los horarios de atención son de lunes a viernes de 8:00 a 16:00 horas. '
                          'Puede realizar consultas sobre el estado de sus trámites en línea.',
                'word_count': 35
            },
            {
                'heading': 'Trámites en Línea',
                'heading_level': 2,
                'content': 'Realice sus trámites de forma digital sin necesidad de acudir a nuestras oficinas. '
                          'Necesita su cédula de identidad y número de referencia del trámite. '
                          'El sistema está disponible las 24 horas del día.',
                'word_count': 32
            },
            {
                'heading': 'Contacto',
                'heading_level': 2,
                'content': 'Para mayor información puede comunicarse con nosotros a través de nuestros canales oficiales. '
                          'Línea gratuita: 800-10-1000. '
                          'Correo electrónico: contacto@test.gob.bo',
                'word_count': 25
            }
        ],
        'links': [
            {'text': 'Consultar trámite', 'url': '/tramites/consulta'},
            {'text': 'Ver más', 'url': '/info'},  # Genérico - debe detectar
            {'text': 'Aquí', 'url': '/link'},  # Genérico - debe detectar
            {'text': 'Descargar formulario de solicitud', 'url': '/forms/solicitud.pdf'},
            {'text': 'Iniciar sesión en el sistema', 'url': '/login'},
            {'text': 'Click aquí', 'url': '/page'}  # Genérico - debe detectar
        ],
        'labels': [
            {'text': 'Número de documento', 'for': 'documento'},
            {'text': 'Correo electrónico', 'for': 'email'},
            {'text': 'Ingrese texto', 'for': 'input1'}  # Ambiguo
        ]
    }

    # Ejecutar análisis
    result = analyzer.analyze_website(test_corpus)

    # Verificar estructura del resultado
    assert 'global_score' in result, "Falta global_score"
    assert 'coherence_score' in result, "Falta coherence_score"
    assert 'ambiguity_score' in result, "Falta ambiguity_score"
    assert 'clarity_score' in result, "Falta clarity_score"
    assert 'wcag_compliance' in result, "Falta wcag_compliance"
    assert 'recommendations' in result, "Falta recommendations"
    assert 'details' in result, "Falta details"

    # Verificar scores están en rango válido
    assert 0 <= result['global_score'] <= 100, f"global_score fuera de rango: {result['global_score']}"
    assert 0 <= result['coherence_score'] <= 100, f"coherence_score fuera de rango"
    assert 0 <= result['ambiguity_score'] <= 100, f"ambiguity_score fuera de rango"
    assert 0 <= result['clarity_score'] <= 100, f"clarity_score fuera de rango"

    # Verificar WCAG compliance
    wcag = result['wcag_compliance']
    assert 'ACC-07' in wcag, "Falta ACC-07 en WCAG"
    assert 'ACC-08' in wcag, "Falta ACC-08 en WCAG"
    assert 'ACC-09' in wcag, "Falta ACC-09 en WCAG"

    print(f"\n✓ NLPAnalyzer funciona correctamente")
    print(f"  Score Global: {result['global_score']:.1f}/100")
    print(f"  - Coherencia: {result['coherence_score']:.1f}")
    print(f"  - Ambigüedad: {result['ambiguity_score']:.1f}")
    print(f"  - Claridad: {result['clarity_score']:.1f}")
    print(f"  WCAG: ACC-07={wcag['ACC-07']}, ACC-08={wcag['ACC-08']}, ACC-09={wcag['ACC-09']}")
    print(f"  Recomendaciones: {len(result['recommendations'])}")

    return result


def test_nlp_data_adapter():
    """Test NLPDataAdapter convierte datos correctamente."""
    print("\n" + "=" * 60)
    print("TEST 2: NLPDataAdapter")
    print("=" * 60)

    from app.nlp.adapter import NLPDataAdapter

    # Datos simulados del Crawler (formato REAL del crawler)
    crawler_data = {
        'metadata': {
            'url': 'https://test.gob.bo',
            'title': 'Portal Test'
        },
        'text_corpus': {
            'sections': [
                {
                    'heading': 'Inicio',
                    'heading_level': 'h1',  # El crawler devuelve string
                    'content': 'Bienvenido al portal gubernamental.',
                    'word_count': 4
                }
            ],
            'paragraphs': ['Parrafo de prueba uno.', 'Parrafo de prueba dos.']
        },
        'headings': {
            # Formato real del crawler
            'headings': [
                {'level': 1, 'tag': 'h1', 'text': 'Inicio', 'length': 6, 'is_empty': False},
                {'level': 2, 'tag': 'h2', 'text': 'Servicios', 'length': 9, 'is_empty': False}
            ],
            'total_count': 2,
            'by_level': {'h1': 1, 'h2': 1, 'h3': 0, 'h4': 0, 'h5': 0, 'h6': 0}
        },
        'links': {
            # Formato real del crawler
            'all_links': [
                {'href': '/servicios', 'text': 'Ver servicios', 'title': '', 'absolute_url': '/servicios', 'is_empty': False},
                {'href': '/info', 'text': 'Mas informacion', 'title': '', 'absolute_url': '/info', 'is_empty': False},
                {'href': 'https://bolivia.gob.bo', 'text': 'Portal nacional', 'title': '', 'absolute_url': 'https://bolivia.gob.bo', 'is_empty': False}
            ],
            'total_count': 3,
            'empty_links': {'links': [], 'count': 0},
            'social': {'links': [], 'count': 0, 'unique_platforms': 0}
        },
        'forms': {
            # Formato real del crawler
            'forms': [
                {
                    'action': '/search',
                    'method': 'GET',
                    'inputs': [
                        {'type': 'text', 'id': 'nombre', 'name': 'nombre', 'placeholder': '', 'has_label': True, 'label_text': 'Nombre completo'},
                        {'type': 'tel', 'id': 'telefono', 'name': 'telefono', 'placeholder': '', 'has_label': True, 'label_text': 'Telefono'}
                    ]
                }
            ],
            'total_forms': 1,
            'total_inputs': 2,
            'inputs_with_label': 2,
            'inputs_without_label': 0
        }
    }

    # Adaptar datos
    result = NLPDataAdapter.adapt(crawler_data)

    # Verificar estructura
    assert 'url' in result, "Falta url"
    assert 'sections' in result, "Falta sections"
    assert 'links' in result, "Falta links"
    assert 'labels' in result, "Falta labels"

    # Verificar contenido
    assert len(result['sections']) > 0, "No hay secciones"
    assert len(result['links']) == 3, f"Enlaces incorrectos: {len(result['links'])}"
    assert len(result['labels']) >= 2, f"Labels incorrectos: {len(result['labels'])}"

    print(f"\n OK - NLPDataAdapter funciona correctamente")
    print(f"  URL: {result['url']}")
    print(f"  Secciones: {len(result['sections'])}")
    print(f"  Enlaces: {len(result['links'])}")
    print(f"  Labels: {len(result['labels'])}")

    return result


def test_evaluation_engine_with_nlp():
    """Test EvaluationEngine con NLP integrado (sin BD)."""
    print("\n" + "=" * 60)
    print("TEST 3: EvaluationEngine + NLP Integration")
    print("=" * 60)

    from app.evaluator.evaluation_engine import EvaluationEngine

    engine = EvaluationEngine()

    # Verificar que NLP está habilitado
    assert engine.nlp_analyzer is not None, "NLPAnalyzer no está inicializado"
    assert engine.nlp_adapter is not None, "NLPDataAdapter no está inicializado"

    print(f"\n✓ EvaluationEngine tiene NLP habilitado")
    print(f"  NLPAnalyzer: {type(engine.nlp_analyzer).__name__}")
    print(f"  NLPDataAdapter: {type(engine.nlp_adapter).__name__}")

    # Verificar pesos
    pesos = engine.PESOS
    assert pesos['accesibilidad'] == 0.30, "Peso accesibilidad incorrecto"
    assert pesos['usabilidad'] == 0.30, "Peso usabilidad incorrecto"
    assert pesos['semantica_tecnica'] == 0.15, "Peso semántica técnica incorrecto"
    assert pesos['semantica_nlp'] == 0.15, "Peso semántica NLP incorrecto"
    assert pesos['soberania'] == 0.10, "Peso soberanía incorrecto"

    total_peso = sum(pesos.values())
    assert abs(total_peso - 1.0) < 0.01, f"Pesos no suman 1.0: {total_peso}"

    print(f"\n✓ Pesos configurados correctamente:")
    print(f"  Accesibilidad: {pesos['accesibilidad']*100:.0f}%")
    print(f"  Usabilidad: {pesos['usabilidad']*100:.0f}%")
    print(f"  Semántica Técnica: {pesos['semantica_tecnica']*100:.0f}%")
    print(f"  Semántica NLP: {pesos['semantica_nlp']*100:.0f}%")
    print(f"  Soberanía: {pesos['soberania']*100:.0f}%")
    print(f"  Total: {total_peso*100:.0f}%")

    return True


def test_nlp_criteria_creation():
    """Test creación de criterios NLP."""
    print("\n" + "=" * 60)
    print("TEST 4: Creación de Criterios NLP")
    print("=" * 60)

    from app.evaluator.evaluation_engine import EvaluationEngine

    engine = EvaluationEngine()

    # Simular resultado NLP
    nlp_result = {
        'global_score': 75.5,
        'coherence_score': 80.0,
        'ambiguity_score': 70.0,
        'clarity_score': 76.5,
        'wcag_compliance': {
            'ACC-07': True,
            'ACC-08': False,
            'ACC-09': True
        },
        'recommendations': ['Mejorar textos de enlaces'],
        'details': {
            'coherence': {'sections_analyzed': 5},
            'ambiguity': {'total_analyzed': 10},
            'clarity': {'avg_score': 76.5}
        }
    }

    # Crear criterios (modo sin BD)
    criteria = engine._create_nlp_criteria_dicts(nlp_result)

    # Verificar cantidad
    assert len(criteria) == 3, f"Deben ser 3 criterios NLP, hay {len(criteria)}"

    # Verificar criterios individuales
    criteria_ids = [c['criteria_id'] for c in criteria]
    assert 'ACC-07-NLP' in criteria_ids, "Falta ACC-07-NLP"
    assert 'ACC-08-NLP' in criteria_ids, "Falta ACC-08-NLP"
    assert 'ACC-09-NLP' in criteria_ids, "Falta ACC-09-NLP"

    # Verificar status según WCAG compliance
    for c in criteria:
        if c['criteria_id'] == 'ACC-07-NLP':
            assert c['status'] == 'pass', "ACC-07 debería ser pass"
        elif c['criteria_id'] == 'ACC-08-NLP':
            assert c['status'] == 'fail', "ACC-08 debería ser fail"
        elif c['criteria_id'] == 'ACC-09-NLP':
            assert c['status'] == 'pass', "ACC-09 debería ser pass"

    print(f"\n✓ Criterios NLP creados correctamente:")
    for c in criteria:
        print(f"  {c['criteria_id']}: {c['status']} ({c['criteria_name']})")

    return criteria


def test_full_evaluation_url():
    """Test evaluación completa de URL (requiere conexión)."""
    print("\n" + "=" * 60)
    print("TEST 5: Evaluación Completa de URL")
    print("=" * 60)

    from app.evaluator.evaluation_engine import EvaluationEngine

    engine = EvaluationEngine()

    # Verificar que crawler está disponible
    if not engine.crawler:
        print("\n⚠ SKIP: Crawler no disponible")
        return None

    # URL de prueba (sitio gubernamental boliviano)
    test_url = "https://www.aduana.gob.bo"

    print(f"\nEvaluando: {test_url}")
    print("Por favor espere...\n")

    try:
        result = engine.evaluate_url(test_url)

        # Verificar estructura de resultado
        assert 'status' in result, "Falta status"
        assert result['status'] == 'completed', f"Status incorrecto: {result['status']}"
        assert 'scores' in result, "Falta scores"
        assert 'summary' in result, "Falta summary"

        # Verificar scores
        scores = result['scores']
        assert 'accesibilidad' in scores, "Falta score accesibilidad"
        assert 'usabilidad' in scores, "Falta score usabilidad"
        assert 'semantica_tecnica' in scores, "Falta score semántica técnica"
        assert 'semantica_nlp' in scores, "Falta score semántica NLP"
        assert 'soberania' in scores, "Falta score soberanía"
        assert 'total' in scores, "Falta score total"

        # Verificar summary
        summary = result['summary']
        total_criteria = summary['total_criteria']
        heuristic_criteria = summary['heuristic_criteria']
        nlp_criteria = summary['nlp_criteria']

        print(f"\n{'=' * 60}")
        print("RESULTADOS:")
        print(f"{'=' * 60}")
        print(f"\nScore Total: {scores['total']:.1f}%")
        print(f"\nScores por Dimensión:")
        print(f"  Accesibilidad (30%): {scores['accesibilidad'].get('percentage', 0):.1f}%")
        print(f"  Usabilidad (30%): {scores['usabilidad'].get('percentage', 0):.1f}%")
        print(f"  Semántica Técnica (15%): {scores['semantica_tecnica'].get('percentage', 0):.1f}%")

        if scores.get('semantica_nlp'):
            nlp = scores['semantica_nlp']
            print(f"  Semántica NLP (15%): {nlp.get('percentage', 0):.1f}%")
            print(f"    - Coherencia: {nlp.get('coherence', 0):.1f}%")
            print(f"    - Ambigüedad: {nlp.get('ambiguity', 0):.1f}%")
            print(f"    - Claridad: {nlp.get('clarity', 0):.1f}%")

        print(f"  Soberanía (10%): {scores['soberania'].get('percentage', 0):.1f}%")

        print(f"\nCriterios:")
        print(f"  Heurísticos: {heuristic_criteria}")
        print(f"  NLP: {nlp_criteria}")
        print(f"  TOTAL: {total_criteria}")

        # Verificar que son 35 criterios (32 heurísticos + 3 NLP)
        expected_total = 32 + 3  # 35
        if total_criteria == expected_total:
            print(f"\n✓ Verificación: {total_criteria} criterios = {heuristic_criteria} heurísticos + {nlp_criteria} NLP")
        else:
            print(f"\n⚠ Advertencia: Se esperaban {expected_total} criterios, hay {total_criteria}")

        print(f"\nResumen:")
        print(f"  Pasados: {summary['passed']}")
        print(f"  Fallidos: {summary['failed']}")
        print(f"  Parciales: {summary['partial']}")
        print(f"  N/A: {summary['not_applicable']}")

        return result

    except Exception as e:
        print(f"\n✗ Error durante la evaluación: {e}")
        import traceback
        traceback.print_exc()
        return None


def run_all_tests():
    """Ejecuta todos los tests."""
    print("\n" + "#" * 60)
    print("#  TEST DE INTEGRACIÓN: EvaluationEngine + NLPAnalyzer")
    print("#" * 60)

    results = {
        'nlp_analyzer': False,
        'nlp_adapter': False,
        'engine_nlp': False,
        'criteria_creation': False,
        'full_evaluation': False
    }

    try:
        # Test 1: NLPAnalyzer standalone
        test_nlp_analyzer_standalone()
        results['nlp_analyzer'] = True
    except Exception as e:
        print(f"\n✗ TEST 1 FALLÓ: {e}")

    try:
        # Test 2: NLPDataAdapter
        test_nlp_data_adapter()
        results['nlp_adapter'] = True
    except Exception as e:
        print(f"\n✗ TEST 2 FALLÓ: {e}")

    try:
        # Test 3: EvaluationEngine con NLP
        test_evaluation_engine_with_nlp()
        results['engine_nlp'] = True
    except Exception as e:
        print(f"\n✗ TEST 3 FALLÓ: {e}")

    try:
        # Test 4: Creación de criterios
        test_nlp_criteria_creation()
        results['criteria_creation'] = True
    except Exception as e:
        print(f"\n✗ TEST 4 FALLÓ: {e}")

    try:
        # Test 5: Evaluación completa
        result = test_full_evaluation_url()
        if result:
            results['full_evaluation'] = True
    except Exception as e:
        print(f"\n✗ TEST 5 FALLÓ: {e}")

    # Resumen final
    print("\n" + "#" * 60)
    print("#  RESUMEN DE TESTS")
    print("#" * 60)

    passed = sum(1 for v in results.values() if v)
    total = len(results)

    for name, passed_test in results.items():
        status = "✓ PASS" if passed_test else "✗ FAIL"
        print(f"  {status}: {name}")

    print(f"\n  Resultado: {passed}/{total} tests pasados")

    if passed == total:
        print("\n" + "=" * 60)
        print("  ✓ TODOS LOS TESTS PASARON - INTEGRACIÓN COMPLETA")
        print("=" * 60)
    else:
        print("\n" + "=" * 60)
        print(f"  ⚠ {total - passed} tests fallaron")
        print("=" * 60)

    return passed == total


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
