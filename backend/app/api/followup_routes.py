"""
Rutas para gestión de seguimientos de criterios no cumplidos.

Permite crear, listar y actualizar seguimientos de correcciones
programados para criterios con estado fail o partial.

Flujo de estados:
  pending   → La institución aún no ha reportado corrección
  corrected → La institución marcó como corregido (pendiente de validación)
  validated → El admin/secretaría validó la corrección
  rejected  → El admin/secretaría rechazó la corrección
  cancelled → Seguimiento cancelado
"""

import logging
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.models.database_models import CriteriaResult, Evaluation, Followup, Institution, User, Website
from app.auth.dependencies import get_current_active_user, allow_admin_secretary
from app.services.email_service import email_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/followups", tags=["followups"])


# ── Schemas ───────────────────────────────────────────────────────────────────

class FollowupCreate(BaseModel):
    evaluation_id: int
    criteria_result_id: int
    due_date: str  # ISO format YYYY-MM-DD
    notes: str = ""


class FollowupUpdate(BaseModel):
    status: str
    notes: Optional[str] = None


class MarkCorrectedRequest(BaseModel):
    notes: str = ""


class ValidateCorrectionRequest(BaseModel):
    approved: bool
    notes: str = ""


# ── Helpers ───────────────────────────────────────────────────────────────────

def _followup_to_dict(f: Followup) -> dict:
    cr = f.criteria_result
    return {
        "id": f.id,
        "evaluation_id": f.evaluation_id,
        "criteria_result_id": f.criteria_result_id,
        "criteria_id": cr.criteria_id if cr else None,
        "criteria_name": cr.criteria_name if cr else None,
        "criteria_status": cr.status if cr else None,
        "due_date": f.due_date.isoformat() if f.due_date else None,
        "status": f.status,
        "notes": f.notes,
        "created_at": f.created_at.isoformat() if f.created_at else None,
        # Campos de corrección
        "corrected_at": f.corrected_at.isoformat() if f.corrected_at else None,
        "corrected_by_user_id": f.corrected_by_user_id,
        # Campos de validación
        "validated_at": f.validated_at.isoformat() if f.validated_at else None,
        "validated_by_user_id": f.validated_by_user_id,
        "validation_notes": f.validation_notes,
    }


def _get_institution_responsible(website: Website, db: Session):
    """
    Retorna el primer User con rol entity_user vinculado a la institución
    cuyo dominio coincida con el del website.  Devuelve None si no existe.
    """
    institution = db.query(Institution).filter(
        Institution.domain == website.domain
    ).first()
    if not institution:
        return None
    return db.query(User).filter(
        User.institution_id == institution.id,
        User.role == "entity_user",
        User.is_active.is_(True),
    ).first()


def _load_followup(followup_id: int, db: Session) -> Followup:
    """Carga un followup con sus relaciones o lanza 404."""
    followup = (
        db.query(Followup)
        .options(joinedload(Followup.criteria_result))
        .filter(Followup.id == followup_id)
        .first()
    )
    if not followup:
        raise HTTPException(status_code=404, detail="Seguimiento no encontrado")
    return followup


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.post("", summary="Crear seguimiento")
async def create_followup(
    data: FollowupCreate,
    current_user=Depends(allow_admin_secretary),
    db: Session = Depends(get_db),
):
    """Crea un seguimiento para un criterio no cumplido. Solo admin/secretaría."""
    # Validar que existe la evaluación
    evaluation = db.query(Evaluation).filter(Evaluation.id == data.evaluation_id).first()
    if not evaluation:
        raise HTTPException(status_code=404, detail="Evaluación no encontrada")

    # Validar que el criteria_result pertenece a la evaluación
    criteria_result = db.query(CriteriaResult).filter(
        CriteriaResult.id == data.criteria_result_id,
        CriteriaResult.evaluation_id == data.evaluation_id
    ).first()
    if not criteria_result:
        raise HTTPException(status_code=404, detail="Criterio no encontrado en esta evaluación")

    try:
        due_date = datetime.fromisoformat(data.due_date)
    except ValueError:
        raise HTTPException(status_code=400, detail="Formato de fecha inválido. Use YYYY-MM-DD")

    followup = Followup(
        evaluation_id=data.evaluation_id,
        criteria_result_id=data.criteria_result_id,
        due_date=due_date,
        notes=data.notes or None,
        status="pending",
    )
    db.add(followup)
    db.commit()
    db.refresh(followup)

    # Recargar con relación para devolver datos completos
    followup = (
        db.query(Followup)
        .options(joinedload(Followup.criteria_result))
        .filter(Followup.id == followup.id)
        .first()
    )

    # Notificación por email (no bloqueante)
    try:
        website = db.query(Website).filter(Website.id == evaluation.website_id).first()
        if website:
            responsible = _get_institution_responsible(website, db)
            if responsible:
                institution = db.query(Institution).filter(
                    Institution.domain == website.domain
                ).first()
                institution_name = institution.name if institution else website.domain
                await email_service.send_followup_created_email(
                    to_email=responsible.email,
                    institution_name=institution_name,
                    criterion_code=criteria_result.criteria_id,
                    criterion_name=criteria_result.criteria_name,
                    due_date=due_date.strftime("%d/%m/%Y"),
                    observations=data.notes or "",
                    evaluation_id=data.evaluation_id,
                )
    except Exception:
        logger.exception("Error al enviar email de seguimiento creado (ignorado)")

    return _followup_to_dict(followup)


