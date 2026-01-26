"""
Verificacion profunda de extraccion de datos del crawler.

Analiza:
1. Links con estructura anidada (iconos, elementos <p>)
2. Buttons en sitios con formularios
3. Labels en sitios con formularios
"""

import json
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.crawler.html_crawler import GobBoCrawler


def test_link_extraction_aduana():
    """Verifica extraccion de links en aduana.gob.bo"""
    print("=" * 80)
    print("TEST 1: EXTRACCION DE LINKS EN ADUANA.GOB.BO")
    print("=" * 80)

    crawler = GobBoCrawler(timeout=30)
    result = crawler.crawl("https://www.aduana.gob.bo")

    if 'error' in result:
        print(f"[ERROR] {result['error']}")
        return

    text_corpus = result.get('text_corpus', {})
    link_texts = text_corpus.get('link_texts', [])

    print(f"\n[INFO] Total links extraidos: {len(link_texts)}")

    # Filtrar links que contengan "leer" o "ver"
    action_links = [l for l in link_texts if any(w in l['text'].lower() for w in ['leer', 'ver mas', 'ver más'])]

    print(f"\n[INFO] Links con 'leer/ver': {len(action_links)}")
    print("-" * 80)

    for i, link in enumerate(action_links[:10], 1):
        text = link['text']
        print(f"\n{i}. Texto: '{text}'")
        print(f"   URL: {link['url']}")
        print(f"   Longitud: {link.get('length', len(text))} caracteres")

        # Verificar caracteres no-ASCII
        non_ascii = [c for c in text if ord(c) > 127]
        if non_ascii:
            print(f"   [WARN] Caracteres no-ASCII: {[hex(ord(c)) for c in non_ascii]}")
        else:
            print(f"   [OK] Solo caracteres ASCII")

        # Verificar espacios multiples
        if '  ' in text:
            print(f"   [WARN] Tiene espacios multiples")

    # Mostrar algunos ejemplos genericos detectados
    print("\n" + "-" * 80)
    print("LINKS GENERICOS DETECTADOS:")
    print("-" * 80)

    generic = [l for l in link_texts if l.get('is_generic', False)]
    print(f"Total genericos: {len(generic)}")

    for link in generic[:5]:
        print(f"  - '{link['text']}' -> {link['url'][:50]}")


def test_forms_site_impuestos():
    """Verifica extraccion en impuestos.gob.bo (sitio con formularios)"""
    print("\n\n" + "=" * 80)
    print("TEST 2: EXTRACCION EN IMPUESTOS.GOB.BO")
    print("=" * 80)

    crawler = GobBoCrawler(timeout=45)

    try:
        result = crawler.crawl("https://www.impuestos.gob.bo")

        if 'error' in result:
            print(f"[ERROR] {result['error']}")
            return

        text_corpus = result.get('text_corpus', {})
        forms_data = result.get('forms', {})

        # Labels
        print("\n" + "-" * 80)
        print("LABELS EXTRAIDOS:")
        print("-" * 80)

        label_texts = text_corpus.get('label_texts', [])
        print(f"Total en text_corpus['label_texts']: {len(label_texts)}")

        if label_texts:
            for i, label in enumerate(label_texts[:5], 1):
                print(f"  {i}. '{label}'")

        # Forms data (mas completo)
        print(f"\nTotal en forms['forms']: {forms_data.get('total_forms', 0)}")
        print(f"Total inputs: {forms_data.get('total_inputs', 0)}")

        if forms_data.get('forms'):
            for form in forms_data['forms'][:2]:
                print(f"\n  Form action: {form.get('action', 'N/A')}")
                for inp in form.get('inputs', [])[:3]:
                    print(f"    - Input: {inp.get('name')} (type={inp.get('type')})")
                    print(f"      Label: '{inp.get('label_text', 'N/A')}'")
                    print(f"      Has label: {inp.get('has_label')}")

        # Buttons
        print("\n" + "-" * 80)
        print("BUTTONS EXTRAIDOS:")
        print("-" * 80)

        button_texts = text_corpus.get('button_texts', [])
        print(f"Total buttons: {len(button_texts)}")

        if button_texts:
            for i, btn in enumerate(button_texts[:5], 1):
                print(f"  {i}. '{btn}'")
        else:
            print("  (ninguno encontrado)")

        # Links
        print("\n" + "-" * 80)
        print("MUESTRA DE LINKS:")
        print("-" * 80)

        link_texts = text_corpus.get('link_texts', [])
        print(f"Total links: {len(link_texts)}")

        for link in link_texts[:5]:
            print(f"  - '{link['text'][:50]}' -> {link['url'][:30]}")

    except Exception as e:
        print(f"[ERROR] No se pudo acceder: {str(e)}")


