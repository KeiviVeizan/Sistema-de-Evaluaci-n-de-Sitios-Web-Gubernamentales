"""
Endpoints para ejecutar evaluaciones de sitios web gubernamentales bolivianos.

Incluye:
- POST /evaluate: Evaluar URL directamente
- POST /evaluate/{website_id}: Evaluar sitio existente
- GET /results/{evaluation_id}: Obtener resultados
- GET /evaluations: Listar evaluaciones
- DELETE /evaluation/{evaluation_id}: Eliminar evaluacion

ARQUITECTURA:
- Endpoints async (no bloquean servidor)
- Evaluacion sync ejecutada en ThreadPoolExecutor
- Patron recomendado por FastAPI para operaciones I/O-bound
"""
from datetime import datetime
from typing import Optional, List
from concurrent.futures import ThreadPoolExecutor
import asyncio
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.evaluator.evaluation_engine import evaluar_url as ejecutar_evaluacion
from app.models.database_models import (
    Evaluation, EvaluationStatus, CriteriaResult, Website, NLPAnalysis, Institution
)
from app.schemas.evaluation_schemas import (
    EvaluateURLRequest,
    EvaluateURLResponse,
    CriteriaResultItem,
    NLPAnalysisDetail,
    EvaluationSummary,
    EvaluationListItem,
    EvaluationListResponse,
    SaveEvaluationRequest,
    SaveEvaluationResponse,
)
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/evaluation", tags=["Evaluation"])

# Thread pool para operaciones I/O-bound (crawling con Playwright)
# max_workers=3 permite hasta 3 evaluaciones concurrentes
_executor = ThreadPoolExecutor(max_workers=3, thread_name_prefix="gob_evaluator")


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
        logger.info(f"Iniciando evaluacion de URL: {request.url}")

        # Ejecutar evaluacion SYNC en thread pool (no bloquea event loop)
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            _executor,
            ejecutar_evaluacion,
            str(request.url)
        )

        logger.info(f"Evaluacion completada - Score: {result.get('scores', {}).get('total', 0):.1f}%")

        # Obtener criterios directamente del resultado (ya vienen de evaluate_url)
        raw_criteria = result.get('criteria_results', [])
        criteria_results = []
        for cr in raw_criteria:
            # Manejar tanto objetos con to_dict() como dicts directos
            if isinstance(cr, dict):
                criteria_results.append(CriteriaResultItem(
                    criteria_id=cr.get('criteria_id', ''),
                    criteria_name=cr.get('criteria_name', ''),
                    dimension=cr.get('dimension', ''),
                    lineamiento=cr.get('lineamiento', ''),
                    status=cr.get('status', 'na'),
                    score=cr.get('score', 0),
                    max_score=cr.get('max_score', 10),
                    details=cr.get('details', {}),
                    evidence=cr.get('evidence', [])
                ))

        # Obtener analisis NLP directamente del resultado
        nlp_data = result.get('nlp_analysis')
        nlp_analysis = None
        if nlp_data:
            nlp_analysis = NLPAnalysisDetail(
                global_score=nlp_data.get('global_score', 0),
                coherence_score=nlp_data.get('coherence_score', 0),
                ambiguity_score=nlp_data.get('ambiguity_score', 0),
                clarity_score=nlp_data.get('clarity_score', 0),
                wcag_compliance=nlp_data.get('wcag_compliance', {}),
                total_sections_analyzed=nlp_data.get('coherence_details', {}).get('sections_analyzed', 0) if nlp_data.get('coherence_details') else 0,
                total_texts_analyzed=nlp_data.get('ambiguity_details', {}).get('total_analyzed', 0) if nlp_data.get('ambiguity_details') else 0,
                recommendations=nlp_data.get('recommendations', []),
                details={
                    'coherence': nlp_data.get('coherence_details'),
                    'ambiguity': nlp_data.get('ambiguity_details'),
                    'clarity': nlp_data.get('clarity_details')
                }
            )

        # Usar summary directamente del resultado
        summary_data = result.get('summary', {})

        # Construir respuesta usando datos directos del resultado
        response = EvaluateURLResponse(
            url=str(request.url),
            status=result.get('status', 'completed'),
            timestamp=result.get('timestamp', datetime.now().isoformat()),
            scores=result.get('scores', {}),
            nlp_analysis=nlp_analysis,
            criteria_results=criteria_results,
            summary=EvaluationSummary(
                total_criteria=summary_data.get('total_criteria', len(criteria_results)),
                heuristic_criteria=summary_data.get('heuristic_criteria', 32),
                nlp_criteria=summary_data.get('nlp_criteria', 3 if nlp_analysis else 0),
                passed=summary_data.get('passed', 0),
                failed=summary_data.get('failed', 0),
                partial=summary_data.get('partial', 0),
                not_applicable=summary_data.get('not_applicable', 0)
            )
        )

        logger.info(f"Response construido: {len(criteria_results)} criterios, NLP: {'Si' if nlp_analysis else 'No'}")
        return response

    except ValueError as e:
        logger.error(f"Error de validación: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error durante evaluación de {request.url}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")


