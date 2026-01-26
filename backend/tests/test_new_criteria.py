"""
Test de verificacion para nuevos criterios ACC-10 y NAV-02.

ACC-10: Idioma de partes (detecta elementos con lang diferente)
NAV-02: Breadcrumbs (detecta migas de pan)
"""

import json
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.crawler.html_crawler import GobBoCrawler


def test_acc10_language_parts(result):
    """Verifica extraccion de ACC-10: Idioma de partes"""
    print("\n" + "=" * 80)
    print("ACC-10: IDIOMA DE PARTES")
    print("=" * 80)

    if 'language_parts' not in result:
        print("[ERROR] No se encontro 'language_parts' en resultado")
        return False

    lang_data = result['language_parts']

    print(f"\n  Idioma principal: {lang_data.get('main_language', 'N/A')}")
    print(f"  Tiene idioma definido: {lang_data.get('has_main_language', False)}")
    print(f"  Elementos con idioma diferente: {lang_data.get('count_different_lang', 0)}")
    print(f"  Contenido multiidioma: {lang_data.get('has_multilingual_content', False)}")
    print(f"  Idiomas encontrados: {lang_data.get('languages_found', [])}")
    print(f"  ACC-10 Cumple: {lang_data.get('acc_10_compliant', False)}")

    # Mostrar ejemplos si hay contenido multiidioma
    if lang_data.get('elements_with_different_lang'):
        print(f"\n  Ejemplos de elementos con idioma diferente:")
        for elem in lang_data['elements_with_different_lang'][:3]:
            print(f"    - <{elem['tag']} lang=\"{elem['lang']}\">")
            print(f"      Texto: \"{elem['text_preview'][:50]}...\"")

    return True


def test_nav02_breadcrumbs(result):
    """Verifica extraccion de NAV-02: Breadcrumbs"""
    print("\n" + "=" * 80)
    print("NAV-02: BREADCRUMBS")
    print("=" * 80)

    if 'breadcrumbs' not in result:
        print("[ERROR] No se encontro 'breadcrumbs' en resultado")
        return False

    bc_data = result['breadcrumbs']

    print(f"\n  Tiene breadcrumbs: {bc_data.get('has_breadcrumbs', False)}")
    print(f"  Tipo detectado: {bc_data.get('breadcrumb_type', 'N/A')}")
    print(f"  Cantidad items: {bc_data.get('breadcrumb_count', 0)}")

    # Mostrar items si hay breadcrumbs
    if bc_data.get('breadcrumb_items'):
        print(f"\n  Items del breadcrumb:")
        for i, item in enumerate(bc_data['breadcrumb_items'][:5], 1):
            print(f"    {i}. \"{item['text']}\" -> {item['href'][:50] if item['href'] else 'N/A'}")

    return True


def test_site(url):
    """Prueba un sitio especifico"""
    print("\n" + "#" * 80)
    print(f"# PROBANDO: {url}")
    print("#" * 80)

    try:
        crawler = GobBoCrawler(timeout=45)
        result = crawler.crawl(url)

        if 'error' in result:
            print(f"[ERROR] No se pudo cargar: {result['error']}")
            return None

        print("[OK] Sitio cargado correctamente")

        # Test ACC-10
        test_acc10_language_parts(result)

        # Test NAV-02
        test_nav02_breadcrumbs(result)

        return result

    except Exception as e:
        print(f"[ERROR] Exception: {str(e)}")
        return None


def run_all_tests():
    """Ejecuta tests en multiples sitios"""
    print("\n" + "=" * 80)
    print("VERIFICACION DE NUEVOS CRITERIOS: ACC-10 y NAV-02")
    print("=" * 80)

    # Lista de sitios a probar
    sites = [
        "https://www.aduana.gob.bo",
        "https://www.impuestos.gob.bo",
        "https://www.minedu.gob.bo"
    ]

    results = {}
    for url in sites:
        result = test_site(url)
        if result:
            results[url] = {
                'language_parts': result.get('language_parts', {}),
                'breadcrumbs': result.get('breadcrumbs', {})
            }

    # Resumen
    print("\n" + "=" * 80)
    print("RESUMEN DE RESULTADOS")
    print("=" * 80)

    print("\n| Sitio | Idioma Principal | Multiidioma | Breadcrumbs | Tipo BC |")
    print("|" + "-" * 78 + "|")

    for url, data in results.items():
        domain = url.split('//')[1].split('/')[0]
        main_lang = data['language_parts'].get('main_language', 'N/A')
        multilang = "Si" if data['language_parts'].get('has_multilingual_content') else "No"
        has_bc = "Si" if data['breadcrumbs'].get('has_breadcrumbs') else "No"
        bc_type = data['breadcrumbs'].get('breadcrumb_type', 'N/A') or 'N/A'

        print(f"| {domain[:25]:<25} | {main_lang:<16} | {multilang:<11} | {has_bc:<11} | {bc_type:<7} |")

    print("\n" + "=" * 80)
    print("[OK] VERIFICACION COMPLETADA")
    print("=" * 80)

    # Estadisticas
    total = len(results)
    with_breadcrumbs = sum(1 for d in results.values() if d['breadcrumbs'].get('has_breadcrumbs'))
    with_multilang = sum(1 for d in results.values() if d['language_parts'].get('has_multilingual_content'))

    print(f"\nEstadisticas ({total} sitios):")
    print(f"  - Con breadcrumbs: {with_breadcrumbs}/{total}")
    print(f"  - Con contenido multiidioma: {with_multilang}/{total}")


if __name__ == "__main__":
    run_all_tests()
