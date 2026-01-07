"""
Script de prueba para el sistema de evaluación
Ejecuta una evaluación completa sobre un sitio web crawleado
"""
import sys
import os
from pathlib import Path

# Asegurar UTF-8 en Windows
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

# Agregar el directorio raíz al path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from app.database import SessionLocal
from app.evaluator.evaluation_engine import EvaluationEngine
from app.models.database_models import Website, ExtractedContent
import json


def print_section(title):
    """Imprime una sección con formato"""
    print("\n" + "="*80)
    print(f"  {title}")
    print("="*80)


def test_evaluation(website_id: int = None):
    """
    Prueba la evaluación de un sitio web

    Args:
        website_id: ID del sitio web a evaluar. Si es None, usa el más reciente.
    """
    db = SessionLocal()

    try:
        # Buscar sitio web
        if website_id:
            website = db.query(Website).filter(Website.id == website_id).first()
        else:
            website = db.query(Website).order_by(Website.id.desc()).first()

        if not website:
            print("❌ No se encontró ningún sitio web en la base de datos")
            print("\nPrimero debes crawlear un sitio usando:")
            print("  POST http://localhost:8000/api/v1/crawler/crawl")
            return

        print_section(f"EVALUANDO SITIO WEB")
        print(f"ID: {website.id}")
        print(f"URL: {website.url}")
        print(f"Institución: {website.institution_name}")

        # Verificar que hay contenido extraído
        extracted = db.query(ExtractedContent).filter(
            ExtractedContent.website_id == website.id
        ).first()

        if not extracted:
            print(f"\n❌ No hay contenido extraído para el sitio {website.id}")
            print("Primero debes crawlear el sitio.")
            return

        print(f"\n✓ Contenido extraído encontrado (ID: {extracted.id})")
        print(f"  Crawleado: {extracted.crawled_at}")

        # Crear engine de evaluación
        print_section("EJECUTANDO EVALUACIÓN")
        engine = EvaluationEngine(db)

        # Ejecutar evaluación
        result = engine.evaluar_sitio(website.id)

        # Mostrar resultados
        print_section("RESULTADOS DE LA EVALUACIÓN")

        print(f"\nEvaluation ID: {result['evaluation_id']}")
        print(f"Estado: {result['status']}")
        print(f"\nCriterios evaluados: {result['total_criteria']}")
        print(f"  ✓ Aprobados: {result['passed']}")
        print(f"  ✗ Fallidos: {result['failed']}")
        print(f"  ~ Parciales: {result['partial']}")
        print(f"  - No aplicables: {result['not_applicable']}")

        print_section("SCORES POR DIMENSIÓN")

        # Accesibilidad
        acc = result['scores']['accesibilidad']
        print(f"\n📊 ACCESIBILIDAD (30%)")
        print(f"  Score: {acc['total_score']:.2f} / {acc['max_score']:.2f}")
        print(f"  Porcentaje: {acc['percentage']:.2f}%")
        print(f"  Criterios: {acc['passed']}/{acc['criteria_count']} aprobados")

        # Usabilidad
        usa = result['scores']['usabilidad']
        print(f"\n📊 USABILIDAD (30%)")
        print(f"  Score: {usa['total_score']:.2f} / {usa['max_score']:.2f}")
        print(f"  Porcentaje: {usa['percentage']:.2f}%")
        print(f"  Criterios: {usa['passed']}/{usa['criteria_count']} aprobados")

        # Semántica Técnica
        sem = result['scores']['semantica_tecnica']
        print(f"\n📊 SEMÁNTICA TÉCNICA (30%)")
        print(f"  Score: {sem['total_score']:.2f} / {sem['max_score']:.2f}")
        print(f"  Porcentaje: {sem['percentage']:.2f}%")
        print(f"  Criterios: {sem['passed']}/{sem['criteria_count']} aprobados")

        # Soberanía Digital
        sob = result['scores']['soberania']
        print(f"\n📊 SOBERANÍA DIGITAL (10%)")
        print(f"  Score: {sob['total_score']:.2f} / {sob['max_score']:.2f}")
        print(f"  Porcentaje: {sob['percentage']:.2f}%")
        print(f"  Criterios: {sob['passed']}/{sob['criteria_count']} aprobados")

        # Score Total
        print_section("SCORE TOTAL")
        print(f"\n🎯 SCORE FINAL PONDERADO: {result['scores']['total']:.2f}%")

        if result['scores']['total'] >= 90:
            rating = "EXCELENTE ⭐⭐⭐⭐⭐"
        elif result['scores']['total'] >= 75:
            rating = "BUENO ⭐⭐⭐⭐"
        elif result['scores']['total'] >= 60:
            rating = "REGULAR ⭐⭐⭐"
        elif result['scores']['total'] >= 45:
            rating = "DEFICIENTE ⭐⭐"
        else:
            rating = "MUY DEFICIENTE ⭐"

        print(f"Calificación: {rating}")

        print_section("PARA VER DETALLES")
        print(f"\n1. Obtener resultados completos:")
        print(f"   GET http://localhost:8000/api/v1/evaluation/results/{result['evaluation_id']}")

        print(f"\n2. Resultados por dimensión:")
        print(f"   GET http://localhost:8000/api/v1/evaluation/results/{result['evaluation_id']}/dimension/accesibilidad")
        print(f"   GET http://localhost:8000/api/v1/evaluation/results/{result['evaluation_id']}/dimension/usabilidad")
        print(f"   GET http://localhost:8000/api/v1/evaluation/results/{result['evaluation_id']}/dimension/semantica")
        print(f"   GET http://localhost:8000/api/v1/evaluation/results/{result['evaluation_id']}/dimension/soberania")

        print(f"\n3. Historial de evaluaciones:")
        print(f"   GET http://localhost:8000/api/v1/evaluation/history/{website.id}")

        print("\n" + "="*80 + "\n")

    except Exception as e:
        print(f"\n❌ Error durante la evaluación: {e}")
        import traceback
        traceback.print_exc()

    finally:
        db.close()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Prueba el sistema de evaluación')
    parser.add_argument('--website-id', type=int, help='ID del sitio web a evaluar')

    args = parser.parse_args()

    test_evaluation(args.website_id)
