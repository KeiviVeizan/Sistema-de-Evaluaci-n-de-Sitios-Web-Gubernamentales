"""
Endpoints para ejecutar evaluaciones
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.evaluator.evaluation_engine import EvaluationEngine
from app.models.database_models import Evaluation, CriteriaResult

router = APIRouter(prefix="/evaluation", tags=["Evaluation"])


@router.post("/evaluate/{website_id}")
async def evaluate_website(
    website_id: int,
    db: Session = Depends(get_db)
):
    """
    Ejecuta la evaluación completa de un sitio web
    El sitio debe haber sido crawleado previamente
    """
    try:
        engine = EvaluationEngine(db)
        result = engine.evaluar_sitio(website_id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/results/{evaluation_id}")
async def get_evaluation_results(
    evaluation_id: int,
    db: Session = Depends(get_db)
):
    """
    Obtiene los resultados detallados de una evaluación
    """
    evaluation = db.query(Evaluation).filter(Evaluation.id == evaluation_id).first()

    if not evaluation:
        raise HTTPException(status_code=404, detail="Evaluación no encontrada")

    # Obtener todos los criterios evaluados
    criteria_results = db.query(CriteriaResult).filter(
        CriteriaResult.evaluation_id == evaluation_id
    ).all()

    # Organizar por dimensión
    results_by_dimension = {}
    for result in criteria_results:
        dim = result.dimension
        if dim not in results_by_dimension:
            results_by_dimension[dim] = []

        results_by_dimension[dim].append({
            "criteria_id": result.criteria_id,
            "criteria_name": result.criteria_name,
            "lineamiento": result.lineamiento,
            "status": result.status,
            "score": result.score,
            "max_score": result.max_score,
            "percentage": (result.score / result.max_score * 100) if result.max_score > 0 else 0,
            "details": result.details
        })

    return {
        "evaluation_id": evaluation.id,
        "website_id": evaluation.website_id,
        "status": evaluation.status,
        "started_at": evaluation.started_at,
        "completed_at": evaluation.completed_at,
        "scores": {
            "accesibilidad": evaluation.score_accessibility,
            "usabilidad": evaluation.score_usability,
            "semantica_web": evaluation.score_semantic_web,
            "soberania_digital": evaluation.score_digital_sovereignty,
            "total": evaluation.score_total
        },
        "results_by_dimension": results_by_dimension,
        "summary": {
            "total_criteria": len(criteria_results),
            "passed": len([r for r in criteria_results if r.status == "pass"]),
            "failed": len([r for r in criteria_results if r.status == "fail"]),
            "partial": len([r for r in criteria_results if r.status == "partial"]),
            "not_applicable": len([r for r in criteria_results if r.status == "na"])
        }
    }


@router.get("/results/{evaluation_id}/dimension/{dimension}")
async def get_dimension_results(
    evaluation_id: int,
    dimension: str,
    db: Session = Depends(get_db)
):
    """
    Obtiene los resultados de una dimensión específica
    """
    evaluation = db.query(Evaluation).filter(Evaluation.id == evaluation_id).first()

    if not evaluation:
        raise HTTPException(status_code=404, detail="Evaluación no encontrada")

    # Obtener criterios de la dimensión
    criteria_results = db.query(CriteriaResult).filter(
        CriteriaResult.evaluation_id == evaluation_id,
        CriteriaResult.dimension == dimension
    ).all()

    if not criteria_results:
        raise HTTPException(
            status_code=404,
            detail=f"No se encontraron resultados para la dimensión '{dimension}'"
        )

    results = []
    for result in criteria_results:
        results.append({
            "criteria_id": result.criteria_id,
            "criteria_name": result.criteria_name,
            "lineamiento": result.lineamiento,
            "status": result.status,
            "score": result.score,
            "max_score": result.max_score,
            "percentage": (result.score / result.max_score * 100) if result.max_score > 0 else 0,
            "details": result.details,
            "evidence": result.evidence
        })

    # Calcular score de la dimensión
    total_score = sum(r['score'] for r in results)
    max_score = sum(r['max_score'] for r in results)
    dimension_percentage = (total_score / max_score * 100) if max_score > 0 else 0

    return {
        "evaluation_id": evaluation_id,
        "dimension": dimension,
        "dimension_score": {
            "total_score": total_score,
            "max_score": max_score,
            "percentage": dimension_percentage
        },
        "criteria": results,
        "summary": {
            "total_criteria": len(results),
            "passed": len([r for r in results if r['status'] == "pass"]),
            "failed": len([r for r in results if r['status'] == "fail"]),
            "partial": len([r for r in results if r['status'] == "partial"]),
            "not_applicable": len([r for r in results if r['status'] == "na"])
        }
    }


@router.get("/history/{website_id}")
async def get_evaluation_history(
    website_id: int,
    db: Session = Depends(get_db)
):
    """
    Obtiene el historial de evaluaciones de un sitio web
    """
    evaluations = db.query(Evaluation).filter(
        Evaluation.website_id == website_id
    ).order_by(Evaluation.started_at.desc()).all()

    if not evaluations:
        raise HTTPException(
            status_code=404,
            detail=f"No se encontraron evaluaciones para website_id={website_id}"
        )

    history = []
    for eval in evaluations:
        history.append({
            "evaluation_id": eval.id,
            "status": eval.status,
            "started_at": eval.started_at,
            "completed_at": eval.completed_at,
            "scores": {
                "accesibilidad": eval.score_accessibility,
                "usabilidad": eval.score_usability,
                "semantica_web": eval.score_semantic_web,
                "soberania_digital": eval.score_digital_sovereignty,
                "total": eval.score_total
            }
        })

    return {
        "website_id": website_id,
        "total_evaluations": len(history),
        "evaluations": history
    }