# ============================================================================
# Metadatos de criterios: dimension, nombre, max_score, pesos por dimension
# ============================================================================

# Pesos de cada dimension en el puntaje total (deben sumar 1.0)
_DIMENSION_WEIGHTS = {
    'accesibilidad':     0.30,
    'usabilidad':        0.30,
    'semantica_tecnica': 0.15,
    'semantica_nlp':     0.15,
    'soberania':         0.10,
}

# Alias: evaluadores usan semantica, el sistema usa semantica_tecnica
_DIMENSION_ALIASES = {
    'semantica': 'semantica_tecnica',
}

# Mapa criterion_id -> metadatos (IDs reales de los evaluadores)
_CRITERIA_META: dict = {
    # Accesibilidad
    'ACC-01': {'name': 'Texto alternativo en imágenes', 'dimension': 'accesibilidad', 'max_score': 10.0},
    'ACC-02': {'name': 'Contraste de color', 'dimension': 'accesibilidad', 'max_score': 10.0},
    'ACC-03': {'name': 'Navegación por teclado', 'dimension': 'accesibilidad', 'max_score': 10.0},
    'ACC-04': {'name': 'Etiquetas en formularios', 'dimension': 'accesibilidad', 'max_score': 10.0},
    'ACC-05': {'name': 'Idioma declarado', 'dimension': 'accesibilidad', 'max_score': 10.0},
    'ACC-06': {'name': 'Estructura de encabezados', 'dimension': 'accesibilidad', 'max_score': 10.0},
    'ACC-07': {'name': 'Coherencia semántica NLP', 'dimension': 'semantica_nlp', 'max_score': 10.0},
    'ACC-07-NLP': {'name': 'Coherencia semántica NLP', 'dimension': 'semantica_nlp', 'max_score': 1.0},
    'ACC-08': {'name': 'Detección de ambigüedad NLP', 'dimension': 'semantica_nlp', 'max_score': 10.0},
    'ACC-08-NLP': {'name': 'Propósito de enlaces (NLP)', 'dimension': 'semantica_nlp', 'max_score': 1.0},
    'ACC-09': {'name': 'Claridad y legibilidad NLP', 'dimension': 'semantica_nlp', 'max_score': 10.0},
    'ACC-09-NLP': {'name': 'Encabezados y etiquetas (NLP)', 'dimension': 'semantica_nlp', 'max_score': 1.0},
    'ACC-10': {'name': 'Subtítulos en multimedia', 'dimension': 'accesibilidad', 'max_score': 10.0},
    # Usabilidad (IDs reales: IDEN-*, NAV-*, PART-*)
    'IDEN-01': {'name': 'Nombre institución en título', 'dimension': 'usabilidad', 'max_score': 14.0},
    'IDEN-02': {'name': "Leyenda 'Bolivia a tu servicio'", 'dimension': 'usabilidad', 'max_score': 12.0},
    'NAV-01': {'name': 'Menú de navegación', 'dimension': 'usabilidad', 'max_score': 16.0},
    'NAV-02': {'name': 'Buscador interno', 'dimension': 'usabilidad', 'max_score': 14.0},
    'PART-01': {'name': 'Enlaces a redes sociales (mín. 2)', 'dimension': 'usabilidad', 'max_score': 12.0},
    'PART-02': {'name': 'Enlace a app mensajería', 'dimension': 'usabilidad', 'max_score': 10.0},
    'PART-03': {'name': 'Enlace a correo electrónico', 'dimension': 'usabilidad', 'max_score': 10.0},
    'PART-04': {'name': 'Enlace a teléfono', 'dimension': 'usabilidad', 'max_score': 8.0},
    'PART-05': {'name': 'Botones compartir en RRSS', 'dimension': 'usabilidad', 'max_score': 4.0},
    # Semantica tecnica (IDs reales: SEM-*, SEO-*, FMT-*)
    'SEM-01': {'name': 'Uso de DOCTYPE HTML5', 'dimension': 'semantica_tecnica', 'max_score': 10.0},
    'SEM-02': {'name': 'Codificación UTF-8', 'dimension': 'semantica_tecnica', 'max_score': 10.0},
    'SEM-03': {'name': 'Elementos semánticos HTML5', 'dimension': 'semantica_tecnica', 'max_score': 14.0},
    'SEM-04': {'name': 'Separación contenido-presentación', 'dimension': 'semantica_tecnica', 'max_score': 10.0},
    'SEO-01': {'name': 'Meta descripción', 'dimension': 'semantica_tecnica', 'max_score': 8.0},
    'SEO-02': {'name': 'Meta Keywords', 'dimension': 'semantica_tecnica', 'max_score': 4.0},
    'SEO-03': {'name': 'Meta viewport', 'dimension': 'semantica_tecnica', 'max_score': 12.0},
    'SEO-04': {'name': 'Jerarquía de headings válida', 'dimension': 'semantica_tecnica', 'max_score': 14.0},
    'FMT-01': {'name': 'Uso de formatos abiertos', 'dimension': 'semantica_tecnica', 'max_score': 10.0},
    'FMT-02': {'name': 'Imágenes optimizadas', 'dimension': 'semantica_tecnica', 'max_score': 8.0},
    # Soberania digital (IDs reales: PROH-*)
    'PROH-01': {'name': 'Sin iframes externos', 'dimension': 'soberania', 'max_score': 25.0},
    'PROH-02': {'name': 'Sin CDNs externos no autorizados', 'dimension': 'soberania', 'max_score': 25.0},
    'PROH-03': {'name': 'Sin fuentes externas', 'dimension': 'soberania', 'max_score': 20.0},
    'PROH-04': {'name': 'Sin trackers externos', 'dimension': 'soberania', 'max_score': 30.0},
}


