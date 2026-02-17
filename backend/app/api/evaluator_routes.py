"""
Rutas del Dashboard del Evaluador.

Provee endpoints para estadísticas personales del evaluador:
- Estadísticas generales (total evaluaciones, tendencia, promedio, etc.)
- Top instituciones por score
- Instituciones que más mejoraron
- Actividad mensual
- Evaluaciones recientes
"""

import logging
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from datetime import datetime, date
from app.database import get_db
from app.models.database_models import Evaluation, Website, Followup, User
from app.auth.dependencies import get_current_active_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/evaluator", tags=["evaluator"])


@router.get("/dashboard/stats")
async def get_evaluator_stats(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Estadísticas generales del evaluador autenticado."""

    # Total de evaluaciones del evaluador
    total_evaluations = db.query(Evaluation).filter(
        Evaluation.evaluator_id == current_user.id
    ).count()

    # Evaluaciones este mes
    now = datetime.now()
    month_start = date(now.year, now.month, 1)
    evaluations_this_month = db.query(Evaluation).filter(
        Evaluation.evaluator_id == current_user.id,
        Evaluation.started_at >= month_start
    ).count()

    # Mes anterior para calcular tendencia
    if now.month == 1:
        prev_month_start = date(now.year - 1, 12, 1)
        prev_month_end = date(now.year, 1, 1)
    else:
        prev_month_start = date(now.year, now.month - 1, 1)
        prev_month_end = month_start

    evaluations_last_month = db.query(Evaluation).filter(
        Evaluation.evaluator_id == current_user.id,
        Evaluation.started_at >= prev_month_start,
        Evaluation.started_at < prev_month_end
    ).count()

    # Calcular tendencia porcentual
    if evaluations_last_month > 0:
        trend = ((evaluations_this_month - evaluations_last_month) / evaluations_last_month) * 100
    else:
        trend = 100.0 if evaluations_this_month > 0 else 0.0

    # Instituciones únicas evaluadas
    unique_institutions = db.query(
        func.count(func.distinct(Website.institution_name))
    ).join(
        Evaluation, Evaluation.website_id == Website.id
    ).filter(
        Evaluation.evaluator_id == current_user.id
    ).scalar() or 0

    # Promedio de cumplimiento
    avg_score = db.query(func.avg(Evaluation.score_total)).filter(
        Evaluation.evaluator_id == current_user.id
    ).scalar() or 0.0

    # Seguimientos pendientes de validar (via evaluation -> evaluator)
    pending_followups = db.query(Followup).join(
        Evaluation, Evaluation.id == Followup.evaluation_id
    ).filter(
        Evaluation.evaluator_id == current_user.id,
        Followup.status == "pending"
    ).count()

    return {
        "total_evaluations": total_evaluations,
        "evaluations_this_month": evaluations_this_month,
        "trend_percentage": round(trend, 1),
        "unique_institutions": unique_institutions,
        "average_score": round(float(avg_score), 2),
        "pending_followups": pending_followups
    }


@router.get("/dashboard/top-institutions")
async def get_top_institutions(
    limit: int = Query(3, ge=1, le=10),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Top instituciones con mejor score evaluadas por el evaluador actual."""

    # Subquery: última evaluación por institución realizada por este evaluador
    subquery = db.query(
        Website.institution_name,
        func.max(Evaluation.started_at).label("last_eval")
    ).join(
        Evaluation, Evaluation.website_id == Website.id
    ).filter(
        Evaluation.evaluator_id == current_user.id
    ).group_by(
        Website.institution_name
    ).subquery()

    top_institutions = db.query(
        Website.institution_name,
        Evaluation.score_total,
        Evaluation.started_at
    ).join(
        Evaluation, Evaluation.website_id == Website.id
    ).join(
        subquery,
        (Website.institution_name == subquery.c.institution_name) &
        (Evaluation.started_at == subquery.c.last_eval)
    ).filter(
        Evaluation.evaluator_id == current_user.id
    ).order_by(
        desc(Evaluation.score_total)
    ).limit(limit).all()

    return [
        {
            "name": inst.institution_name,
            "score": round(float(inst.score_total), 2),
            "evaluated_at": inst.started_at.isoformat()
        }
        for inst in top_institutions
    ]


@router.get("/dashboard/improved-institutions")
async def get_improved_institutions(
    limit: int = Query(3, ge=1, le=10),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Instituciones que más mejoraron entre su primera y última evaluación."""

    # Instituciones con al menos 2 evaluaciones de este evaluador
    institutions_with_multiple_evals = db.query(
        Website.institution_name
    ).join(
        Evaluation, Evaluation.website_id == Website.id
    ).filter(
        Evaluation.evaluator_id == current_user.id
    ).group_by(
        Website.institution_name
    ).having(
        func.count(Evaluation.id) >= 2
    ).all()

    improvements = []

    for (inst_name,) in institutions_with_multiple_evals:
        # Primera y última evaluación ordenadas cronológicamente
        evals = db.query(Evaluation).join(
            Website, Website.id == Evaluation.website_id
        ).filter(
            Website.institution_name == inst_name,
            Evaluation.evaluator_id == current_user.id
        ).order_by(
            Evaluation.started_at
        ).all()

        if len(evals) >= 2:
            first_score = float(evals[0].score_total)
            last_score = float(evals[-1].score_total)
            improvement = last_score - first_score

            if improvement > 0:
                improvements.append({
                    "name": inst_name,
                    "first_score": round(first_score, 2),
                    "last_score": round(last_score, 2),
                    "improvement": round(improvement, 2)
                })

    # Ordenar por mayor mejora
    improvements.sort(key=lambda x: x["improvement"], reverse=True)

    return improvements[:limit]


@router.get("/dashboard/monthly-activity")
async def get_monthly_activity(
    months: int = Query(6, ge=1, le=12),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Actividad mensual del evaluador para los últimos N meses."""

    now = datetime.now()
    activity = []

    for i in range(months - 1, -1, -1):
        target_month = now.month - i
        target_year = now.year

        while target_month <= 0:
            target_month += 12
            target_year -= 1

        month_start = date(target_year, target_month, 1)

        if target_month == 12:
            month_end = date(target_year + 1, 1, 1)
        else:
            month_end = date(target_year, target_month + 1, 1)

        count = db.query(Evaluation).filter(
            Evaluation.evaluator_id == current_user.id,
            Evaluation.started_at >= month_start,
            Evaluation.started_at < month_end
        ).count()

        month_name = month_start.strftime("%b")

        activity.append({
            "month": month_name,
            "count": count
        })

    return activity


@router.get("/dashboard/recent-evaluations")
async def get_recent_evaluations(
    limit: int = Query(5, ge=1, le=20),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Evaluaciones recientes del evaluador autenticado."""

    evaluations = db.query(Evaluation).filter(
        Evaluation.evaluator_id == current_user.id
    ).order_by(
        desc(Evaluation.started_at)
    ).limit(limit).all()

    result = []

    for ev in evaluations:
        institution_name = "Desconocida"

        if ev.website_id:
            website = db.query(Website).filter(Website.id == ev.website_id).first()
            if website and website.institution_name:
                institution_name = website.institution_name

        result.append({
            "id": ev.id,
            "institution_name": institution_name,
            "score": round(float(ev.score_total), 2),
            "evaluated_at": ev.started_at.isoformat() if ev.started_at else None,
            "status": "Completada"
        })

    return result
