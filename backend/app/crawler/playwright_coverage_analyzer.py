"""
Analizador de Cobertura Playwright vs HTML Estatico

Mide el beneficio de usar Playwright comparando la extraccion
con y sin JavaScript. Esta metodologia es mas objetiva que
usar ground truth manual.

Autor: Sistema GOB.BO Evaluator
Fecha: 2025-01-25
"""

import json
import requests
from typing import Dict, List, Any
from bs4 import BeautifulSoup
from urllib3.exceptions import InsecureRequestWarning
import warnings

# Suprimir warnings de SSL
warnings.filterwarnings('ignore', category=InsecureRequestWarning)


class PlaywrightCoverageAnalyzer:
    """
    Mide cobertura comparando extraccion con y sin JavaScript.

    Metodologia:
    1. Extraccion SIN JavaScript (requests + BeautifulSoup)
    2. Extraccion CON JavaScript (Playwright + BeautifulSoup)
    3. Comparar resultados para medir beneficio de Playwright
    """

    # Pesos para calculo de cobertura ponderada
    WEIGHTS = {
        'links': 0.25,
        'text_words': 0.30,
        'headings': 0.20,
        'images': 0.15,
        'forms': 0.10
    }

    # Benchmarks de Googlebot
    GOOGLEBOT_BENCHMARKS = {
        'MPA': 97.0,
        'SPA': 85.0
    }

    def __init__(self, timeout: int = 30):
        """
        Inicializa el analizador.

        Args:
            timeout: Timeout en segundos para requests
        """
        self.timeout = timeout
        self.session = requests.Session()
        self.session.verify = False
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })

    def _extract_static(self, url: str) -> Dict[str, int]:
        """
        Extrae contenido SIN JavaScript (solo HTML estatico).

        Args:
            url: URL a analizar

        Returns:
            dict: Conteos de elementos extraidos
        """
        try:
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
            static_html = response.text
        except Exception as e:
            print(f"  [WARN] Error obteniendo HTML estatico: {e}")
            return {
                'links': 0,
                'images': 0,
                'headings': 0,
                'forms': 0,
                'text_words': 0,
                'buttons': 0
            }

        soup = BeautifulSoup(static_html, 'html.parser')

        # Eliminar scripts y estilos para contar texto
        for element in soup(['script', 'style', 'noscript']):
            element.decompose()

        # Contar elementos
        links = len(soup.find_all('a', href=True))
        images = len(soup.find_all('img'))
        headings = len(soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6']))
        forms = len(soup.find_all('form'))

        # Contar palabras de texto visible
        body = soup.find('body')
        text = body.get_text(separator=' ', strip=True) if body else ''
        text_words = len(text.split())

        # Contar botones
        buttons = len(soup.find_all('button'))
        buttons += len(soup.find_all('input', type=['submit', 'button', 'reset']))

        return {
            'links': links,
            'images': images,
            'headings': headings,
            'forms': forms,
            'text_words': text_words,
            'buttons': buttons
        }

    def _extract_with_playwright(self, crawler_result: Dict[str, Any]) -> Dict[str, int]:
        """
        Extrae conteos del resultado de Playwright.

        Args:
            crawler_result: Resultado del GobBoCrawler

        Returns:
            dict: Conteos de elementos extraidos
        """
        text_corpus = crawler_result.get('text_corpus', {})

        # Links
        links_data = crawler_result.get('links', {})
        links = links_data.get('total_count', 0)
        if links == 0:
            links = len(links_data.get('all_links', []))

        # Images
        images_data = crawler_result.get('images', {})
        images = images_data.get('total_count', 0)
        if images == 0:
            images = len(images_data.get('images', []))

        # Headings
        headings_data = crawler_result.get('headings', {})
        headings = headings_data.get('total_count', 0)
        if headings == 0:
            headings = len(headings_data.get('headings', []))

        # Forms
        forms_data = crawler_result.get('forms', {})
        forms = forms_data.get('total_count', 0)
        if forms == 0:
            forms = len(forms_data.get('forms', []))

        # Text words
        text_words = text_corpus.get('total_words', 0)

        # Buttons
        buttons = text_corpus.get('total_buttons', 0)
        if buttons == 0:
            button_texts = text_corpus.get('button_texts', [])
            buttons = len(button_texts) if isinstance(button_texts, list) else 0

        return {
            'links': links,
            'images': images,
            'headings': headings,
            'forms': forms,
            'text_words': text_words,
            'buttons': buttons
        }

    def measure_playwright_benefit(self, url: str, crawler) -> Dict[str, Any]:
        """
        Compara lo que se extrae con Playwright vs sin JavaScript.

        Args:
            url: URL a analizar
            crawler: Instancia de GobBoCrawler

        Returns:
            dict: Analisis completo con cobertura y beneficio
        """
        print(f"  [1/3] Extrayendo HTML estatico...")
        without_js = self._extract_static(url)

        print(f"  [2/3] Extrayendo con Playwright...")
        crawler_result = crawler.crawl(url)

        if 'error' in crawler_result:
            return {
                'url': url,
                'error': crawler_result['error']
            }

        with_playwright = self._extract_with_playwright(crawler_result)

        print(f"  [3/3] Calculando metricas...")

        # Calcular cobertura por categoria
        # La cobertura mide cuanto del contenido de Playwright estaba en HTML estatico
        coverage_by_category = {}
        playwright_benefit = {}

        for key in without_js:
            static_count = without_js[key]
            pw_count = with_playwright[key]

            # Cobertura: que porcentaje del contenido Playwright ya estaba en estatico
            if pw_count > 0:
                # Si Playwright tiene mas, el estatico cubre menos del 100%
                coverage = min((static_count / pw_count) * 100, 100.0)
            else:
                coverage = 100.0 if static_count == 0 else 0.0

            coverage_by_category[key] = round(coverage, 2)

            # Beneficio: cuanto mas extrae Playwright
            playwright_benefit[f'additional_{key}'] = max(0, pw_count - static_count)

        # Promedio ponderado de cobertura
        total_coverage = 0.0
        total_weight = 0.0

        for key, weight in self.WEIGHTS.items():
            if key in coverage_by_category:
                total_coverage += coverage_by_category[key] * weight
                total_weight += weight

        if total_weight > 0:
            total_coverage = total_coverage / total_weight

        total_coverage = round(total_coverage, 2)

        # Detectar tipo de arquitectura
        # Si HTML estatico tiene <50% del contenido de Playwright, es SPA
        if with_playwright['links'] + with_playwright['text_words'] > 0:
            static_ratio = (
                without_js['links'] + without_js['text_words']
            ) / (
                with_playwright['links'] + with_playwright['text_words']
            )
        else:
            static_ratio = 1.0

        architecture_type = 'SPA' if static_ratio < 0.5 else 'MPA'

        # Calcular beneficio total de Playwright
        total_additional = sum(
            v for k, v in playwright_benefit.items()
            if k in ['additional_links', 'additional_text_words', 'additional_headings']
        )

        # Porcentaje de mejora que aporta Playwright
        playwright_improvement = 100 - total_coverage

        return {
            'url': url,
            'architecture_type': architecture_type,
            'without_js': without_js,
            'with_playwright': with_playwright,
            'coverage_by_category': coverage_by_category,
            'static_coverage_percent': total_coverage,
            'playwright_improvement_percent': round(playwright_improvement, 2),
            'playwright_benefit': playwright_benefit,
            'total_additional_elements': total_additional,
            'interpretation': self._interpret_results(
                architecture_type,
                total_coverage,
                playwright_improvement
            )
        }

    def _interpret_results(self, arch: str, static_cov: float, pw_improvement: float) -> str:
        """Genera interpretacion de resultados"""
        if arch == 'MPA':
            if static_cov >= 95:
                return f"MPA tradicional. HTML estatico contiene {static_cov:.1f}% del contenido. Playwright aporta poco beneficio adicional ({pw_improvement:.1f}%)."
            elif static_cov >= 80:
                return f"MPA con contenido dinamico. HTML estatico tiene {static_cov:.1f}% del contenido. Playwright mejora la extraccion en {pw_improvement:.1f}%."
            else:
                return f"MPA con mucho contenido dinamico. Playwright es importante, mejora {pw_improvement:.1f}%."
        else:  # SPA
            if static_cov >= 50:
                return f"SPA con SSR parcial. HTML estatico tiene {static_cov:.1f}% del contenido. Playwright captura el resto ({pw_improvement:.1f}%)."
            else:
                return f"SPA pura. Solo {static_cov:.1f}% en HTML estatico. Playwright es ESENCIAL, aporta {pw_improvement:.1f}% del contenido."

    def analyze_multiple_sites(self, urls: List[str], crawler) -> Dict[str, Any]:
        """
        Analiza multiples sitios y genera estadisticas agregadas.

        Args:
            urls: Lista de URLs a analizar
            crawler: Instancia de GobBoCrawler

        Returns:
            dict: Resultados y estadisticas agregadas
        """
        results = []
        errors = []

        for url in urls:
            print(f"\n[SITIO] {url}")
            result = self.measure_playwright_benefit(url, crawler)

            if 'error' in result:
                errors.append({'url': url, 'error': result['error']})
                print(f"  [ERROR] {result['error']}")
            else:
                results.append(result)
                print(f"  Arquitectura: {result['architecture_type']}")
                print(f"  Cobertura estatica: {result['static_coverage_percent']}%")
                print(f"  Mejora Playwright: +{result['playwright_improvement_percent']}%")

        # Estadisticas agregadas
        mpas = [r for r in results if r['architecture_type'] == 'MPA']
        spas = [r for r in results if r['architecture_type'] == 'SPA']

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
            # Para MPAs, comparamos cuanto contenido capturamos vs Googlebot
            # Nuestro crawler con Playwright deberia acercarse al 97% de Googlebot
            avg_static = summary['mpas']['avg_static_coverage']
            avg_pw = 100  # Con Playwright capturamos todo lo que cargamos
            googlebot_comparison['mpas'] = {
                'static_only': avg_static,
                'with_playwright': avg_pw,
                'googlebot_benchmark': self.GOOGLEBOT_BENCHMARKS['MPA'],
                'vs_googlebot': round(avg_pw - self.GOOGLEBOT_BENCHMARKS['MPA'], 2)
            }

        if spas:
            avg_static = summary['spas']['avg_static_coverage']
            avg_pw = 100
            googlebot_comparison['spas'] = {
                'static_only': avg_static,
                'with_playwright': avg_pw,
                'googlebot_benchmark': self.GOOGLEBOT_BENCHMARKS['SPA'],
                'vs_googlebot': round(avg_pw - self.GOOGLEBOT_BENCHMARKS['SPA'], 2)
            }

        return {
            'methodology': 'Comparison: Playwright vs Static HTML',
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
                'avg_static_coverage': None,
                'avg_playwright_improvement': None,
                'min_static_coverage': None,
                'max_static_coverage': None
            }

        static_coverages = [r['static_coverage_percent'] for r in results]
        pw_improvements = [r['playwright_improvement_percent'] for r in results]

        return {
            'count': len(results),
            'avg_static_coverage': round(sum(static_coverages) / len(static_coverages), 2),
            'avg_playwright_improvement': round(sum(pw_improvements) / len(pw_improvements), 2),
            'min_static_coverage': round(min(static_coverages), 2),
            'max_static_coverage': round(max(static_coverages), 2)
        }

    def print_report(self, report: Dict[str, Any]) -> None:
        """Imprime reporte formateado en consola"""
        print("\n" + "=" * 80)
        print("ANALISIS DE COBERTURA: Playwright vs HTML Estatico")
        print("=" * 80)

        for result in report['results']:
            print(f"\n[SITIO] {result['url']}")
            print(f"   Arquitectura: {result['architecture_type']}")
            print(f"   Cobertura HTML estatico: {result['static_coverage_percent']}%")
            print(f"   Mejora con Playwright: +{result['playwright_improvement_percent']}%")
            print(f"\n   Comparacion por categoria:")
            print(f"   {'Categoria':<12} {'Estatico':>10} {'Playwright':>12} {'Diferencia':>12}")
            print(f"   {'-'*48}")

            for key in result['without_js']:
                static = result['without_js'][key]
                pw = result['with_playwright'][key]
                diff = pw - static
                diff_str = f"+{diff}" if diff > 0 else str(diff)
                print(f"   {key:<12} {static:>10} {pw:>12} {diff_str:>12}")

            print(f"\n   {result['interpretation']}")

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
            print(f"\n[MPA] Multi-Page Applications ({stats['count']} sitios):")
            print(f"   Cobertura estatica promedio: {stats['avg_static_coverage']}%")
            print(f"   Mejora Playwright promedio: +{stats['avg_playwright_improvement']}%")
            print(f"   Rango cobertura: {stats['min_static_coverage']}% - {stats['max_static_coverage']}%")

        if summary['spas']['count'] > 0:
            stats = summary['spas']
            print(f"\n[SPA] Single-Page Applications ({stats['count']} sitios):")
            print(f"   Cobertura estatica promedio: {stats['avg_static_coverage']}%")
            print(f"   Mejora Playwright promedio: +{stats['avg_playwright_improvement']}%")
            print(f"   Rango cobertura: {stats['min_static_coverage']}% - {stats['max_static_coverage']}%")

        # Comparacion con Googlebot
        gbot = report.get('googlebot_comparison', {})
        if gbot:
            print("\n" + "=" * 80)
            print("COMPARACION CON GOOGLEBOT")
            print("=" * 80)

            if 'mpas' in gbot:
                comp = gbot['mpas']
                status = "[OK]" if comp['vs_googlebot'] >= -2 else "[!!]"
                print(f"\nMPAs:")
                print(f"  Solo HTML estatico:  {comp['static_only']}%")
                print(f"  Con Playwright:      ~{comp['with_playwright']}%")
                print(f"  Googlebot benchmark: {comp['googlebot_benchmark']}%")
                print(f"  vs Googlebot:        {comp['vs_googlebot']:+.2f}% {status}")

            if 'spas' in gbot:
                comp = gbot['spas']
                status = "[OK]" if comp['vs_googlebot'] >= 0 else "[!!]"
                print(f"\nSPAs:")
                print(f"  Solo HTML estatico:  {comp['static_only']}%")
                print(f"  Con Playwright:      ~{comp['with_playwright']}%")
                print(f"  Googlebot benchmark: {comp['googlebot_benchmark']}%")
                print(f"  vs Googlebot:        {comp['vs_googlebot']:+.2f}% {status}")

    def save_report(self, report: Dict[str, Any], output_file: str = 'playwright_coverage_analysis.json') -> None:
        """Guarda reporte en archivo JSON"""
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        print(f"\n[OK] Resultados guardados en: {output_file}")
