"""
Rutas de estadísticas y métricas para el Dashboard Administrativo.

Provee endpoints para:
- Evaluaciones por día (agrupadas por evaluador)
- Actividad por hora en un día
- Calendario mensual con conteo de evaluaciones
- Métricas generales del sistema
"""

import logging
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, date, timedelta
from app.database import get_db
from app.models.database_models import Evaluation, User, Website, Institution, Followup
from app.auth.dependencies import allow_admin_secretary

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/stats", tags=["statistics"])

# Bolivia es UTC-4 (sin horario de verano)
BOLIVIA_UTC_OFFSET = timedelta(hours=-4)


def bolivia_day_to_utc_range(date_str: str):
    """
    Convierte una fecha en zona horaria Bolivia (UTC-4) a un rango UTC
    para filtrar registros almacenados en UTC.

    Ejemplo: '2026-02-13' Bolivia → [2026-02-13T04:00Z, 2026-02-14T04:00Z)
    """
    target_date = datetime.strptime(date_str, "%Y-%m-%d").date()
    # Inicio del día en Bolivia = medianoche Bolivia = 04:00 UTC
    start_utc = datetime(target_date.year, target_date.month, target_date.day, 0, 0, 0) - BOLIVIA_UTC_OFFSET
    end_utc = start_utc + timedelta(days=1)
    return start_utc, end_utc


def utc_to_bolivia_hour(dt_utc: datetime) -> int:
    """Convierte un datetime UTC al hour en zona horaria Bolivia (UTC-4)."""
    bolivia_dt = dt_utc + BOLIVIA_UTC_OFFSET
    return bolivia_dt.hour


@router.get("/daily-evaluations")
async def get_daily_evaluations(
    date: str = Query(..., description="Fecha en formato YYYY-MM-DD"),
    current_user=Depends(allow_admin_secretary),
    db: Session = Depends(get_db)
):
    """Obtener evaluaciones realizadas en un día específico, agrupadas por evaluador."""
    # Convertir fecha Bolivia a rango UTC para consultar correctamente
    start_utc, end_utc = bolivia_day_to_utc_range(date)
    logger.info(f"daily-evaluations: fecha={date}, rango UTC=[{start_utc}, {end_utc})")

    evaluations = db.query(Evaluation).filter(
        Evaluation.started_at >= start_utc,
        Evaluation.started_at < end_utc
    ).all()

    logger.info(f"Encontradas {len(evaluations)} evaluaciones")

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
        # Hora en zona horaria Bolivia para mostrar al usuario
        bolivia_hour = utc_to_bolivia_hour(ev.started_at) if ev.started_at else 0

        # Obtener el nombre actual de la institución desde la tabla institutions
        # usando el dominio del website (evita nombres desactualizados en websites)
        institution_name = "N/A"
        if website:
            institution = db.query(Institution).filter(Institution.domain == website.domain).first()
            if institution:
                institution_name = institution.name
            else:
                institution_name = website.institution_name  # fallback

        evaluations_by_evaluator[evaluator_id]["evaluations"].append({
            "id": ev.id,
            "institution_name": institution_name,
            "website_url": website.url if website else "N/A",
            "domain": website.domain if website else "N/A",
            "score": round(ev.score_total, 2) if ev.score_total is not None else None,
            "status": ev.status.value if ev.status else "unknown",
            "started_at": ev.started_at.isoformat() if ev.started_at else None,
            "completed_at": ev.completed_at.isoformat() if ev.completed_at else None,
            "hour": bolivia_hour,
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
    """Obtener actividad por hora en un día específico (horas en zona horaria Bolivia)."""
    # Convertir fecha Bolivia a rango UTC
    start_utc, end_utc = bolivia_day_to_utc_range(date)
    logger.info(f"hourly-activity: fecha={date}, rango UTC=[{start_utc}, {end_utc})")

    evaluations = db.query(Evaluation).filter(
        Evaluation.started_at >= start_utc,
        Evaluation.started_at < end_utc
    ).all()

    logger.info(f"Encontradas {len(evaluations)} evaluaciones para gráfico")

    # Agrupar por hora Bolivia (no UTC)
    hourly_data = {hour: 0 for hour in range(24)}

    for ev in evaluations:
        if ev.started_at:
            hour = utc_to_bolivia_hour(ev.started_at)
            hourly_data[hour] += 1
            logger.info(f"Eval {ev.id}: UTC={ev.started_at.hour}h → Bolivia={hour}h")

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
    """Obtener conteo de evaluaciones por cada día del mes (en zona horaria Bolivia)."""
    import calendar as cal_module

    # Rango UTC que cubre todo el mes en Bolivia
    first_day_str = f"{year}-{month:02d}-01"
    days_in_month = cal_module.monthrange(year, month)[1]
    last_day_str = f"{year}-{month:02d}-{days_in_month:02d}"

    start_utc, _ = bolivia_day_to_utc_range(first_day_str)
    _, end_utc = bolivia_day_to_utc_range(last_day_str)

    evaluations = db.query(Evaluation).filter(
        Evaluation.started_at >= start_utc,
        Evaluation.started_at < end_utc
    ).all()

    # Agrupar por fecha Bolivia
    calendar_data = {}
    for ev in evaluations:
        if ev.started_at:
            bolivia_dt = ev.started_at + BOLIVIA_UTC_OFFSET
            day_str = bolivia_dt.date().isoformat()
            calendar_data[day_str] = calendar_data.get(day_str, 0) + 1

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
