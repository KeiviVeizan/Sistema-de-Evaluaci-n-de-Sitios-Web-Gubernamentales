"""
Tests de validación para AmbiguityDetector.

Estos tests verifican la detección automática de textos problemáticos:
- Textos genéricos ("Ver más", "Haga clic aquí")
- Textos ambiguos ("Nombre", "Fecha")
- Textos no descriptivos ("Información", "Datos")
- Textos demasiado cortos (< 3 caracteres)
- Textos técnicos (siglas sin explicar)
"""

from app.nlp.ambiguity import AmbiguityDetector, AmbiguityCategory


def test_textos_genericos():
    """Test 1: Detecta textos genéricos en enlaces."""
    print("=" * 70)
    print("TEST 1: Textos Genéricos (ACC-08)")
    print("=" * 70)

    detector = AmbiguityDetector()

    generic_texts = [
        "Ver más",
        "Leer más",
        "Haga clic aquí",
        "Click aquí",
        "[+]",
        "+ ver más",
        "Descargar",
        "Más información",
        "Continuar",
        "info"
    ]

    print("\n✓ Probando enlaces genéricos:")
    for text in generic_texts:
        result = detector.analyze_text(text, "link")
        assert result.is_problematic, f"'{text}' debería ser problemático"
        assert result.category == AmbiguityCategory.TEXTO_GENERICO, \
            f"'{text}' debería ser GENERICO, obtuvo {result.category.value}"
        assert result.wcag_criterion == "ACC-08 (WCAG 2.4.4 Link Purpose - Level A)"
        print(f"  ✓ '{text}': {result.category.value}")

    print("\n✅ Test 1 PASADO\n")


def test_textos_ambiguos():
    """Test 2: Detecta textos ambiguos en labels."""
    print("=" * 70)
    print("TEST 2: Textos Ambiguos (ACC-07)")
    print("=" * 70)

    detector = AmbiguityDetector()

    ambiguous_texts = [
        "Nombre",
        "Apellido",
        "Fecha",
        "Documento",
        "Número",
        "Código",
        "Tipo",
        "Estado",
        "Datos"
    ]

    print("\n✓ Probando labels ambiguos:")
    for text in ambiguous_texts:
        result = detector.analyze_text(text, "label")
        assert result.is_problematic, f"'{text}' debería ser problemático"
        assert result.category == AmbiguityCategory.TEXTO_AMBIGUO, \
            f"'{text}' debería ser AMBIGUO, obtuvo {result.category.value}"
        assert result.wcag_criterion == "ACC-07 (WCAG 3.3.2 Labels or Instructions - Level A)"
        print(f"  ✓ '{text}': {result.category.value}")
        print(f"    Recomendación: {result.recommendation[:80]}...")

    print("\n✅ Test 2 PASADO\n")


def test_textos_no_descriptivos():
    """Test 3: Detecta textos no descriptivos en headings."""
    print("=" * 70)
    print("TEST 3: Textos No Descriptivos (ACC-09)")
    print("=" * 70)

    detector = AmbiguityDetector()

    non_descriptive_texts = [
        "Información",
        "Datos",
        "Sección",
        "Contenido",
        "Detalles",
        "Otros",
        "General"
    ]

    print("\n✓ Probando headings no descriptivos:")
    for text in non_descriptive_texts:
        result = detector.analyze_text(text, "heading")
        assert result.is_problematic, f"'{text}' debería ser problemático"
        assert result.category == AmbiguityCategory.TEXTO_NO_DESCRIPTIVO, \
            f"'{text}' debería ser NO_DESCRIPTIVO, obtuvo {result.category.value}"
        assert result.wcag_criterion == "ACC-09 (WCAG 2.4.6 Headings and Labels - Level AA)"
        print(f"  ✓ '{text}': {result.category.value}")

    print("\n✅ Test 3 PASADO\n")


def test_textos_muy_cortos():
    """Test 4: Detecta textos demasiado cortos."""
    print("=" * 70)
    print("TEST 4: Textos Demasiado Cortos (< 3 caracteres)")
    print("=" * 70)

    detector = AmbiguityDetector(min_text_length=3)

    short_texts = [
        "Ok",
        "No",
        "Sí",
        "Si",
        "Ve",
        "Ir"
    ]

    print("\n✓ Probando textos muy cortos:")
    for text in short_texts:
        result = detector.analyze_text(text, "button")
        assert result.is_problematic, f"'{text}' debería ser problemático"
        assert result.category == AmbiguityCategory.TEXTO_DEMASIADO_CORTO, \
            f"'{text}' debería ser DEMASIADO_CORTO, obtuvo {result.category.value}"
        print(f"  ✓ '{text}' ({len(text)} chars): {result.category.value}")

    print("\n✅ Test 4 PASADO\n")