def _status_to_score(status: str, max_score: float) -> float:
    """Convierte estado de criterio a puntaje numerico."""
    mapping = {'pass': max_score, 'partial': max_score * 0.5, 'fail': 0.0, 'na': 0.0}
    return mapping.get(status, 0.0)


def _calculate_scores(criteria_results: list[CriteriaResult]) -> dict:
    """
    Calcula puntajes por dimension y puntaje total a partir de CriteriaResult.

    Normaliza alias de dimensiones (ej: 'semantica' -> 'semantica_tecnica').

    Returns:
        dict con puntaje por dimension (0-100) y total ponderado.
    """
    dim_totals: dict[str, dict] = {
        dim: {'score': 0.0, 'max': 0.0, 'passed': 0, 'failed': 0, 'partial': 0, 'na': 0}
        for dim in _DIMENSION_WEIGHTS
    }

    for cr in criteria_results:
        # Normalizar alias de dimensiones
        dim = _DIMENSION_ALIASES.get(cr.dimension, cr.dimension)
        if dim not in dim_totals:
            continue
        bucket = dim_totals[dim]
        bucket['max'] += cr.max_score
        bucket['score'] += cr.score
        if cr.status == 'pass':
            bucket['passed'] += 1
        elif cr.status == 'fail':
            bucket['failed'] += 1
        elif cr.status == 'partial':
            bucket['partial'] += 1
        else:
            bucket['na'] += 1

    scores: dict = {}
    total_weighted = 0.0
    for dim, weight in _DIMENSION_WEIGHTS.items():
        bucket = dim_totals[dim]
        pct = (bucket['score'] / bucket['max'] * 100) if bucket['max'] > 0 else 0.0
        pct = round(pct, 2)
        scores[dim] = {
            'percentage': pct,
            'passed': bucket['passed'],
            'failed': bucket['failed'],
            'partial': bucket['partial'],
            'not_applicable': bucket['na'],
        }
        total_weighted += pct * weight

    scores['total'] = round(total_weighted, 2)
    return scores


# ============================================================================
# ENDPOINT: Guardar evaluación manual
# ============================================================================

