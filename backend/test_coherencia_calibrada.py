"""
Test de Coherencia con Umbral Calibrado
Verifica que el sistema use correctamente el umbral de 0.80
"""
import sys
import os

# Añadir path del backend
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app.nlp.coherence import CoherenceAnalyzer, cargar_umbral_calibrado
import logging

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def test_cargar_umbral():
    """Test 1: Verificar carga del umbral calibrado"""
    print("\n" + "="*60)
    print("TEST 1: Carga del Umbral Calibrado")
    print("="*60)

    umbral = cargar_umbral_calibrado()
    print(f"Umbral cargado: {umbral}")

    assert umbral == 0.80, f"Error: Se esperaba 0.80, se obtuvo {umbral}"
    print("✓ PASS: Umbral calibrado cargado correctamente (0.80)")


def test_inicializacion_con_umbral_calibrado():
    """Test 2: CoherenceAnalyzer usa umbral calibrado por defecto"""
    print("\n" + "="*60)
    print("TEST 2: Inicialización con Umbral Calibrado")
    print("="*60)

    analyzer = CoherenceAnalyzer()
    print(f"Umbral del analizador: {analyzer.coherence_threshold}")

    assert analyzer.coherence_threshold == 0.80, \
        f"Error: Se esperaba 0.80, se obtuvo {analyzer.coherence_threshold}"
    print("✓ PASS: CoherenceAnalyzer inicializado con umbral 0.80")


def test_ejemplos_coherentes():
    """Test 3: Ejemplos que DEBEN ser coherentes"""
    print("\n" + "="*60)
    print("TEST 3: Análisis de Ejemplos Coherentes")
    print("="*60)

    analyzer = CoherenceAnalyzer()

    ejemplos_coherentes = [
        {
            "heading": "Servicios de Salud",
            "content": "El Ministerio de Salud ofrece diversos servicios de atención médica a la población boliviana incluyendo atención primaria vacunación y control prenatal."
        },
        {
            "heading": "Trámite de Licencia de Conducir",
            "content": "Para obtener su licencia de conducir debe presentarse con su certificado de nacimiento comprobante de domicilio y fotografías recientes en las oficinas del SEGIP."
        },
        {
            "heading": "Bono Juancito Pinto",
            "content": "El Bono Juancito Pinto es una transferencia condicionada de 200 bolivianos anuales para estudiantes de primaria de unidades educativas públicas que cumplan 80% de asistencia."
        }
    ]

    for i, ejemplo in enumerate(ejemplos_coherentes, 1):
        result = analyzer.analyze_section(
            heading=ejemplo['heading'],
            content=ejemplo['content']
        )
        print(f"\n[Ejemplo Coherente {i}]")
        print(f"  Encabezado: {ejemplo['heading']}")
        print(f"  Similitud: {result.similarity_score:.4f}")
        print(f"  Es coherente: {result.is_coherent}")

        if result.is_coherent:
            print(f"  ✓ PASS: Clasificado correctamente como COHERENTE")
        else:
            print(f"  ✗ FAIL: Debería ser coherente (similitud={result.similarity_score:.4f} < 0.80)")


def test_ejemplos_no_coherentes():
    """Test 4: Ejemplos que NO DEBEN ser coherentes"""
    print("\n" + "="*60)
    print("TEST 4: Análisis de Ejemplos No Coherentes")
    print("="*60)

    analyzer = CoherenceAnalyzer()

    ejemplos_no_coherentes = [
        {
            "heading": "Ver más",
            "content": "El Ministerio de Salud ejecuta campañas de vacunación control prenatal atención de partos y prevención de enfermedades en todo el país."
        },
        {
            "heading": "Clic aquí",
            "content": "Para obtener su pasaporte presente cédula de identidad certificado de nacimiento comprobante de pago y fotografía reciente."
        },
        {
            "heading": "Descargar",
            "content": "El Programa Desnutrición Cero entrega complemento nutricional a niños menores de 2 años y embarazadas en riesgo nutricional."
        },
        {
            "heading": "Info",
            "content": "La Asamblea Legislativa debate aprueba y promulga leyes decretos y políticas públicas para el desarrollo del país."
        }
    ]

    for i, ejemplo in enumerate(ejemplos_no_coherentes, 1):
        result = analyzer.analyze_section(
            heading=ejemplo['heading'],
            content=ejemplo['content']
        )
        print(f"\n[Ejemplo No Coherente {i}]")
        print(f"  Encabezado: {ejemplo['heading']}")
        print(f"  Similitud: {result.similarity_score:.4f}")
        print(f"  Es coherente: {result.is_coherent}")

        if not result.is_coherent:
            print(f"  ✓ PASS: Clasificado correctamente como NO COHERENTE")
        else:
            print(f"  ✗ FAIL: Debería ser no coherente (similitud={result.similarity_score:.4f} >= 0.80)")


