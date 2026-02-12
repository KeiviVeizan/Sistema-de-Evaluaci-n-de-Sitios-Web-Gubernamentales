"""
Tarea programada: envío de recordatorios por email para notificaciones no leídas.

Envía un email a los evaluadores que tengan notificaciones no leídas
con más de 24 horas de antigüedad y sin email previo enviado.

Uso:
    python -m app.tasks.notification_emailer

Configurar como cron job (ejecutar cada hora, por ejemplo):
    0 * * * * cd /path/to/backend && python -m app.tasks.notification_emailer
"""

import asyncio
import logging

logger = logging.getLogger(__name__)


async def send_notification_reminders() -> None:
    """
    Consulta notificaciones no leídas con más de 24 horas y envía
    un email de recordatorio a cada evaluador correspondiente.
    """
    # Importaciones dentro de la función para evitar problemas de contexto
    from app.database import SessionLocal
    from app.services.notification_service import get_unread_notifications_older_than
    from app.services.email_service import email_service
    from app.models.database_models import User
    from app.config import settings

    db = SessionLocal()

    try:
        notifications = get_unread_notifications_older_than(db, hours=24)
        logger.info(f"Encontradas {len(notifications)} notificaciones pendientes de email")

        for notif in notifications:
            user = db.query(User).filter(User.id == notif.user_id).first()

            if not user or not user.email:
                logger.warning(
                    f"Notificación {notif.id}: usuario {notif.user_id} sin email, omitida"
                )
                continue

            link = (
                f"{settings.frontend_url}{notif.link}"
                if notif.link
                else None
            )

            sent = await email_service.send_notification_reminder(
                to_email=user.email,
                title=notif.title,
                message=notif.message,
                link=link,
            )

            if sent:
                notif.email_sent = True
                db.commit()
                logger.info(f"Recordatorio enviado a {user.email} (notif id={notif.id})")
            else:
                logger.warning(
                    f"No se pudo enviar recordatorio a {user.email} (notif id={notif.id})"
                )

    except Exception:
        logger.exception("Error en send_notification_reminders")
    finally:
        db.close()


if __name__ == "__main__":
    logging.basicConfig(
        level="INFO",
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    asyncio.run(send_notification_reminders())
