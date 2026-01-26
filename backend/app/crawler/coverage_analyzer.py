"""
Analizador de Cobertura de Extraccion

Mide cuanto del contenido visible extrae el crawler comparando
contra inspecciones manuales (ground truth).

Autor: Sistema GOB.BO Evaluator
Fecha: 2025-01-25
"""

import json
import os
from typing import Dict, List, Any
from dataclasses import dataclass


@dataclass
class CoverageResult:
    """Resultado de analisis de cobertura para una categoria"""
    expected: int
    extracted: int
    missing: int
    coverage_percent: float


class CoverageAnalyzer:
    """Analiza cobertura de extraccion comparando con ground truth"""

    # Pesos para calculo de cobertura total ponderada
    DEFAULT_WEIGHTS = {
        'links': 0.25,
        'text_words': 0.30,
        'sections': 0.20,
        'images': 0.10,
        'forms': 0.10,
        'buttons': 0.03,
        'labels': 0.02
    }

    # Benchmarks de Googlebot (basados en estudios)
    GOOGLEBOT_BENCHMARKS = {
        'MPA': 97.0,
        'SPA': 85.0
    }

    def __init__(self, ground_truth_file: str = None):
        """
        Inicializa el analizador de cobertura.

        Args:
            ground_truth_file: Ruta al archivo JSON con ground truth.
                              Si no se especifica, busca en tests/ground_truth_sites.json
        """
        if ground_truth_file is None:
            # Buscar archivo por defecto
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            ground_truth_file = os.path.join(base_dir, 'tests', 'ground_truth_sites.json')

        self.ground_truth_file = ground_truth_file
        self.ground_truth: Dict[str, Dict] = {}

        self._load_ground_truth()

    def _load_ground_truth(self) -> None:
        """Carga datos de ground truth desde archivo JSON"""
        try:
            with open(self.ground_truth_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.ground_truth = {
                    site['url']: site for site in data.get('sites', [])
                }
        except FileNotFoundError:
            print(f"[WARN] Archivo ground truth no encontrado: {self.ground_truth_file}")
            self.ground_truth = {}
        except json.JSONDecodeError as e:
            print(f"[ERROR] Error parseando ground truth: {e}")
            self.ground_truth = {}

    def get_available_sites(self) -> List[str]:
        """Retorna lista de URLs con ground truth disponible"""
        return list(self.ground_truth.keys())

    def has_ground_truth(self, url: str) -> bool:
        """Verifica si hay ground truth para una URL"""
        return url in self.ground_truth

    def _extract_counts_from_result(self, result: Dict[str, Any]) -> Dict[str, int]:
        """
        Extrae conteos de elementos desde resultado del crawler.

        Args:
            result: Resultado completo del crawler

        Returns:
            dict: Conteos por categoria
        """
        text_corpus = result.get('text_corpus', {})

        # Contar links - usar total_count o contar all_links
        links_data = result.get('links', {})
        if isinstance(links_data, dict):
            links_count = links_data.get('total_count', 0)
            if links_count == 0:
                links_count = len(links_data.get('all_links', []))
        elif isinstance(links_data, list):
            links_count = len(links_data)
        else:
            links_count = 0

        # Contar imagenes - usar total_count o contar images
        images_data = result.get('images', {})
        if isinstance(images_data, dict):
            images_count = images_data.get('total_count', 0)
            if images_count == 0:
                images_count = len(images_data.get('images', []))
        elif isinstance(images_data, list):
            images_count = len(images_data)
        else:
            images_count = 0

        # Contar formularios - usar total_count o contar forms
        forms_data = result.get('forms', {})
        if isinstance(forms_data, dict):
            forms_count = forms_data.get('total_count', 0)
            if forms_count == 0:
                forms_count = len(forms_data.get('forms', []))
        elif isinstance(forms_data, list):
            forms_count = len(forms_data)
        else:
            forms_count = 0

        # Contar secciones (headings con contenido)
        sections_count = text_corpus.get('total_sections', 0)
        if sections_count == 0:
            # Fallback a headings
            headings_data = result.get('headings', {})
            if isinstance(headings_data, dict):
                sections_count = headings_data.get('total_count', 0)
                if sections_count == 0:
                    sections_count = len(headings_data.get('headings', []))

        # Contar botones
        buttons = text_corpus.get('button_texts', [])
        buttons_count = len(buttons) if isinstance(buttons, list) else text_corpus.get('total_buttons', 0)

        # Contar labels
        labels = text_corpus.get('label_texts', [])
        labels_count = len(labels) if isinstance(labels, list) else text_corpus.get('total_labels', 0)

        # Contar palabras
        text_words = text_corpus.get('total_words', 0)

        return {
            'links': links_count,
            'images': images_count,
            'forms': forms_count,
            'sections': sections_count,
            'buttons': buttons_count,
            'labels': labels_count,
            'text_words': text_words
        }

    def measure_coverage(self, crawler_result: Dict[str, Any], url: str = None) -> Dict[str, Any]:
        """
        Mide cobertura comparando extraccion vs ground truth.

        Args:
            crawler_result: Resultado del crawler para la URL
            url: URL analizada (opcional, se extrae del resultado si no se proporciona)

        Returns:
            dict: Analisis de cobertura completo
        """
        if url is None:
            url = crawler_result.get('url', '')

        if url not in self.ground_truth:
            return {
                'error': f'No hay ground truth disponible para {url}',
                'suggestion': 'Agregar inspeccion manual a ground_truth_sites.json',
                'available_sites': self.get_available_sites()
            }

        # Ground truth (inspeccion manual)
        gt_site = self.ground_truth[url]
        gt = gt_site['manual_inspection']
        architecture = gt_site.get('architecture', 'MPA')

        # Extraccion del crawler
        extracted = self._extract_counts_from_result(crawler_result)

        # Calcular cobertura por categoria
        coverage = {}
        comparison = {}

        for key in gt:
            gt_value = gt[key]
            extracted_value = extracted.get(key, 0)

            if gt_value > 0:
                cov_percent = round(min(extracted_value / gt_value * 100, 100), 2)
            else:
                cov_percent = 100.0 if extracted_value == 0 else 100.0

            coverage[key] = cov_percent
            comparison[key] = {
                'expected': gt_value,
                'extracted': extracted_value,
                'missing': max(0, gt_value - extracted_value),
                'coverage_percent': cov_percent
            }

        # Promedio ponderado
        total_coverage = 0.0
        total_weight = 0.0

        for key, weight in self.DEFAULT_WEIGHTS.items():
            if key in coverage:
                total_coverage += coverage[key] * weight
                total_weight += weight

        if total_weight > 0:
            total_coverage = total_coverage / total_weight * 100 / 100

        total_coverage = round(total_coverage, 2)

        # Comparacion con Googlebot
        googlebot_benchmark = self.GOOGLEBOT_BENCHMARKS.get(architecture, 95.0)
        diff_vs_googlebot = round(total_coverage - googlebot_benchmark, 2)

        return {
            'url': url,
            'architecture': architecture,
            'total_coverage_percent': total_coverage,
            'coverage_by_category': coverage,
            'ground_truth': gt,
            'extracted': extracted,
            'comparison': comparison,
            'googlebot_comparison': {
                'benchmark': googlebot_benchmark,
                'your_crawler': total_coverage,
                'difference': diff_vs_googlebot,
                'better_than_googlebot': diff_vs_googlebot >= 0
            },
            'inspection_date': gt_site.get('inspection_date', 'unknown'),
            'notes': gt_site.get('notes', '')
        }

    def measure_coverage_with_crawl(self, crawler, url: str) -> Dict[str, Any]:
        """
        Crawlea una URL y mide su cobertura.

        Args:
            crawler: Instancia de GobBoCrawler
            url: URL a analizar

        Returns:
            dict: Analisis de cobertura completo
        """
        if url not in self.ground_truth:
            return {
                'error': f'No hay ground truth disponible para {url}',
                'suggestion': 'Agregar inspeccion manual a ground_truth_sites.json',
                'available_sites': self.get_available_sites()
            }

        # Crawlear
        result = crawler.crawl(url)

        if 'error' in result:
            return {
                'error': f'Error al crawlear: {result["error"]}',
                'url': url
            }

        return self.measure_coverage(result, url)

    def generate_report(self, crawler, urls: List[str] = None) -> Dict[str, Any]:
        """
        Genera reporte de cobertura para multiples sitios.

        Args:
            crawler: Instancia de GobBoCrawler
            urls: Lista de URLs a analizar. Si es None, usa todas las del ground truth

        Returns:
            dict: Reporte completo con estadisticas agregadas
        """
        if urls is None:
            urls = self.get_available_sites()

        results = []
        errors = []

        for url in urls:
            print(f"\n[INFO] Analizando: {url}")
            coverage = self.measure_coverage_with_crawl(crawler, url)

            if 'error' in coverage:
                errors.append({'url': url, 'error': coverage['error']})
                print(f"  [ERROR] {coverage['error']}")
            else:
                results.append(coverage)
                print(f"  Arquitectura: {coverage['architecture']}")
                print(f"  Cobertura Total: {coverage['total_coverage_percent']}%")

        # Estadisticas agregadas
        mpas = [r for r in results if r['architecture'] == 'MPA']
        spas = [r for r in results if r['architecture'] == 'SPA']

        summary = {
            'total_sites': len(urls),
            'successful': len(results),
            'failed': len(errors),
            'mpas': self._calculate_stats(mpas),
            'spas': self._calculate_stats(spas),
            'all_sites': self._calculate_stats(results)
        }

        # Comparacion con Googlebot
        googlebot_comparison = {}

        if mpas:
            avg_mpa = summary['mpas']['average_coverage']
            googlebot_comparison['mpas'] = {
                'your_crawler': avg_mpa,
                'googlebot': self.GOOGLEBOT_BENCHMARKS['MPA'],
                'difference': round(avg_mpa - self.GOOGLEBOT_BENCHMARKS['MPA'], 2),
                'better': avg_mpa >= self.GOOGLEBOT_BENCHMARKS['MPA']
            }

        if spas:
            avg_spa = summary['spas']['average_coverage']
            googlebot_comparison['spas'] = {
                'your_crawler': avg_spa,
                'googlebot': self.GOOGLEBOT_BENCHMARKS['SPA'],
                'difference': round(avg_spa - self.GOOGLEBOT_BENCHMARKS['SPA'], 2),
                'better': avg_spa >= self.GOOGLEBOT_BENCHMARKS['SPA']
            }

        return {
            'results': results,
            'errors': errors,
            'summary': summary,
            'googlebot_comparison': googlebot_comparison
        }

    def _calculate_stats(self, results: List[Dict]) -> Dict[str, Any]:
        """Calcula estadisticas para un grupo de resultados"""
        if not results:
            return {
                'count': 0,
                'average_coverage': None,
                'min_coverage': None,
                'max_coverage': None
            }

        coverages = [r['total_coverage_percent'] for r in results]

        return {
            'count': len(results),
            'average_coverage': round(sum(coverages) / len(coverages), 2),
            'min_coverage': round(min(coverages), 2),
            'max_coverage': round(max(coverages), 2)
        }

    def print_report(self, report: Dict[str, Any]) -> None:
        """Imprime reporte formateado en consola"""
        print("\n" + "=" * 80)
        print("ANALISIS DE COBERTURA DE EXTRACCION")
        print("=" * 80)

        for result in report['results']:
            print(f"\n[SITIO] {result['url']}")
            print(f"   Arquitectura: {result['architecture']}")
            print(f"   Cobertura Total: {result['total_coverage_percent']}%")
            print(f"\n   Detalles por categoria:")

            for cat, data in result['comparison'].items():
                print(f"   - {cat:12s}: {data['coverage_percent']:5.1f}% ({data['extracted']}/{data['expected']})")

        if report['errors']:
            print(f"\n[ERRORES] {len(report['errors'])} sitios fallaron:")
            for err in report['errors']:
                print(f"   - {err['url']}: {err['error']}")

        # Estadisticas agregadas
        summary = report['summary']
        print("\n" + "=" * 80)
        print("ESTADISTICAS AGREGADAS")
        print("=" * 80)

        if summary['mpas']['count'] > 0:
            stats = summary['mpas']
            print(f"\n[MPA] MPAs ({stats['count']} sitios):")
            print(f"   Cobertura promedio: {stats['average_coverage']}%")
            print(f"   Rango: {stats['min_coverage']}% - {stats['max_coverage']}%")

        if summary['spas']['count'] > 0:
            stats = summary['spas']
            print(f"\n[SPA] SPAs ({stats['count']} sitios):")
            print(f"   Cobertura promedio: {stats['average_coverage']}%")
            print(f"   Rango: {stats['min_coverage']}% - {stats['max_coverage']}%")

        # Comparacion con Googlebot
        gbot = report.get('googlebot_comparison', {})
        if gbot:
            print("\n" + "=" * 80)
            print("COMPARACION CON GOOGLEBOT")
            print("=" * 80)

            if 'mpas' in gbot:
                comp = gbot['mpas']
                status = "[OK]" if comp['better'] else "[!!]"
                print(f"\nMPAs:")
                print(f"  Tu crawler:   {comp['your_crawler']}%")
                print(f"  Googlebot:    {comp['googlebot']}%")
                print(f"  Diferencia:   {comp['difference']:+.2f}% {status}")

            if 'spas' in gbot:
                comp = gbot['spas']
                status = "[OK]" if comp['better'] else "[!!]"
                print(f"\nSPAs:")
                print(f"  Tu crawler:   {comp['your_crawler']}%")
                print(f"  Googlebot:    {comp['googlebot']}%")
                print(f"  Diferencia:   {comp['difference']:+.2f}% {status}")

    def save_report(self, report: Dict[str, Any], output_file: str = 'coverage_analysis_results.json') -> None:
        """Guarda reporte en archivo JSON"""
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        print(f"\n[OK] Resultados guardados en: {output_file}")
