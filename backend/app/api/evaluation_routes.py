"""
Endpoints para ejecutar evaluaciones de sitios web gubernamentales bolivianos.

Incluye:
- POST /evaluate: Evaluar URL directamente
- POST /evaluate/{website_id}: Evaluar sitio existente
- GET /results/{evaluation_id}: Obtener resultados
- GET /evaluations: Listar evaluaciones
- DELETE /evaluation/{evaluation_id}: Eliminar evaluación
"""
from datetime import datetime
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.evaluator.evaluation_engine import EvaluationEngine
from app.models.database_models import Evaluation, CriteriaResult, Website, NLPAnalysis
from app.schemas.evaluation_schemas import (
    EvaluateURLRequest,
    EvaluateURLResponse,
    CriteriaResultItem,
    NLPAnalysisDetail,
    EvaluationSummary,
    EvaluationListItem,
    EvaluationListResponse,
)
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/evaluation", tags=["Evaluation"])


# ============================================================================
# ENDPOINT PRINCIPAL: Evaluar URL directamente
# ============================================================================

@router.post(
    "/evaluate",
    response_model=EvaluateURLResponse,
    summary="Evaluar URL gubernamental",
    description="""
Evalúa un sitio web gubernamental boliviano (.gob.bo) y retorna los resultados completos.

**Proceso:**
1. Valida que la URL sea un dominio .gob.bo
2. Ejecuta crawling del sitio (si es necesario)
3. Aplica 32 evaluadores heurísticos + 3 NLP
4. Calcula scores por dimensión
5. Persiste resultados en base de datos

**Dimensiones evaluadas:**
- Accesibilidad (30%): WCAG 2.0, contraste, navegación
- Usabilidad (30%): Estructura, responsive, carga
- Semántica Técnica (15%): HTML5, metadatos, SEO
- Semántica NLP (15%): Coherencia, claridad, ambigüedad
- Soberanía Digital (10%): Hosting, certificados, privacidad
""",
    responses={
        200: {"description": "Evaluación completada exitosamente"},
        400: {"description": "URL inválida o no es dominio .gob.bo"},
        500: {"description": "Error interno durante la evaluación"},
    }
)
async def evaluate_url(
    request: EvaluateURLRequest,
    db: Session = Depends(get_db)
):
    """
    Evalúa una URL gubernamental boliviana y retorna resultados completos.

    - **url**: URL del sitio web (debe ser .gob.bo)
    - **institution_name**: Nombre de la institución (opcional)
    - **force_recrawl**: Forzar re-crawling (default: False)
    """
    try:
        logger.info(f"Iniciando evaluación de URL: {request.url}")

        # Crear instancia del motor de evaluación
        engine = EvaluationEngine(db)

        # Evaluar la URL usando el método evaluar_url
        result = engine.evaluar_url(request.url, force_recrawl=request.force_recrawl)

        # Obtener la evaluación de la BD para datos adicionales
        evaluation = db.query(Evaluation).filter(
            Evaluation.id == result.get('evaluation_id')
        ).first()

        # Obtener criterios evaluados
        criteria_results = []
        if evaluation:
            db_criteria = db.query(CriteriaResult).filter(
                CriteriaResult.evaluation_id == evaluation.id
            ).all()

            for cr in db_criteria:
                criteria_results.append(CriteriaResultItem(
                    criteria_id=cr.criteria_id,
                    criteria_name=cr.criteria_name,
                    dimension=cr.dimension,
                    lineamiento=cr.lineamiento or "",
                    status=cr.status,
                    score=cr.score,
                    max_score=cr.max_score,
                    details=cr.details,
                    evidence=cr.evidence
                ))

        # Obtener análisis NLP si existe
        nlp_analysis = None
        if evaluation:
            nlp_record = db.query(NLPAnalysis).filter(
                NLPAnalysis.evaluation_id == evaluation.id
            ).first()

            if nlp_record:
                nlp_analysis = NLPAnalysisDetail(
                    global_score=nlp_record.nlp_global_score,
                    coherence_score=nlp_record.coherence_score,
                    ambiguity_score=nlp_record.ambiguity_score,
                    clarity_score=nlp_record.clarity_score,
                    wcag_compliance=nlp_record.wcag_compliance or {},
                    total_sections_analyzed=nlp_record.coherence_details.get('sections_analyzed', 0) if nlp_record.coherence_details else 0,
                    total_texts_analyzed=nlp_record.ambiguity_details.get('total_analyzed', 0) if nlp_record.ambiguity_details else 0,
                    recommendations=nlp_record.recommendations or [],
                    details={
                        'coherence': nlp_record.coherence_details,
                        'ambiguity': nlp_record.ambiguity_details,
                        'clarity': nlp_record.clarity_details
                    }
                )

        # Contar criterios por estado
        passed = len([c for c in criteria_results if c.status == 'pass'])
        failed = len([c for c in criteria_results if c.status == 'fail'])
        partial = len([c for c in criteria_results if c.status == 'partial'])
        not_applicable = len([c for c in criteria_results if c.status == 'na'])

        # Contar criterios NLP (ACC-07, ACC-08, ACC-09)
        nlp_criteria_ids = ['ACC-07', 'ACC-08', 'ACC-09']
        nlp_criteria = len([c for c in criteria_results if c.criteria_id in nlp_criteria_ids])
        heuristic_criteria = len(criteria_results) - nlp_criteria

        # Construir respuesta
        response = EvaluateURLResponse(
            url=request.url,
            status=result.get('status', 'completed'),
            timestamp=datetime.now().isoformat(),
            scores=result.get('scores', {}),
            nlp_analysis=nlp_analysis,
            criteria_results=criteria_results,
            summary=EvaluationSummary(
                total_criteria=len(criteria_results),
                heuristic_criteria=heuristic_criteria,
                nlp_criteria=nlp_criteria,
                passed=passed,
                failed=failed,
                partial=partial,
                not_applicable=not_applicable
            )
        )

        logger.info(f"Evaluación completada: {request.url} - Score: {result.get('scores', {}).get('total', 0)}%")
        return response

    except ValueError as e:
        logger.error(f"Error de validación: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error durante evaluación de {request.url}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")