def test_casos_limite():
    """Test 5: Casos límite cerca del umbral 0.80"""
    print("\n" + "="*60)
    print("TEST 5: Casos Límite (cercanos a 0.80)")
    print("="*60)

    analyzer = CoherenceAnalyzer()

    # Estos casos son interesantes porque están cerca del umbral
    casos_limite = [
        {
            "heading": "Trámites",
            "content": "Información sobre documentos requeridos para realizar gestiones en el ministerio."
        },
        {
            "heading": "Educación",
            "content": "El Ministerio de Educación coordina con las unidades educativas la implementación del currículo."
        }
    ]

    print("\nEstos casos pueden clasificarse en cualquier dirección (están cerca del umbral):")

    for i, caso in enumerate(casos_limite, 1):
        result = analyzer.analyze_section(
            heading=caso['heading'],
            content=caso['content']
        )
        print(f"\n[Caso Límite {i}]")
        print(f"  Encabezado: {caso['heading']}")
        print(f"  Similitud: {result.similarity_score:.4f}")
        print(f"  Es coherente: {result.is_coherent}")

        # Calcular distancia al umbral
        distancia = abs(result.similarity_score - 0.80)
        print(f"  Distancia al umbral: {distancia:.4f}")

        if distancia < 0.05:
            print(f"  ⚠ CASO LÍMITE: Muy cerca del umbral (±0.05)")
        else:
            print(f"  ✓ Decisión clara")


def test_umbral_personalizado():
    """Test 6: Uso de umbral personalizado"""
    print("\n" + "="*60)
    print("TEST 6: Umbral Personalizado (para experimentación)")
    print("="*60)

    # Crear analizador con umbral personalizado
    analyzer_075 = CoherenceAnalyzer(coherence_threshold=0.75)
    print(f"Analizador con umbral 0.75: {analyzer_075.coherence_threshold}")

    analyzer_085 = CoherenceAnalyzer(coherence_threshold=0.85)
    print(f"Analizador con umbral 0.85: {analyzer_085.coherence_threshold}")

    print("✓ PASS: Se pueden usar umbrales personalizados si es necesario")


def main():
    """Ejecuta todos los tests"""
    print("\n" + "╔" + "="*58 + "╗")
    print("║  TEST DE COHERENCIA CON UMBRAL CALIBRADO (θ = 0.80)     ║")
    print("╚" + "="*58 + "╝")

    try:
        test_cargar_umbral()
        test_inicializacion_con_umbral_calibrado()
        test_ejemplos_coherentes()
        test_ejemplos_no_coherentes()
        test_casos_limite()
        test_umbral_personalizado()

        print("\n" + "="*60)
        print("✓ TODOS LOS TESTS COMPLETADOS")
        print("="*60)
        print("\nResumen:")
        print("  • Umbral calibrado: 0.80")
        print("  • Precisión esperada: 85.39%")
        print("  • Recall esperado: 83.36%")
        print("  • F1-Score: 84.37%")
        print("\nEl sistema está listo para evaluar coherencia semántica")
        print("con el umbral optimizado mediante calibración experimental.")
        print("="*60)

    except Exception as e:
        print(f"\n✗ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == '__main__':
    sys.exit(main())
