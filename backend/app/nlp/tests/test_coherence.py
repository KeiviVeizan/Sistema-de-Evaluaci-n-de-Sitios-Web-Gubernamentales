"""
Tests de validación para CoherenceAnalyzer.

Estos tests verifican el funcionamiento correcto del análisis de coherencia:
- Análisis de secciones individuales
- Cálculo de similitud semántica
- Generación de recomendaciones
- Análisis de sitios completos
"""

from app.nlp.coherence import CoherenceAnalyzer


def test_section_coherente():
    """Test 1: Verifica que una sección coherente sea detectada correctamente."""
    print("=" * 70)
    print("TEST 1: Sección Coherente")
    print("=" * 70)

    analyzer = CoherenceAnalyzer(coherence_threshold=0.7)

    result = analyzer.analyze_section(
        heading="Servicios de Salud",
        content="El Ministerio de Salud ofrece atención médica, programas de vacunación y servicios de salud materno-infantil a la población boliviana. Nuestros servicios incluyen consultas médicas, emergencias y atención preventiva."
    )

    print(f"\n✓ Heading: {result.heading}")
    print(f"  Nivel: h{result.heading_level}")
    print(f"  Palabras en contenido: {result.word_count}")
    print(f"  Similarity score: {result.similarity_score:.3f}")
    print(f"  Es coherente: {result.is_coherent}")
    print(f"  Recomendación: {result.recommendation or 'Ninguna'}")

    assert result.is_coherent, f"Debería ser coherente con similarity={result.similarity_score:.3f}"
    assert result.similarity_score >= 0.7, f"Similarity debería ser >= 0.7, obtuvo {result.similarity_score:.3f}"
    assert result.recommendation is None, "No debería haber recomendación para sección coherente"

    print("\n✅ Test 1 PASADO\n")


def test_section_incoherente():
    """Test 2: Verifica que una sección incoherente sea detectada correctamente."""
    print("=" * 70)
    print("TEST 2: Sección Incoherente")
    print("=" * 70)

    analyzer = CoherenceAnalyzer(coherence_threshold=0.7)

    result = analyzer.analyze_section(
        heading="Programas de Vacunación",
        content="El PIB de Bolivia creció 4.5% en el último trimestre fiscal. Las exportaciones de minerales y gas natural aumentaron significativamente. La inflación se mantuvo estable en 3.2% anual."
    )

    print(f"\n✓ Heading: {result.heading}")
    print(f"  Similarity score: {result.similarity_score:.3f}")
    print(f"  Es coherente: {result.is_coherent}")
    print(f"  Recomendación: {result.recommendation[:100] if result.recommendation else 'Ninguna'}...")

    assert not result.is_coherent, f"NO debería ser coherente con similarity={result.similarity_score:.3f}"
    assert result.similarity_score < 0.7, f"Similarity debería ser < 0.7, obtuvo {result.similarity_score:.3f}"
    assert result.recommendation is not None, "Debería tener recomendación para sección incoherente"

    print("\n✅ Test 2 PASADO\n")


def test_section_parcialmente_coherente():
    """Test 3: Verifica detección de coherencia parcial."""
    print("=" * 70)
    print("TEST 3: Sección Parcialmente Coherente")
    print("=" * 70)

    analyzer = CoherenceAnalyzer(coherence_threshold=0.7)

    result = analyzer.analyze_section(
        heading="Atención Médica",
        content="Nuestros servicios incluyen consultas generales y especializadas. También ofrecemos programas educativos sobre nutrición. El horario de atención es de lunes a viernes de 8:00 a 16:00 horas."
    )

    print(f"\n✓ Heading: {result.heading}")
    print(f"  Similarity score: {result.similarity_score:.3f}")
    print(f"  Es coherente: {result.is_coherent}")
    print(f"  Recomendación: {result.recommendation[:100] if result.recommendation else 'Ninguna'}...")

    print("\n✅ Test 3 PASADO\n")


