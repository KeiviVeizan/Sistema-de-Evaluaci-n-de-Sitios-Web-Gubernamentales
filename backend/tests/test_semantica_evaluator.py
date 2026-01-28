"""
Test del Evaluador de Semántica Técnica

Verifica que el EvaluadorSemantica funciona correctamente
con datos reales extraídos por el crawler.
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.evaluator.semantica_evaluator import EvaluadorSemantica
from app.crawler.html_crawler import GobBoCrawler


def test_with_mock_data():
    """Test con datos mock"""
    print("=" * 80)
    print("TEST 1: Evaluador de Semántica con datos mock")
    print("=" * 80)

    evaluador = EvaluadorSemantica()

    # Datos mock simulando salida del crawler
    mock_content = {
        'url': 'https://www.ejemplo.gob.bo',
        'metadata': {
            'title': 'Ministerio de Ejemplo - Gobierno del Estado Plurinacional de Bolivia',
            'title_length': 60,
            'has_title': True,
            'lang': 'es',
            'has_lang': True,
            'description': 'Portal oficial del Ministerio de Ejemplo de Bolivia. Información sobre servicios y trámites.',
            'description_length': 95,
            'has_description': True,
            'keywords': 'ministerio, bolivia, gobierno, servicios, tramites',
            'has_keywords': True,
            'viewport': 'width=device-width, initial-scale=1.0',
            'has_viewport': True
        },
        'structure': {
            'has_html5_doctype': True,
            'doctype_text': 'html',
            'has_utf8_charset': True,
            'charset_declared': 'utf-8',
            'has_html': True,
            'has_head': True,
            'has_body': True
        },
        'semantic_elements': {
            'header': {'count': 1, 'present': True},
            'nav': {'count': 2, 'present': True},
            'main': {'count': 1, 'present': True},
            'footer': {'count': 1, 'present': True},
            'article': {'count': 3, 'present': True},
            'section': {'count': 5, 'present': True},
            'aside': {'count': 1, 'present': True}
        },
        'headings': {
            'h1_count': 1,
            'has_single_h1': True,
            'hierarchy_valid': True,
            'hierarchy_errors': [],
            'by_level': {'h1': 1, 'h2': 4, 'h3': 6, 'h4': 2, 'h5': 0, 'h6': 0}
        },
        'forms': {
            'total_forms': 2,
            'total_inputs': 5,
            'inputs_with_label': 4,
            'inputs_without_label': 1,
            'forms': []
        }
    }

    results = evaluador.evaluate(mock_content)

    print(f"\nResultados de evaluación ({len(results)} criterios):\n")

    total_score = 0
    max_score = 0

    for result in results:
        r = result.to_dict()
        status_icon = {
            'pass': '[OK]',
            'partial': '[~~]',
            'fail': '[!!]',
            'na': '[NA]'
        }.get(r['status'], '[??]')

        print(f"  {status_icon} {r['criteria_id']}: {r['criteria_name']}")
        print(f"       Score: {r['score']}/{r['max_score']} ({r['score_percentage']:.1f}%)")
        print(f"       {r['details'].get('message', '')}")
        print()

        total_score += r['score']
        max_score += r['max_score']

    print("-" * 80)
    print(f"TOTAL: {total_score:.2f}/{max_score} ({(total_score/max_score*100):.1f}%)")
    print()

    return True


def test_with_real_crawler():
    """Test con datos reales del crawler"""
    print("=" * 80)
    print("TEST 2: Evaluador de Semántica con datos reales")
    print("=" * 80)

    print("\n[INFO] Crawleando https://www.aduana.gob.bo ...")

    crawler = GobBoCrawler(timeout=45)
    extracted = crawler.crawl('https://www.aduana.gob.bo')

    if 'error' in extracted:
        print(f"[ERROR] No se pudo crawlear: {extracted['error']}")
        return False

    print("[OK] Contenido extraído correctamente")

    # Evaluar
    evaluador = EvaluadorSemantica()
    results = evaluador.evaluate(extracted)

    print(f"\nResultados de evaluación ({len(results)} criterios):\n")

    total_score = 0
    max_score = 0
    passed = 0
    failed = 0
    partial = 0

    for result in results:
        r = result.to_dict()
        status_icon = {
            'pass': '[OK]',
            'partial': '[~~]',
            'fail': '[!!]',
            'na': '[NA]'
        }.get(r['status'], '[??]')

        if r['status'] == 'pass':
            passed += 1
        elif r['status'] == 'fail':
            failed += 1
        elif r['status'] == 'partial':
            partial += 1

        print(f"  {status_icon} {r['criteria_id']}: {r['criteria_name']}")
        print(f"       Score: {r['score']}/{r['max_score']} ({r['score_percentage']:.1f}%)")
        print(f"       {r['details'].get('message', '')}")
        print()

        total_score += r['score']
        max_score += r['max_score']

    print("-" * 80)
    print(f"RESUMEN:")
    print(f"  - Pasaron: {passed}")
    print(f"  - Parciales: {partial}")
    print(f"  - Fallaron: {failed}")
    print(f"\nSCORE TOTAL: {total_score:.2f}/{max_score} ({(total_score/max_score*100):.1f}%)")
    print()

    return True


def test_sem01_tags_semanticos():
    """Test específico para SEM-01: Tags HTML5 semánticos"""
    print("=" * 80)
    print("TEST 3: SEM-01 - Tags HTML5 Semánticos")
    print("=" * 80)

    evaluador = EvaluadorSemantica()

    # Caso 1: Todos los tags presentes
    mock_all_tags = {
        'url': 'https://test.gob.bo',
        'metadata': {'title': 'Test', 'has_title': True, 'title_length': 4},
        'structure': {'has_html5_doctype': True, 'has_utf8_charset': True},
        'semantic_elements': {
            'header': {'present': True},
            'nav': {'present': True},
            'main': {'present': True},
            'article': {'present': True},
            'section': {'present': True},
            'aside': {'present': True},
            'footer': {'present': True}
        },
        'headings': {'h1_count': 1, 'has_single_h1': True, 'hierarchy_valid': True, 'by_level': {}},
        'forms': {'total_inputs': 0, 'inputs_with_label': 0}
    }

    results = evaluador.evaluate(mock_all_tags)
    sem01 = next(r for r in results if r.criteria_id == "SEM-01")

    print(f"\n  Caso 1 (7/7 tags): Score {sem01.score}/{sem01.max_score} - Status: {sem01.status}")
    assert sem01.status == "pass", f"Esperado pass, obtenido {sem01.status}"
    assert sem01.score == 14.0, f"Esperado 14, obtenido {sem01.score}"

    # Caso 2: Solo 3 tags (partial)
    evaluador.clear_results()
    mock_partial = {
        'url': 'https://test.gob.bo',
        'metadata': {'title': 'Test', 'has_title': True, 'title_length': 4},
        'structure': {'has_html5_doctype': True, 'has_utf8_charset': True},
        'semantic_elements': {
            'header': {'present': True},
            'nav': {'present': True},
            'main': {'present': True},
            'article': {'present': False},
            'section': {'present': False},
            'aside': {'present': False},
            'footer': {'present': False}
        },
        'headings': {'h1_count': 1, 'has_single_h1': True, 'hierarchy_valid': True, 'by_level': {}},
        'forms': {'total_inputs': 0, 'inputs_with_label': 0}
    }

    results = evaluador.evaluate(mock_partial)
    sem01 = next(r for r in results if r.criteria_id == "SEM-01")

    print(f"  Caso 2 (3/7 tags): Score {sem01.score}/{sem01.max_score} - Status: {sem01.status}")
    assert sem01.status == "partial", f"Esperado partial, obtenido {sem01.status}"
    assert sem01.score == 6.0, f"Esperado 6, obtenido {sem01.score}"

    # Caso 3: Solo 2 tags (fail)
    evaluador.clear_results()
    mock_fail = {
        'url': 'https://test.gob.bo',
        'metadata': {'title': 'Test', 'has_title': True, 'title_length': 4},
        'structure': {'has_html5_doctype': True, 'has_utf8_charset': True},
        'semantic_elements': {
            'header': {'present': True},
            'nav': {'present': True},
            'main': {'present': False},
            'article': {'present': False},
            'section': {'present': False},
            'aside': {'present': False},
            'footer': {'present': False}
        },
        'headings': {'h1_count': 1, 'has_single_h1': True, 'hierarchy_valid': True, 'by_level': {}},
        'forms': {'total_inputs': 0, 'inputs_with_label': 0}
    }

    results = evaluador.evaluate(mock_fail)
    sem01 = next(r for r in results if r.criteria_id == "SEM-01")

    print(f"  Caso 3 (2/7 tags): Score {sem01.score}/{sem01.max_score} - Status: {sem01.status}")
    assert sem01.status == "fail", f"Esperado fail, obtenido {sem01.status}"
    assert sem01.score == 4.0, f"Esperado 4, obtenido {sem01.score}"

    print("\n[OK] SEM-01 funciona correctamente")
    return True


def test_sem03_headings():
    """Test específico para SEM-03: Jerarquía de headings"""
    print("=" * 80)
    print("TEST 4: SEM-03 - Jerarquía de Headings")
    print("=" * 80)

    evaluador = EvaluadorSemantica()

    # Caso 1: Jerarquía perfecta
    mock_perfect = {
        'url': 'https://test.gob.bo',
        'metadata': {'title': 'Test', 'has_title': True, 'title_length': 4},
        'structure': {'has_html5_doctype': True, 'has_utf8_charset': True},
        'semantic_elements': {},
        'headings': {
            'h1_count': 1,
            'has_single_h1': True,
            'hierarchy_valid': True,
            'hierarchy_errors': [],
            'by_level': {'h1': 1, 'h2': 3, 'h3': 5}
        },
        'forms': {'total_inputs': 0, 'inputs_with_label': 0}
    }

    results = evaluador.evaluate(mock_perfect)
    sem03 = next(r for r in results if r.criteria_id == "SEM-03")

    print(f"\n  Caso 1 (1 h1 + válida): Score {sem03.score}/{sem03.max_score} - Status: {sem03.status}")
    assert sem03.status == "pass", f"Esperado pass, obtenido {sem03.status}"
    assert sem03.score == 10.0, f"Esperado 10, obtenido {sem03.score}"

    # Caso 2: Múltiples h1 (partial)
    evaluador.clear_results()
    mock_multi_h1 = {
        'url': 'https://test.gob.bo',
        'metadata': {'title': 'Test', 'has_title': True, 'title_length': 4},
        'structure': {'has_html5_doctype': True, 'has_utf8_charset': True},
        'semantic_elements': {},
        'headings': {
            'h1_count': 3,
            'has_single_h1': False,
            'hierarchy_valid': True,
            'hierarchy_errors': [],
            'by_level': {'h1': 3, 'h2': 2}
        },
        'forms': {'total_inputs': 0, 'inputs_with_label': 0}
    }

    results = evaluador.evaluate(mock_multi_h1)
    sem03 = next(r for r in results if r.criteria_id == "SEM-03")

    print(f"  Caso 2 (3 h1 + válida): Score {sem03.score}/{sem03.max_score} - Status: {sem03.status}")
    assert sem03.status == "partial", f"Esperado partial, obtenido {sem03.status}"
    assert sem03.score == 5.0, f"Esperado 5, obtenido {sem03.score}"

    # Caso 3: Sin h1 y jerarquía inválida (fail)
    evaluador.clear_results()
    mock_fail = {
        'url': 'https://test.gob.bo',
        'metadata': {'title': 'Test', 'has_title': True, 'title_length': 4},
        'structure': {'has_html5_doctype': True, 'has_utf8_charset': True},
        'semantic_elements': {},
        'headings': {
            'h1_count': 0,
            'has_single_h1': False,
            'hierarchy_valid': False,
            'hierarchy_errors': [{'position': 0, 'expected_max': 1, 'found': 3}],
            'by_level': {'h3': 2, 'h4': 1}
        },
        'forms': {'total_inputs': 0, 'inputs_with_label': 0}
    }

    results = evaluador.evaluate(mock_fail)
    sem03 = next(r for r in results if r.criteria_id == "SEM-03")

    print(f"  Caso 3 (0 h1 + inválida): Score {sem03.score}/{sem03.max_score} - Status: {sem03.status}")
    assert sem03.status == "fail", f"Esperado fail, obtenido {sem03.status}"
    assert sem03.score == 0.0, f"Esperado 0, obtenido {sem03.score}"

    print("\n[OK] SEM-03 funciona correctamente")
    return True


def main():
    print("\n" + "=" * 80)
    print("TEST DEL EVALUADOR DE SEMÁNTICA")
    print("=" * 80 + "\n")

    # Test 1: Datos mock
    test_with_mock_data()

    # Test 2: Datos reales
    print("\n")
    test_with_real_crawler()

    # Test 3: SEM-01 específico
    print("\n")
    test_sem01_tags_semanticos()

    # Test 4: SEM-03 específico
    print("\n")
    test_sem03_headings()

    print("\n" + "=" * 80)
    print("[OK] TESTS COMPLETADOS")
    print("=" * 80)


if __name__ == "__main__":
    main()
