"""
Script para verificar los datos extraídos de un sitio web
"""
import sys
import os
from pathlib import Path
import json

# Asegurar UTF-8 en Windows
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

# Agregar el directorio raíz al path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from app.database import SessionLocal
from app.models.database_models import Website, ExtractedContent


def check_extracted_data(website_id: int = None):
    """
    Verifica los datos extraídos de un sitio web
    """
    db = SessionLocal()

    try:
        # Buscar sitio web
        if website_id:
            website = db.query(Website).filter(Website.id == website_id).first()
        else:
            website = db.query(Website).order_by(Website.id.desc()).first()

        if not website:
            print("❌ No se encontró ningún sitio web")
            return

        print("="*80)
        print(f"SITIO WEB: {website.url}")
        print(f"ID: {website.id}")
        print("="*80)

        # Obtener contenido extraído
        extracted = db.query(ExtractedContent).filter(
            ExtractedContent.website_id == website.id
        ).first()

        if not extracted:
            print("❌ No hay contenido extraído")
            return

        print(f"\n✓ Contenido extraído el: {extracted.crawled_at}")
        print(f"✓ HTTP Status: {extracted.http_status_code}")

        # Verificar cada campo
        print("\n" + "="*80)
        print("METADATA")
        print("="*80)
        metadata = extracted.page_metadata or {}
        print(json.dumps(metadata, indent=2, ensure_ascii=False))

        print("\n" + "="*80)
        print("ESTRUCTURA HTML")
        print("="*80)
        structure = extracted.html_structure or {}
        print(json.dumps(structure, indent=2, ensure_ascii=False))

        print("\n" + "="*80)
        print("ELEMENTOS SEMÁNTICOS")
        print("="*80)
        semantic = extracted.semantic_elements or {}
        print(json.dumps(semantic, indent=2, ensure_ascii=False))

        print("\n" + "="*80)
        print("ENCABEZADOS (HEADINGS)")
        print("="*80)
        headings = extracted.headings or {}
        print(f"Total: {headings.get('total_count', 0)}")
        print(f"H1: {headings.get('h1_count', 0)}")
        if headings.get('headings'):
            print(f"Primeros 5 headings:")
            for h in headings['headings'][:5]:
                print(f"  - {h.get('tag')}: {h.get('text', '')[:60]}")

        print("\n" + "="*80)
        print("IMÁGENES")
        print("="*80)
        images = extracted.images or {}
        print(f"Total: {images.get('total_count', 0)}")
        print(f"Con alt: {images.get('with_alt_count', 0)}")
        if images.get('images'):
            print(f"Primeras 5 imágenes:")
            for img in images['images'][:5]:
                print(f"  - {img.get('src', '')[:60]}")
                print(f"    Alt: {img.get('alt', 'N/A')[:60]}")

        print("\n" + "="*80)
        print("ENLACES")
        print("="*80)
        links = extracted.links or {}
        print(f"Total: {links.get('total_count', 0)}")
        print(f"Enlaces vacíos: {links.get('empty_links', {}).get('count', 0)}")
        print(f"Texto genérico: {links.get('generic_text', {}).get('count', 0)}")

        print("\n" + "="*80)
        print("FORMULARIOS")
        print("="*80)
        forms = extracted.forms or {}
        print(f"Total formularios: {forms.get('total_forms', 0)}")
        print(f"Total inputs: {forms.get('total_inputs', 0)}")
        print(f"Inputs con label: {forms.get('inputs_with_label', 0)}")

        print("\n" + "="*80)
        print("RECURSOS EXTERNOS")
        print("="*80)
        external = extracted.external_resources or {}
        print(f"Scripts: {len(external.get('scripts', []))}")
        print(f"Stylesheets: {len(external.get('stylesheets', []))}")
        if external.get('scripts'):
            print("Primeros 5 scripts:")
            for script in external['scripts'][:5]:
                print(f"  - {script[:80]}")

        print("\n" + "="*80)
        print("CORPUS DE TEXTO")
        print("="*80)
        text_corpus = extracted.text_corpus or {}
        print(f"Total secciones: {text_corpus.get('total_sections', 0)}")
        print(f"Secciones con contenido: {text_corpus.get('sections_with_content', 0)}")
        print(f"Total palabras: {text_corpus.get('total_words', 0)}")

        if text_corpus.get('sections'):
            print(f"\nPrimeras 3 secciones:")
            for i, section in enumerate(text_corpus['sections'][:3], 1):
                print(f"\n  Sección {i}:")
                print(f"    Heading: {section.get('heading', 'N/A')[:60]}")
                print(f"    Párrafos: {len(section.get('paragraphs', []))}")
                if section.get('paragraphs'):
                    print(f"    Primer párrafo: {section['paragraphs'][0][:100]}...")

        print("\n" + "="*80)

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

    finally:
        db.close()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Verifica datos extraídos')
    parser.add_argument('--website-id', type=int, help='ID del sitio web')

    args = parser.parse_args()

    check_extracted_data(args.website_id)
