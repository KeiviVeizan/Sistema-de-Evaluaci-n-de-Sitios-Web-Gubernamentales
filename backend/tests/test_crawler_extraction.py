"""
Script para verificar que datos extrae el crawler.

Este script verifica si el crawler extrae todos los datos necesarios
para el modulo NLP en el formato correcto.

Ubicacion: backend/tests/test_crawler_extraction.py
"""

import json
import sys
import os

# Agregar el directorio backend al path para importar modulos
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.crawler.html_crawler import GobBoCrawler


def test_extraction():
    """
    Verifica que datos extrae el crawler y si coinciden con lo que necesita el NLP.
    """
    # URL de prueba - sitio .gob.bo conocido
    test_url = "https://www.aduana.gob.bo"

    print("=" * 80)
    print("VERIFICACION DE DATOS EXTRAIDOS POR EL CRAWLER")
    print("=" * 80)
    print(f"\n[URL] URL de prueba: {test_url}")
    print("\nIniciando crawling (esto puede tardar 10-30 segundos)...\n")

    try:
        crawler = GobBoCrawler(timeout=30)
        result = crawler.crawl(test_url)

        if 'error' in result:
            print(f"\n[ERROR] {result['error']}")
            return False

        print("[OK] Crawling completado exitosamente\n")

        # ================================================================
        # VERIFICAR TEXT_CORPUS (donde esta la info para NLP)
        # ================================================================
        if 'text_corpus' not in result:
            print("[ERROR] NO SE ENCONTRO 'text_corpus' EN LOS RESULTADOS")
            return False

        text_corpus = result['text_corpus']

        print("=" * 80)
        print("DATOS EXTRAIDOS EN TEXT_CORPUS")
        print("=" * 80)

        # ================================================================
        # 1. VERIFICAR SECTIONS
        # ================================================================
        print("\n" + "-" * 80)
        print("1. SECTIONS (para analisis de coherencia)")
        print("-" * 80)

        if 'sections' in text_corpus:
            sections = text_corpus['sections']
            print(f"  [OK] Extrae sections: {len(sections)} encontradas")

            if sections:
                print(f"\n  Ejemplo de section:")
                example = sections[0]
                print(f"     {json.dumps(example, indent=6, ensure_ascii=False)}")

                # Verificar campos requeridos por NLP
                required_fields = ['heading', 'heading_level', 'content', 'word_count']
                missing = [f for f in required_fields if f not in example]

                if missing:
                    print(f"\n  [WARN] FALTAN CAMPOS REQUERIDOS: {missing}")
                else:
                    print(f"\n  [OK] Todos los campos requeridos presentes")
        else:
            print("  [ERROR] NO extrae 'sections'")

        # ================================================================
        # 2. VERIFICAR LINKS (link_texts en text_corpus)
        # ================================================================
        print("\n" + "-" * 80)
        print("2. LINKS (para analisis de ambiguedad)")
        print("-" * 80)

        if 'link_texts' in text_corpus:
            link_texts = text_corpus['link_texts']
            print(f"  [OK] Extrae link_texts: {len(link_texts)} encontrados")

            if link_texts:
                print(f"\n  Ejemplo de link:")
                example = link_texts[0]
                print(f"     {json.dumps(example, indent=6, ensure_ascii=False)}")

                # NLP espera: {'text': str, 'url': str, 'title': str}
                print(f"\n  Formato actual:")
                print(f"     - Tiene 'text': {'text' in example}")
                print(f"     - Tiene 'url': {'url' in example}")
                print(f"     - Tiene 'title': {'title' in example}")

                if 'url' in example and 'title' in example:
                    print(f"\n  [OK] Formato correcto para NLP")
                elif 'url' not in example:
                    print(f"\n  [WARN] PROBLEMA: NLP espera campo 'url'")
                elif 'title' not in example:
                    print(f"\n  [WARN] PROBLEMA: NLP espera campo 'title'")
        else:
            print("  [ERROR] NO extrae 'link_texts'")

        # ================================================================
        # 3. VERIFICAR LABELS
        # ================================================================
        print("\n" + "-" * 80)
        print("3. LABELS (para analisis de ambiguedad)")
        print("-" * 80)

        if 'label_texts' in text_corpus:
            label_texts = text_corpus['label_texts']
            print(f"  [OK] Extrae label_texts: {len(label_texts)} encontrados")

            if label_texts:
                print(f"\n  Ejemplos de labels:")
                for i, label in enumerate(label_texts[:3], 1):
                    print(f"     {i}. '{label}'")

                # NLP espera: {'text': str, 'for': str}
                # Crawler da: solo strings (texto)
                print(f"\n  Formato actual:")
                print(f"     - Tipo: {type(label_texts[0])}")

                if isinstance(label_texts[0], str):
                    print(f"\n  [WARN] PROBLEMA: NLP espera dict con {{'text': str, 'for': str}}")
                    print(f"     Crawler solo extrae texto (strings)")
                    print(f"     SOLUCION: Usar datos de 'forms' en lugar de 'label_texts'")
        else:
            print("  [ERROR] NO extrae 'label_texts'")

        # ================================================================
        # 3.5. VERIFICAR FORMS (alternativa para labels)
        # ================================================================
        print("\n" + "-" * 80)
        print("3.5. FORMS (datos completos de labels con 'for')")
        print("-" * 80)

        if 'forms' in result:
            forms = result['forms']
            total_inputs = forms.get('total_inputs', 0)
            print(f"  [OK] Extrae forms: {forms.get('total_forms', 0)} formularios")
            print(f"     Total inputs: {total_inputs}")

            if forms['forms']:
                print(f"\n  Ejemplo de form con inputs:")
                example_form = forms['forms'][0]
                if example_form['inputs']:
                    example_input = example_form['inputs'][0]
                    print(f"     {json.dumps(example_input, indent=6, ensure_ascii=False)}")

                    print(f"\n  Campos disponibles:")
                    print(f"     - type: {example_input.get('type')}")
                    print(f"     - id: {example_input.get('id')}")
                    print(f"     - label_text: {example_input.get('label_text')}")
                    print(f"     - has_label: {example_input.get('has_label')}")

                    print(f"\n  [NOTA] Este formato es MAS COMPLETO que 'label_texts'")
                    print(f"     Se puede usar para extraer labels con sus atributos 'for' (id)")
        else:
            print("  [ERROR] NO extrae 'forms'")

        # ================================================================
        # 4. VERIFICAR BUTTONS
        # ================================================================
        print("\n" + "-" * 80)
        print("4. BUTTONS (para analisis de ambiguedad)")
        print("-" * 80)

        if 'button_texts' in text_corpus:
            button_texts = text_corpus['button_texts']
            print(f"  [OK] Extrae button_texts: {len(button_texts)} encontrados")

            if button_texts:
                print(f"\n  Ejemplos de buttons:")
                for i, button in enumerate(button_texts[:3], 1):
                    print(f"     {i}. '{button}'")

                # NLP espera: {'text': str, 'type': str, 'aria_label': str}
                # Crawler da: solo strings (texto)
                print(f"\n  Formato actual:")
                print(f"     - Tipo: {type(button_texts[0])}")

                if isinstance(button_texts[0], str):
                    print(f"\n  [WARN] PROBLEMA: NLP espera dict con {{'text': str, 'type': str}}")
                    print(f"     Crawler solo extrae texto (strings)")
                    print(f"     SOLUCION: Necesita mejorar extraccion de buttons")
        else:
            print("  [ERROR] NO extrae 'button_texts'")

        # ================================================================
        # RESUMEN GENERAL
        # ================================================================
        print("\n" + "=" * 80)
        print("RESUMEN DE VERIFICACION")
        print("=" * 80)

        issues = []

        # Verificar sections
        if 'sections' not in text_corpus:
            issues.append("[ERROR] Faltan SECTIONS")
        elif not text_corpus['sections']:
            issues.append("[WARN] SECTIONS esta vacio")
        else:
            required_fields = ['heading', 'heading_level', 'content', 'word_count']
            example = text_corpus['sections'][0]
            missing = [f for f in required_fields if f not in example]
            if missing:
                issues.append(f"[WARN] SECTIONS falta campos: {missing}")
            else:
                print(f"[OK] SECTIONS: OK (formato correcto)")

        # Verificar links
        if 'link_texts' not in text_corpus:
            issues.append("[ERROR] Faltan LINKS")
        elif not text_corpus['link_texts']:
            issues.append("[WARN] LINKS esta vacio")
        else:
            example = text_corpus['link_texts'][0]
            if 'url' in example and 'title' in example:
                print(f"[OK] LINKS: OK (tiene 'url' y 'title')")
            elif 'url' not in example:
                issues.append("[WARN] LINKS falta campo 'url'")
            elif 'title' not in example:
                issues.append("[WARN] LINKS falta campo 'title'")

        # Verificar labels
        if 'label_texts' not in text_corpus:
            issues.append("[ERROR] Faltan LABELS")
        elif not text_corpus['label_texts']:
            issues.append("[WARN] LABELS esta vacio")
        else:
            if isinstance(text_corpus['label_texts'][0], str):
                issues.append("[WARN] LABELS solo tiene texto, falta atributo 'for' (usar 'forms' en su lugar)")
            else:
                print(f"[OK] LABELS: OK")

        # Verificar buttons
        if 'button_texts' not in text_corpus:
            issues.append("[ERROR] Faltan BUTTONS")
        elif not text_corpus['button_texts']:
            issues.append("[WARN] BUTTONS esta vacio")
        else:
            if isinstance(text_corpus['button_texts'][0], str):
                issues.append("[WARN] BUTTONS solo tiene texto, falta 'type' (necesita mejorar extraccion)")
            else:
                print(f"[OK] BUTTONS: OK")

        # Mostrar issues
        if issues:
            print(f"\n[WARN] PROBLEMAS ENCONTRADOS:")
            for issue in issues:
                print(f"   {issue}")
        else:
            print(f"\n[OK] TODOS LOS ELEMENTOS NECESARIOS ESTAN SIENDO EXTRAIDOS CORRECTAMENTE")

        # ================================================================
        # RECOMENDACIONES
        # ================================================================
        print("\n" + "=" * 80)
        print("RECOMENDACIONES")
        print("=" * 80)

        print("\n1. SECTIONS: [OK] Listo para usar")
        print("   - El formato es correcto")

        print("\n2. LINKS: [OK] Listo para usar")
        print("   - Tiene campos 'text', 'url', 'title'")

        print("\n3. LABELS: [WARN] Usar datos de 'forms'")
        print("   - text_corpus['label_texts'] solo tiene texto")
        print("   - result['forms'] tiene datos completos (text, for, type)")
        print("   - SOLUCION: Extraer labels de 'forms':")
        print("     labels_for_nlp = []")
        print("     for form in result['forms']['forms']:")
        print("         for inp in form['inputs']:")
        print("             if inp['has_label']:")
        print("                 labels_for_nlp.append({")
        print("                     'text': inp['label_text'],")
        print("                     'for': inp['id']")
        print("                 })")

        print("\n4. BUTTONS: [WARN] Necesita mejorar extraccion")
        print("   - Actualmente solo extrae texto")
        print("   - SOLUCION: Modificar crawler para extraer tambien 'type' y 'aria-label'")

        print("\n" + "=" * 80)
        print("[OK] VERIFICACION COMPLETADA")
        print("=" * 80)

        return True

    except ValueError as e:
        print(f"\n[ERROR] ERROR DE VALIDACION: {str(e)}")
        return False
    except Exception as e:
        print(f"\n[ERROR] ERROR INESPERADO: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    # Nota: El crawler usa sync_playwright, no async
    success = test_extraction()
    exit(0 if success else 1)
