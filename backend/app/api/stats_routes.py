"""
Rutas de estadísticas y métricas para el Dashboard Administrativo.

Provee endpoints para:
- Evaluaciones por día (agrupadas por evaluador)
- Actividad por hora en un día
- Calendario mensual con conteo de evaluaciones
- Métricas generales del sistema
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, date
from app.database import get_db
from app.models.database_models import Evaluation, User, Website, Followup
from app.auth.dependencies import allow_admin_secretary

router = APIRouter(prefix="/stats", tags=["statistics"])


@router.get("/daily-evaluations")
async def get_daily_evaluations(
    date: str = Query(..., description="Fecha en formato YYYY-MM-DD"),
    current_user=Depends(allow_admin_secretary),
    db: Session = Depends(get_db)
):
    """Obtener evaluaciones realizadas en un día específico, agrupadas por evaluador."""
    target_date = datetime.strptime(date, "%Y-%m-%d").date()

    evaluations = db.query(Evaluation).filter(
        func.date(Evaluation.started_at) == target_date
    ).all()

    evaluations_by_evaluator = {}
    for ev in evaluations:
        evaluator_id = ev.evaluator_id
        if not evaluator_id:
            evaluator_id = 0  # Evaluaciones sin evaluador asignado

        if evaluator_id not in evaluations_by_evaluator:
            if evaluator_id == 0:
                evaluations_by_evaluator[evaluator_id] = {
                    "evaluator_name": "Sin evaluador",
                    "evaluator_email": "",
                    "evaluations": []
                }
            else:
                evaluator = db.query(User).filter(User.id == evaluator_id).first()
                if evaluator:
                    evaluations_by_evaluator[evaluator_id] = {
                        "evaluator_name": evaluator.full_name or evaluator.username,
                        "evaluator_email": evaluator.email,
                        "evaluations": []
                    }
                else:
                    evaluations_by_evaluator[evaluator_id] = {
                        "evaluator_name": f"Evaluador #{evaluator_id}",
                        "evaluator_email": "",
                        "evaluations": []
                    }

        website = db.query(Website).filter(Website.id == ev.website_id).first()

        evaluations_by_evaluator[evaluator_id]["evaluations"].append({
            "id": ev.id,
            "institution_name": website.institution_name if website else "N/A",
            "domain": website.domain if website else "N/A",
            "score": round(ev.score_total, 2) if ev.score_total is not None else None,
            "status": ev.status.value if ev.status else "unknown",
            "started_at": ev.started_at.isoformat() if ev.started_at else None,
            "completed_at": ev.completed_at.isoformat() if ev.completed_at else None,
        })

    return {
        "date": date,
        "total_evaluations": len(evaluations),
        "evaluations_by_evaluator": list(evaluations_by_evaluator.values())
    }


@router.get("/hourly-activity")
async def get_hourly_activity(
    date: str = Query(..., description="Fecha en formato YYYY-MM-DD"),
    current_user=Depends(allow_admin_secretary),
    db: Session = Depends(get_db)
):
    """Obtener actividad por hora en un día específico."""
    target_date = datetime.strptime(date, "%Y-%m-%d").date()

    evaluations = db.query(Evaluation).filter(
        func.date(Evaluation.started_at) == target_date
    ).all()

    hourly_data = {hour: 0 for hour in range(24)}

    for ev in evaluations:
        hour = ev.started_at.hour
        hourly_data[hour] += 1

    return {
        "date": date,
        "hourly_activity": [
            {"hour": hour, "count": count}
            for hour, count in sorted(hourly_data.items())
        ]
    }


@router.get("/monthly-calendar")
async def get_monthly_calendar(
    year: int = Query(...),
    month: int = Query(...),
    current_user=Depends(allow_admin_secretary),
    db: Session = Depends(get_db)
):
    """Obtener conteo de evaluaciones por cada día del mes."""
    start_date = date(year, month, 1)
    if month == 12:
        end_date = date(year + 1, 1, 1)
    else:
        end_date = date(year, month + 1, 1)

    evaluations = db.query(
        func.date(Evaluation.started_at).label('ev_date'),
        func.count(Evaluation.id).label('count')
    ).filter(
        Evaluation.started_at >= start_date,
        Evaluation.started_at < end_date
    ).group_by(
        func.date(Evaluation.started_at)
    ).all()

    calendar_data = {}
    for ev_date, count in evaluations:
        if ev_date:
            calendar_data[ev_date.isoformat()] = count

    return {
        "year": year,
        "month": month,
        "days": calendar_data
    }


@router.get("/overview")
async def get_overview(
    current_user=Depends(allow_admin_secretary),
    db: Session = Depends(get_db)
):
    """Métricas generales del sistema."""
    total_websites = db.query(Website).count()
    total_evaluations = db.query(Evaluation).count()

    now = datetime.now()
    month_start = date(now.year, now.month, 1)
    evaluations_this_month = db.query(Evaluation).filter(
        Evaluation.started_at >= month_start
    ).count()

    avg_score = db.query(func.avg(Evaluation.score_total)).scalar() or 0

    pending_followups = db.query(Followup).filter(
        Followup.status == "pending"
    ).count()

    return {
        "total_websites": total_websites,
        "total_evaluations": total_evaluations,
        "evaluations_this_month": evaluations_this_month,
        "average_score": round(float(avg_score), 2),
        "pending_followups": pending_followups
    }
