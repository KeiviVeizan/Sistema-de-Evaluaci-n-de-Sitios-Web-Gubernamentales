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
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from app.database import get_db
from app.evaluator.evaluation_engine import evaluar_url as ejecutar_evaluacion
from app.models.database_models import (
    Evaluation, EvaluationStatus, CriteriaResult, Website, NLPAnalysis, Institution, User, Followup
)
from app.auth.dependencies import get_current_active_user
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
from app.services.report_generator import generate_evaluation_report, get_report_filename

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

# Alias: normaliza variantes de nombre de dimensión al nombre canónico interno
_DIMENSION_ALIASES = {
    # Semántica técnica
    'semantica': 'semantica_tecnica',
    'Semántica Técnica': 'semantica_tecnica',
    'semantica tecnica': 'semantica_tecnica',
    # Semántica NLP
    'Semántica NLP': 'semantica_nlp',
    'semantica nlp': 'semantica_nlp',
    'Análisis Semántico (IA)': 'semantica_nlp',
    'Análisis Semántico IA': 'semantica_nlp',
    'análisis semántico (ia)': 'semantica_nlp',
    'nlp': 'semantica_nlp',
    'NLP': 'semantica_nlp',
    # Soberanía digital
    'soberania_digital': 'soberania',
    'Soberanía Digital': 'soberania',
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
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Guarda una evaluación manual con sus resultados de criterios.

    - **institution_id**: ID de la institución evaluada
    - **criteria_results**: Array de {criterion_id, status, observations}
    """
    # ── DEBUG ────────────────────────────────────────────────────────────────
    logger.info("=" * 60)
    logger.info("DEBUG save_evaluation: datos recibidos del frontend")
    logger.info(f"  institution_id : {request.institution_id}")
    logger.info(f"  criteria_results count: {len(request.criteria_results)}")
    logger.info(f"  scores_override recibido: {request.scores_override}")
    for item in request.criteria_results:
        meta = _CRITERIA_META.get(item.criterion_id, {})
        logger.info(
            f"  criterio: id={item.criterion_id!r:20s}  "
            f"status={item.status!r:10s}  "
            f"score={item.score}  max_score={item.max_score}  "
            f"meta_dimension={meta.get('dimension', 'NO_EN_META')!r}"
        )
    logger.info("=" * 60)
    # ── FIN DEBUG ────────────────────────────────────────────────────────────

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
        evaluator_id=current_user.id,
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

    # ── DEBUG: dimensiones asignadas a cada criterio guardado ────────────────
    logger.info("DEBUG save_evaluation: criteria_records a guardar en BD")
    from collections import defaultdict
    dim_summary: dict = defaultdict(list)
    for cr in criteria_records:
        dim_summary[cr.dimension].append(f"{cr.criteria_id}(score={cr.score}/{cr.max_score})")
    for dim, items in sorted(dim_summary.items()):
        logger.info(f"  dimension={dim!r}: {items}")
    # ── FIN DEBUG ────────────────────────────────────────────────────────────

    # 5. Calcular puntajes
    # Si el frontend envía scores_override (calculados por el engine), usarlos directamente
    if request.scores_override:
        scores = request.scores_override
        # Asegurar que el campo 'total' existe
        if 'total' not in scores:
            scores = _calculate_scores(criteria_records)
        # Si semantica_nlp viene null en el override pero hay criterios NLP guardados,
        # calcular el score NLP desde esos criterios para no perder el 0% por null
        if scores.get('semantica_nlp') is None:
            recalc = _calculate_scores(criteria_records)
            if recalc.get('semantica_nlp', {}).get('percentage', 0) > 0:
                scores = dict(scores)  # copia para no mutar el original
                scores['semantica_nlp'] = recalc['semantica_nlp']
                logger.info(
                    f"semantica_nlp era null en scores_override; "
                    f"recalculado desde criterios: {scores['semantica_nlp']}"
                )
    else:
        scores = _calculate_scores(criteria_records)

    # ── DEBUG: scores finales usados para guardar ────────────────────────────
    logger.info("DEBUG save_evaluation: scores finales a persistir")
    logger.info(f"  fuente: {'scores_override' if request.scores_override else '_calculate_scores'}")
    for key, val in scores.items():
        if isinstance(val, dict):
            logger.info(f"  {key}: percentage={val.get('percentage')}  (dict completo: {val})")
        else:
            logger.info(f"  {key}: {val}")
    # ── FIN DEBUG ────────────────────────────────────────────────────────────

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

    # ── DEBUG: valores finales en el objeto Evaluation antes del commit ───────
    logger.info("DEBUG save_evaluation: campos evaluation antes de commit")
    logger.info(f"  score_accessibility       = {evaluation.score_accessibility}")
    logger.info(f"  score_usability           = {evaluation.score_usability}")
    logger.info(f"  score_semantic_web        = {evaluation.score_semantic_web}  "
                f"(sem_tecnica={sem_tecnica}, sem_nlp={sem_nlp})")
    logger.info(f"  score_digital_sovereignty = {evaluation.score_digital_sovereignty}")
    logger.info(f"  score_total               = {evaluation.score_total}")
    # ── FIN DEBUG ────────────────────────────────────────────────────────────

    # 7. Guardar NLPAnalysis si scores_override contiene semantica_nlp
    nlp_override = scores.get('semantica_nlp') if isinstance(scores, dict) else None
    if isinstance(nlp_override, dict) and nlp_override.get('percentage', 0) > 0:
        wcag_raw = nlp_override.get('wcag_compliance', {})
        nlp_record = NLPAnalysis(
            evaluation_id=evaluation.id,
            nlp_global_score=float(nlp_override.get('percentage', 0)),
            coherence_score=float(nlp_override.get('coherence', 0)),
            ambiguity_score=float(nlp_override.get('ambiguity', 0)),
            clarity_score=float(nlp_override.get('clarity', 0)),
            wcag_compliance=wcag_raw if isinstance(wcag_raw, dict) else {},
            coherence_details={},
            ambiguity_details={},
            clarity_details={},
            recommendations=[],
        )
        db.add(nlp_record)
        logger.info(
            f"✓ NLPAnalysis creado desde scores_override: "
            f"global={nlp_record.nlp_global_score}, "
            f"coherence={nlp_record.coherence_score}, "
            f"ambiguity={nlp_record.ambiguity_score}, "
            f"clarity={nlp_record.clarity_score}"
        )
    else:
        logger.info("✗ semantica_nlp no presente o percentage=0 en scores_override; NLPAnalysis no creado")

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
# Mis evaluaciones (para evaluador)
# ============================================================================

@router.get(
    "/my-evaluations",
    summary="Mis evaluaciones como evaluador",
    description="Retorna todas las evaluaciones que el evaluador autenticado ha realizado, "
                "incluyendo el estado de sus seguimientos."
)
async def get_my_evaluations(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Obtener evaluaciones que YO hice como evaluador, con sus seguimientos."""
    evaluations = (
        db.query(Evaluation)
        .filter(Evaluation.evaluator_id == current_user.id)
        .order_by(Evaluation.completed_at.desc())
        .all()
    )

    result = []
    for evaluation in evaluations:
        website = db.query(Website).filter(Website.id == evaluation.website_id).first()
        institution = (
            db.query(Institution).filter(Institution.domain == website.domain).first()
            if website else None
        )

        followups = (
            db.query(Followup)
            .filter(Followup.evaluation_id == evaluation.id)
            .all()
        )

        result.append({
            "id": evaluation.id,
            "institution_name": institution.name if institution else (website.domain if website else ""),
            "website_url": website.domain if website else "",
            "overall_score": evaluation.score_total,
            "created_at": (evaluation.completed_at or evaluation.started_at).isoformat()
                if (evaluation.completed_at or evaluation.started_at) else None,
            "followups": [
                {
                    "id": f.id,
                    "status": f.status,
                    "due_date": f.due_date.isoformat() if f.due_date else None,
                }
                for f in followups
            ],
        })

    return result


# ============================================================================
# Evaluaciones por institución (para entity_user)
# ============================================================================

@router.get(
    "/by-institution/{institution_id}",
    summary="Listar evaluaciones de una institución",
    description="Retorna las evaluaciones del sitio web de la institución indicada. "
                "Un entity_user solo puede consultar su propia institución.",
)
async def get_evaluations_by_institution(
    institution_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Lista todas las evaluaciones asociadas al dominio de la institución.

    - **institution_id**: ID de la institución
    """
    # Verificar que la institución existe
    institution = db.query(Institution).filter(Institution.id == institution_id).first()
    if not institution:
        raise HTTPException(status_code=404, detail="Institución no encontrada")

    # Control de acceso: entity_user solo puede ver su propia institución
    if current_user.role.value == "entity_user":
        if current_user.institution_id != institution_id:
            raise HTTPException(
                status_code=403,
                detail="No tiene permisos para ver las evaluaciones de esta institución",
            )

    # Obtener evaluaciones a través del dominio compartido entre Institution y Website
    evaluations = (
        db.query(Evaluation)
        .join(Website, Evaluation.website_id == Website.id)
        .filter(Website.domain == institution.domain)
        .order_by(Evaluation.started_at.desc())
        .all()
    )

    result = []
    for ev in evaluations:
        result.append({
            "id": ev.id,
            "website_id": ev.website_id,
            "website_url": ev.website.url if ev.website else "",
            "institution_name": institution.name,
            "score_total": ev.score_total,
            "score_accessibility": ev.score_accessibility,
            "score_usability": ev.score_usability,
            "score_semantic_web": ev.score_semantic_web,
            "score_digital_sovereignty": ev.score_digital_sovereignty,
            "status": ev.status,
            "started_at": ev.started_at.isoformat() if ev.started_at else None,
            "completed_at": ev.completed_at.isoformat() if ev.completed_at else None,
        })

    return result


# ============================================================================
# Generar informe PDF de una evaluación
# ============================================================================

@router.get(
    "/{evaluation_id}/report",
    summary="Descargar informe PDF",
    description="Genera y descarga un informe PDF con los resultados de la evaluación.",
    responses={
        200: {"description": "PDF generado exitosamente", "content": {"application/pdf": {}}},
        404: {"description": "Evaluación no encontrada"},
        500: {"description": "Error generando el informe"},
    }
)
async def download_evaluation_report(
    evaluation_id: int,
    db: Session = Depends(get_db)
):
    """
    Genera un informe PDF para la evaluación indicada.

    - **evaluation_id**: ID de la evaluación
    """
    # Validar que la evaluación existe
    evaluation = db.query(Evaluation).filter(Evaluation.id == evaluation_id).first()
    if not evaluation:
        raise HTTPException(status_code=404, detail="Evaluación no encontrada")

    try:
        pdf_bytes = generate_evaluation_report(evaluation_id, db)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error generando PDF para evaluación {evaluation_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error generando el informe: {str(e)}")

    filename = get_report_filename(evaluation_id, db)
    headers = {
        "Content-Disposition": f'attachment; filename="{filename}"',
    }
    return StreamingResponse(
        iter([pdf_bytes]),
        media_type="application/pdf",
        headers=headers,
    )


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
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Obtiene una evaluación completa por su ID.

    - Admin/Secretary/Evaluator: pueden ver cualquier evaluación.
    - entity_user: solo puede ver evaluaciones de su propia institución.
    """
    evaluation = db.query(Evaluation).filter(Evaluation.id == evaluation_id).first()

    if not evaluation:
        raise HTTPException(status_code=404, detail="Evaluación no encontrada")

    # Control de acceso para entity_user: solo puede ver evaluaciones de su institución
    if current_user.role.value == "entity_user":
        website = db.query(Website).filter(Website.id == evaluation.website_id).first()
        if not website:
            raise HTTPException(status_code=403, detail="No autorizado para ver esta evaluación")
        institution = db.query(Institution).filter(Institution.domain == website.domain).first()
        if not institution or current_user.institution_id != institution.id:
            raise HTTPException(status_code=403, detail="No autorizado para ver esta evaluación")

    # Obtener website
    website = db.query(Website).filter(Website.id == evaluation.website_id).first()

    # Obtener criterios
    db_criteria = db.query(CriteriaResult).filter(
        CriteriaResult.evaluation_id == evaluation_id
    ).all()

    criteria_results = [
        CriteriaResultItem(
            id=cr.id,
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
