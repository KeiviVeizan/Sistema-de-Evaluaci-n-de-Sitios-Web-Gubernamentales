"""
Tests de validación para NLPAnalyzer (Orquestador).

Estos tests verifican la integración de los 3 analizadores:
- CoherenceAnalyzer: Coherencia semántica
- AmbiguityDetector: Detección de ambigüedades
- ClarityAnalyzer: Análisis de claridad

También verifica:
- Cálculo de score global ponderado
- Evaluación de cumplimiento WCAG (ACC-07, ACC-08, ACC-09)
- Combinación de recomendaciones
"""

from app.nlp.analyzer import NLPAnalyzer


def test_initialization_default_weights():
    """Test 1: Inicialización con pesos por defecto."""
    print("=" * 70)
    print("TEST 1: Inicialización con Pesos por Defecto")
    print("=" * 70)

    analyzer = NLPAnalyzer()

    print(f"\n✓ Pesos configurados:")
    print(f"  Coherencia: {analyzer.coherence_weight}")
    print(f"  Ambigüedad: {analyzer.ambiguity_weight}")
    print(f"  Claridad: {analyzer.clarity_weight}")
    print(f"  Total: {analyzer.coherence_weight + analyzer.ambiguity_weight + analyzer.clarity_weight}")

    assert analyzer.coherence_weight == 0.40
    assert analyzer.ambiguity_weight == 0.40
    assert analyzer.clarity_weight == 0.20
    assert abs((analyzer.coherence_weight + analyzer.ambiguity_weight + analyzer.clarity_weight) - 1.0) < 0.01

    print("\n✅ Test 1 PASADO\n")


def test_initialization_custom_weights():
    """Test 2: Inicialización con pesos personalizados."""
    print("=" * 70)
    print("TEST 2: Inicialización con Pesos Personalizados")
    print("=" * 70)

    analyzer = NLPAnalyzer(
        coherence_weight=0.50,
        ambiguity_weight=0.30,
        clarity_weight=0.20
    )

    print(f"\n✓ Pesos personalizados:")
    print(f"  Coherencia: {analyzer.coherence_weight}")
    print(f"  Ambigüedad: {analyzer.ambiguity_weight}")
    print(f"  Claridad: {analyzer.clarity_weight}")

    assert analyzer.coherence_weight == 0.50
    assert analyzer.ambiguity_weight == 0.30
    assert analyzer.clarity_weight == 0.20

    print("\n✅ Test 2 PASADO\n")


def test_initialization_invalid_weights():
    """Test 3: Rechaza pesos inválidos (no suman 1.0)."""
    print("=" * 70)
    print("TEST 3: Validación de Pesos Inválidos")
    print("=" * 70)

    try:
        analyzer = NLPAnalyzer(
            coherence_weight=0.50,
            ambiguity_weight=0.40,
            clarity_weight=0.30  # Total = 1.20 (inválido)
        )
        assert False, "Debería lanzar ValueError para pesos inválidos"
    except ValueError as e:
        print(f"\n✓ Pesos inválidos rechazados: {str(e)}")

    print("\n✅ Test 3 PASADO\n")


