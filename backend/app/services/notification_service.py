"""
Servicio de notificaciones in-app.

Gestiona la creación y consulta de notificaciones para evaluadores.
Las notificaciones se generan cuando una institución marca un seguimiento
como corregido, para que el evaluador responsable sea notificado.
"""

import logging
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy.orm import Session

from app.models.database_models import Notification

logger = logging.getLogger(__name__)


def create_notification(
    db: Session,
    user_id: int,
    type: str,
    title: str,
    message: str,
    link: Optional[str] = None,
) -> Notification:
    """
    Crea una notificación in-app para un usuario específico.

    Args:
        db: Sesión de base de datos
        user_id: ID del usuario destinatario (evaluador)
        type: Tipo de notificación (ej: 'followup_corrected')
        title: Título breve de la notificación
        message: Mensaje descriptivo
        link: Enlace relativo al recurso relacionado (opcional)

    Returns:
        Notificación creada
    """
    notification = Notification(
        user_id=user_id,
        type=type,
        title=title,
        message=message,
        link=link,
        read=False,
        email_sent=False,
    )
    db.add(notification)
    db.commit()
    db.refresh(notification)
    logger.info(
        f"Notificación creada: user_id={user_id}, type={type}, title={title!r}"
    )
    return notification


def get_unread_notifications_older_than(
    db: Session, hours: int = 24
) -> list[Notification]:
    """
    Obtiene notificaciones no leídas y sin email enviado que superen
    el umbral de horas indicado. Se usan para enviar recordatorios por email.

    Args:
        db: Sesión de base de datos
        hours: Antigüedad mínima en horas (default 24)

    Returns:
        Lista de notificaciones pendientes de email
    """
    cutoff_time = datetime.utcnow() - timedelta(hours=hours)

    notifications = (
        db.query(Notification)
        .filter(
            Notification.read == False,  # noqa: E712
            Notification.email_sent == False,  # noqa: E712
            Notification.created_at < cutoff_time,
        )
        .all()
    )
    return notifications