def test_siglas_sin_explicar():
    """Test 5: Detecta siglas sin explicar."""
    print("=" * 70)
    print("TEST 5: Siglas Sin Explicar (ACC-09)")
    print("=" * 70)

    detector = AmbiguityDetector()

    acronyms = [
        "SIGEP",
        "RDA",
        "CITE",
        "ADSIB",
        "RUDE",
        "PDF",
        "CI",
        "NIT"
    ]

    print("\n✓ Probando siglas:")
    for text in acronyms:
        result = detector.analyze_text(text, "link")
        assert result.is_problematic, f"'{text}' debería ser problemático"
        assert result.category == AmbiguityCategory.TEXTO_EXCESIVAMENTE_TECNICO, \
            f"'{text}' debería ser EXCESIVAMENTE_TECNICO, obtuvo {result.category.value}"
        assert result.wcag_criterion == "ACC-09 (WCAG 2.4.6 Headings and Labels - Level AA)"
        print(f"  ✓ '{text}': {result.category.value}")
        print(f"    Recomendación: {result.recommendation[:90]}...")

    print("\n✅ Test 5 PASADO\n")


def test_textos_claros():
    """Test 6: Textos claros NO son marcados como problemáticos."""
    print("=" * 70)
    print("TEST 6: Textos Claros (No Problemáticos)")
    print("=" * 70)

    detector = AmbiguityDetector()

    clear_texts = [
        "Descargar informe anual 2024",
        "Ver requisitos para trámite de pasaporte",
        "Nombre completo del solicitante",
        "Fecha de nacimiento",
        "Servicios de Salud",
        "Maestras y Maestros",
        "Educación Superior",
        "Atención al usuario",
        "Formulario de registro completo"
    ]

    print("\n✓ Probando textos claros:")
    for text in clear_texts:
        result = detector.analyze_text(text, "link")
        assert not result.is_problematic, \
            f"'{text}' NO debería ser problemático, obtuvo {result.category.value}"
        assert result.category == AmbiguityCategory.TEXTO_CLARO
        assert result.recommendation is None
        print(f"  ✓ '{text}': {result.category.value}")

    print("\n✅ Test 6 PASADO\n")


def test_texto_vacio():
    """Test 7: Manejo de texto vacío."""
    print("=" * 70)
    print("TEST 7: Texto Vacío")
    print("=" * 70)

    detector = AmbiguityDetector()

    empty_texts = ["", "   ", "\t", "\n"]

    print("\n✓ Probando textos vacíos:")
    for text in empty_texts:
        result = detector.analyze_text(text, "link")
        assert result.is_problematic
        assert result.category == AmbiguityCategory.TEXTO_DEMASIADO_CORTO
        assert result.text == "[VACÍO]"
        print(f"  ✓ '{repr(text)}': {result.category.value}")

    print("\n✅ Test 7 PASADO\n")


def test_casos_reales_gob_bo():
    """Test 8: Casos reales de sitios .gob.bo."""
    print("=" * 70)
    print("TEST 8: Casos Reales de Sitios .gob.bo")
    print("=" * 70)

    detector = AmbiguityDetector()

    # Casos basados en el sitio web real que compartió el usuario
    real_cases = [
        {"text": "Ver más", "type": "link", "expected": AmbiguityCategory.TEXTO_GENERICO},
        {"text": "Leer más", "type": "link", "expected": AmbiguityCategory.TEXTO_GENERICO},
        {"text": "[+] Ver más Noticias", "type": "link", "expected": AmbiguityCategory.TEXTO_GENERICO},
        {"text": "Maestras y Maestros", "type": "link", "expected": AmbiguityCategory.TEXTO_CLARO},
        {"text": "Educación Superior", "type": "link", "expected": AmbiguityCategory.TEXTO_CLARO},
        {"text": "FORMULARIO RUDE", "type": "button", "expected": AmbiguityCategory.TEXTO_EXCESIVAMENTE_TECNICO},
        {"text": "Atención al usuario", "type": "link", "expected": AmbiguityCategory.TEXTO_CLARO},
        {"text": "OTHER ARTICLES", "type": "heading", "expected": AmbiguityCategory.TEXTO_CLARO},  # En inglés pero descriptivo
        {"text": "NOTICIAS", "type": "heading", "expected": AmbiguityCategory.TEXTO_CLARO}
    ]

    print("\n✓ Analizando casos reales:")
    for i, case in enumerate(real_cases, 1):
        result = detector.analyze_text(case["text"], case["type"])

        status = "✓" if result.category == case["expected"] else "✗"
        print(f"\n  {status} Caso {i}: '{case['text']}' ({case['type']})")
        print(f"    Esperado: {case['expected'].value}")
        print(f"    Obtenido: {result.category.value}")
        print(f"    Problemático: {result.is_problematic}")

        if result.is_problematic:
            print(f"    WCAG: {result.wcag_criterion}")
            print(f"    Recomendación: {result.recommendation[:80]}...")

        assert result.category == case["expected"], \
            f"Caso {i} falló: esperado {case['expected'].value}, obtuvo {result.category.value}"

    print("\n✅ Test 8 PASADO\n")