@router.post(
    "/save",
    response_model=SaveEvaluationResponse,
    summary="Guardar evaluación manual",
    description="""
Guarda los resultados de una evaluación manual realizada por un evaluador.

**Proceso:**
1. Busca la institución y su sitio web asociado
2. Crea un registro de evaluación completada
3. Guarda los resultados de cada criterio
4. Calcula puntajes por dimensión y total
5. Retorna evaluation_id y scores
""",
    responses={
        200: {"description": "Evaluación guardada exitosamente"},
        404: {"description": "Institución no encontrada"},
        422: {"description": "Datos inválidos"},
        500: {"description": "Error interno"},
    }
)
async def save_evaluation(
    request: SaveEvaluationRequest,
    db: Session = Depends(get_db)
):
    """
    Guarda una evaluación manual con sus resultados de criterios.

    - **institution_id**: ID de la institución evaluada
    - **criteria_results**: Array de {criterion_id, status, observations}
    """
    # 1. Buscar institución
    institution = db.query(Institution).filter(Institution.id == request.institution_id).first()
    if not institution:
        raise HTTPException(
            status_code=404,
            detail=f"Institución con id={request.institution_id} no encontrada"
        )

    # 2. Buscar o crear Website vinculado a la institución
    website = db.query(Website).filter(Website.domain == institution.domain).first()
    if not website:
        website = Website(
            url=f"https://{institution.domain}",
            domain=institution.domain,
            institution_name=institution.name,
        )
        db.add(website)
        db.flush()  # Obtener ID sin hacer commit aún

    # 3. Crear registro de evaluación
    now = datetime.utcnow()
    evaluation = Evaluation(
        website_id=website.id,
        status=EvaluationStatus.IN_PROGRESS,
        started_at=now,
    )
    db.add(evaluation)
    db.flush()  # Obtener evaluation.id

    # 4. Crear CriteriaResult para cada criterio recibido
    criteria_records: list[CriteriaResult] = []
    for item in request.criteria_results:
        meta = _CRITERIA_META.get(item.criterion_id, {
            'name': item.criterion_id,
            'dimension': 'accesibilidad',
            'max_score': 10.0,
        })
        # Usar max_score del frontend si viene, si no del meta
        effective_max_score = item.max_score if item.max_score is not None else meta['max_score']
        # Usar score real del frontend si viene, si no calcular desde status
        effective_score = item.score if item.score is not None else _status_to_score(item.status, effective_max_score)
        cr = CriteriaResult(
            evaluation_id=evaluation.id,
            criteria_id=item.criterion_id,
            criteria_name=meta['name'],
            dimension=meta['dimension'],
            lineamiento=item.criterion_id,
            status=item.status,
            score=effective_score,
            max_score=effective_max_score,
            details={'observations': item.observations} if item.observations else {},
            evidence=[],
        )
        db.add(cr)
        criteria_records.append(cr)

    # 5. Calcular puntajes
    # Si el frontend envía scores_override (calculados por el engine), usarlos directamente
    if request.scores_override:
        scores = request.scores_override
        # Asegurar que el campo 'total' existe
        if 'total' not in scores:
            scores = _calculate_scores(criteria_records)
    else:
        scores = _calculate_scores(criteria_records)

    # Helper: extrae 'percentage' de un valor que puede ser dict, número o None
    def _pct(val):
        if val is None:
            return 0.0
        if isinstance(val, dict):
            return float(val.get('percentage', 0) or 0)
        return float(val)

    # 6. Actualizar evaluación con puntajes y marcar como completada
    evaluation.score_accessibility = _pct(scores.get('accesibilidad'))
    evaluation.score_usability = _pct(scores.get('usabilidad'))
    # score_semantic_web combina semántica técnica y NLP (promedio), igual que el engine
    sem_tecnica = _pct(scores.get('semantica_tecnica') or scores.get('semantica'))
    sem_nlp = _pct(scores.get('semantica_nlp'))
    if sem_nlp > 0:
        evaluation.score_semantic_web = (sem_tecnica + sem_nlp) / 2
    else:
        evaluation.score_semantic_web = sem_tecnica
    evaluation.score_digital_sovereignty = _pct(scores.get('soberania'))
    evaluation.score_total = float(scores.get('total', 0) or 0)
    evaluation.status = EvaluationStatus.COMPLETED
    evaluation.completed_at = datetime.utcnow()

    try:
        db.commit()
        db.refresh(evaluation)
        logger.info(
            f"Evaluación manual guardada: id={evaluation.id}, "
            f"institution={institution.name}, total={evaluation.score_total:.1f}%"
        )
    except Exception as e:
        db.rollback()
        logger.error(f"Error guardando evaluación: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error al guardar la evaluación: {str(e)}")

    return SaveEvaluationResponse(
        evaluation_id=evaluation.id,
        institution_id=institution.id,
        scores=scores,
        total_score=evaluation.score_total,
        created_at=evaluation.completed_at.isoformat(),
    )


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
