"""
Servicio de envío de correos electrónicos.

Utiliza fastapi-mail para enviar correos a través de Gmail SMTP.
Incluye templates HTML para códigos 2FA y notificaciones.
"""

import logging
from typing import Optional

from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType

logger = logging.getLogger(__name__)


class EmailService:
    """
    Servicio para envío de correos electrónicos.

    Maneja el envío de códigos 2FA y otras notificaciones del sistema.
    Si las credenciales no están configuradas, los correos se logean
    en consola (modo desarrollo).
    """

    def __init__(self):
        self._config: Optional[ConnectionConfig] = None
        self._fastmail: Optional[FastMail] = None
        self._initialized = False

    def _initialize(self):
        """Inicializa la configuración de correo de forma lazy."""
        if self._initialized:
            return

        # Importar settings aquí para evitar problemas de importación circular
        from app.config import settings

        logger.info("=" * 50)
        logger.info("Inicializando servicio de email...")
        logger.info(f"  MAIL_USERNAME: {settings.mail_username or '(no configurado)'}")
        logger.info(f"  MAIL_SERVER: {settings.mail_server}")
        logger.info(f"  MAIL_PORT: {settings.mail_port}")
        logger.info(f"  MAIL_TLS: {settings.mail_tls}")
        logger.info(f"  MAIL_FROM: {settings.mail_from}")
        logger.info("=" * 50)

        if not settings.mail_username or not settings.mail_password:
            logger.warning(
                "Credenciales de correo no configuradas. "
                "Configure MAIL_USERNAME y MAIL_PASSWORD en .env"
            )
            self._initialized = True
            return

        try:
            self._config = ConnectionConfig(
                MAIL_USERNAME=settings.mail_username,
                MAIL_PASSWORD=settings.mail_password,
                MAIL_FROM=settings.mail_from,
                MAIL_FROM_NAME=settings.mail_from_name,
                MAIL_PORT=settings.mail_port,
                MAIL_SERVER=settings.mail_server,
                MAIL_STARTTLS=settings.mail_tls,
                MAIL_SSL_TLS=settings.mail_ssl,
                USE_CREDENTIALS=True,
                VALIDATE_CERTS=True,
            )
            self._fastmail = FastMail(self._config)
            logger.info("Servicio de email inicializado correctamente")
        except Exception as e:
            logger.error(f"Error al inicializar servicio de email: {str(e)}")
            self._fastmail = None

        self._initialized = True

    def _get_2fa_html_template(self, code: str, username: str) -> str:
        """Genera el HTML del correo de código 2FA."""
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
        </head>
        <body style="margin: 0; padding: 0; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f4f4f4;">
            <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <tr>
                    <td style="background-color: #800000; padding: 30px; text-align: center; border-radius: 12px 12px 0 0;">
                        <h1 style="color: white; margin: 0; font-size: 24px;">
                            Evaluador GOB.BO
                        </h1>
                        <p style="color: rgba(255,255,255,0.8); margin: 8px 0 0; font-size: 14px;">
                            Sistema de Evaluación de Sitios Web Gubernamentales
                        </p>
                    </td>
                </tr>
                <tr>
                    <td style="background-color: white; padding: 40px 30px; border-radius: 0 0 12px 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
                        <h2 style="color: #333; margin: 0 0 20px; font-size: 20px;">
                            Código de Verificación
                        </h2>
                        <p style="color: #666; margin: 0 0 30px; font-size: 15px; line-height: 1.6;">
                            Hola <strong>{username}</strong>,<br><br>
                            Has solicitado iniciar sesión en el sistema. Usa el siguiente código para completar tu autenticación:
                        </p>
                        <div style="background: linear-gradient(135deg, #800000, #a00000); padding: 25px; border-radius: 12px; text-align: center; margin: 0 0 30px;">
                            <span style="font-size: 36px; font-weight: bold; color: white; letter-spacing: 8px; font-family: 'Courier New', monospace;">
                                {code}
                            </span>
                        </div>
                        <p style="color: #888; font-size: 13px; margin: 0 0 20px; padding: 15px; background: #f9f9f9; border-radius: 8px; border-left: 4px solid #800000;">
                            <strong>Importante:</strong> Este código expira en 5 minutos y solo puede usarse una vez.
                        </p>
                        <p style="color: #999; font-size: 12px; margin: 0; text-align: center;">
                            Si no solicitaste este código, ignora este mensaje.<br>
                            Tu cuenta permanece segura.
                        </p>
                    </td>
                </tr>
                <tr>
                    <td style="padding: 20px; text-align: center;">
                        <p style="color: #999; font-size: 11px; margin: 0;">
                            Este es un mensaje automático del Sistema de Evaluación GOB.BO<br>
                            Por favor no respondas a este correo.
                        </p>
                    </td>
                </tr>
            </table>
        </body>
        </html>
        """

    def _get_welcome_html_template(
        self, email: str, password: str, role: str, institution_name: str = None
    ) -> str:
        """Genera el HTML del correo de bienvenida con credenciales."""
        from app.config import settings

        role_names = {
            "superadmin": "Superadministrador",
            "secretary": "Secretaría",
            "evaluator": "Evaluador",
            "entity_user": "Usuario de Institución",
        }
        role_display = role_names.get(role, role)

        institution_block = (
            f'<p style="margin: 0 0 8px;"><strong>Institución:</strong> {institution_name}</p>'
            if institution_name
            else ""
        )

        next_step_extra = (
            "<li>Revise las evaluaciones de su institución</li>"
            if role == "entity_user"
            else "<li>Comience a trabajar en el sistema</li>"
        )

        return f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
</head>
<body style="margin:0;padding:0;font-family:'Segoe UI',Tahoma,Geneva,Verdana,sans-serif;background-color:#f4f4f4;">
    <table role="presentation" width="100%" cellspacing="0" cellpadding="0"
           style="max-width:600px;margin:0 auto;padding:20px;">
        <tr>
            <td style="background-color:#800000;padding:30px;text-align:center;border-radius:12px 12px 0 0;">
                <h1 style="color:white;margin:0;font-size:24px;">Evaluador GOB.BO</h1>
                <p style="color:rgba(255,255,255,0.8);margin:8px 0 0;font-size:14px;">
                    Sistema de Evaluación de Sitios Web Gubernamentales
                </p>
            </td>
        </tr>
        <tr>
            <td style="background-color:white;padding:40px 30px;border-radius:0 0 12px 12px;
                       box-shadow:0 4px 6px rgba(0,0,0,0.1);">
                <h2 style="color:#333;margin:0 0 16px;font-size:20px;">
                    ¡Bienvenido al sistema!
                </h2>
                <p style="color:#555;margin:0 0 20px;font-size:15px;line-height:1.6;">
                    Se ha creado una cuenta para usted en el Sistema de Evaluación
                    de Cumplimiento Web Gubernamental.
                </p>

                <!-- Datos del usuario -->
                <div style="background:#f9f9f9;padding:20px;border-radius:8px;margin:0 0 20px;">
                    {institution_block}
                    <p style="margin:0;"><strong>Rol asignado:</strong> {role_display}</p>
                </div>

                <!-- Credenciales -->
                <div style="background:#fff8f8;padding:20px;border-left:4px solid #800000;
                            border-radius:0 8px 8px 0;margin:0 0 20px;">
                    <h3 style="color:#800000;margin:0 0 12px;font-size:16px;">
                        Sus credenciales de acceso
                    </h3>
                    <p style="margin:0 0 8px;font-size:15px;">
                        <strong>Email:</strong> {email}
                    </p>
                    <p style="margin:0;font-size:15px;">
                        <strong>Contraseña:</strong>
                        <code style="background:#e5e7eb;padding:4px 10px;border-radius:4px;
                                     font-size:15px;letter-spacing:1px;">{password}</code>
                    </p>
                </div>

                <!-- Advertencia de seguridad -->
                <p style="color:#92400e;background:#fef3c7;padding:12px 16px;border-radius:8px;
                          font-size:13px;margin:0 0 24px;line-height:1.5;">
                    <strong>Importante:</strong> Por seguridad, le recomendamos cambiar su
                    contraseña después del primer inicio de sesión.
                </p>

                <!-- Botón de acceso -->
                <div style="text-align:center;margin:0 0 28px;">
                    <a href="{settings.frontend_url}/login"
                       style="display:inline-block;background:#800000;color:white;
                              padding:14px 36px;text-decoration:none;border-radius:8px;
                              font-size:15px;font-weight:600;">
                        Acceder al Sistema
                    </a>
                </div>

                <!-- Próximos pasos -->
                <h3 style="color:#333;font-size:16px;margin:0 0 10px;">Próximos pasos:</h3>
                <ol style="color:#555;font-size:14px;line-height:1.8;margin:0;padding-left:20px;">
                    <li>Haga clic en el botón de arriba o visite
                        <a href="{settings.frontend_url}" style="color:#800000;">{settings.frontend_url}</a>
                    </li>
                    <li>Inicie sesión con sus credenciales</li>
                    <li>Complete su perfil si es necesario</li>
                    {next_step_extra}
                </ol>
            </td>
        </tr>
        <tr>
            <td style="padding:20px;text-align:center;">
                <p style="color:#999;font-size:11px;margin:0;line-height:1.6;">
                    Este es un mensaje automático del Sistema de Evaluación GOB.BO<br>
                    Si tiene problemas para acceder, contacte al administrador del sistema.<br>
                    Por favor no respondas a este correo.
                </p>
            </td>
        </tr>
    </table>
</body>
</html>"""

    async def send_welcome_email(
        self,
        email: str,
        password: str,
        role: str,
        institution_name: str = None,
    ) -> bool:
        """
        Envía email de bienvenida con credenciales al nuevo usuario.

        Args:
            email: Dirección de correo del destinatario
            password: Contraseña generada en texto plano (solo en este envío)
            role: Rol asignado al usuario
            institution_name: Nombre de la institución (opcional)

        Returns:
            True si el correo se envió correctamente, False en caso contrario
        """
        self._initialize()

        subject = "Bienvenido al Sistema de Evaluación GOB.BO — Sus credenciales de acceso"
        html_content = self._get_welcome_html_template(email, password, role, institution_name)

        if not self._fastmail:
            logger.info("=" * 50)
            logger.info("[MODO DESARROLLO] Correo de bienvenida simulado:")
            logger.info(f"  Para: {email}")
            logger.info(f"  Rol: {role}")
            logger.info(f"  Contraseña generada: {password}")
            if institution_name:
                logger.info(f"  Institución: {institution_name}")
            logger.info("=" * 50)
            return True

        try:
            logger.info(f"Enviando correo de bienvenida a {email}...")
            message = MessageSchema(
                subject=subject,
                recipients=[email],
                body=html_content,
                subtype=MessageType.html,
            )
            await self._fastmail.send_message(message)
            logger.info(f"Correo de bienvenida enviado exitosamente a {email}")
            return True
        except Exception as e:
            logger.error(
                f"Error al enviar correo de bienvenida a {email}: "
                f"{type(e).__name__}: {str(e)}"
            )
            logger.info("=" * 50)
            logger.info(f"[FALLBACK] Credenciales para {email} — contraseña: {password}")
            logger.info("=" * 50)
            return False

    async def send_2fa_code(self, email: str, code: str, username: str) -> bool:
        """
        Envía el código de verificación 2FA por correo electrónico.

        Args:
            email: Dirección de correo del destinatario
            code: Código de 6 dígitos
            username: Nombre de usuario para personalizar el mensaje

        Returns:
            True si el correo se envió correctamente, False en caso contrario
        """
        # Inicializar de forma lazy
        self._initialize()

        subject = f"Código de Verificación: {code} - Evaluador GOB.BO"
        html_content = self._get_2fa_html_template(code, username)

        # Si no hay configuración de correo, usar modo desarrollo (log en consola)
        if not self._fastmail:
            logger.info("=" * 50)
            logger.info("[MODO DESARROLLO] Correo 2FA simulado:")
            logger.info(f"  Para: {email}")
            logger.info(f"  Usuario: {username}")
            logger.info(f"  Código: {code}")
            logger.info("=" * 50)
            return True

        try:
            logger.info(f"Intentando enviar correo 2FA a {email}...")

            message = MessageSchema(
                subject=subject,
                recipients=[email],
                body=html_content,
                subtype=MessageType.html,
            )

            await self._fastmail.send_message(message)
            logger.info(f"Correo 2FA enviado exitosamente a {email}")
            return True

        except Exception as e:
            logger.error(f"Error al enviar correo 2FA a {email}: {type(e).__name__}: {str(e)}")
            # En caso de error, logeamos el código para no bloquear al usuario
            logger.info("=" * 50)
            logger.info(f"[FALLBACK] Código 2FA para {username}: {code}")
            logger.info("=" * 50)
            return False

    @staticmethod
    def _get_followup_created_html(
        institution_name: str,
        criterion_code: str,
        criterion_name: str,
        due_date: str,
        observations: str,
        evaluation_url: str,
    ) -> str:
        """Template HTML para notificación de seguimiento creado."""
        obs_block = observations if observations else "Sin observaciones adicionales."
        return f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