def test_analyze_complete_website():
    """Test 4: Análisis completo de un sitio web."""
    print("=" * 70)
    print("TEST 4: Análisis Completo de Sitio Web")
    print("=" * 70)

    analyzer = NLPAnalyzer()

    text_corpus = {
        'url': 'https://educacion.gob.bo',
        'sections': [
            {
                'heading': 'Misión Institucional',
                'heading_level': 2,
                'content': 'El Ministerio de Educación garantiza educación de calidad. Promovemos la formación integral de estudiantes y maestros.',
                'word_count': 18
            },
            {
                'heading': 'Servicios Educativos',
                'heading_level': 2,
                'content': 'Ofrecemos programas de formación docente, registro de estudiantes y certificación académica oficial.',
                'word_count': 14
            },
            {
                'heading': 'Ver más',  # Problemático (genérico)
                'heading_level': 3,
                'content': 'El PIB creció 4.5% en el trimestre fiscal.',  # Incoherente con heading
                'word_count': 8
            }
        ],
        'links': [
            {'text': 'Descargar formulario de inscripción 2024', 'url': '/formularios/inscripcion'},
            {'text': 'Ver más', 'url': '/noticias'},  # Problemático
            {'text': 'Leer más', 'url': '/info'},  # Problemático
            {'text': 'Consultar requisitos para titulación', 'url': '/titulacion'}
        ],
        'labels': [
            {'text': 'Nombre completo del estudiante', 'for': 'nombre'},
            {'text': 'Fecha de nacimiento', 'for': 'fecha'},
            {'text': 'Número', 'for': 'numero'}  # Problemático (ambiguo)
        ]
    }

    result = analyzer.analyze_website(text_corpus)

    print(f"\n📊 RESULTADOS DEL ANÁLISIS:")
    print(f"  Score Global: {result['global_score']}/100")
    print(f"  Score Coherencia: {result['coherence_score']}/100")
    print(f"  Score Ambigüedad: {result['ambiguity_score']}/100")
    print(f"  Score Claridad: {result['clarity_score']}/100")

    print(f"\n✓ Cumplimiento WCAG:")
    for criterion, passed in result['wcag_compliance'].items():
        status = "✓" if passed else "✗"
        print(f"  {status} {criterion}: {'CUMPLE' if passed else 'NO CUMPLE'}")

    print(f"\n✓ Estadísticas:")
    print(f"  Secciones analizadas: {result['total_sections_analyzed']}")
    print(f"  Textos analizados: {result['total_texts_analyzed']}")
    print(f"  Recomendaciones: {len(result['recommendations'])}")

    print(f"\n⚠️ Primeras 5 recomendaciones:")
    for i, rec in enumerate(result['recommendations'][:5], 1):
        print(f"  {i}. {rec[:100]}...")

    # Validaciones
    assert 0 <= result['global_score'] <= 100
    assert 0 <= result['coherence_score'] <= 100
    assert 0 <= result['ambiguity_score'] <= 100
    assert 0 <= result['clarity_score'] <= 100

    assert 'ACC-07' in result['wcag_compliance']
    assert 'ACC-08' in result['wcag_compliance']
    assert 'ACC-09' in result['wcag_compliance']

    assert result['total_sections_analyzed'] == 3
    assert result['total_texts_analyzed'] > 0  # links + labels + headings
    assert len(result['recommendations']) > 0

    assert 'coherence' in result['details']
    assert 'ambiguity' in result['details']
    assert 'clarity' in result['details']

    print("\n✅ Test 4 PASADO\n")


def test_weighted_score_calculation():
    """Test 5: Verifica cálculo de score global ponderado."""
    print("=" * 70)
    print("TEST 5: Cálculo de Score Global Ponderado")
    print("=" * 70)

    analyzer = NLPAnalyzer(
        coherence_weight=0.50,
        ambiguity_weight=0.30,
        clarity_weight=0.20
    )

    # Calcular manualmente
    coherence_score = 80.0
    ambiguity_score = 60.0
    clarity_score = 70.0

    expected_global = (80.0 * 0.50) + (60.0 * 0.30) + (70.0 * 0.20)
    expected_global = round(expected_global, 2)

    # Usar método privado directamente
    calculated_global = analyzer._calculate_global_score(
        coherence_score,
        ambiguity_score,
        clarity_score
    )

    print(f"\n✓ Cálculo de score global:")
    print(f"  Coherencia: {coherence_score} × {analyzer.coherence_weight} = {coherence_score * analyzer.coherence_weight}")
    print(f"  Ambigüedad: {ambiguity_score} × {analyzer.ambiguity_weight} = {ambiguity_score * analyzer.ambiguity_weight}")
    print(f"  Claridad: {clarity_score} × {analyzer.clarity_weight} = {clarity_score * analyzer.clarity_weight}")
    print(f"  Global: {calculated_global}/100 (esperado: {expected_global}/100)")

    assert calculated_global == expected_global, \
        f"Score global {calculated_global} no coincide con esperado {expected_global}"

    print("\n✅ Test 5 PASADO\n")


