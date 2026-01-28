"""
Test de Integracion End-to-End del Motor de Evaluacion

Este script prueba el flujo completo:
1. Crawler extrae contenido de un sitio real
2. Los 4 evaluadores procesan el contenido
3. Se calcula el score final ponderado (30-30-30-10)
"""
import sys
import os
import logging

# Configurar path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(message)s'
)
logger = logging.getLogger(__name__)


def test_evaluacion_completa():
    """Test end-to-end con aduana.gob.bo"""
    print("=" * 80)
    print("TEST DE INTEGRACION END-TO-END")
    print("Motor de Evaluacion GOB.BO")
    print("=" * 80)

    # Importar motor de evaluacion
    from app.evaluator.evaluation_engine import EvaluationEngine

    # Crear motor (sin BD)
    print("\n[1] Inicializando motor de evaluacion...")
    engine = EvaluationEngine()
    print("    OK - Motor inicializado con 4 evaluadores reales")

    # Evaluar sitio
    url = "https://www.aduana.gob.bo"
    print(f"\n[2] Evaluando: {url}")
    print("    Crawleando sitio (puede tomar 30-60 segundos)...")

    try:
        resultado = engine.evaluate_url(url)
    except Exception as e:
        print(f"\n    ERROR: {e}")
        return False

    # Mostrar resultados
    print("\n" + "=" * 80)
    print("RESULTADOS DE LA EVALUACION")
    print("=" * 80)

    scores = resultado['scores']

    # Tabla de scores por dimension
    print(f"\n{'Dimension':<20} {'Score':<15} {'Criterios':<20}")
    print("-" * 55)

    for dimension in ['accesibilidad', 'usabilidad', 'semantica', 'soberania']:
        dim_data = scores.get(dimension, {})
        percentage = dim_data.get('percentage', 0)
        passed = dim_data.get('passed', 0)
        failed = dim_data.get('failed', 0)
        partial = dim_data.get('partial', 0)
        total = passed + failed + partial

        peso = {'accesibilidad': 30, 'usabilidad': 30, 'semantica': 30, 'soberania': 10}[dimension]
        print(f"{dimension.capitalize():<20} {percentage:>5.1f}% (x{peso}%)   "
              f"P:{passed} F:{failed} Partial:{partial}")

    print("-" * 55)
    print(f"{'SCORE TOTAL':<20} {scores['total']:>5.1f}%")
    print("=" * 80)

    # Resumen de criterios
    summary = resultado['summary']
    print(f"\nRESUMEN DE CRITERIOS:")
    print(f"  Total criterios: {summary['total_criteria']}")
    print(f"  Aprobados (pass): {summary['passed']}")
    print(f"  Reprobados (fail): {summary['failed']}")
    print(f"  Parciales: {summary['partial']}")
    print(f"  No aplicables: {summary['not_applicable']}")

    # Mostrar criterios fallidos
    print("\n" + "=" * 80)
    print("CRITERIOS REPROBADOS (requieren atencion)")
    print("=" * 80)

    failed_criteria = [c for c in resultado['criteria_results'] if c['status'] == 'fail']

    if not failed_criteria:
        print("  Ninguno - Todos los criterios estan aprobados o parciales")
    else:
        for c in failed_criteria[:10]:  # Mostrar primeros 10
            print(f"\n  {c['criteria_id']}: {c['criteria_name']}")
            print(f"    Score: {c['score']}/{c['max_score']}")
            print(f"    Dimension: {c['dimension']}")
            if 'message' in c.get('details', {}):
                print(f"    Mensaje: {c['details']['message']}")

    # Verificaciones
    print("\n" + "=" * 80)
    print("VERIFICACIONES")
    print("=" * 80)

    checks = []

    # 1. Score total en rango valido
    if 0 <= scores['total'] <= 100:
        checks.append(("Score total en rango [0-100]", True, f"{scores['total']:.1f}%"))
    else:
        checks.append(("Score total en rango [0-100]", False, f"{scores['total']:.1f}%"))

    # 2. Todas las dimensiones tienen scores
    all_dims_have_scores = all(
        dimension in scores and 'percentage' in scores[dimension]
        for dimension in ['accesibilidad', 'usabilidad', 'semantica', 'soberania']
    )
    checks.append(("Todas las dimensiones evaluadas", all_dims_have_scores, "4/4"))

    # 3. Se evaluaron criterios
    criteria_count = summary['total_criteria']
    checks.append(("Criterios evaluados", criteria_count > 0, f"{criteria_count} criterios"))

    # 4. Score total es promedio ponderado correcto
    expected_total = (
        scores['accesibilidad'].get('percentage', 0) * 0.30 +
        scores['usabilidad'].get('percentage', 0) * 0.30 +
        scores['semantica'].get('percentage', 0) * 0.30 +
        scores['soberania'].get('percentage', 0) * 0.10
    )
    score_match = abs(scores['total'] - expected_total) < 0.1
    checks.append(("Score ponderado correcto", score_match, f"{expected_total:.1f}% esperado"))

    # Mostrar verificaciones
    all_passed = True
    for check_name, passed, value in checks:
        status = "OK" if passed else "FAIL"
        print(f"  [{status}] {check_name}: {value}")
        if not passed:
            all_passed = False

    print("\n" + "=" * 80)
    if all_passed:
        print("RESULTADO: TODAS LAS VERIFICACIONES PASARON")
    else:
        print("RESULTADO: ALGUNAS VERIFICACIONES FALLARON")
    print("=" * 80)

    return all_passed


def test_multiples_sitios():
    """Test con multiples sitios gubernamentales"""
    from app.evaluator.evaluation_engine import EvaluationEngine

    sitios = [
        "https://www.aduana.gob.bo",
        # Agregar mas sitios si es necesario
    ]

    print("\n" + "=" * 80)
    print("TEST DE MULTIPLES SITIOS")
    print("=" * 80)

    engine = EvaluationEngine()
    resultados = []

    for url in sitios:
        print(f"\n[Evaluando] {url}")
        try:
            resultado = engine.evaluate_url(url)
            resultados.append({
                'url': url,
                'score': resultado['scores']['total'],
                'status': 'OK'
            })
            print(f"    Score: {resultado['scores']['total']:.1f}%")
        except Exception as e:
            resultados.append({
                'url': url,
                'score': 0,
                'status': f'ERROR: {e}'
            })
            print(f"    ERROR: {e}")

    # Resumen
    print("\n" + "=" * 80)
    print("RESUMEN DE EVALUACIONES")
    print("=" * 80)

    for r in resultados:
        status_icon = "OK" if r['status'] == 'OK' else "ERR"
        print(f"  [{status_icon}] {r['url']}: {r['score']:.1f}%")

    return all(r['status'] == 'OK' for r in resultados)


if __name__ == "__main__":
    print("\n")
    print("#" * 80)
    print("#" + " " * 78 + "#")
    print("#" + "   GOB.BO EVALUATOR - TEST DE INTEGRACION END-TO-END".center(78) + "#")
    print("#" + " " * 78 + "#")
    print("#" * 80)
    print("\n")

    success = test_evaluacion_completa()

    print("\n")
    if success:
        print("=" * 80)
        print("EVALUACION END-TO-END COMPLETADA EXITOSAMENTE")
        print("El motor de evaluacion esta funcionando correctamente")
        print("con los 4 evaluadores REALES integrados.")
        print("=" * 80)
    else:
        print("=" * 80)
        print("HAY PROBLEMAS EN LA INTEGRACION")
        print("Revisar los errores anteriores.")
        print("=" * 80)
        sys.exit(1)
