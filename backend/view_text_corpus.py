"""
Script para visualizar el corpus textual extraído de un sitio web.

Uso:
    python view_text_corpus.py <website_id>

Ejemplo:
    python view_text_corpus.py 1
"""

import sys
import io
import json
from pathlib import Path

# Configurar encoding UTF-8 para Windows
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# Agregar el directorio app al path
sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy.orm import Session
from app.database import get_db
from app.models.database_models import Website, ExtractedContent


def view_text_corpus(website_id: int):
    """
    Muestra el corpus textual extraído de un sitio web.

    Args:
        website_id: ID del sitio web
    """
    db = next(get_db())

    try:
        # Obtener website
        website = db.query(Website).filter(Website.id == website_id).first()

        if not website:
            print(f"✗ No se encontró el sitio web con ID {website_id}")
            return

        # Obtener contenido extraído
        content = db.query(ExtractedContent).filter(
            ExtractedContent.website_id == website_id
        ).first()

        if not content:
            print(f"✗ No hay contenido extraído para el sitio web {website_id}")
            return

        print(f"\n{'='*80}")
        print(f"CORPUS TEXTUAL - {website.institution_name}")
        print(f"URL: {website.url}")
        print(f"{'='*80}\n")

        text_corpus = content.text_corpus or {}

        # 1. INFORMACIÓN GENERAL
        print("=== INFORMACIÓN GENERAL ===\n")
        print(f"Título: {text_corpus.get('title', 'N/A')}")
        print(f"Meta Description: {text_corpus.get('meta_description', 'N/A')}")
        print(f"Total de palabras: {text_corpus.get('total_words', 0):,}")
        print(f"Total de caracteres: {text_corpus.get('total_characters', 0):,}")
        print(f"'Bolivia a tu servicio': {'✓ Sí' if text_corpus.get('has_bolivia_service_text') else '✗ No'}")

        # 2. HEADER
        print(f"\n=== TEXTO DEL HEADER ===\n")
        header_text = text_corpus.get('header_text', '')
        if header_text:
            print(f"{header_text}\n")
        else:
            print("(No se encontró header)\n")

        # 3. SECCIONES
        sections = text_corpus.get('sections', [])
        print(f"=== SECCIONES ({len(sections)} encontradas) ===\n")

        for i, section in enumerate(sections, 1):
            print(f"[{i}] {section['heading_level'].upper()}: {section['heading']}")
            print(f"    Palabras: {section.get('word_count', 0)}")
            print(f"    Párrafos: {len(section.get('paragraphs', []))}")
            print(f"    Contenido (preview):")

            # Mostrar primeros 2 párrafos
            for j, para in enumerate(section.get('paragraphs', [])[:2], 1):
                print(f"      [{j}] {para[:150]}{'...' if len(para) > 150 else ''}")

            print()

        # 4. NAVEGACIÓN
        nav_texts = text_corpus.get('navigation_texts', [])
        print(f"=== NAVEGACIÓN ({len(nav_texts)} items) ===\n")
        print(f"Items: {', '.join(nav_texts[:20])}")
        if len(nav_texts) > 20:
            print(f"... y {len(nav_texts) - 20} más")
        print()

        # 5. ENLACES GENÉRICOS
        generic_count = text_corpus.get('generic_links', 0)
        generic_examples = text_corpus.get('generic_link_examples', [])

        print(f"=== ENLACES GENÉRICOS ({generic_count} encontrados) ===\n")
        if generic_examples:
            print("Ejemplos:")
            for example in generic_examples:
                print(f"  • \"{example}\"")
        else:
            print("✓ No se encontraron enlaces con texto genérico")
        print()

        # 6. BOTONES
        button_texts = text_corpus.get('button_texts', [])
        print(f"=== BOTONES ({len(button_texts)} encontrados) ===\n")
        if button_texts:
            print(f"Textos: {', '.join(button_texts[:15])}")
            if len(button_texts) > 15:
                print(f"... y {len(button_texts) - 15} más")
        else:
            print("(No se encontraron botones)")
        print()

        # 7. LABELS DE FORMULARIOS
        label_texts = text_corpus.get('label_texts', [])
        print(f"=== LABELS DE FORMULARIOS ({len(label_texts)} encontrados) ===\n")
        if label_texts:
            print(f"Textos: {', '.join(label_texts[:15])}")
            if len(label_texts) > 15:
                print(f"... y {len(label_texts) - 15} más")
        else:
            print("(No se encontraron labels)")
        print()

        # 8. TEXTO COMPLETO (PREVIEW)
        full_text = text_corpus.get('full_text', '')
        print(f"=== TEXTO COMPLETO (primeros 1000 caracteres) ===\n")
        print(f"{full_text[:1000]}")
        if len(full_text) > 1000:
            print(f"\n... (continúa por {len(full_text) - 1000} caracteres más)")
        print()

        # 9. OPCIÓN PARA GUARDAR JSON COMPLETO
        print(f"{'='*80}")
        save = input("\n¿Deseas guardar el corpus completo en un archivo JSON? (s/n): ")

        if save.lower() == 's':
            output_file = Path(__file__).parent / f"text_corpus_{website_id}.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(text_corpus, f, indent=2, ensure_ascii=False)
            print(f"✓ Guardado en: {output_file}")

    finally:
        db.close()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python view_text_corpus.py <website_id>")
        print("\nEjemplo: python view_text_corpus.py 1")
        sys.exit(1)

    try:
        website_id = int(sys.argv[1])
        view_text_corpus(website_id)
    except ValueError:
        print("✗ Error: El website_id debe ser un número entero")
        sys.exit(1)
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
