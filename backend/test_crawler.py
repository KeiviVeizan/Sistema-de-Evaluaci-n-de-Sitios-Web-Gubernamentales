"""
Script de prueba para el crawler GobBoCrawler.

Prueba el crawler sin necesidad de levantar la API completa.
"""

import json
import sys
import warnings
from pathlib import Path
import io

# Configurar encoding UTF-8 para Windows
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# Agregar el directorio app al path
sys.path.insert(0, str(Path(__file__).parent))

from app.crawler.html_crawler import GobBoCrawler

# Suprimir warnings de SSL
warnings.filterwarnings('ignore', message='Unverified HTTPS request')


def test_crawler(url: str):
    """
    Prueba el crawler con una URL específica.

    Args:
        url: URL del sitio web a crawlear
    """
    print(f"\n{'='*80}")
    print(f"PROBANDO CRAWLER CON: {url}")
    print(f"{'='*80}\n")

    try:
        # Crear crawler
        crawler = GobBoCrawler(timeout=30)

        # Ejecutar crawling
        print("Iniciando crawling...")
        result = crawler.crawl(url)

        print("\n✓ Crawling completado exitosamente\n")

        # Mostrar resumen
        print(f"{'='*80}")
        print("RESUMEN DEL CRAWLING")
        print(f"{'='*80}\n")

        print(f"URL: {result['url']}")
        print(f"URL Final: {result['final_url']}")
        print(f"Status Code: {result['http_status_code']}")
        print(f"Crawled At: {result['crawled_at']}\n")

        # Robots.txt
        print("--- ROBOTS.TXT ---")
        robots = result.get('robots_txt', {})
        print(f"  • Existe: {robots.get('exists')}")
        if robots.get('exists'):
            print(f"  • Accesible: {robots.get('accessible')}")
            print(f"  • Permite crawling: {robots.get('allows_crawling')}")
            print(f"  • Tiene sitemap: {robots.get('has_sitemap')}")
            if robots.get('sitemap_urls'):
                print(f"  • Sitemaps: {len(robots.get('sitemap_urls'))}")
        if robots.get('error'):
            print(f"  • Error: {robots.get('error')}")

        # Estructura
        print("\n--- ESTRUCTURA DEL DOCUMENTO ---")
        structure = result.get('structure', {})
        print(f"  • DOCTYPE HTML5: {structure.get('has_html5_doctype')}")
        print(f"  • Charset UTF-8: {structure.get('has_utf8_charset')}")
        print(f"  • Código obsoleto: {structure.get('has_obsolete_code')}")
        if structure.get('obsolete_elements'):
            print(f"  • Elementos obsoletos encontrados: {len(structure.get('obsolete_elements'))}")

        # Metadata
        print("\n--- METADATOS ---")
        metadata = result.get('metadata', {})
        print(f"  • Title: {metadata.get('title', 'N/A')[:80]}...")
        print(f"  • Lang: {metadata.get('lang', 'N/A')}")
        print(f"  • Description: {metadata.get('has_description')}")
        print(f"  • Viewport: {metadata.get('has_viewport')}")

        # Elementos semánticos
        print("\n--- ELEMENTOS SEMÁNTICOS ---")
        semantic = result.get('semantic_elements', {})
        summary = semantic.get('summary', {})
        print(f"  • Tipos usados: {summary.get('types_used', 0)}/7")
        print(f"  • Estructura básica completa: {summary.get('has_basic_structure')}")

        # Headings
        print("\n--- ENCABEZADOS ---")
        headings = result.get('headings', {})
        print(f"  • Total: {headings.get('total_count', 0)}")
        print(f"  • H1: {headings.get('h1_count', 0)}")
        print(f"  • H1 único: {headings.get('has_single_h1')}")
        print(f"  • Jerarquía válida: {headings.get('hierarchy_valid')}")

        # Imágenes
        print("\n--- IMÁGENES ---")
        images = result.get('images', {})
        print(f"  • Total: {images.get('total_count', 0)}")
        print(f"  • Con alt: {images.get('with_alt', 0)}")
        print(f"  • Sin alt: {images.get('without_alt', 0)}")
        print(f"  • Compliance alt: {images.get('alt_compliance_percentage', 0):.1f}%")

        # Enlaces
        print("\n--- ENLACES ---")
        links = result.get('links', {})
        print(f"  • Total: {links.get('total_count', 0)}")
        print(f"  • Enlaces vacíos (sin texto): {links.get('empty_links', {}).get('count', 0)}")
        print(f"  • Textos genéricos: {links.get('generic_text', {}).get('count', 0)}")
        print(f"  • Redes sociales: {links.get('social', {}).get('count', 0)}")
        print(f"  • Email: {links.get('email', {}).get('count', 0)}")
        print(f"  • Teléfono: {links.get('phone', {}).get('count', 0)}")
        print(f"  • Mensajería: {links.get('messaging', {}).get('count', 0)}")

        # Formularios
        print("\n--- FORMULARIOS ---")
        forms = result.get('forms', {})
        print(f"  • Total: {forms.get('total_forms', 0)}")
        print(f"  • Inputs totales: {forms.get('total_inputs', 0)}")
        print(f"  • Inputs con label: {forms.get('inputs_with_label', 0)}")
        print(f"  • Compliance labels: {forms.get('label_compliance_percentage', 0):.1f}%")

        # Media
        print("\n--- MULTIMEDIA ---")
        media = result.get('media', {})
        print(f"  • Audio: {media.get('audio', {}).get('count', 0)}")
        print(f"  • Video: {media.get('video', {}).get('count', 0)}")
        print(f"  • Con autoplay: {media.get('has_autoplay_media')}")

        # Recursos externos
        print("\n--- RECURSOS EXTERNOS ---")
        external = result.get('external_resources', {})
        print(f"  • iframes externos: {external.get('iframes', {}).get('count', 0)}")
        print(f"  • CDN externos: {external.get('cdn', {}).get('count', 0)}")
        print(f"  • Fuentes externas: {external.get('fonts', {}).get('count', 0)}")
        print(f"  • Trackers: {external.get('trackers', {}).get('count', 0)}")

        # Texto
        print("\n--- CORPUS TEXTUAL ---")
        corpus = result.get('text_corpus', {})
        print(f"  • 'Bolivia a tu servicio': {corpus.get('has_bolivia_service_text')}")
        print(f"  • Secciones para NLP: {corpus.get('total_sections', 0)}")

        # Guardar resultado completo en JSON
        output_file = Path(__file__).parent / "crawler_output.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)

        print(f"\n✓ Resultado completo guardado en: {output_file}")
        print(f"\n{'='*80}\n")

    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    # Probar con un sitio .gob.bo
    test_url = "https://www.migracion.gob.bo"

    if len(sys.argv) > 1:
        test_url = sys.argv[1]

    test_crawler(test_url)
