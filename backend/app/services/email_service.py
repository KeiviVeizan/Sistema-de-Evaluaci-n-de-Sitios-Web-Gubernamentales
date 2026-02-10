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


# Instancia global del servicio
email_service = EmailService()
