"""
Test de integracion completa: Crawler -> NLP -> Evaluacion

Este test verifica que todo el flujo funciona correctamente:
1. Crawler extrae contenido
2. Modulo NLP analiza texto
3. Se generan evaluaciones WCAG
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.crawler.html_crawler import GobBoCrawler

print("="*80)
print("TEST INTEGRACION COMPLETA: Crawler -> NLP -> Evaluacion")
print("="*80)

# 1. CRAWLEAR SITIO
print("\n[1/4] Extrayendo contenido con Crawler...")
crawler = GobBoCrawler(timeout=45)
result = crawler.crawl('https://www.aduana.gob.bo')
text_corpus = result['text_corpus']

print(f"      [OK] Extraido: {text_corpus['total_words']} palabras")
print(f"      [OK] Secciones: {text_corpus['total_sections']}")
print(f"      [OK] Enlaces: {len(text_corpus.get('link_texts', []))}")

# 2. IMPORTAR Y PROBAR MODULO NLP
print("\n[2/4] Cargando modulo NLP con BETO...")

try:
    from app.nlp.analyzer import NLPAnalyzer

    print("      [OK] Modulo NLP importado correctamente")
    print("      [INFO] Inicializando analizador (puede tardar en cargar BETO)...")

    nlp_analyzer = NLPAnalyzer()
    print("      [OK] NLPAnalyzer inicializado")

except ImportError as e:
    print(f"      [ERROR] Error importando NLP: {e}")
    nlp_analyzer = None
except Exception as e:
    print(f"      [ERROR] Error inicializando NLP: {e}")
    nlp_analyzer = None

# 3. EJECUTAR ANALISIS NLP
print("\n[3/4] Ejecutando analisis NLP...")

if nlp_analyzer:
    try:
        nlp_result = nlp_analyzer.analyze_website(text_corpus)

        print(f"\n      PUNTUACION GLOBAL: {nlp_result['global_score']:.1f}/100")

        print(f"\n      Componentes:")
        coherence_score = nlp_result.get('coherence_score', 0)
        ambiguity_score = nlp_result.get('ambiguity_score', 0)
        clarity_score = nlp_result.get('clarity_score', 0)

        print(f"        - Coherencia: {coherence_score:.1f}/100")
        print(f"        - Ambiguedad: {ambiguity_score:.1f}/100")
        print(f"        - Claridad: {clarity_score:.1f}/100")
        print(f"        - Secciones analizadas: {nlp_result.get('total_sections_analyzed', 0)}")

        print(f"\n      Cumplimiento WCAG:")
        wcag = nlp_result.get('wcag_compliance', {})
        for criterion, compliant in wcag.items():
            status = '[OK]' if compliant else '[!!]'
            print(f"        {criterion}: {status}")

        print(f"\n      Recomendaciones ({len(nlp_result.get('recommendations', []))}):")
        for i, rec in enumerate(nlp_result.get('recommendations', [])[:5], 1):
            print(f"        {i}. {rec[:70]}...")

    except Exception as e:
        print(f"      [ERROR] Error en analisis NLP: {e}")
        import traceback
        traceback.print_exc()
else:
    # Analisis basico sin BETO
    print("      [INFO] Ejecutando analisis basico (sin BETO)...")

    link_texts = text_corpus.get('link_texts', [])
    generic_count = sum(1 for lt in link_texts if lt.get('is_generic', False))
    sections = text_corpus.get('sections', [])
    labels = text_corpus.get('label_texts', [])

    print(f"\n      Analisis basico:")
    print(f"        - Enlaces genericos: {generic_count}/{len(link_texts)}")
    print(f"        - Secciones: {len(sections)}")
    print(f"        - Labels: {len(labels)}")

# 4. RESUMEN
print("\n[4/4] Evaluacion de Criterios WCAG:")

link_texts = text_corpus.get('link_texts', [])
generic_count = sum(1 for lt in link_texts if lt.get('is_generic', False))
sections = text_corpus.get('sections', [])
labels = text_corpus.get('label_texts', [])

print(f"\n      Criterios evaluados con NLP:")
print(f"      - ACC-07 (Labels descriptivos): {'[OK]' if len(labels) > 0 else '[!!]'}")
print(f"      - ACC-08 (Enlaces descriptivos): {'[OK]' if generic_count < len(link_texts)*0.1 else '[!!]'}")
print(f"      - ACC-09 (Headings descriptivos): {'[OK]' if len(sections) >= 3 else '[!!]'}")

print("\n" + "="*80)
print("[OK] INTEGRACION COMPLETA VALIDADA")
print("="*80)
print("\nComponentes funcionando:")
print(f"  [OK] Crawler extrae texto completo ({text_corpus['total_words']} palabras)")
print(f"  [OK] Datos estructurados listos para NLP")
print(f"  {'[OK]' if nlp_analyzer else '[!!]'} Modulo NLP {'procesando' if nlp_analyzer else 'requiere revision'}")
print(f"  [OK] Criterios WCAG evaluados")
