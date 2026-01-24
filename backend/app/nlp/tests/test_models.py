"""
Tests de validación para BETOModelManager.

Estos tests verifican el funcionamiento correcto del modelo BETO:
- Patrón Singleton
- Generación de embeddings
- Cálculo de similitud semántica
"""

from app.nlp.models import beto_manager, BETOModelManager


def test_singleton():
    """Verifica que BETOModelManager implementa correctamente el patrón Singleton."""
    manager1 = BETOModelManager()
    manager2 = BETOModelManager()
    manager3 = beto_manager

    assert manager1 is manager2, "Singleton no funciona: manager1 y manager2 son diferentes instancias"
    assert manager1 is manager3, "Singleton no funciona: manager1 y beto_manager son diferentes instancias"
    assert manager2 is manager3, "Singleton no funciona: manager2 y beto_manager son diferentes instancias"

    print("✓ Test Singleton PASADO")
    print(f"  - Todas las instancias apuntan al mismo objeto: {id(manager1)}")


def test_embedding_generation():
    """Verifica que se pueden generar embeddings correctamente."""
    text = "Servicios de Salud en Bolivia"

    print(f"\n✓ Generando embedding para: '{text}'")
    print("  (Esto descargará el modelo si es la primera vez - ~500MB, puede tardar 1-2 min)")

    emb = beto_manager.encode(text)

    assert emb.shape == (768,), f"Shape incorrecto: esperado (768,), obtenido {emb.shape}"
    assert emb.dtype == 'float32' or emb.dtype == 'float64', f"Tipo incorrecto: {emb.dtype}"

    print(f"✓ Test Embedding PASADO")
    print(f"  - Shape: {emb.shape}")
    print(f"  - Dtype: {emb.dtype}")
    print(f"  - Primeros 5 valores: {emb[:5]}")
    print(f"  - Norma L2: {((emb ** 2).sum()) ** 0.5:.4f}")


def test_similarity_computation():
    """Verifica el cálculo de similitud semántica entre textos."""
    text1 = "Servicios de Salud"
    text2 = "El ministerio ofrece atención médica y programas de vacunación"
    text3 = "Trámites de pasaporte y documentos de identidad"

    print(f"\n✓ Calculando similitudes:")
    print(f"  Texto 1: '{text1}'")
    print(f"  Texto 2: '{text2}'")
    print(f"  Texto 3: '{text3}'")

    # Similitud alta (textos relacionados)
    sim_alta = beto_manager.compute_similarity(text1, text2)
    assert 0 <= sim_alta <= 1, f"Similitud fuera de rango [0,1]: {sim_alta}"
    print(f"\n  Similitud Texto1 ↔ Texto2: {sim_alta:.4f} (esperado: alta)")

    # Similitud baja (textos no relacionados)
    sim_baja = beto_manager.compute_similarity(text1, text3)
    assert 0 <= sim_baja <= 1, f"Similitud fuera de rango [0,1]: {sim_baja}"
    print(f"  Similitud Texto1 ↔ Texto3: {sim_baja:.4f} (esperado: baja)")

    # Similitud perfecta (mismo texto)
    sim_perfecta = beto_manager.compute_similarity(text1, text1)
    assert 0.99 <= sim_perfecta <= 1.0, f"Similitud de mismo texto debería ser ~1.0: {sim_perfecta}"
    print(f"  Similitud Texto1 ↔ Texto1: {sim_perfecta:.4f} (esperado: ~1.0)")

    # Verificar que textos relacionados tienen mayor similitud
    assert sim_alta > sim_baja, (
        f"Textos relacionados deberían tener mayor similitud: "
        f"sim_alta={sim_alta:.4f} vs sim_baja={sim_baja:.4f}"
    )

    print(f"\n✓ Test Similitud PASADO")
    print(f"  - Todas las similitudes están en rango [0, 1]")
    print(f"  - Similitud(relacionados) > Similitud(no relacionados): {sim_alta:.4f} > {sim_baja:.4f}")


def test_error_handling():
    """Verifica el manejo de errores."""
    print("\n✓ Probando manejo de errores:")

    # Test 1: Texto vacío
    try:
        beto_manager.encode("")
        assert False, "Debería lanzar ValueError para texto vacío"
    except ValueError as e:
        print(f"  ✓ ValueError para texto vacío: {str(e)}")

    # Test 2: Texto solo espacios
    try:
        beto_manager.encode("   ")
        assert False, "Debería lanzar ValueError para texto solo espacios"
    except ValueError as e:
        print(f"  ✓ ValueError para texto solo espacios: {str(e)}")

    # Test 3: Métrica inválida
    try:
        beto_manager.compute_similarity("Texto 1", "Texto 2", metric="invalid")
        assert False, "Debería lanzar ValueError para métrica inválida"
    except ValueError as e:
        print(f"  ✓ ValueError para métrica inválida: {str(e)}")

    print("\n✓ Test Manejo de Errores PASADO")


def test_lazy_loading():
    """Verifica que el modelo se carga solo cuando se necesita (lazy loading)."""
    print("\n✓ Probando lazy loading:")

    # Crear nueva instancia (pero es singleton, así que es la misma)
    manager = BETOModelManager()

    # Si ya se cargó en tests anteriores, esto será True
    is_loaded = manager._is_loaded
    print(f"  - Modelo ya cargado: {is_loaded}")

    if not is_loaded:
        print("  - Modelo NO cargado en __init__ (lazy loading correcto)")
        # Cargar explícitamente
        manager.load_model()
        assert manager._is_loaded, "Modelo debería estar cargado después de load_model()"
        print("  - Modelo cargado exitosamente con load_model()")
    else:
        print("  - Modelo ya estaba cargado de tests anteriores")
        # Intentar cargar de nuevo (debería ser idempotente)
        manager.load_model()
        assert manager._is_loaded, "Modelo debería seguir cargado"
        print("  - load_model() es idempotente (no recarga si ya está cargado)")

    print("\n✓ Test Lazy Loading PASADO")


def run_all_tests():
    """Ejecuta todos los tests en orden."""
    print("=" * 70)
    print("INICIANDO TESTS DE BETOModelManager")
    print("=" * 70)

    try:
        test_singleton()
        test_embedding_generation()
        test_similarity_computation()
        test_error_handling()
        test_lazy_loading()

        print("\n" + "=" * 70)
        print("✅ TODOS LOS TESTS PASARON EXITOSAMENTE")
        print("=" * 70)

        print("\n📊 Resumen:")
        print("  ✓ Patrón Singleton: OK")
        print("  ✓ Generación de embeddings [768]: OK")
        print("  ✓ Cálculo de similitud coseno: OK")
        print("  ✓ Manejo de errores: OK")
        print("  ✓ Lazy loading: OK")

        return True

    except Exception as e:
        print("\n" + "=" * 70)
        print(f"❌ TESTS FALLARON")
        print("=" * 70)
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)
