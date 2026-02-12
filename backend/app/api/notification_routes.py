"""
Rutas para gestión de notificaciones in-app.

Permite a los evaluadores consultar, marcar como leídas y gestionar
sus notificaciones. Solo el usuario autenticado ve sus propias notificaciones.
"""

import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.database_models import Notification, User
from app.auth.dependencies import get_current_active_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/notifications", tags=["notifications"])


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.get("", summary="Listar notificaciones del usuario actual")
async def get_notifications(
    unread_only: bool = False,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Retorna las últimas 50 notificaciones del usuario autenticado.
    Opcionalmente filtra solo las no leídas.
    """
    query = db.query(Notification).filter(
        Notification.user_id == current_user.id
    )

    if unread_only:
        query = query.filter(Notification.read == False)  # noqa: E712

    notifications = (
        query.order_by(Notification.created_at.desc()).limit(50).all()
    )

    return [
        {
            "id": n.id,
            "type": n.type,
            "title": n.title,
            "message": n.message,
            "link": n.link,
            "read": n.read,
            "created_at": n.created_at.isoformat() if n.created_at else None,
        }
        for n in notifications
    ]


@router.get("/unread-count", summary="Contador de notificaciones no leídas")
async def get_unread_count(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Retorna el número de notificaciones no leídas del usuario actual."""
    count = (
        db.query(Notification)
        .filter(
            Notification.user_id == current_user.id,
            Notification.read == False,  # noqa: E712
        )
        .count()
    )
    return {"count": count}


@router.patch("/{notification_id}/read", summary="Marcar notificación como leída")
async def mark_as_read(
    notification_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Marca una notificación específica del usuario como leída."""
    notification = (
        db.query(Notification)
        .filter(
            Notification.id == notification_id,
            Notification.user_id == current_user.id,
        )
        .first()
    )

    if not notification:
        raise HTTPException(status_code=404, detail="Notificación no encontrada")

    notification.read = True
    db.commit()
    return {"success": True}


@router.post("/mark-all-read", summary="Marcar todas las notificaciones como leídas")
async def mark_all_read(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Marca todas las notificaciones no leídas del usuario como leídas."""
    updated = (
        db.query(Notification)
        .filter(
            Notification.user_id == current_user.id,
            Notification.read == False,  # noqa: E712
        )
        .update({"read": True})
    )
    db.commit()
    return {"success": True, "updated": updated}