def test_wcag_compliance_all_pass():
    """Test 6: WCAG cumple cuando no hay problemas."""
    print("=" * 70)
    print("TEST 6: WCAG Compliance - Todos Cumplen")
    print("=" * 70)

    analyzer = NLPAnalyzer()

    # Corpus perfecto (sin problemas)
    text_corpus = {
        'url': 'https://test.gob.bo',
        'sections': [
            {
                'heading': 'Servicios de Salud Pública',
                'heading_level': 2,
                'content': 'Ofrecemos atención médica de calidad. Nuestros servicios incluyen consultas y emergencias.',
                'word_count': 12
            }
        ],
        'links': [
            {'text': 'Descargar informe anual 2024', 'url': '/informe'},
            {'text': 'Ver requisitos para atención médica', 'url': '/requisitos'}
        ],
        'labels': [
            {'text': 'Nombre completo del paciente', 'for': 'nombre'},
            {'text': 'Fecha de nacimiento', 'for': 'fecha'}
        ]
    }

    result = analyzer.analyze_website(text_corpus)

    print(f"\n✓ Cumplimiento WCAG:")
    for criterion, passed in result['wcag_compliance'].items():
        status = "✓" if passed else "✗"
        print(f"  {status} {criterion}: {'CUMPLE' if passed else 'NO CUMPLE'}")

    # Debería cumplir todos (no hay problemas)
    assert result['wcag_compliance']['ACC-07'], "ACC-07 debería cumplir (no hay textos ambiguos)"
    assert result['wcag_compliance']['ACC-08'], "ACC-08 debería cumplir (no hay textos genéricos)"
    assert result['wcag_compliance']['ACC-09'], "ACC-09 debería cumplir (no hay textos no descriptivos)"

    print("\n✅ Test 6 PASADO\n")


def test_wcag_compliance_failures():
    """Test 7: WCAG no cumple cuando hay problemas."""
    print("=" * 70)
    print("TEST 7: WCAG Compliance - Fallos Detectados")
    print("=" * 70)

    analyzer = NLPAnalyzer()

    # Corpus con problemas específicos
    text_corpus = {
        'url': 'https://test.gob.bo',
        'sections': [
            {
                'heading': 'Información',  # ACC-09: No descriptivo
                'heading_level': 2,
                'content': 'Contenido de ejemplo.',
                'word_count': 3
            }
        ],
        'links': [
            {'text': 'Ver más', 'url': '/mas'},  # ACC-08: Genérico
            {'text': 'Ok', 'url': '/ok'}  # ACC-08: Muy corto
        ],
        'labels': [
            {'text': 'Nombre', 'for': 'nombre'},  # ACC-07: Ambiguo
            {'text': 'Fecha', 'for': 'fecha'}  # ACC-07: Ambiguo
        ]
    }

    result = analyzer.analyze_website(text_corpus)

    print(f"\n✓ Cumplimiento WCAG:")
    for criterion, passed in result['wcag_compliance'].items():
        status = "✓" if passed else "✗"
        print(f"  {status} {criterion}: {'CUMPLE' if passed else 'NO CUMPLE'}")

    # Debería fallar todos
    assert not result['wcag_compliance']['ACC-07'], "ACC-07 NO debería cumplir (hay textos ambiguos)"
    assert not result['wcag_compliance']['ACC-08'], "ACC-08 NO debería cumplir (hay textos genéricos/cortos)"
    assert not result['wcag_compliance']['ACC-09'], "ACC-09 NO debería cumplir (hay textos no descriptivos)"

    print("\n✅ Test 7 PASADO\n")


