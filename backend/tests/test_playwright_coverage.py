"""
Test de Cobertura: Playwright vs HTML Estatico

Compara la extraccion con y sin JavaScript para medir
el beneficio real de usar Playwright en sitios .gob.bo

Uso:
    cd backend
    python tests/test_playwright_coverage.py
"""

import sys
import os

# Agregar path del proyecto
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.crawler.html_crawler import GobBoCrawler
from app.crawler.playwright_coverage_analyzer import PlaywrightCoverageAnalyzer


# Sitios de prueba
TEST_SITES = [
    "https://www.aduana.gob.bo",
    "https://www.impuestos.gob.bo",
    "https://www.minedu.gob.bo",
    "https://www.ruat.gob.bo",
    "https://www.oopp.gob.bo",
    "https://www.mintrabajo.gob.bo"
]


def main():
    print("=" * 80)
    print("ANALISIS DE COBERTURA: Playwright vs HTML Estatico")
    print("=" * 80)
    print("\nMetodologia:")
    print("  1. Extraer contenido SIN JavaScript (requests + BeautifulSoup)")
    print("  2. Extraer contenido CON JavaScript (Playwright)")
    print("  3. Comparar para medir beneficio de Playwright")
    print("=" * 80)

    # Inicializar
    analyzer = PlaywrightCoverageAnalyzer(timeout=30)
    crawler = GobBoCrawler(timeout=45)

    # Analizar todos los sitios
    report = analyzer.analyze_multiple_sites(TEST_SITES, crawler)

    # Imprimir reporte
    analyzer.print_report(report)

    # Guardar resultados
    output_file = os.path.join(os.path.dirname(__file__), 'playwright_coverage_analysis.json')
    analyzer.save_report(report, output_file)

    # Conclusion
    print("\n" + "=" * 80)
    print("CONCLUSION")
    print("=" * 80)

    summary = report['summary']
    all_stats = summary['all_sites']

    if all_stats['count'] > 0:
        print(f"\nTotal sitios analizados: {all_stats['count']}")
        print(f"Cobertura HTML estatico promedio: {all_stats['avg_static_coverage']}%")
        print(f"Mejora promedio con Playwright: +{all_stats['avg_playwright_improvement']}%")

        if all_stats['avg_static_coverage'] >= 90:
            print("\n[INFO] La mayoria de sitios .gob.bo son MPAs tradicionales.")
            print("       Playwright mejora la extraccion pero no es critico.")
        elif all_stats['avg_static_coverage'] >= 70:
            print("\n[INFO] Los sitios tienen contenido dinamico moderado.")
            print("       Playwright aporta mejoras significativas.")
        else:
            print("\n[INFO] Los sitios tienen mucho contenido dinamico.")
            print("       Playwright es ESENCIAL para extraccion completa.")
    else:
        print("\n[WARN] No se pudieron analizar sitios")


def test_single_site(url: str):
    """Prueba un solo sitio"""
    print(f"\n[TEST] Analizando: {url}")

    analyzer = PlaywrightCoverageAnalyzer(timeout=30)
    crawler = GobBoCrawler(timeout=45)

    result = analyzer.measure_playwright_benefit(url, crawler)

    if 'error' in result:
        print(f"[ERROR] {result['error']}")
        return

    print(f"\n{'=' * 60}")
    print(f"RESULTADOS: {url}")
    print(f"{'=' * 60}")

    print(f"\nArquitectura detectada: {result['architecture_type']}")
    print(f"Cobertura HTML estatico: {result['static_coverage_percent']}%")
    print(f"Mejora con Playwright: +{result['playwright_improvement_percent']}%")

    print(f"\nComparacion detallada:")
    print(f"{'Elemento':<15} {'Sin JS':>10} {'Con PW':>10} {'Mejora':>10}")
    print(f"{'-'*45}")

    for key in result['without_js']:
        static = result['without_js'][key]
        pw = result['with_playwright'][key]
        diff = pw - static
        diff_str = f"+{diff}" if diff > 0 else str(diff)
        print(f"{key:<15} {static:>10} {pw:>10} {diff_str:>10}")

    print(f"\n{result['interpretation']}")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        # Si se pasa URL como argumento
        test_single_site(sys.argv[1])
    else:
        # Ejecutar analisis completo
        main()