</head>
<body style="margin:0;padding:0;font-family:'Segoe UI',Tahoma,Geneva,Verdana,sans-serif;background-color:#f4f4f4;">
    <table role="presentation" width="100%" cellspacing="0" cellpadding="0"
           style="max-width:600px;margin:0 auto;padding:20px;">
        <tr>
            <td style="background-color:#800000;padding:30px;text-align:center;border-radius:12px 12px 0 0;">
                <h1 style="color:white;margin:0;font-size:24px;">Evaluador GOB.BO</h1>
                <p style="color:rgba(255,255,255,0.8);margin:8px 0 0;font-size:14px;">
                    Seguimiento Asignado
                </p>
            </td>
        </tr>
        <tr>
            <td style="background-color:white;padding:40px 30px;border-radius:0 0 12px 12px;
                       box-shadow:0 4px 6px rgba(0,0,0,0.1);">
                <p style="color:#555;font-size:15px;line-height:1.6;margin:0 0 20px;">
                    Estimado equipo de <strong>{institution_name}</strong>,
                </p>
                <p style="color:#555;font-size:15px;line-height:1.6;margin:0 0 24px;">
                    Se ha programado un seguimiento para corregir un criterio de cumplimiento
                    detectado en la evaluación de su sitio web.
                </p>

                <!-- Criterio -->
                <div style="background:#f9f9f9;padding:20px;border-radius:8px;margin:0 0 20px;">
                    <h3 style="color:#333;font-size:16px;margin:0 0 8px;">Criterio a corregir</h3>
                    <p style="margin:0 0 6px;font-size:15px;">
                        <strong>{criterion_code}</strong> — {criterion_name}
                    </p>
                    <p style="margin:0;font-size:14px;color:#666;">
                        <strong>Observaciones:</strong> {obs_block}
                    </p>
                </div>

                <!-- Alerta fecha límite -->
                <div style="background:#fef3c7;border-left:4px solid #f59e0b;padding:15px 20px;
                            border-radius:0 8px 8px 0;margin:0 0 24px;">
                    <p style="margin:0;font-size:14px;color:#92400e;">
                        <strong>Fecha límite de corrección:</strong> {due_date}
                    </p>
                </div>

                <!-- Pasos -->
                <h3 style="color:#333;font-size:16px;margin:0 0 10px;">Próximos pasos</h3>
                <ol style="color:#555;font-size:14px;line-height:1.8;margin:0 0 28px;padding-left:20px;">
                    <li>Revise el detalle completo de la evaluación</li>
                    <li>Implemente las correcciones necesarias en su sitio web</li>
                    <li>Marque el seguimiento como <strong>Corregido</strong> en el sistema</li>
                    <li>Espere la validación del administrador</li>
                </ol>

                <!-- Botón -->
                <div style="text-align:center;margin:0 0 10px;">
                    <a href="{evaluation_url}"
                       style="display:inline-block;background:#800000;color:white;
                              padding:14px 36px;text-decoration:none;border-radius:8px;
                              font-size:15px;font-weight:600;">
                        Ver Evaluación Completa
                    </a>
                </div>
            </td>
        </tr>
        <tr>
            <td style="padding:20px;text-align:center;">
                <p style="color:#999;font-size:11px;margin:0;line-height:1.6;">
                    Este es un mensaje automático del Sistema de Evaluación GOB.BO<br>
                    Por favor no respondas a este correo.
                </p>
            </td>
        </tr>
    </table>