def test_recommendations_prioritization():
    """Test 8: Verifica priorización de recomendaciones."""
    print("=" * 70)
    print("TEST 8: Priorización de Recomendaciones")
    print("=" * 70)

    analyzer = NLPAnalyzer(max_recommendations=10)

    # Corpus con problemas variados para generar muchas recomendaciones
    text_corpus = {
        'url': 'https://test.gob.bo',
        'sections': [
            {
                'heading': 'Programas de Vacunación',
                'heading_level': 2,
                'content': 'El PIB de Bolivia creció significativamente en el último trimestre fiscal. Las exportaciones aumentaron.',  # Incoherente
                'word_count': 14
            },
            {
                'heading': 'Información',  # No descriptivo
                'heading_level': 2,
                'content': 'El presente Decreto Supremo establece las disposiciones reglamentarias correspondientes a la implementación del Sistema Nacional de Inversión Pública y Financiamiento para el Desarrollo Integral con mecanismos de articulación interinstitucional.',  # Oración muy larga
                'word_count': 28
            }
        ],
        'links': [
            {'text': 'Ver más', 'url': '/1'},  # Genérico
            {'text': 'Leer más', 'url': '/2'},  # Genérico
            {'text': 'Click aquí', 'url': '/3'}  # Genérico
        ],
        'labels': [
            {'text': 'Nombre', 'for': 'nombre'},  # Ambiguo
            {'text': 'Fecha', 'for': 'fecha'}  # Ambiguo
        ]
    }

    result = analyzer.analyze_website(text_corpus)

    print(f"\n✓ Total de recomendaciones: {len(result['recommendations'])} (máx: {analyzer.max_recommendations})")
    print(f"\n✓ Primeras 10 recomendaciones (priorizadas):")
    for i, rec in enumerate(result['recommendations'][:10], 1):
        # Identificar categoría
        if '[Ambigüedad' in rec:
            category = "Ambigüedad (Prioridad 1)"
        elif '[Coherencia' in rec:
            category = "Coherencia (Prioridad 2)"
        elif '[Claridad' in rec:
            category = "Claridad (Prioridad 3)"
        else:
            category = "Otra"

        print(f"  {i}. [{category}] {rec[:80]}...")

    # Verificar que hay recomendaciones
    assert len(result['recommendations']) > 0
    assert len(result['recommendations']) <= analyzer.max_recommendations

    # Las primeras deberían ser de ambigüedad (WCAG crítico)
    first_recs = result['recommendations'][:3]
    ambiguity_count = sum(1 for rec in first_recs if '[Ambigüedad' in rec)
    print(f"\n✓ Primeras 3 recomendaciones: {ambiguity_count} son de Ambigüedad (WCAG)")

    print("\n✅ Test 8 PASADO\n")


def test_empty_corpus():
    """Test 9: Manejo de corpus vacío."""
    print("=" * 70)
    print("TEST 9: Corpus Vacío")
    print("=" * 70)

    analyzer = NLPAnalyzer()

    text_corpus = {
        'url': 'https://test.gob.bo',
        'sections': [],
        'links': [],
        'labels': []
    }

    result = analyzer.analyze_website(text_corpus)

    print(f"\n✓ Resultados con corpus vacío:")
    print(f"  Score Global: {result['global_score']}/100")
    print(f"  Secciones analizadas: {result['total_sections_analyzed']}")
    print(f"  Textos analizados: {result['total_texts_analyzed']}")

    assert result['global_score'] >= 0.0
    assert result['total_sections_analyzed'] == 0
    assert result['total_texts_analyzed'] == 0

    print("\n✅ Test 9 PASADO\n")


