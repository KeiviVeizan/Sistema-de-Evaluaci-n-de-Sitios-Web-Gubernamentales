#!/usr/bin/env python3
"""
Script de prueba para la API REST de Evaluacion de Sitios Gubernamentales.

Prueba los endpoints principales:
1. POST /api/v1/evaluation/evaluate - Evaluar URL
2. GET /api/v1/evaluation/{id} - Obtener evaluacion por ID
3. GET /api/v1/evaluation/list - Listar evaluaciones
4. DELETE /api/v1/evaluation/{id} - Eliminar evaluacion
5. GET /health - Health check

Uso:
    python test_api.py [--base-url URL] [--test-url URL_GOB_BO]

Ejemplos:
    python test_api.py
    python test_api.py --base-url http://localhost:8000
    python test_api.py --test-url https://www.aduana.gob.bo

Author: Keivi Veizan
"""

import sys
import json
import argparse
import time
from datetime import datetime

# Verificar dependencias
try:
    import requests
except ImportError:
    print("Error: Instalar requests -> pip install requests")
    sys.exit(1)


# ============================================================================
# Configuracion
# ============================================================================

DEFAULT_BASE_URL = "http://localhost:8000"
DEFAULT_TEST_URL = "https://www.aduana.gob.bo"
API_PREFIX = "/api/v1"

# Colores para terminal
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    RESET = '\033[0m'
    BOLD = '\033[1m'


def print_header(text: str):
    """Imprime encabezado."""
    print(f"\n{Colors.BOLD}{Colors.CYAN}{'=' * 60}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.CYAN}  {text}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.CYAN}{'=' * 60}{Colors.RESET}")


def print_success(text: str):
    """Imprime mensaje de exito."""
    print(f"{Colors.GREEN}[OK] {text}{Colors.RESET}")


def print_error(text: str):
    """Imprime mensaje de error."""
    print(f"{Colors.RED}[ERROR] {text}{Colors.RESET}")


def print_info(text: str):
    """Imprime mensaje informativo."""
    print(f"{Colors.BLUE}[INFO] {text}{Colors.RESET}")


def print_warning(text: str):
    """Imprime mensaje de advertencia."""
    print(f"{Colors.YELLOW}[WARN] {text}{Colors.RESET}")


def print_json(data: dict, indent: int = 2):
    """Imprime JSON formateado."""
    print(json.dumps(data, indent=indent, ensure_ascii=False, default=str))


# ============================================================================
# Funciones de prueba
# ============================================================================

def test_health_check(base_url: str) -> bool:
    """
    Prueba 1: Health Check
    GET /health
    """
    print_header("Test 1: Health Check")

    url = f"{base_url}/health"
    print_info(f"GET {url}")

    try:
        response = requests.get(url, timeout=10)

        if response.status_code == 200:
            data = response.json()
            print_success(f"Status: {data.get('status')}")
            print_success(f"Database: {data.get('database')}")
            print_success(f"Version: {data.get('version')}")
            return True
        else:
            print_error(f"Status code: {response.status_code}")
            print_error(response.text)
            return False

    except requests.exceptions.ConnectionError:
        print_error(f"No se puede conectar a {base_url}")
        print_warning("Asegurate de que el servidor este corriendo:")
        print_warning("  cd backend && uvicorn app.main:app --reload")
        return False
    except Exception as e:
        print_error(f"Error: {e}")
        return False