</body>
</html>"""

    async def send_followup_created_email(
        self,
        to_email: str,
        institution_name: str,
        criterion_code: str,
        criterion_name: str,
        due_date: str,
        observations: str,
        evaluation_id: int,
    ) -> bool:
        """
        Envía email cuando se crea un seguimiento para un criterio.

        Args:
            to_email: Email del responsable de la institución
            institution_name: Nombre de la institución
            criterion_code: Código del criterio (criteria_id)
            criterion_name: Nombre descriptivo del criterio
            due_date: Fecha límite en formato legible
            observations: Observaciones/notas del seguimiento
            evaluation_id: ID de la evaluación para construir el enlace

        Returns:
            True si el correo se envió correctamente, False en caso contrario
        """
        self._initialize()

        from app.config import settings

        subject = f"Seguimiento asignado: {criterion_code} — {institution_name}"
        evaluation_url = f"{settings.frontend_url}/admin/evaluations/{evaluation_id}"
        html_content = self._get_followup_created_html(
            institution_name, criterion_code, criterion_name,
            due_date, observations, evaluation_url,
        )

        if not self._fastmail:
            logger.info("=" * 50)
            logger.info("[MODO DESARROLLO] Email de seguimiento creado simulado:")
            logger.info(f"  Para: {to_email}")
            logger.info(f"  Institución: {institution_name}")
            logger.info(f"  Criterio: {criterion_code} — {criterion_name}")
            logger.info(f"  Fecha límite: {due_date}")
            logger.info("=" * 50)
            return True

        try:
            logger.info(f"Enviando email de seguimiento creado a {to_email}...")
            message = MessageSchema(
                subject=subject,
                recipients=[to_email],
                body=html_content,
                subtype=MessageType.html,
            )
            await self._fastmail.send_message(message)
            logger.info(f"Email de seguimiento creado enviado exitosamente a {to_email}")
            return True
        except Exception as e:
            logger.error(
                f"Error al enviar email de seguimiento creado a {to_email}: "
                f"{type(e).__name__}: {str(e)}"
            )
            return False

    @staticmethod
    def _get_followup_validated_html(
        institution_name: str,
        criterion_code: str,
        criterion_name: str,
        approved: bool,
        notes: str,
    ) -> str:
        """Template HTML para notificación de validación/rechazo de corrección."""
        status_color = "#10b981" if approved else "#ef4444"
        status_label = "Aprobada" if approved else "Rechazada"
        header_title = f"Corrección {status_label}"

        if approved:
            detail_block = """
                <p style="color:#065f46;font-size:15px;margin:0;">
                    ¡Felicitaciones! La corrección ha sido <strong>validada exitosamente</strong>.
                    El criterio queda registrado como corregido en el sistema.
                </p>"""
        else:
            rejection_notes = notes if notes else "Sin notas adicionales."
            detail_block = f"""
                <p style="color:#7f1d1d;font-size:14px;margin:0 0 8px;">
                    <strong>Motivo del rechazo:</strong>
                </p>
                <p style="color:#7f1d1d;font-size:14px;margin:0 0 12px;">{rejection_notes}</p>
                <p style="color:#555;font-size:14px;margin:0;font-style:italic;">
                    Por favor, realice las correcciones necesarias y vuelva a marcar
                    el seguimiento como <strong>Corregido</strong>.
                </p>"""

        return f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
</head>
<body style="margin:0;padding:0;font-family:'Segoe UI',Tahoma,Geneva,Verdana,sans-serif;background-color:#f4f4f4;">
    <table role="presentation" width="100%" cellspacing="0" cellpadding="0"
           style="max-width:600px;margin:0 auto;padding:20px;">
        <tr>
            <td style="background-color:{status_color};padding:30px;text-align:center;border-radius:12px 12px 0 0;">
                <h1 style="color:white;margin:0;font-size:24px;">Evaluador GOB.BO</h1>
                <p style="color:rgba(255,255,255,0.9);margin:8px 0 0;font-size:16px;font-weight:600;">
                    {header_title}
                </p>
            </td>
        </tr>
        <tr>
            <td style="background-color:white;padding:40px 30px;border-radius:0 0 12px 12px;
                       box-shadow:0 4px 6px rgba(0,0,0,0.1);">
                <p style="color:#555;font-size:15px;line-height:1.6;margin:0 0 20px;">
                    Estimado equipo de <strong>{institution_name}</strong>,
                </p>

                <!-- Criterio y resultado -->
                <div style="background:#f9f9f9;padding:20px;border-left:4px solid {status_color};
                            border-radius:0 8px 8px 0;margin:0 0 24px;">
                    <p style="margin:0 0 8px;font-size:15px;">
                        <strong>Criterio:</strong> {criterion_code} — {criterion_name}
                    </p>
                    <p style="margin:0 0 16px;font-size:15px;">
                        <strong>Estado:</strong>
                        <span style="color:{status_color};font-weight:600;">{status_label}</span>
                    </p>
                    {detail_block}
                </div>
            </td>
        </tr>
        <tr>
            <td style="padding:20px;text-align:center;">
                <p style="color:#999;font-size:11px;margin:0;line-height:1.6;">
                    Este es un mensaje automático del Sistema de Evaluación GOB.BO<br>
                    Por favor no respondas a este correo.
                </p>
            </td>
        </tr>
    </table>
</body>
</html>"""

    async def send_followup_validated_email(
        self,
        to_email: str,
        institution_name: str,
        criterion_code: str,
        criterion_name: str,
        approved: bool,
        notes: str = "",
    ) -> bool:
        """
        Envía email cuando se valida o rechaza una corrección de seguimiento.

        Args:
            to_email: Email del responsable de la institución
            institution_name: Nombre de la institución
            criterion_code: Código del criterio (criteria_id)
            criterion_name: Nombre descriptivo del criterio
            approved: True si fue aprobado, False si fue rechazado
            notes: Notas de validación (motivo del rechazo, si aplica)

        Returns:
            True si el correo se envió correctamente, False en caso contrario
        """
        self._initialize()

        action = "aprobada" if approved else "rechazada"
        subject = f"Corrección {action}: {criterion_code} — {institution_name}"
        html_content = self._get_followup_validated_html(
            institution_name, criterion_code, criterion_name, approved, notes,
        )

        if not self._fastmail:
            logger.info("=" * 50)
            logger.info(f"[MODO DESARROLLO] Email de corrección {action} simulado:")
            logger.info(f"  Para: {to_email}")
            logger.info(f"  Institución: {institution_name}")
            logger.info(f"  Criterio: {criterion_code} — {criterion_name}")
            if not approved and notes:
                logger.info(f"  Motivo rechazo: {notes}")
            logger.info("=" * 50)
            return True

        try:
            logger.info(f"Enviando email de corrección {action} a {to_email}...")
            message = MessageSchema(
                subject=subject,
                recipients=[to_email],
                body=html_content,
                subtype=MessageType.html,
            )
            await self._fastmail.send_message(message)
            logger.info(f"Email de corrección {action} enviado exitosamente a {to_email}")
            return True
        except Exception as e:
            logger.error(
                f"Error al enviar email de corrección {action} a {to_email}: "
                f"{type(e).__name__}: {str(e)}"
            )
            return False


    @staticmethod
    def _get_notification_reminder_html(title: str, message: str, link: Optional[str]) -> str:
        """Template HTML para recordatorio de notificación no leída."""
        button_block = (
            f'<div style="text-align:center;margin:20px 0;">'
            f'<a href="{link}" style="display:inline-block;background:#800000;color:white;'
            f'padding:12px 30px;text-decoration:none;border-radius:5px;font-size:15px;font-weight:600;">'
            f'Ver en el Sistema</a></div>'
            if link else ""
        )
        return f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
