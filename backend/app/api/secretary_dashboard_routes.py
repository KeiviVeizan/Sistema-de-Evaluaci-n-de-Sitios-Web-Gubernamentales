"""
Rutas del Dashboard de Secretaría.

Endpoints específicos para el panel del rol secretary:
- Estadísticas consolidadas (usuarios, instituciones)
- Últimos usuarios registrados
- Instituciones más evaluadas
- Registros mensuales de usuarios (tendencia)
- Distribución de usuarios por rol
"""

import logging
from datetime import datetime, date
from dateutil.relativedelta import relativedelta

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, case, extract
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.database_models import (
    User,
    UserRole,
    Institution,
    Evaluation,
    Website,
)
from app.auth.dependencies import allow_admin_secretary

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/secretary/dashboard", tags=["Secretary Dashboard"])


@router.get("/stats")
async def get_secretary_stats(
    current_user=Depends(allow_admin_secretary),
    db: Session = Depends(get_db),
):
    """Estadísticas consolidadas para el dashboard de secretaría."""
    # Total de usuarios que gestiona el secretary (evaluadores + entidades)
    total_evaluators = db.query(User).filter(User.role == UserRole.EVALUATOR).count()
    total_entity_users = db.query(User).filter(User.role == UserRole.ENTITY_USER).count()
    total_managed_users = total_evaluators + total_entity_users

    # Total de instituciones
    total_institutions = db.query(Institution).count()
    active_institutions = db.query(Institution).filter(Institution.is_active == True).count()
    inactive_institutions = total_institutions - active_institutions

    # Usuarios nuevos este mes (evaluadores + entidades)
    now = datetime.utcnow()
    month_start = date(now.year, now.month, 1)
    new_users_this_month = db.query(User).filter(
        User.created_at >= month_start,
        User.role.in_([UserRole.EVALUATOR, UserRole.ENTITY_USER]),
    ).count()

    # Usuarios activos vs inactivos (evaluadores + entidades)
    active_users = db.query(User).filter(
        User.role.in_([UserRole.EVALUATOR, UserRole.ENTITY_USER]),
        User.is_active == True,
    ).count()
    inactive_users = total_managed_users - active_users

    return {
        "total_managed_users": total_managed_users,
        "total_evaluators": total_evaluators,
        "total_entity_users": total_entity_users,
        "total_institutions": total_institutions,
        "active_institutions": active_institutions,
        "inactive_institutions": inactive_institutions,
        "new_users_this_month": new_users_this_month,
        "active_users": active_users,
        "inactive_users": inactive_users,
    }


@router.get("/recent-users")
async def get_recent_users(
    limit: int = Query(default=8, ge=1, le=20),
    current_user=Depends(allow_admin_secretary),
    db: Session = Depends(get_db),
):
    """Últimos usuarios registrados (evaluadores y entidades)."""
    users = (
        db.query(User)
        .filter(User.role.in_([UserRole.EVALUATOR, UserRole.ENTITY_USER]))
        .order_by(User.created_at.desc())
        .limit(limit)
        .all()
    )

    result = []
    for u in users:
        institution_name = None
        if u.institution_id and u.institution:
            institution_name = u.institution.name
        result.append({
            "id": u.id,
            "full_name": u.full_name or u.username,
            "email": u.email,
            "role": u.role.value,
            "is_active": u.is_active,
            "institution_name": institution_name,
            "created_at": u.created_at.isoformat(),
        })

    return {"users": result}


@router.get("/top-institutions")
async def get_top_institutions(
    limit: int = Query(default=6, ge=1, le=20),
    current_user=Depends(allow_admin_secretary),
    db: Session = Depends(get_db),
):
    """Instituciones con más evaluaciones realizadas."""
    # Contar evaluaciones por dominio de institución
    results = (
        db.query(
            Institution.id,
            Institution.name,
            Institution.domain,
            Institution.is_active,
            func.count(Evaluation.id).label("eval_count"),
        )
        .outerjoin(Website, Website.domain == Institution.domain)
        .outerjoin(Evaluation, Evaluation.website_id == Website.id)
        .group_by(Institution.id, Institution.name, Institution.domain, Institution.is_active)
        .order_by(func.count(Evaluation.id).desc())
        .limit(limit)
        .all()
    )

    # Obtener el máximo para calcular porcentajes relativos
    max_count = results[0].eval_count if results and results[0].eval_count > 0 else 1

    return {
        "institutions": [
            {
                "id": r.id,
                "name": r.name,
                "domain": r.domain,
                "is_active": r.is_active,
                "evaluation_count": r.eval_count,
                "percentage": round((r.eval_count / max_count) * 100, 1) if max_count > 0 else 0,
            }
            for r in results
        ]
    }


@router.get("/monthly-registrations")
async def get_monthly_registrations(
    months: int = Query(default=6, ge=1, le=12),
    current_user=Depends(allow_admin_secretary),
    db: Session = Depends(get_db),
):
    """Tendencia de registro de usuarios por mes (evaluadores y entidades)."""
    now = datetime.utcnow()
    start_date = date(now.year, now.month, 1) - relativedelta(months=months - 1)

    # Consultar registros agrupados por año-mes
    results = (
        db.query(
            extract("year", User.created_at).label("year"),
            extract("month", User.created_at).label("month"),
            func.count(User.id).label("count"),
            func.sum(case((User.role == UserRole.EVALUATOR, 1), else_=0)).label("evaluators"),
            func.sum(case((User.role == UserRole.ENTITY_USER, 1), else_=0)).label("entity_users"),
        )
        .filter(
            User.created_at >= start_date,
            User.role.in_([UserRole.EVALUATOR, UserRole.ENTITY_USER]),
        )
        .group_by(
            extract("year", User.created_at),
            extract("month", User.created_at),
        )
        .order_by(
            extract("year", User.created_at),
            extract("month", User.created_at),
        )
        .all()
    )

    # Generar todos los meses en el rango (incluso sin datos)
    month_names = [
        "Ene", "Feb", "Mar", "Abr", "May", "Jun",
        "Jul", "Ago", "Sep", "Oct", "Nov", "Dic",
    ]

    monthly_data = []
    current = start_date
    end = date(now.year, now.month, 1)

    results_map = {}
    for r in results:
        key = (int(r.year), int(r.month))
        results_map[key] = {
            "count": r.count,
            "evaluators": int(r.evaluators or 0),
            "entity_users": int(r.entity_users or 0),
        }

    while current <= end:
        key = (current.year, current.month)
        data = results_map.get(key, {"count": 0, "evaluators": 0, "entity_users": 0})
        monthly_data.append({
            "month": month_names[current.month - 1],
            "year": current.year,
            "label": f"{month_names[current.month - 1]} {current.year}",
            "total": data["count"],
            "evaluators": data["evaluators"],
            "entity_users": data["entity_users"],
        })
        current += relativedelta(months=1)

    return {"monthly_data": monthly_data}