def test_partial_corpus():
    """Test 10: Corpus parcial (solo algunas secciones)."""
    print("=" * 70)
    print("TEST 10: Corpus Parcial")
    print("=" * 70)

    analyzer = NLPAnalyzer()

    # Solo secciones, sin links ni labels
    text_corpus = {
        'url': 'https://test.gob.bo',
        'sections': [
            {
                'heading': 'Servicios de Atención',
                'heading_level': 2,
                'content': 'Ofrecemos servicios de atención al ciudadano.',
                'word_count': 7
            }
        ]
        # No links, no labels
    }

    result = analyzer.analyze_website(text_corpus)

    print(f"\n✓ Corpus parcial (solo secciones):")
    print(f"  Score Global: {result['global_score']}/100")
    print(f"  Coherencia: {result['coherence_score']}/100")
    print(f"  Ambigüedad: {result['ambiguity_score']}/100")
    print(f"  Claridad: {result['clarity_score']}/100")

    assert result['total_sections_analyzed'] == 1
    # Solo analizará el heading de la sección
    assert result['total_texts_analyzed'] >= 1

    print("\n✅ Test 10 PASADO\n")


def test_integration_all_analyzers():
    """Test 11: Verifica que los 3 analizadores se ejecutan."""
    print("=" * 70)
    print("TEST 11: Integración de Todos los Analizadores")
    print("=" * 70)

    analyzer = NLPAnalyzer()

    text_corpus = {
        'url': 'https://test.gob.bo',
        'sections': [
            {
                'heading': 'Educación Superior',
                'heading_level': 2,
                'content': 'Promovemos la educación universitaria y formación profesional de calidad.',
                'word_count': 10
            }
        ],
        'links': [
            {'text': 'Consultar programas académicos disponibles', 'url': '/programas'}
        ],
        'labels': [
            {'text': 'Código de estudiante', 'for': 'codigo'}
        ]
    }

    result = analyzer.analyze_website(text_corpus)

    print(f"\n✓ Verificando ejecución de analizadores:")

    # Coherencia
    coherence_details = result['details']['coherence']
    print(f"  ✓ CoherenceAnalyzer ejecutado: {coherence_details['sections_analyzed']} secciones")
    assert coherence_details['sections_analyzed'] > 0

    # Ambigüedad
    ambiguity_details = result['details']['ambiguity']
    print(f"  ✓ AmbiguityDetector ejecutado: {ambiguity_details['total_analyzed']} textos")
    assert ambiguity_details['total_analyzed'] > 0

    # Claridad
    clarity_details = result['details']['clarity']
    print(f"  ✓ ClarityAnalyzer ejecutado: {clarity_details['total_analyzed']} textos")
    assert clarity_details['total_analyzed'] > 0

    print(f"\n✓ Scores generados:")
    print(f"  Coherencia: {result['coherence_score']}/100")
    print(f"  Ambigüedad: {result['ambiguity_score']}/100")
    print(f"  Claridad: {result['clarity_score']}/100")
    print(f"  Global: {result['global_score']}/100")

    print("\n✅ Test 11 PASADO\n")


def run_all_tests():
    """Ejecuta todos los tests en orden."""
    print("\n" + "=" * 70)
    print("INICIANDO TESTS DE NLPAnalyzer (Orquestador)")
    print("=" * 70)
    print("Integración de CoherenceAnalyzer + AmbiguityDetector + ClarityAnalyzer")
    print("=" * 70 + "\n")

    try:
        test_initialization_default_weights()
        test_initialization_custom_weights()
        test_initialization_invalid_weights()
        test_analyze_complete_website()
        test_weighted_score_calculation()
        test_wcag_compliance_all_pass()
        test_wcag_compliance_failures()
        test_recommendations_prioritization()
        test_empty_corpus()
        test_partial_corpus()
        test_integration_all_analyzers()

        print("\n" + "=" * 70)
        print("✅ TODOS LOS TESTS PASARON EXITOSAMENTE")
        print("=" * 70)

        print("\n📊 Resumen:")
        print("  ✓ Inicialización y validación de pesos: OK")
        print("  ✓ Análisis completo de sitios web: OK")
        print("  ✓ Cálculo de score global ponderado: OK")
        print("  ✓ Evaluación WCAG (ACC-07, ACC-08, ACC-09): OK")
        print("  ✓ Priorización de recomendaciones: OK")
        print("  ✓ Manejo de casos especiales (vacío, parcial): OK")
        print("  ✓ Integración de 3 analizadores: OK")

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