</head>
<body style="margin:0;padding:0;font-family:'Segoe UI',Tahoma,Geneva,Verdana,sans-serif;background-color:#f4f4f4;">
    <table role="presentation" width="100%" cellspacing="0" cellpadding="0"
           style="max-width:600px;margin:0 auto;padding:20px;">
        <tr>
            <td style="background-color:#f59e0b;padding:30px;text-align:center;border-radius:12px 12px 0 0;">
                <h1 style="color:white;margin:0;font-size:24px;">&#9200; Recordatorio</h1>
                <p style="color:rgba(255,255,255,0.9);margin:8px 0 0;font-size:14px;">
                    Evaluador GOB.BO
                </p>
            </td>
        </tr>
        <tr>
            <td style="background-color:white;padding:40px 30px;border-radius:0 0 12px 12px;
                       box-shadow:0 4px 6px rgba(0,0,0,0.1);">
                <p style="color:#555;font-size:15px;line-height:1.6;margin:0 0 20px;">
                    Tiene una notificación pendiente en el sistema:
                </p>
                <div style="background:#f9f9f9;padding:20px;border-left:4px solid #f59e0b;
                            border-radius:0 8px 8px 0;margin:0 0 20px;">
                    <h3 style="color:#333;margin:0 0 10px;font-size:16px;">{title}</h3>
                    <p style="color:#555;margin:0;font-size:14px;line-height:1.6;">{message}</p>
                </div>
                {button_block}
                <p style="color:#6b7280;font-size:13px;margin:20px 0 0;line-height:1.6;">
                    Este es un recordatorio automático porque la notificación lleva
                    más de 24 horas sin revisar.
                </p>
            </td>
        </tr>
        <tr>
            <td style="padding:20px;text-align:center;">
                <p style="color:#999;font-size:11px;margin:0;line-height:1.6;">
                    Este es un mensaje automático del Sistema de Evaluación GOB.BO<br>
                    Por favor no respondas a este correo.
                </p>
            </td>
        </tr>
    </table>
