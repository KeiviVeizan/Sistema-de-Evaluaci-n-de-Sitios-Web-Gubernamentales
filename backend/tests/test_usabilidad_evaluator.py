"""
Test del Evaluador de Usabilidad

Verifica que el EvaluadorUsabilidad funciona correctamente
con datos reales extraidos por el crawler.
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.evaluator.usabilidad_evaluator import EvaluadorUsabilidad
from app.crawler.html_crawler import GobBoCrawler


def test_with_mock_data():
    """Test con datos mock"""
    print("=" * 80)
    print("TEST 1: Evaluador de Usabilidad con datos mock")
    print("=" * 80)

    evaluador = EvaluadorUsabilidad()

    # Datos mock simulando salida del crawler
    mock_content = {
        'metadata': {
            'title': 'Aduana Nacional de Bolivia - Gobierno del Estado Plurinacional',
            'lang': 'es'
        },
        'images': {
            'total_count': 10,
            'images': [
                {'src': '/images/escudo-bolivia.png', 'alt': 'Escudo de Bolivia'},
                {'src': '/images/logo.png', 'alt': 'Logo institucional'}
            ]
        },
        'semantic_elements': {
            'nav': {'count': 2, 'present': True},
            'footer': {'count': 1, 'present': True},
            'header': {'count': 1, 'present': True}
        },
        'links': {
            'total_count': 50,
            'social': {
                'links': [
                    {'href': 'https://facebook.com/aduanabolivia', 'text': 'Facebook'},
                    {'href': 'https://twitter.com/aduanabolivia', 'text': 'Twitter'}
                ]
            },
            'email': {
                'links': [{'href': 'mailto:contacto@aduana.gob.bo', 'text': 'Email'}]
            },
            'phone': {
                'links': [{'href': 'tel:+59122345678', 'text': 'Telefono'}]
            },
            'all_links': [
                {'href': '/sitemap', 'text': 'Mapa del sitio'},
                {'href': '/contacto', 'text': 'Contacto'}
            ]
        },
        'forms': {
            'total_forms': 2,
            'forms': [
                {
                    'action': '/search',
                    'inputs': [
                        {'type': 'search', 'name': 'q', 'placeholder': 'Buscar...'}
                    ]
                },
                {
                    'action': '/contacto',
                    'inputs': [
                        {'type': 'text', 'name': 'nombre'},
                        {'type': 'email', 'name': 'email'},
                        {'type': 'textarea', 'name': 'mensaje'}
                    ]
                }
            ]
        },
        'text_corpus': {
            'has_bolivia_service_text': True,
            'footer_text': 'Contacto: contacto@aduana.gob.bo Tel: +591 2 2345678 Av. 20 de Octubre, La Paz',
            'sections': [
                {'heading': 'Servicios de la Aduana Nacional', 'paragraphs': ['Informacion...']}
            ]
        },
        'structure': {}
    }

    results = evaluador.evaluate(mock_content)

    print(f"\nResultados de evaluacion ({len(results)} criterios):\n")

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
    print("TEST 2: Evaluador de Usabilidad con datos reales")
    print("=" * 80)

    print("\n[INFO] Crawleando https://www.aduana.gob.bo ...")

    crawler = GobBoCrawler(timeout=45)
    extracted = crawler.crawl('https://www.aduana.gob.bo')

    if 'error' in extracted:
        print(f"[ERROR] No se pudo crawlear: {extracted['error']}")
        return False

    print("[OK] Contenido extraido correctamente")

    # Evaluar
    evaluador = EvaluadorUsabilidad()
    results = evaluador.evaluate(extracted)

    print(f"\nResultados de evaluacion ({len(results)} criterios):\n")

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


def main():
    print("\n" + "=" * 80)
    print("TEST DEL EVALUADOR DE USABILIDAD")
    print("=" * 80 + "\n")

    # Test 1: Datos mock
    test_with_mock_data()

    # Test 2: Datos reales
    print("\n")
    test_with_real_crawler()

    print("\n" + "=" * 80)
    print("[OK] TESTS COMPLETADOS")
    print("=" * 80)


if __name__ == "__main__":
    main()