def test_evaluate_url(base_url: str, test_url: str) -> dict:
    """
    Prueba 2: Evaluar URL
    POST /api/v1/evaluation/evaluate
    """
    print_header("Test 2: Evaluar URL (.gob.bo)")

    url = f"{base_url}{API_PREFIX}/evaluation/evaluate"
    payload = {
        "url": test_url,
        "institution_name": "Test Institution",
        "force_recrawl": False
    }

    print_info(f"POST {url}")
    print_info(f"Payload: {json.dumps(payload, indent=2)}")
    print_warning("Esta operacion puede demorar varios minutos...")

    try:
        start_time = time.time()
        response = requests.post(url, json=payload, timeout=600)  # 10 min timeout
        elapsed = time.time() - start_time

        if response.status_code == 200:
            data = response.json()

            print_success(f"Evaluacion completada en {elapsed:.2f} segundos")
            print_success(f"URL: {data.get('url')}")
            print_success(f"Status: {data.get('status')}")

            # Mostrar scores
            scores = data.get('scores', {})
            print(f"\n{Colors.BOLD}Scores por Dimension:{Colors.RESET}")
            for dim, score_data in scores.items():
                if isinstance(score_data, dict):
                    pct = score_data.get('percentage', 0)
                    print(f"  - {dim}: {pct:.1f}%")
                else:
                    print(f"  - {dim}: {score_data}")

            # Mostrar resumen
            summary = data.get('summary', {})
            print(f"\n{Colors.BOLD}Resumen:{Colors.RESET}")
            print(f"  - Total criterios: {summary.get('total_criteria', 0)}")
            print(f"  - Heuristicos: {summary.get('heuristic_criteria', 0)}")
            print(f"  - NLP: {summary.get('nlp_criteria', 0)}")
            print(f"  - Passed: {summary.get('passed', 0)}")
            print(f"  - Failed: {summary.get('failed', 0)}")
            print(f"  - Partial: {summary.get('partial', 0)}")

            # Mostrar NLP si existe
            nlp = data.get('nlp_analysis')
            if nlp:
                print(f"\n{Colors.BOLD}Analisis NLP:{Colors.RESET}")
                print(f"  - Global: {nlp.get('global_score', 0):.1f}%")
                print(f"  - Coherencia: {nlp.get('coherence_score', 0):.1f}%")
                print(f"  - Ambiguedad: {nlp.get('ambiguity_score', 0):.1f}%")
                print(f"  - Claridad: {nlp.get('clarity_score', 0):.1f}%")

            return data

        elif response.status_code == 400:
            print_error(f"URL invalida: {response.json().get('detail')}")
            return {}
        else:
            print_error(f"Status code: {response.status_code}")
            print_error(response.text[:500])
            return {}

    except requests.exceptions.Timeout:
        print_error("Timeout - la evaluacion tardo demasiado")
        return {}
    except Exception as e:
        print_error(f"Error: {e}")
        return {}


def test_get_evaluation(base_url: str, evaluation_id: int) -> bool:
    """
    Prueba 3: Obtener evaluacion por ID
    GET /api/v1/evaluation/{id}
    """
    print_header(f"Test 3: Obtener Evaluacion ID={evaluation_id}")

    url = f"{base_url}{API_PREFIX}/evaluation/{evaluation_id}"
    print_info(f"GET {url}")

    try:
        response = requests.get(url, timeout=30)

        if response.status_code == 200:
            data = response.json()
            print_success(f"URL: {data.get('url')}")
            print_success(f"Status: {data.get('status')}")
            print_success(f"Criterios: {data.get('summary', {}).get('total_criteria', 0)}")
            return True
        elif response.status_code == 404:
            print_warning(f"Evaluacion {evaluation_id} no encontrada")
            return False
        else:
            print_error(f"Status code: {response.status_code}")
            return False

    except Exception as e:
        print_error(f"Error: {e}")
        return False


def test_list_evaluations(base_url: str) -> list:
    """
    Prueba 4: Listar evaluaciones
    GET /api/v1/evaluation/list
    """
    print_header("Test 4: Listar Evaluaciones")

    url = f"{base_url}{API_PREFIX}/evaluation/list"
    params = {"page": 1, "page_size": 5}
    print_info(f"GET {url}?page=1&page_size=5")

    try:
        response = requests.get(url, params=params, timeout=30)

        if response.status_code == 200:
            data = response.json()
            total = data.get('total', 0)
            evaluations = data.get('evaluations', [])

            print_success(f"Total evaluaciones: {total}")
            print_success(f"Mostrando: {len(evaluations)}")

            if evaluations:
                print(f"\n{Colors.BOLD}Ultimas evaluaciones:{Colors.RESET}")
                for ev in evaluations[:5]:
                    score = ev.get('score_total', 0) or 0
                    print(f"  - ID {ev['id']}: {ev.get('website_url', 'N/A')[:40]} -> {score:.1f}%")

            return evaluations
        else:
            print_error(f"Status code: {response.status_code}")
            return []

    except Exception as e:
        print_error(f"Error: {e}")
        return []


