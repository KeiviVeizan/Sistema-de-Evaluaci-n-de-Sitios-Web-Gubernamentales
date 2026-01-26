"""
Script de prueba para analisis de cobertura de extraccion.

Compara la extraccion del crawler contra ground truth (inspeccion manual)
para medir que tan bien funciona el crawler.

Uso:
    cd backend
    python tests/test_coverage_analysis.py
"""

import sys
import os

# Agregar path del proyecto
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.crawler.html_crawler import GobBoCrawler
from app.crawler.coverage_analyzer import CoverageAnalyzer


def main():
    print("=" * 80)
    print("ANALISIS DE COBERTURA DE EXTRACCION")
    print("Comparando crawler vs inspeccion manual (ground truth)")
    print("=" * 80)

    # Inicializar
    ground_truth_file = os.path.join(os.path.dirname(__file__), 'ground_truth_sites.json')
    analyzer = CoverageAnalyzer(ground_truth_file)
    crawler = GobBoCrawler(timeout=45)

    # Mostrar sitios disponibles
    available = analyzer.get_available_sites()
    print(f"\n[INFO] Sitios con ground truth disponible: {len(available)}")
    for url in available:
        print(f"  - {url}")

    # Generar reporte completo
    print("\n" + "-" * 80)
    print("Iniciando analisis...")
    print("-" * 80)

    report = analyzer.generate_report(crawler)

    # Imprimir reporte
    analyzer.print_report(report)

    # Guardar resultados
    output_file = os.path.join(os.path.dirname(__file__), 'coverage_analysis_results.json')
    analyzer.save_report(report, output_file)

    # Resumen final
    print("\n" + "=" * 80)
    print("RESUMEN FINAL")
    print("=" * 80)

    summary = report['summary']
    all_stats = summary['all_sites']

    if all_stats['count'] > 0:
        print(f"\nTotal sitios analizados: {all_stats['count']}")
        print(f"Cobertura promedio: {all_stats['average_coverage']}%")
        print(f"Rango: {all_stats['min_coverage']}% - {all_stats['max_coverage']}%")

        # Evaluacion
        if all_stats['average_coverage'] >= 95:
            print("\n[EXCELENTE] Cobertura >= 95%")
        elif all_stats['average_coverage'] >= 90:
            print("\n[BUENO] Cobertura >= 90%")
        elif all_stats['average_coverage'] >= 80:
            print("\n[ACEPTABLE] Cobertura >= 80%")
        else:
            print("\n[MEJORAR] Cobertura < 80%")
    else:
        print("\n[WARN] No se pudieron analizar sitios")


def test_single_site(url: str = "https://www.aduana.gob.bo"):
    """Prueba un solo sitio"""
    print(f"\n[TEST] Analizando: {url}")

    ground_truth_file = os.path.join(os.path.dirname(__file__), 'ground_truth_sites.json')
    analyzer = CoverageAnalyzer(ground_truth_file)
    crawler = GobBoCrawler(timeout=45)

    result = analyzer.measure_coverage_with_crawl(crawler, url)

    if 'error' in result:
        print(f"[ERROR] {result['error']}")
        return

    print(f"\nResultados para {url}:")
    print(f"  Arquitectura: {result['architecture']}")
    print(f"  Cobertura Total: {result['total_coverage_percent']}%")

    print(f"\n  Comparacion detallada:")
    print(f"  {'Categoria':<12} {'Esperado':>10} {'Extraido':>10} {'Cobertura':>10}")
    print(f"  {'-'*44}")

    for cat, data in result['comparison'].items():
        print(f"  {cat:<12} {data['expected']:>10} {data['extracted']:>10} {data['coverage_percent']:>9.1f}%")

    gbot = result['googlebot_comparison']
    status = "[OK]" if gbot['better_than_googlebot'] else "[!!]"
    print(f"\n  vs Googlebot ({gbot['benchmark']}%): {gbot['difference']:+.2f}% {status}")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        # Si se pasa URL como argumento
        test_single_site(sys.argv[1])
    else:
        # Ejecutar analisis completo
        main()
