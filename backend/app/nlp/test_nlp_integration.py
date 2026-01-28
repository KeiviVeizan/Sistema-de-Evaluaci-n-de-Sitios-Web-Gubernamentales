"""
Test de Integracion del Modulo NLP

Prueba el flujo completo:
1. Crawler extrae text_corpus
2. NLPAnalyzer procesa el contenido
3. Se generan scores y recomendaciones
"""
import sys
import os
import logging

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)


def test_nlp_con_datos_reales():
    """Test end-to-end con sitio real"""
    print("=" * 80)
    print("TEST DE INTEGRACION: Modulo NLP con BETO")
    print("=" * 80)

    # 1. Importar modulos
    print("\n[1] Importando modulos...")
    try:
        from app.crawler.html_crawler import GobBoCrawler
        from app.nlp.analyzer import NLPAnalyzer
        print("    OK - Modulos importados")
    except ImportError as e:
        print(f"    ERROR: {e}")
        return False

    # 2. Crawlear sitio
    url = "https://www.aduana.gob.bo"
    print(f"\n[2] Crawleando {url}...")
    crawler = GobBoCrawler(timeout=45)
    extracted = crawler.crawl(url)

    if 'error' in extracted:
        print(f"    ERROR: {extracted['error']}")
        return False

    text_corpus = extracted.get('text_corpus', {})
    print(f"    OK - text_corpus extraido")
    print(f"    - Secciones: {text_corpus.get('total_sections', 0)}")
    print(f"    - Links: {len(text_corpus.get('links', []))}")
    print(f"    - Labels: {len(text_corpus.get('labels', []))}")

    # 3. Inicializar NLPAnalyzer
    print("\n[3] Inicializando NLPAnalyzer...")
    try:
        analyzer = NLPAnalyzer()
        print("    OK - NLPAnalyzer inicializado")
    except Exception as e:
        print(f"    ERROR: {e}")
        return False

    # 4. Analizar contenido
    print("\n[4] Analizando contenido con NLP...")
    try:
        result = analyzer.analyze_website(text_corpus)
        print("    OK - Analisis completado")
    except Exception as e:
        print(f"    ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

    # 5. Mostrar resultados
    print("\n" + "=" * 80)
    print("RESULTADOS DEL ANALISIS NLP")
    print("=" * 80)

    print(f"\n{'Metrica':<25} {'Score':<15}")
    print("-" * 40)
    print(f"{'Score Global':<25} {result.get('global_score', 0):>6.1f}/100")
    print(f"{'Coherencia Semantica':<25} {result.get('coherence_score', 0):>6.1f}/100")
    print(f"{'Claridad Textos':<25} {result.get('ambiguity_score', 0):>6.1f}/100")
    print(f"{'Legibilidad (F.Huerta)':<25} {result.get('clarity_score', 0):>6.1f}/100")

    # WCAG Compliance
    print("\n" + "-" * 40)
    print("CUMPLIMIENTO WCAG:")
    wcag = result.get('wcag_compliance', {})
    for criterion, compliant in wcag.items():
        status = "CUMPLE" if compliant else "NO CUMPLE"
        print(f"  {criterion}: {status}")

    # Estadisticas
    print("\n" + "-" * 40)
    print("ESTADISTICAS:")
    print(f"  Secciones analizadas: {result.get('total_sections_analyzed', 0)}")
    print(f"  Textos analizados: {result.get('total_texts_analyzed', 0)}")

    # Recomendaciones (primeras 5)
    recs = result.get('recommendations', [])
    if recs:
        print("\n" + "-" * 40)
        print(f"RECOMENDACIONES (primeras 5 de {len(recs)}):")
        for i, rec in enumerate(recs[:5], 1):
            print(f"  {i}. {rec[:100]}...")

    print("\n" + "=" * 80)
    print("TEST COMPLETADO EXITOSAMENTE")
    print("=" * 80)

    return True


def test_nlp_con_mock():
    """Test rapido con datos mock (sin crawling)"""
    print("=" * 80)
    print("TEST RAPIDO: NLPAnalyzer con datos mock")
    print("=" * 80)

    from app.nlp.analyzer import NLPAnalyzer

    # Datos mock
    text_corpus = {
        'url': 'https://test.gob.bo',
        'sections': [
            {
                'heading': 'Servicios al Ciudadano',
                'heading_level': 2,
                'content': 'Ofrecemos diversos servicios para facilitar los tramites de los ciudadanos bolivianos.',
                'word_count': 10
            },
            {
                'heading': 'Tramites en Linea',
                'heading_level': 2,
                'content': 'Puede realizar sus tramites de forma digital sin necesidad de acudir a nuestras oficinas.',
                'word_count': 13
            }
        ],
        'links': [
            {'text': 'Ver mas', 'url': '/pagina'},
            {'text': 'Descargar formulario de solicitud', 'url': '/form.pdf'},
            {'text': 'Aqui', 'url': '/info'}
        ],
        'labels': [
            {'text': 'Nombre completo', 'for': 'nombre'},
            {'text': 'Fecha', 'for': 'fecha'}
        ]
    }

    print("\n[1] Inicializando NLPAnalyzer...")
    analyzer = NLPAnalyzer()

    print("\n[2] Analizando datos mock...")
    result = analyzer.analyze_website(text_corpus)

    print("\n" + "=" * 80)
    print("RESULTADOS:")
    print("=" * 80)
    print(f"Score Global: {result.get('global_score', 0):.1f}/100")
    print(f"Coherencia: {result.get('coherence_score', 0):.1f}/100")
    print(f"Claridad Textos: {result.get('ambiguity_score', 0):.1f}/100")
    print(f"Legibilidad: {result.get('clarity_score', 0):.1f}/100")

    # Verificar deteccion de ambiguedades
    details = result.get('details', {}).get('ambiguity', {})
    problematic = details.get('problematic_count', 0)
    print(f"\nTextos problematicos detectados: {problematic}")

    if problematic > 0:
        print("  - 'Ver mas' deberia detectarse como generico")
        print("  - 'Aqui' deberia detectarse como generico")
        print("  - 'Fecha' deberia detectarse como ambiguo")

    print("\n" + "=" * 80)
    return True


if __name__ == "__main__":
    print("\n")
    print("#" * 80)
    print("#" + " MODULO NLP - TEST DE INTEGRACION ".center(78) + "#")
    print("#" * 80)

    # Test rapido primero
    print("\n--- TEST RAPIDO (sin crawling) ---")
    test_nlp_con_mock()

    # Test con datos reales
    print("\n\n--- TEST COMPLETO (con crawling real) ---")
    try:
        test_nlp_con_datos_reales()
    except Exception as e:
        print(f"Error en test real: {e}")
        import traceback
        traceback.print_exc()