</body>
</html>"""

    async def send_notification_reminder(
        self,
        to_email: str,
        title: str,
        message: str,
        link: Optional[str] = None,
    ) -> bool:
        """
        Envía un email de recordatorio para una notificación in-app no leída.

        Args:
            to_email: Email del evaluador destinatario
            title: Título de la notificación original
            message: Mensaje de la notificación original
            link: URL completa al recurso relacionado (opcional)

        Returns:
            True si el email se envió correctamente, False en caso contrario
        """
        self._initialize()

        subject = f"Recordatorio: {title}"
        html_content = self._get_notification_reminder_html(title, message, link)

        if not self._fastmail:
            logger.info("=" * 50)
            logger.info("[MODO DESARROLLO] Email de recordatorio simulado:")
            logger.info(f"  Para: {to_email}")
            logger.info(f"  Asunto: {subject}")
            logger.info("=" * 50)
            return True

        try:
            logger.info(f"Enviando recordatorio de notificación a {to_email}...")
            message_schema = MessageSchema(
                subject=subject,
                recipients=[to_email],
                body=html_content,
                subtype=MessageType.html,
            )
            await self._fastmail.send_message(message_schema)
            logger.info(f"Recordatorio enviado exitosamente a {to_email}")
            return True
        except Exception as e:
            logger.error(
                f"Error al enviar recordatorio a {to_email}: "
                f"{type(e).__name__}: {str(e)}"
            )
            return False

    def _get_password_changed_html(self, username: str) -> str:
        """Template HTML para confirmacion de cambio de contrasena."""
        from datetime import datetime as dt
        change_date = dt.now().strftime("%d/%m/%Y %H:%M")
        return (
            "<!DOCTYPE html>"
            "<html lang=es><head><meta charset=UTF-8></head>"
            "<body style=margin:0;padding:0;font-family:Arial,sans-serif;background-color:#f4f4f4;>"
            "<table role=presentation width=100% cellspacing=0 cellpadding=0 style=max-width:600px;margin:0 auto;padding:20px;>"
            "<tr><td style=background-color:#10b981;padding:30px;text-align:center;border-radius:12px 12px 0 0;>"
            "<h1 style=color:white;margin:0;font-size:24px;>Evaluador GOB.BO</h1>"
            "<p style=color:rgba(255,255,255,0.9);margin:8px 0 0;font-size:16px;font-weight:600;>Contrasena Actualizada</p>"
            "</td></tr>"
            "<tr><td style=background-color:white;padding:40px 30px;border-radius:0 0 12px 12px;box-shadow:0 4px 6px rgba(0,0,0,0.1);>"
            f"<p style=color:#555;font-size:15px;>Hola <strong>{username}</strong>,</p>"
            "<p style=color:#555;font-size:15px;>Tu contrasena ha sido actualizada exitosamente.</p>"
            f"<div style=background:#f9f9f9;padding:16px;border-radius:8px;margin:0 0 24px;><p style=margin:0;><strong>Fecha:</strong> {change_date}</p></div>"
            "<div style=background:#fef3c7;border-left:4px solid #f59e0b;padding:15px;border-radius:0 8px 8px 0;>"
            "<p style=margin:0;font-size:14px;color:#92400e;><strong>No fuiste tu?</strong><br>Si no realizaste este cambio, contacta al administrador.</p>"
            "</div></td></tr>"
            "<tr><td style=padding:20px;text-align:center;><p style=color:#999;font-size:11px;>Mensaje automatico del Sistema GOB.BO</p></td></tr>"
            "</table></body></html>"
        )

    async def send_password_changed_email(self, to_email: str, username: str) -> bool:
        """Envia email de confirmacion de cambio de contrasena."""
        self._initialize()
        subject = "Contrasena actualizada - GOB.BO"
        html_content = self._get_password_changed_html(username)
        if not self._fastmail:
            logger.info("=" * 50)
            logger.info("[MODO DESARROLLO] Email cambio de contrasena simulado:")
            logger.info(f"  Para: {to_email} / Usuario: {username}")
            logger.info("=" * 50)
            return True
        try:
            message = MessageSchema(
                subject=subject,
                recipients=[to_email],
                body=html_content,
                subtype=MessageType.html,
            )
            await self._fastmail.send_message(message)
            logger.info(f"Email cambio contrasena enviado a {to_email}")
            return True
        except Exception as e:
            logger.error(f"Error al enviar email cambio contrasena: {type(e).__name__}: {str(e)}")
            return False


# Instancia global del servicio
email_service = EmailService()