def test_analisis_multiple():
    """Test 9: Análisis de múltiples textos a la vez."""
    print("=" * 70)
    print("TEST 9: Análisis Múltiple")
    print("=" * 70)

    detector = AmbiguityDetector()

    texts = [
        {'text': 'Ver más', 'element_type': 'link'},
        {'text': 'Nombre', 'element_type': 'label'},
        {'text': 'Descargar informe anual 2024', 'element_type': 'link'},
        {'text': 'SIGEP', 'element_type': 'link'},
        {'text': 'Info', 'element_type': 'button'},
        {'text': 'Servicios de Salud', 'element_type': 'heading'},
        {'text': 'Datos', 'element_type': 'heading'},
        {'text': 'Ok', 'element_type': 'button'}
    ]

    summary = detector.analyze_multiple(texts)

    print(f"\n✓ Resumen del análisis:")
    print(f"  Total analizado: {summary['total_analyzed']}")
    print(f"  Problemáticos: {summary['problematic_count']}")
    print(f"  Claros: {summary['clear_count']}")
    print(f"\n  Por categoría:")
    for cat, count in summary['by_category'].items():
        print(f"    - {cat}: {count}")
    print(f"\n  Por tipo de elemento:")
    for etype, count in summary['by_element_type'].items():
        print(f"    - {etype}: {count}")

    assert summary['total_analyzed'] == 8
    assert summary['problematic_count'] == 6  # Ver más, Nombre, SIGEP, Info, Datos, Ok
    assert summary['clear_count'] == 2  # Descargar informe..., Servicios de Salud
    assert len(summary['recommendations']) == 6
    assert len(summary['details']) == 8

    print("\n✅ Test 9 PASADO\n")


def test_confidence_scores():
    """Test 10: Verifica scores de confianza."""
    print("=" * 70)
    print("TEST 10: Scores de Confianza")
    print("=" * 70)

    detector = AmbiguityDetector()

    # Textos problemáticos tienen confianza 1.0 (reglas)
    problematic = detector.analyze_text("Ver más", "link")
    assert problematic.confidence == 1.0, "Reglas deberían tener confianza 1.0"
    print(f"✓ Texto problemático: confidence={problematic.confidence}")

    # Textos claros tienen confianza 0.8 (no usamos BETO)
    clear = detector.analyze_text("Servicios de Salud", "link")
    assert clear.confidence == 0.8, "Textos claros deberían tener confianza 0.8"
    print(f"✓ Texto claro: confidence={clear.confidence}")

    print("\n✅ Test 10 PASADO\n")


def test_lista_vacia():
    """Test 11: Análisis de lista vacía."""
    print("=" * 70)
    print("TEST 11: Lista Vacía")
    print("=" * 70)

    detector = AmbiguityDetector()
    summary = detector.analyze_multiple([])

    assert summary['total_analyzed'] == 0
    assert summary['problematic_count'] == 0
    assert summary['clear_count'] == 0
    assert len(summary['recommendations']) == 0

    print("✓ Lista vacía manejada correctamente")
    print("\n✅ Test 11 PASADO\n")


def run_all_tests():
    """Ejecuta todos los tests en orden."""
    print("\n" + "=" * 70)
    print("INICIANDO TESTS DE AmbiguityDetector")
    print("=" * 70)
    print("Detección automática de textos problemáticos según WCAG 2.0")
    print("=" * 70 + "\n")

    try:
        test_textos_genericos()
        test_textos_ambiguos()
        test_textos_no_descriptivos()
        test_textos_muy_cortos()
        test_siglas_sin_explicar()
        test_textos_claros()
        test_texto_vacio()
        test_casos_reales_gob_bo()
        test_analisis_multiple()
        test_confidence_scores()
        test_lista_vacia()

        print("\n" + "=" * 70)
        print("✅ TODOS LOS TESTS PASARON EXITOSAMENTE")
        print("=" * 70)

        print("\n📊 Resumen:")
        print("  ✓ Textos genéricos (ACC-08): OK")
        print("  ✓ Textos ambiguos (ACC-07): OK")
        print("  ✓ Textos no descriptivos (ACC-09): OK")
        print("  ✓ Textos muy cortos: OK")
        print("  ✓ Siglas sin explicar: OK")
        print("  ✓ Textos claros (no problemáticos): OK")
        print("  ✓ Casos especiales (vacío): OK")
        print("  ✓ Casos reales de sitios .gob.bo: OK")
        print("  ✓ Análisis múltiple: OK")
        print("  ✓ Scores de confianza: OK")

        return True

    except Exception as e:
        print("\n" + "=" * 70)
        print("❌ TESTS FALLARON")
        print("=" * 70)
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)