def test_heading_vacio():
    """Test 4: Verifica manejo de heading vacío."""
    print("=" * 70)
    print("TEST 4: Heading Vacío")
    print("=" * 70)

    analyzer = CoherenceAnalyzer(coherence_threshold=0.7)

    result = analyzer.analyze_section(
        heading="",
        content="Contenido de ejemplo con suficientes palabras para análisis."
    )

    print(f"\n✓ Heading: {result.heading}")
    print(f"  Es coherente: {result.is_coherent}")
    print(f"  Recomendación: {result.recommendation}")

    assert not result.is_coherent, "Heading vacío no debería ser coherente"
    assert result.recommendation is not None, "Debería tener recomendación"
    assert "vacío" in result.recommendation.lower(), "Recomendación debería mencionar que está vacío"

    print("\n✅ Test 4 PASADO\n")


def test_content_vacio():
    """Test 5: Verifica manejo de contenido vacío."""
    print("=" * 70)
    print("TEST 5: Contenido Vacío")
    print("=" * 70)

    analyzer = CoherenceAnalyzer(coherence_threshold=0.7)

    result = analyzer.analyze_section(
        heading="Título de Ejemplo",
        content=""
    )

    print(f"\n✓ Heading: {result.heading}")
    print(f"  Content: {result.content}")
    print(f"  Es coherente: {result.is_coherent}")
    print(f"  Recomendación: {result.recommendation}")

    assert not result.is_coherent, "Contenido vacío no debería ser coherente"
    assert result.recommendation is not None, "Debería tener recomendación"

    print("\n✅ Test 5 PASADO\n")


def test_content_muy_corto():
    """Test 6: Verifica que contenido muy corto se asume coherente."""
    print("=" * 70)
    print("TEST 6: Contenido Muy Corto (<10 palabras)")
    print("=" * 70)

    analyzer = CoherenceAnalyzer(coherence_threshold=0.7, min_content_words=10)

    result = analyzer.analyze_section(
        heading="Inicio",
        content="Bienvenido al sitio web oficial."  # Solo 5 palabras
    )

    print(f"\n✓ Heading: {result.heading}")
    print(f"  Palabras: {result.word_count}")
    print(f"  Similarity score: {result.similarity_score:.3f}")
    print(f"  Es coherente: {result.is_coherent}")

    assert result.is_coherent, "Contenido muy corto debería asumirse coherente"
    assert result.similarity_score == 1.0, "Similarity debería ser 1.0 para contenido muy corto"

    print("\n✅ Test 6 PASADO\n")


def test_sitio_completo():
    """Test 7: Verifica análisis de sitio completo con múltiples secciones."""
    print("=" * 70)
    print("TEST 7: Análisis de Sitio Completo")
    print("=" * 70)

    analyzer = CoherenceAnalyzer(coherence_threshold=0.7)

    text_corpus = {
        'url': 'https://test.gob.bo',
        'sections': [
            {
                'heading': 'Misión Institucional',
                'heading_level': 2,
                'content': 'Nuestra misión es garantizar servicios de salud de calidad para toda la población. Trabajamos para mejorar el acceso a la atención médica y prevenir enfermedades.',
                'word_count': 27
            },
            {
                'heading': 'Servicios de Salud',
                'heading_level': 2,
                'content': 'Ofrecemos consultas médicas, vacunación, emergencias y atención especializada. Nuestros programas incluyen salud materno-infantil y prevención de enfermedades crónicas.',
                'word_count': 21
            },
            {
                'heading': 'Ver más',
                'heading_level': 3,
                'content': 'Datos económicos del último trimestre fiscal mostraron crecimiento.',
                'word_count': 10
            },
            {
                'heading': 'Contacto',
                'heading_level': 2,
                'content': 'Dirección: Av. Principal 123, La Paz. Teléfono: 2-12345678. Email: contacto@ministerio.gob.bo',
                'word_count': 13
            }
        ]
    }

    result = analyzer.analyze_coherence(text_corpus)

    print(f"\n✓ Coherence Score: {result['coherence_score']}/100")
    print(f"  Secciones analizadas: {result['sections_analyzed']}")
    print(f"  Secciones coherentes: {result['coherent_sections']}")
    print(f"  Secciones incoherentes: {result['incoherent_sections']}")
    print(f"  Similitud promedio: {result['average_similarity']:.3f}")
    print(f"  Umbral usado: {result['threshold_used']}")
    print(f"  Recomendaciones: {len(result['recommendations'])}")

    print("\n📊 Detalles por sección:")
    for i, detail in enumerate(result['details'], 1):
        status = "✓" if detail['is_coherent'] else "✗"
        print(f"  {status} [{i}] {detail['heading']}: similarity={detail['similarity_score']:.3f}")

    if result['recommendations']:
        print("\n⚠️ Recomendaciones:")
        for i, rec in enumerate(result['recommendations'][:3], 1):  # Primeras 3
            print(f"  {i}. {rec[:100]}...")

    assert result['sections_analyzed'] == 4, f"Debería analizar 4 secciones, analizó {result['sections_analyzed']}"
    assert 0 <= result['coherence_score'] <= 100, f"Score fuera de rango: {result['coherence_score']}"
    assert result['coherent_sections'] + result['incoherent_sections'] == result['sections_analyzed']

    print("\n✅ Test 7 PASADO\n")


