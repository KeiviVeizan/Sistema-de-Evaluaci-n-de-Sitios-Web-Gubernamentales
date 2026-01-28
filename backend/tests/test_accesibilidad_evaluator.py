"""
Test del Evaluador de Accesibilidad

Verifica que el EvaluadorAccesibilidad funciona correctamente
con datos reales extraidos por el crawler.
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.evaluator.accesibilidad_evaluator import EvaluadorAccesibilidad
from app.crawler.html_crawler import GobBoCrawler


def test_with_mock_data():
    """Test con datos mock"""
    print("=" * 80)
    print("TEST 1: Evaluador con datos mock")
    print("=" * 80)

    evaluador = EvaluadorAccesibilidad()

    # Datos mock simulando salida del crawler
    mock_content = {
        'metadata': {
            'lang': 'es',
            'title': 'Aduana Nacional de Bolivia',
            'title_length': 26
        },
        'images': {
            'total_count': 10,
            'with_alt': 8,
            'without_alt': 2,
            'images': [
                {'src': 'logo.png', 'has_alt': True, 'alt': 'Logo'},
                {'src': 'banner.jpg', 'has_alt': False, 'alt': ''}
            ]
        },
        'headings': {
            'total_count': 5,
            'h1_count': 1,
            'hierarchy_valid': True,
            'headings': [
                {'level': 'h1', 'text': 'Bienvenido'},
                {'level': 'h2', 'text': 'Servicios'}
            ]
        },
        'forms': {
            'total_count': 1,
            'total_inputs': 3,
            'inputs_with_label': 2,
            'forms': []
        },
        'media': {
            'has_autoplay': False,
            'audio_count': 0,
            'video_count': 1
        },
        'links': {
            'total_count': 50,
            'generic_text': {'count': 3},
            'empty_links': {'count': 1}
        },
        'language_parts': {
            'main_language': 'es',
            'has_main_language': True,
            'elements_with_different_lang': [],
            'count_different_lang': 0,
            'acc_10_compliant': True
        }
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
    print("TEST 2: Evaluador con datos reales del crawler")
    print("=" * 80)

    print("\n[INFO] Crawleando https://www.aduana.gob.bo ...")

    crawler = GobBoCrawler(timeout=45)
    extracted = crawler.crawl('https://www.aduana.gob.bo')

    if 'error' in extracted:
        print(f"[ERROR] No se pudo crawlear: {extracted['error']}")
        return False

    print("[OK] Contenido extraido correctamente")

    # Evaluar
    evaluador = EvaluadorAccesibilidad()
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
    print("TEST DEL EVALUADOR DE ACCESIBILIDAD")
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