# ============================================================================
# Listar evaluaciones
# ============================================================================

@router.get(
    "/list",
    response_model=EvaluationListResponse,
    summary="Listar evaluaciones",
    description="Obtiene una lista paginada de todas las evaluaciones realizadas."
)
async def list_evaluations(
    page: int = Query(1, ge=1, description="Número de página"),
    page_size: int = Query(10, ge=1, le=100, description="Tamaño de página"),
    status: Optional[str] = Query(None, description="Filtrar por estado"),
    db: Session = Depends(get_db)
):
    """
    Lista evaluaciones con paginación.

    - **page**: Número de página (default: 1)
    - **page_size**: Items por página (default: 10, max: 100)
    - **status**: Filtrar por estado (pending, in_progress, completed, failed)
    """
    try:
        # Query base
        query = db.query(Evaluation).join(Website)

        # Filtro por estado
        if status:
            query = query.filter(Evaluation.status == status)

        # Total
        total = query.count()

        # Paginación
        offset = (page - 1) * page_size
        evaluations = query.order_by(Evaluation.started_at.desc()).offset(offset).limit(page_size).all()

        # Construir respuesta
        items = []
        for ev in evaluations:
            items.append(EvaluationListItem(
                id=ev.id,
                website_id=ev.website_id,
                website_url=ev.website.url if ev.website else "",
                institution_name=ev.website.institution_name if ev.website else None,
                score_total=ev.score_total,
                status=ev.status,
                started_at=ev.started_at,
                completed_at=ev.completed_at
            ))

        return EvaluationListResponse(
            total=total,
            page=page,
            page_size=page_size,
            evaluations=items
        )

    except Exception as e:
        logger.error(f"Error listando evaluaciones: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Obtener evaluación por ID
# ============================================================================

@router.get(
    "/{evaluation_id}",
    response_model=EvaluateURLResponse,
    summary="Obtener evaluación por ID",
    description="Obtiene los resultados completos de una evaluación específica."
)
async def get_evaluation_by_id(
    evaluation_id: int,
    db: Session = Depends(get_db)
):
    """
    Obtiene una evaluación completa por su ID.
    """
    evaluation = db.query(Evaluation).filter(Evaluation.id == evaluation_id).first()

    if not evaluation:
        raise HTTPException(status_code=404, detail="Evaluación no encontrada")

    # Obtener website
    website = db.query(Website).filter(Website.id == evaluation.website_id).first()

    # Obtener criterios
    db_criteria = db.query(CriteriaResult).filter(
        CriteriaResult.evaluation_id == evaluation_id
    ).all()

    criteria_results = [
        CriteriaResultItem(
            criteria_id=cr.criteria_id,
            criteria_name=cr.criteria_name,
            dimension=cr.dimension,
            lineamiento=cr.lineamiento or "",
            status=cr.status,
            score=cr.score,
            max_score=cr.max_score,
            details=cr.details,
            evidence=cr.evidence
        ) for cr in db_criteria
    ]

    # Obtener análisis NLP
    nlp_analysis = None
    nlp_record = db.query(NLPAnalysis).filter(
        NLPAnalysis.evaluation_id == evaluation_id
    ).first()

    if nlp_record:
        nlp_analysis = NLPAnalysisDetail(
            global_score=nlp_record.nlp_global_score,
            coherence_score=nlp_record.coherence_score,
            ambiguity_score=nlp_record.ambiguity_score,
            clarity_score=nlp_record.clarity_score,
            wcag_compliance=nlp_record.wcag_compliance or {},
            total_sections_analyzed=nlp_record.coherence_details.get('sections_analyzed', 0) if nlp_record.coherence_details else 0,
            total_texts_analyzed=nlp_record.ambiguity_details.get('total_analyzed', 0) if nlp_record.ambiguity_details else 0,
            recommendations=nlp_record.recommendations or [],
            details={
                'coherence': nlp_record.coherence_details,
                'ambiguity': nlp_record.ambiguity_details,
                'clarity': nlp_record.clarity_details
            }
        )

    # Contar criterios
    passed = len([c for c in criteria_results if c.status == 'pass'])
    failed = len([c for c in criteria_results if c.status == 'fail'])
    partial = len([c for c in criteria_results if c.status == 'partial'])
    not_applicable = len([c for c in criteria_results if c.status == 'na'])

    nlp_criteria_ids = ['ACC-07', 'ACC-08', 'ACC-09']
    nlp_criteria = len([c for c in criteria_results if c.criteria_id in nlp_criteria_ids])
    heuristic_criteria = len(criteria_results) - nlp_criteria

    # Construir scores
    scores = {
        'accesibilidad': {'percentage': evaluation.score_accessibility or 0},
        'usabilidad': {'percentage': evaluation.score_usability or 0},
        'semantica_tecnica': {'percentage': evaluation.score_semantic_web or 0},
        'semantica_nlp': {'percentage': nlp_record.nlp_global_score if nlp_record else 0},
        'soberania': {'percentage': evaluation.score_digital_sovereignty or 0},
        'total': evaluation.score_total or 0
    }

    return EvaluateURLResponse(
        url=website.url if website else "",
        status=evaluation.status,
        timestamp=evaluation.started_at.isoformat() if evaluation.started_at else "",
        scores=scores,
        nlp_analysis=nlp_analysis,
        criteria_results=criteria_results,
        summary=EvaluationSummary(
            total_criteria=len(criteria_results),
            heuristic_criteria=heuristic_criteria,
            nlp_criteria=nlp_criteria,
            passed=passed,
            failed=failed,
            partial=partial,
            not_applicable=not_applicable
        )
    )


# ============================================================================
# Eliminar evaluación
# ============================================================================

@router.delete(
    "/{evaluation_id}",
    summary="Eliminar evaluación",
    description="Elimina una evaluación y todos sus resultados asociados."
)
async def delete_evaluation(
    evaluation_id: int,
    db: Session = Depends(get_db)
):
    """
    Elimina una evaluación por su ID.

    También elimina: criterios asociados y análisis NLP.
    """
    evaluation = db.query(Evaluation).filter(Evaluation.id == evaluation_id).first()

    if not evaluation:
        raise HTTPException(status_code=404, detail="Evaluación no encontrada")

    try:
        # Los registros relacionados se eliminan por CASCADE
        db.delete(evaluation)
        db.commit()

        logger.info(f"Evaluación {evaluation_id} eliminada exitosamente")
        return {"message": f"Evaluación {evaluation_id} eliminada exitosamente"}

    except Exception as e:
        db.rollback()
        logger.error(f"Error eliminando evaluación {evaluation_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# ENDPOINTS LEGACY (mantener compatibilidad)
# ============================================================================

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