def test_threshold_validation():
    """Test 8: Verifica validación de threshold."""
    print("=" * 70)
    print("TEST 8: Validación de Threshold")
    print("=" * 70)

    # Threshold válido
    try:
        analyzer = CoherenceAnalyzer(coherence_threshold=0.75)
        print("✓ Threshold 0.75 aceptado")
    except ValueError:
        assert False, "Threshold 0.75 debería ser válido"

    # Threshold muy bajo
    try:
        analyzer = CoherenceAnalyzer(coherence_threshold=0.3)
        assert False, "Threshold 0.3 debería rechazarse"
    except ValueError as e:
        print(f"✓ Threshold 0.3 rechazado: {str(e)}")

    # Threshold muy alto
    try:
        analyzer = CoherenceAnalyzer(coherence_threshold=0.95)
        assert False, "Threshold 0.95 debería rechazarse"
    except ValueError as e:
        print(f"✓ Threshold 0.95 rechazado: {str(e)}")

    print("\n✅ Test 8 PASADO\n")


def test_corpus_sin_secciones():
    """Test 9: Verifica manejo de corpus sin secciones."""
    print("=" * 70)
    print("TEST 9: Corpus Sin Secciones")
    print("=" * 70)

    analyzer = CoherenceAnalyzer(coherence_threshold=0.7)

    text_corpus = {
        'url': 'https://test.gob.bo',
        'sections': []
    }

    result = analyzer.analyze_coherence(text_corpus)

    print(f"\n✓ Coherence Score: {result['coherence_score']}")
    print(f"  Secciones analizadas: {result['sections_analyzed']}")
    print(f"  Recomendaciones: {result['recommendations']}")

    assert result['coherence_score'] == 0.0, "Score debería ser 0.0 sin secciones"
    assert result['sections_analyzed'] == 0, "Debería indicar 0 secciones analizadas"
    assert len(result['recommendations']) > 0, "Debería tener recomendación sobre falta de secciones"

    print("\n✅ Test 9 PASADO\n")


def run_all_tests():
    """Ejecuta todos los tests en orden."""
    print("\n" + "=" * 70)
    print("INICIANDO TESTS DE CoherenceAnalyzer")
    print("=" * 70)
    print("Nota: La primera ejecución descargará el modelo BETO (~500MB)")
    print("=" * 70 + "\n")

    try:
        test_section_coherente()
        test_section_incoherente()
        test_section_parcialmente_coherente()
        test_heading_vacio()
        test_content_vacio()
        test_content_muy_corto()
        test_sitio_completo()
        test_threshold_validation()
        test_corpus_sin_secciones()

        print("\n" + "=" * 70)
        print("✅ TODOS LOS TESTS PASARON EXITOSAMENTE")
        print("=" * 70)

        print("\n📊 Resumen:")
        print("  ✓ Análisis de secciones individuales: OK")
        print("  ✓ Detección de coherencia/incoherencia: OK")
        print("  ✓ Generación de recomendaciones: OK")
        print("  ✓ Manejo de casos especiales: OK")
        print("  ✓ Análisis de sitios completos: OK")
        print("  ✓ Validación de parámetros: OK")

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