def test_forms_site_educacion():
    """Verifica extraccion en educacion.gob.bo (sitio con formularios)"""
    print("\n\n" + "=" * 80)
    print("TEST 3: EXTRACCION EN EDUCACION.GOB.BO")
    print("=" * 80)

    crawler = GobBoCrawler(timeout=45)

    try:
        result = crawler.crawl("https://www.minedu.gob.bo")

        if 'error' in result:
            print(f"[ERROR] {result['error']}")
            return

        text_corpus = result.get('text_corpus', {})
        forms_data = result.get('forms', {})

        print(f"\n[INFO] Datos extraidos:")
        print(f"  - Sections: {text_corpus.get('total_sections', 0)}")
        print(f"  - Links: {text_corpus.get('total_links', 0)}")
        print(f"  - Labels: {text_corpus.get('total_labels', 0)}")
        print(f"  - Buttons: {len(text_corpus.get('button_texts', []))}")
        print(f"  - Forms: {forms_data.get('total_forms', 0)}")
        print(f"  - Inputs: {forms_data.get('total_inputs', 0)}")

        # Buttons
        button_texts = text_corpus.get('button_texts', [])
        if button_texts:
            print("\n  BUTTONS encontrados:")
            for i, btn in enumerate(button_texts[:5], 1):
                print(f"    {i}. '{btn}'")

        # Labels desde forms
        if forms_data.get('forms'):
            print("\n  LABELS desde forms:")
            for form in forms_data['forms'][:2]:
                for inp in form.get('inputs', [])[:3]:
                    if inp.get('has_label'):
                        print(f"    - '{inp.get('label_text')}' (for={inp.get('id')})")

    except Exception as e:
        print(f"[ERROR] No se pudo acceder: {str(e)}")


def analyze_text_quality():
    """Analiza calidad de textos extraidos"""
    print("\n\n" + "=" * 80)
    print("ANALISIS DE CALIDAD DE TEXTOS")
    print("=" * 80)

    crawler = GobBoCrawler(timeout=30)
    result = crawler.crawl("https://www.aduana.gob.bo")

    if 'error' in result:
        print(f"[ERROR] {result['error']}")
        return

    text_corpus = result.get('text_corpus', {})

    # Analizar sections
    sections = text_corpus.get('sections', [])
    print(f"\n[SECTIONS] {len(sections)} encontradas")

    issues = []
    for i, section in enumerate(sections):
        heading = section.get('heading', '')
        content = section.get('content', '')

        # Verificar heading vacio
        if len(heading.strip()) < 3:
            issues.append(f"Section {i+1}: Heading muy corto '{heading}'")

        # Verificar contenido vacio
        if len(content.strip()) < 10:
            issues.append(f"Section {i+1}: Contenido muy corto ({len(content)} chars)")

        # Verificar caracteres raros
        non_ascii_heading = sum(1 for c in heading if ord(c) > 127 and ord(c) < 256)
        if non_ascii_heading > 5:
            issues.append(f"Section {i+1}: Muchos caracteres especiales en heading")

    if issues:
        print("\n[WARN] Problemas detectados:")
        for issue in issues[:10]:
            print(f"  - {issue}")
    else:
        print("\n[OK] No se detectaron problemas")

    # Mostrar ejemplo de section completa
    if sections:
        print("\n[EJEMPLO] Primera section:")
        s = sections[0]
        print(f"  Heading: '{s.get('heading', '')}'")
        print(f"  Level: {s.get('heading_level', '')}")
        print(f"  Content: '{s.get('content', '')[:100]}...'")
        print(f"  Words: {s.get('word_count', 0)}")


if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("VERIFICACION PROFUNDA DE EXTRACCION DEL CRAWLER")
    print("=" * 80)

    # Test 1: Links en aduana
    test_link_extraction_aduana()

    # Test 2: Forms en impuestos
    test_forms_site_impuestos()

    # Test 3: Forms en educacion
    test_forms_site_educacion()

    # Analisis de calidad
    analyze_text_quality()

    print("\n" + "=" * 80)
    print("[OK] VERIFICACION COMPLETADA")
    print("=" * 80)