@router.get("", summary="Listar seguimientos")
async def list_followups(
    status: Optional[str] = None,
    evaluation_id: Optional[int] = None,
    current_user=Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Lista seguimientos con filtros opcionales.

    - Admin/secretaría/evaluador: ven todos los seguimientos.
    - entity_user: solo ve seguimientos de evaluaciones de su institución
      (filtrado por el dominio de la institución vs el dominio del website).
    """
    query = (
        db.query(Followup)
        .options(joinedload(Followup.criteria_result))
        .join(Evaluation, Followup.evaluation_id == Evaluation.id)
    )

    # Usuarios de institución: solo ven los seguimientos de su institución
    if current_user.role.value == "entity_user":
        if not current_user.institution_id:
            return []
        # Obtener el dominio de la institución del usuario
        institution = db.query(Institution).filter(
            Institution.id == current_user.institution_id
        ).first()
        if not institution:
            return []
        # Filtrar por websites cuyo dominio coincida con el dominio de la institución
        query = (
            query
            .join(Website, Evaluation.website_id == Website.id)
            .filter(Website.domain == institution.domain)
        )

    if status:
        query = query.filter(Followup.status == status)
    if evaluation_id:
        query = query.filter(Followup.evaluation_id == evaluation_id)

    followups = query.order_by(Followup.due_date.asc()).all()
    return [_followup_to_dict(f) for f in followups]


@router.patch("/{followup_id}/mark-corrected", summary="Institución marca como corregido")
async def mark_corrected(
    followup_id: int,
    data: MarkCorrectedRequest,
    current_user=Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Permite a un usuario de institución reportar que corrigió el problema.
    Solo usuarios con rol entity_user pueden usar este endpoint.
    El seguimiento debe estar en estado 'pending' o 'rejected'.
    """
    if current_user.role.value not in ("entity_user",):
        raise HTTPException(
            status_code=403,
            detail="Solo usuarios de institución pueden marcar correcciones"
        )

    followup = _load_followup(followup_id, db)

    if followup.status not in ("pending", "rejected"):
        raise HTTPException(
            status_code=400,
            detail=f"No se puede marcar como corregido un seguimiento en estado '{followup.status}'"
        )

    followup.status = "corrected"
    followup.corrected_at = datetime.utcnow()
    followup.corrected_by_user_id = current_user.id
    if data.notes:
        followup.notes = data.notes

    db.commit()
    db.refresh(followup)
    return _followup_to_dict(_load_followup(followup_id, db))


@router.patch("/{followup_id}/validate", summary="Admin valida o rechaza corrección")
async def validate_correction(
    followup_id: int,
    data: ValidateCorrectionRequest,
    current_user=Depends(allow_admin_secretary),
    db: Session = Depends(get_db),
):
    """
    Permite al admin/secretaría validar o rechazar una corrección reportada.
    El seguimiento debe estar en estado 'corrected'.
    """
    followup = _load_followup(followup_id, db)

    if followup.status != "corrected":
        raise HTTPException(
            status_code=400,
            detail=f"Solo se puede validar un seguimiento en estado 'corrected'. Estado actual: '{followup.status}'"
        )

    if data.approved:
        followup.status = "validated"
        followup.validated_at = datetime.utcnow()
    else:
        followup.status = "rejected"

    followup.validated_by_user_id = current_user.id
    followup.validation_notes = data.notes or None

    db.commit()
    db.refresh(followup)

    # Notificación por email (no bloqueante)
    try:
        evaluation = db.query(Evaluation).filter(
            Evaluation.id == followup.evaluation_id
        ).first()
        criteria_result = followup.criteria_result
        if evaluation and criteria_result:
            website = db.query(Website).filter(Website.id == evaluation.website_id).first()
            if website:
                responsible = _get_institution_responsible(website, db)
                if responsible:
                    institution = db.query(Institution).filter(
                        Institution.domain == website.domain
                    ).first()
                    institution_name = institution.name if institution else website.domain
                    await email_service.send_followup_validated_email(
                        to_email=responsible.email,
                        institution_name=institution_name,
                        criterion_code=criteria_result.criteria_id,
                        criterion_name=criteria_result.criteria_name,
                        approved=data.approved,
                        notes=data.notes or "",
                    )
    except Exception:
        logger.exception("Error al enviar email de validación de seguimiento (ignorado)")

    return _followup_to_dict(_load_followup(followup_id, db))


@router.patch("/{followup_id}/cancel", summary="Admin cancela un seguimiento")
async def cancel_followup(
    followup_id: int,
    current_user=Depends(allow_admin_secretary),
    db: Session = Depends(get_db),
):
    """Cancela un seguimiento. Solo admin/secretaría."""
    followup = _load_followup(followup_id, db)

    if followup.status in ("validated", "cancelled"):
        raise HTTPException(
            status_code=400,
            detail=f"No se puede cancelar un seguimiento en estado '{followup.status}'"
        )

    followup.status = "cancelled"
    db.commit()
    db.refresh(followup)
    return _followup_to_dict(_load_followup(followup_id, db))


@router.patch("/{followup_id}", summary="Actualizar seguimiento (legacy)")
async def update_followup(
    followup_id: int,
    data: FollowupUpdate,
    current_user=Depends(allow_admin_secretary),
    db: Session = Depends(get_db),
):
    """
    Actualiza estado y/o notas de un seguimiento.
    Endpoint legacy para compatibilidad — solo admin/secretaría.
    Para el flujo correcto usar /mark-corrected y /validate.
    """
    followup = _load_followup(followup_id, db)

    valid_statuses = {"pending", "corrected", "validated", "rejected", "cancelled"}
    if data.status not in valid_statuses:
        raise HTTPException(
            status_code=400,
            detail=f"Estado inválido. Valores permitidos: {', '.join(sorted(valid_statuses))}"
        )

    followup.status = data.status
    if data.notes is not None:
        followup.notes = data.notes

    db.commit()
    db.refresh(followup)
    return _followup_to_dict(_load_followup(followup_id, db))