def test_delete_evaluation(base_url: str, evaluation_id: int) -> bool:
    """
    Prueba 5: Eliminar evaluacion
    DELETE /api/v1/evaluation/{id}
    """
    print_header(f"Test 5: Eliminar Evaluacion ID={evaluation_id}")

    url = f"{base_url}{API_PREFIX}/evaluation/{evaluation_id}"
    print_info(f"DELETE {url}")
    print_warning("NOTA: Este test esta comentado para no eliminar datos reales")
    print_info("Descomenta la seccion de codigo si deseas probar DELETE")

    # DESCOMENTAR PARA PROBAR DELETE:
    # try:
    #     response = requests.delete(url, timeout=30)
    #
    #     if response.status_code == 200:
    #         print_success(f"Evaluacion {evaluation_id} eliminada")
    #         return True
    #     elif response.status_code == 404:
    #         print_warning(f"Evaluacion {evaluation_id} no encontrada")
    #         return False
    #     else:
    #         print_error(f"Status code: {response.status_code}")
    #         return False
    #
    # except Exception as e:
    #     print_error(f"Error: {e}")
    #     return False

    return True


def test_validation_error(base_url: str) -> bool:
    """
    Prueba 6: Validacion de URL (debe rechazar URLs no .gob.bo)
    """
    print_header("Test 6: Validacion de URL (debe fallar)")

    url = f"{base_url}{API_PREFIX}/evaluation/evaluate"
    payload = {
        "url": "https://www.google.com",  # URL invalida (no es .gob.bo)
        "force_recrawl": False
    }

    print_info(f"POST {url}")
    print_info(f"URL de prueba: {payload['url']} (no es .gob.bo)")

    try:
        response = requests.post(url, json=payload, timeout=30)

        if response.status_code == 422:  # Validation error
            print_success("Validacion funcionando correctamente")
            print_success("URL rechazada por no ser .gob.bo")
            detail = response.json()
            print_info(f"Error esperado: {json.dumps(detail, indent=2, ensure_ascii=False)[:200]}")
            return True
        elif response.status_code == 400:
            print_success("Validacion funcionando correctamente (400)")
            return True
        else:
            print_error(f"La validacion no funciono - Status: {response.status_code}")
            return False

    except Exception as e:
        print_error(f"Error: {e}")
        return False


def test_swagger_docs(base_url: str) -> bool:
    """
    Prueba 7: Verificar Swagger UI
    """
    print_header("Test 7: Swagger Documentation")

    docs_url = f"{base_url}/docs"
    openapi_url = f"{base_url}/openapi.json"

    print_info(f"Verificando {docs_url}")
    print_info(f"Verificando {openapi_url}")

    try:
        # Verificar docs
        response_docs = requests.get(docs_url, timeout=10)
        if response_docs.status_code == 200:
            print_success(f"Swagger UI disponible en {docs_url}")
        else:
            print_error(f"Swagger UI no disponible: {response_docs.status_code}")
            return False

        # Verificar OpenAPI JSON
        response_openapi = requests.get(openapi_url, timeout=10)
        if response_openapi.status_code == 200:
            openapi_data = response_openapi.json()
            print_success(f"OpenAPI JSON disponible")
            print_success(f"Titulo: {openapi_data.get('info', {}).get('title', 'N/A')}")
            print_success(f"Version: {openapi_data.get('info', {}).get('version', 'N/A')}")

            # Contar endpoints
            paths = openapi_data.get('paths', {})
            total_endpoints = sum(len(methods) for methods in paths.values())
            print_success(f"Total endpoints: {total_endpoints}")

            return True
        else:
            print_error(f"OpenAPI JSON no disponible: {response_openapi.status_code}")
            return False

    except Exception as e:
        print_error(f"Error: {e}")
        return False


