"""
Test del Evaluador de Semántica Técnica

Verifica que el EvaluadorSemantica funciona correctamente
con datos reales extraídos por el crawler.

Criterios según Tabla 12:
- SEM-01 a SEM-04: Semántica HTML5 (44 pts)
- SEO-01 a SEO-04: Optimización SEO (38 pts)
- FMT-01 a FMT-02: Formato técnico (18 pts)
Total: 100 puntos
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
        'images': {
            'total_count': 5,
            'images': [
                {'src': '/images/logo.webp', 'alt': 'Logo'},
                {'src': '/images/banner.avif', 'alt': 'Banner'},
                {'src': '/images/icon.svg', 'alt': 'Icono'},
                {'src': '/images/foto.jpg', 'alt': 'Foto'},
                {'src': '/images/bg.png', 'alt': 'Fondo'}
            ]
        },
        'links': {
            'total_count': 20,
            'all_links': [
                {'href': '/documentos/informe.pdf', 'text': 'Informe PDF'},
                {'href': '/documentos/datos.csv', 'text': 'Datos CSV'},
                {'href': '/contacto', 'text': 'Contacto'},
                {'href': '/servicios', 'text': 'Servicios'}
            ]
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

    # Verificar que la suma total de max_score sea 100
    assert max_score == 100, f"Esperado max_score total=100, obtenido {max_score}"
    assert len(results) == 10, f"Esperado 10 criterios, obtenido {len(results)}"
    print("[OK] max_score total = 100, 10 criterios evaluados")

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


def test_sem03_elementos_semanticos():
    """Test específico para SEM-03: Elementos semánticos HTML5"""
    print("=" * 80)
    print("TEST 3: SEM-03 - Elementos Semánticos HTML5")
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
        'images': {'total_count': 0, 'images': []},
        'links': {'all_links': []},
        'forms': {'total_inputs': 0, 'inputs_with_label': 0}
    }

    results = evaluador.evaluate(mock_all_tags)
    sem03 = next(r for r in results if r.criteria_id == "SEM-03")

    print(f"\n  Caso 1 (7/7 tags): Score {sem03.score}/{sem03.max_score} - Status: {sem03.status}")
    assert sem03.status == "pass", f"Esperado pass, obtenido {sem03.status}"
    assert sem03.score == 14.0, f"Esperado 14, obtenido {sem03.score}"

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
        'images': {'total_count': 0, 'images': []},
        'links': {'all_links': []},
        'forms': {'total_inputs': 0, 'inputs_with_label': 0}
    }

    results = evaluador.evaluate(mock_partial)
    sem03 = next(r for r in results if r.criteria_id == "SEM-03")

    print(f"  Caso 2 (3/7 tags): Score {sem03.score}/{sem03.max_score} - Status: {sem03.status}")
    assert sem03.status == "partial", f"Esperado partial, obtenido {sem03.status}"
    assert sem03.score == 6.0, f"Esperado 6, obtenido {sem03.score}"

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
        'images': {'total_count': 0, 'images': []},
        'links': {'all_links': []},
        'forms': {'total_inputs': 0, 'inputs_with_label': 0}
    }

    results = evaluador.evaluate(mock_fail)
    sem03 = next(r for r in results if r.criteria_id == "SEM-03")

    print(f"  Caso 3 (2/7 tags): Score {sem03.score}/{sem03.max_score} - Status: {sem03.status}")
    assert sem03.status == "fail", f"Esperado fail, obtenido {sem03.status}"
    assert sem03.score == 4.0, f"Esperado 4, obtenido {sem03.score}"

    print("\n[OK] SEM-03 (elementos semánticos) funciona correctamente")
    return True


def test_seo04_headings():
    """Test específico para SEO-04: Jerarquía de headings (WCAG 1.3.1 A)"""
    print("=" * 80)
    print("TEST 4: SEO-04 - Jerarquía de Headings (14 pts)")
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
        'images': {'total_count': 0, 'images': []},
        'links': {'all_links': []},
        'forms': {'total_inputs': 0, 'inputs_with_label': 0}
    }

    results = evaluador.evaluate(mock_perfect)
    seo04 = next(r for r in results if r.criteria_id == "SEO-04")

    print(f"\n  Caso 1 (1 h1 + válida): Score {seo04.score}/{seo04.max_score} - Status: {seo04.status}")
    assert seo04.status == "pass", f"Esperado pass, obtenido {seo04.status}"
    assert seo04.score == 14.0, f"Esperado 14, obtenido {seo04.score}"

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
        'images': {'total_count': 0, 'images': []},
        'links': {'all_links': []},
        'forms': {'total_inputs': 0, 'inputs_with_label': 0}
    }

    results = evaluador.evaluate(mock_multi_h1)
    seo04 = next(r for r in results if r.criteria_id == "SEO-04")

    print(f"  Caso 2 (3 h1 + válida): Score {seo04.score}/{seo04.max_score} - Status: {seo04.status}")
    assert seo04.status == "partial", f"Esperado partial, obtenido {seo04.status}"
    assert seo04.score == 7.0, f"Esperado 7, obtenido {seo04.score}"

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
        'images': {'total_count': 0, 'images': []},
        'links': {'all_links': []},
        'forms': {'total_inputs': 0, 'inputs_with_label': 0}
    }

    results = evaluador.evaluate(mock_fail)
    seo04 = next(r for r in results if r.criteria_id == "SEO-04")

    print(f"  Caso 3 (0 h1 + inválida): Score {seo04.score}/{seo04.max_score} - Status: {seo04.status}")
    assert seo04.status == "fail", f"Esperado fail, obtenido {seo04.status}"
    assert seo04.score == 0.0, f"Esperado 0, obtenido {seo04.score}"

    print("\n[OK] SEO-04 (headings) funciona correctamente")
    return True


def test_fmt01_formatos_abiertos():
    """Test específico para FMT-01: Uso de formatos abiertos"""
    print("=" * 80)
    print("TEST 5: FMT-01 - Formatos Abiertos (10 pts)")
    print("=" * 80)

    evaluador = EvaluadorSemantica()

    # Caso 1: Solo formatos abiertos (pass)
    mock_open = {
        'url': 'https://test.gob.bo',
        'metadata': {},
        'structure': {'has_html5_doctype': True, 'has_utf8_charset': True},
        'semantic_elements': {},
        'headings': {'h1_count': 1, 'has_single_h1': True, 'hierarchy_valid': True, 'by_level': {}},
        'images': {'total_count': 0, 'images': []},
        'links': {
            'all_links': [
                {'href': '/docs/informe.pdf', 'text': 'Informe'},
                {'href': '/docs/datos.csv', 'text': 'Datos'},
                {'href': '/docs/manual.odt', 'text': 'Manual'}
            ]
        },
        'forms': {}
    }

    results = evaluador.evaluate(mock_open)
    fmt01 = next(r for r in results if r.criteria_id == "FMT-01")

    print(f"\n  Caso 1 (solo abiertos): Score {fmt01.score}/{fmt01.max_score} - Status: {fmt01.status}")
    assert fmt01.status == "pass", f"Esperado pass, obtenido {fmt01.status}"
    assert fmt01.score == 10.0, f"Esperado 10, obtenido {fmt01.score}"

    # Caso 2: Mayoría propietarios (fail)
    evaluador.clear_results()
    mock_proprietary = {
        'url': 'https://test.gob.bo',
        'metadata': {},
        'structure': {'has_html5_doctype': True, 'has_utf8_charset': True},
        'semantic_elements': {},
        'headings': {'h1_count': 1, 'has_single_h1': True, 'hierarchy_valid': True, 'by_level': {}},
        'images': {'total_count': 0, 'images': []},
        'links': {
            'all_links': [
                {'href': '/docs/informe.docx', 'text': 'Informe Word'},
                {'href': '/docs/datos.xlsx', 'text': 'Datos Excel'},
                {'href': '/docs/pres.pptx', 'text': 'Presentación'},
                {'href': '/docs/otro.pdf', 'text': 'PDF'}
            ]
        },
        'forms': {}
    }

    results = evaluador.evaluate(mock_proprietary)
    fmt01 = next(r for r in results if r.criteria_id == "FMT-01")

    print(f"  Caso 2 (3/4 propietarios): Score {fmt01.score}/{fmt01.max_score} - Status: {fmt01.status}")
    assert fmt01.status == "fail", f"Esperado fail, obtenido {fmt01.status}"
    assert fmt01.score == 0.0, f"Esperado 0, obtenido {fmt01.score}"

    # Caso 3: Sin documentos (pass por defecto)
    evaluador.clear_results()
    mock_no_docs = {
        'url': 'https://test.gob.bo',
        'metadata': {},
        'structure': {'has_html5_doctype': True, 'has_utf8_charset': True},
        'semantic_elements': {},
        'headings': {'h1_count': 1, 'has_single_h1': True, 'hierarchy_valid': True, 'by_level': {}},
        'images': {'total_count': 0, 'images': []},
        'links': {
            'all_links': [
                {'href': '/contacto', 'text': 'Contacto'},
                {'href': '/servicios', 'text': 'Servicios'}
            ]
        },
        'forms': {}
    }

    results = evaluador.evaluate(mock_no_docs)
    fmt01 = next(r for r in results if r.criteria_id == "FMT-01")

    print(f"  Caso 3 (sin documentos): Score {fmt01.score}/{fmt01.max_score} - Status: {fmt01.status}")
    assert fmt01.status == "pass", f"Esperado pass, obtenido {fmt01.status}"
    assert fmt01.score == 10.0, f"Esperado 10, obtenido {fmt01.score}"

    print("\n[OK] FMT-01 (formatos abiertos) funciona correctamente")
    return True


def test_fmt02_imagenes_optimizadas():
    """Test específico para FMT-02: Imágenes optimizadas"""
    print("=" * 80)
    print("TEST 6: FMT-02 - Imágenes Optimizadas (8 pts)")
    print("=" * 80)

    evaluador = EvaluadorSemantica()

    # Caso 1: Mayoría optimizadas (pass)
    mock_optimized = {
        'url': 'https://test.gob.bo',
        'metadata': {},
        'structure': {'has_html5_doctype': True, 'has_utf8_charset': True},
        'semantic_elements': {},
        'headings': {'h1_count': 1, 'has_single_h1': True, 'hierarchy_valid': True, 'by_level': {}},
        'images': {
            'total_count': 4,
            'images': [
                {'src': '/img/logo.webp', 'alt': 'Logo'},
                {'src': '/img/banner.avif', 'alt': 'Banner'},
                {'src': '/img/icon.svg', 'alt': 'Icono'},
                {'src': '/img/foto.jpg', 'alt': 'Foto'}
            ]
        },
        'links': {'all_links': []},
        'forms': {}
    }

    results = evaluador.evaluate(mock_optimized)
    fmt02 = next(r for r in results if r.criteria_id == "FMT-02")

    print(f"\n  Caso 1 (3/4 optimizadas): Score {fmt02.score}/{fmt02.max_score} - Status: {fmt02.status}")
    assert fmt02.status == "pass", f"Esperado pass, obtenido {fmt02.status}"
    assert fmt02.score == 8.0, f"Esperado 8, obtenido {fmt02.score}"

    # Caso 2: Todas pesadas (fail)
    evaluador.clear_results()
    mock_heavy = {
        'url': 'https://test.gob.bo',
        'metadata': {},
        'structure': {'has_html5_doctype': True, 'has_utf8_charset': True},
        'semantic_elements': {},
        'headings': {'h1_count': 1, 'has_single_h1': True, 'hierarchy_valid': True, 'by_level': {}},
        'images': {
            'total_count': 3,
            'images': [
                {'src': '/img/foto1.jpg', 'alt': 'Foto 1'},
                {'src': '/img/foto2.png', 'alt': 'Foto 2'},
                {'src': '/img/foto3.bmp', 'alt': 'Foto 3'}
            ]
        },
        'links': {'all_links': []},
        'forms': {}
    }

    results = evaluador.evaluate(mock_heavy)
    fmt02 = next(r for r in results if r.criteria_id == "FMT-02")

    print(f"  Caso 2 (0/3 optimizadas): Score {fmt02.score}/{fmt02.max_score} - Status: {fmt02.status}")
    assert fmt02.status == "fail", f"Esperado fail, obtenido {fmt02.status}"
    assert fmt02.score == 0.0, f"Esperado 0, obtenido {fmt02.score}"

    # Caso 3: Sin imágenes (na)
    evaluador.clear_results()
    mock_no_images = {
        'url': 'https://test.gob.bo',
        'metadata': {},
        'structure': {'has_html5_doctype': True, 'has_utf8_charset': True},
        'semantic_elements': {},
        'headings': {'h1_count': 1, 'has_single_h1': True, 'hierarchy_valid': True, 'by_level': {}},
        'images': {'total_count': 0, 'images': []},
        'links': {'all_links': []},
        'forms': {}
    }

    results = evaluador.evaluate(mock_no_images)
    fmt02 = next(r for r in results if r.criteria_id == "FMT-02")

    print(f"  Caso 3 (sin imágenes): Score {fmt02.score}/{fmt02.max_score} - Status: {fmt02.status}")
    assert fmt02.status == "na", f"Esperado na, obtenido {fmt02.status}"

    print("\n[OK] FMT-02 (imágenes optimizadas) funciona correctamente")
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

    # Test 3: SEM-03 (elementos semánticos) específico
    print("\n")
    test_sem03_elementos_semanticos()

    # Test 4: SEO-04 (headings) específico
    print("\n")
    test_seo04_headings()

    # Test 5: FMT-01 (formatos abiertos) específico
    print("\n")
    test_fmt01_formatos_abiertos()

    # Test 6: FMT-02 (imágenes optimizadas) específico
    print("\n")
    test_fmt02_imagenes_optimizadas()

    print("\n" + "=" * 80)
    print("[OK] TESTS COMPLETADOS")
    print("=" * 80)


if __name__ == "__main__":
    main()
