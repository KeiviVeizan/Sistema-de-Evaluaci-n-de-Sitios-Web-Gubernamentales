"""
Rutas del dashboard para usuarios de entidad (entity_user).

Proporciona estadísticas, evolución de score, seguimientos pendientes
e historial de evaluaciones para la institución del usuario.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.database import get_db
from app.models.database_models import (
    Evaluation, Website, Institution, Followup, CriteriaResult, User
)
from app.auth.dependencies import get_current_active_user

router = APIRouter(prefix="/entity", tags=["entity-dashboard"])


def get_user_institution(current_user, db: Session) -> Institution:
    """Obtener la institución del usuario actual."""
    if not current_user.institution_id:
        raise HTTPException(400, "Usuario sin institución asignada")

    institution = db.query(Institution).filter(
        Institution.id == current_user.institution_id
    ).first()

    if not institution:
        raise HTTPException(404, "Institución no encontrada")

    return institution


def get_institution_website_ids(institution: Institution, db: Session) -> list[int]:
    """Obtener IDs de websites vinculados a la institución por dominio."""
    websites = db.query(Website).filter(
        Website.domain == institution.domain
    ).all()
    return [w.id for w in websites]


@router.get("/dashboard/stats")
async def get_entity_stats(
    current_user=Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Estadísticas generales de la entidad."""
    institution = get_user_institution(current_user, db)
    website_ids = get_institution_website_ids(institution, db)

    if not website_ids:
        return {
            "institution_name": institution.name,
            "last_score": 0,
            "total_evaluations": 0,
            "pending_followups": 0,
            "improvement": 0,
            "first_score": 0,
            "current_score": 0
        }

    # Total evaluaciones recibidas
    total_evaluations = db.query(Evaluation).filter(
        Evaluation.website_id.in_(website_ids)
    ).count()

    # Última evaluación
    last_evaluation = db.query(Evaluation).filter(
        Evaluation.website_id.in_(website_ids)
    ).order_by(desc(Evaluation.started_at)).first()

    last_score = round(last_evaluation.score_total, 2) if last_evaluation and last_evaluation.score_total else 0

    # Primera evaluación (para calcular mejora)
    first_evaluation = db.query(Evaluation).filter(
        Evaluation.website_id.in_(website_ids)
    ).order_by(Evaluation.started_at).first()

    first_score = round(first_evaluation.score_total, 2) if first_evaluation and first_evaluation.score_total else 0
    improvement = round(last_score - first_score, 2) if first_evaluation and last_evaluation else 0

    # Seguimientos pendientes (a través de evaluation → website)
    pending_followups = db.query(Followup).join(
        Evaluation, Followup.evaluation_id == Evaluation.id
    ).filter(
        Evaluation.website_id.in_(website_ids),
        Followup.status == "pending"
    ).count()

    return {
        "institution_name": institution.name,
        "last_score": last_score,
        "total_evaluations": total_evaluations,
        "pending_followups": pending_followups,
        "improvement": improvement,
        "first_score": first_score,
        "current_score": last_score
    }


@router.get("/dashboard/score-evolution")
async def get_score_evolution(
    current_user=Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Evolución del score en el tiempo."""
    institution = get_user_institution(current_user, db)
    website_ids = get_institution_website_ids(institution, db)

    if not website_ids:
        return []

    evaluations = db.query(Evaluation).filter(
        Evaluation.website_id.in_(website_ids)
    ).order_by(Evaluation.started_at).all()

    return [
        {
            "date": ev.started_at.strftime("%d/%m/%Y") if ev.started_at else "N/A",
            "score": round(ev.score_total, 2) if ev.score_total else 0,
            "evaluator": None
        }
        for ev in evaluations
    ]


@router.get("/dashboard/pending-followups")
async def get_pending_followups(
    current_user=Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Seguimientos pendientes de la entidad."""
    institution = get_user_institution(current_user, db)
    website_ids = get_institution_website_ids(institution, db)

    if not website_ids:
        return []

    followups = db.query(Followup).join(
        Evaluation, Followup.evaluation_id == Evaluation.id
    ).filter(
        Evaluation.website_id.in_(website_ids),
        Followup.status == "pending"
    ).order_by(desc(Followup.created_at)).all()

    result = []
    for f in followups:
        # Obtener info del criterio a través de criteria_result
        criteria_result = db.query(CriteriaResult).filter(
            CriteriaResult.id == f.criteria_result_id
        ).first()

        # Obtener evaluador a través de la evaluación
        evaluator = None
        evaluation = db.query(Evaluation).filter(
            Evaluation.id == f.evaluation_id
        ).first()
        if evaluation and evaluation.evaluator_id:
            evaluator = db.query(User).filter(
                User.id == evaluation.evaluator_id
            ).first()

        result.append({
            "id": f.id,
            "criterion": criteria_result.criteria_name if criteria_result else "N/A",
            "criterion_code": criteria_result.criteria_id if criteria_result else "N/A",
            "description": f.notes or "Observación pendiente",
            "due_date": f.due_date.isoformat() if f.due_date else None,
            "created_at": f.created_at.isoformat() if f.created_at else None,
            "evaluator_name": (evaluator.full_name or evaluator.username) if evaluator else "Evaluador"
        })

    return result


@router.get("/dashboard/evaluation-history")
async def get_evaluation_history(
    current_user=Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Historial de evaluaciones de la entidad."""
    institution = get_user_institution(current_user, db)
    website_ids = get_institution_website_ids(institution, db)

    if not website_ids:
        return []

    evaluations = db.query(Evaluation).filter(
        Evaluation.website_id.in_(website_ids)
    ).order_by(desc(Evaluation.started_at)).all()

    result = []
    for ev in evaluations:
        evaluator = None
        if ev.evaluator_id:
            evaluator = db.query(User).filter(User.id == ev.evaluator_id).first()

        result.append({
            "id": ev.id,
            "score": round(ev.score_total, 2) if ev.score_total else 0,
            "evaluated_at": ev.started_at.isoformat() if ev.started_at else None,
            "evaluator_name": (evaluator.full_name or evaluator.username) if evaluator else "No asignado",
            "status": ev.status.value if ev.status else "completed"
        })

    return result