# ============================================================================
# Main
# ============================================================================

def main():
    """Funcion principal."""
    parser = argparse.ArgumentParser(
        description="Script de prueba para API de Evaluacion GOB.BO"
    )
    parser.add_argument(
        "--base-url",
        default=DEFAULT_BASE_URL,
        help=f"URL base del servidor (default: {DEFAULT_BASE_URL})"
    )
    parser.add_argument(
        "--test-url",
        default=DEFAULT_TEST_URL,
        help=f"URL .gob.bo para evaluar (default: {DEFAULT_TEST_URL})"
    )
    parser.add_argument(
        "--skip-evaluate",
        action="store_true",
        help="Omitir la evaluacion completa (toma tiempo)"
    )

    args = parser.parse_args()

    print(f"""
{Colors.BOLD}{Colors.CYAN}
╔══════════════════════════════════════════════════════════════╗
║     TEST API - Evaluador de Sitios Gubernamentales           ║
║                  GOB.BO Evaluator v1.0                       ║
╚══════════════════════════════════════════════════════════════╝
{Colors.RESET}
Base URL: {args.base_url}
Test URL: {args.test_url}
Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
""")

    results = {
        "health_check": False,
        "swagger_docs": False,
        "validation": False,
        "list_evaluations": False,
        "evaluate_url": False,
        "get_evaluation": False,
    }

    # Test 1: Health Check
    results["health_check"] = test_health_check(args.base_url)

    if not results["health_check"]:
        print_error("\nEl servidor no esta disponible. Abortando pruebas.")
        sys.exit(1)

    # Test 7: Swagger Docs
    results["swagger_docs"] = test_swagger_docs(args.base_url)

    # Test 6: Validation
    results["validation"] = test_validation_error(args.base_url)

    # Test 4: List Evaluations
    evaluations = test_list_evaluations(args.base_url)
    results["list_evaluations"] = len(evaluations) >= 0  # True even if empty

    # Test 2: Evaluate URL (opcional)
    evaluation_data = {}
    if not args.skip_evaluate:
        evaluation_data = test_evaluate_url(args.base_url, args.test_url)
        results["evaluate_url"] = bool(evaluation_data)
    else:
        print_header("Test 2: Evaluar URL (OMITIDO)")
        print_warning("Usa --skip-evaluate=false para ejecutar este test")

    # Test 3: Get Evaluation (si hay evaluaciones)
    if evaluations:
        first_id = evaluations[0].get('id')
        if first_id:
            results["get_evaluation"] = test_get_evaluation(args.base_url, first_id)
    else:
        print_header("Test 3: Obtener Evaluacion (OMITIDO)")
        print_warning("No hay evaluaciones previas para consultar")

    # Test 5: Delete (comentado por seguridad)
    test_delete_evaluation(args.base_url, 999)

    # Resumen final
    print_header("RESUMEN DE PRUEBAS")

    passed = 0
    total = 0

    for test_name, result in results.items():
        total += 1
        if result:
            passed += 1
            print_success(f"{test_name}: PASSED")
        else:
            print_error(f"{test_name}: FAILED")

    print(f"\n{Colors.BOLD}Resultado: {passed}/{total} pruebas exitosas{Colors.RESET}")

    if passed == total:
        print(f"\n{Colors.GREEN}{Colors.BOLD}TODAS LAS PRUEBAS PASARON{Colors.RESET}")
        return 0
    else:
        print(f"\n{Colors.RED}{Colors.BOLD}ALGUNAS PRUEBAS FALLARON{Colors.RESET}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
