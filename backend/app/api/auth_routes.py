"""
Rutas de autenticación: login con 2FA, perfil del usuario actual
y recuperación de contraseña.
"""

import logging
import random
import re
import string
from datetime import datetime, timedelta
from typing import Dict

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.database_models import User
from app.auth.security import verify_password, create_access_token, hash_password
from app.auth.dependencies import get_current_active_user
from app.schemas.auth_schemas import TokenResponse, UserResponse
from app.services.email_service import email_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["Auth"])


# ============================================================================
# Schemas para 2FA
# ============================================================================

class LoginRequest(BaseModel):
    """Request para el primer paso de login."""
    username: str
    password: str


class Verify2FARequest(BaseModel):
    """Request para verificar código 2FA."""
    username: str
    code: str


# ============================================================================
# Almacenamiento temporal de códigos 2FA
# En producción, usar Redis con TTL
# ============================================================================

_2fa_codes: Dict[str, str] = {}

# Almacenamiento temporal de códigos de recuperación de contraseña
# En producción, usar Redis con TTL
_password_reset_codes: Dict[str, dict] = {}


# ============================================================================
# Endpoints
# ============================================================================

@router.post(
    "/login",
    summary="Paso 1: Validar credenciales y generar código 2FA",
)
async def login(
    credentials: LoginRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """
    Valida credenciales y genera código de verificación de 6 dígitos.
    El código se envía al correo electrónico del usuario.
    """
    # Aceptar username o email en el campo "username"
    user = db.query(User).filter(
        (User.username == credentials.username) | (User.email == credentials.username)
    ).first()

    if not user:
        logger.warning(f"Login fallido: usuario '{credentials.username}' no encontrado")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales incorrectas",
        )

    db.refresh(user)

    if not verify_password(credentials.password, user.hashed_password):
        logger.warning(f"Login fallido para '{user.username or user.email}': contraseña incorrecta")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales incorrectas",
        )

    logger.info(f"Contraseña correcta para '{user.username or user.email}'")

    if not user.is_active:
        logger.warning(f"Login rechazado: usuario '{user.username or user.email}' desactivado")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuario desactivado",
        )

    # Usar username si existe, sino email como clave del código 2FA
    user_key = user.username or user.email

    # Generar código de 6 dígitos
    code = str(random.randint(100000, 999999))
    _2fa_codes[user_key] = code

    logger.info(f"Código 2FA generado para '{user_key}' (email: {user.email})")

    # Enviar código por correo electrónico (en segundo plano)
    background_tasks.add_task(
        email_service.send_2fa_code,
        email=user.email,
        code=code,
        username=user_key,
    )

    logger.info(f"Tarea de envío 2FA encolada para {user.email}")

    return {
        "message": "Código de verificación enviado a tu correo electrónico.",
        "username": user_key,
    }


@router.post(
    "/verify-2fa",
    response_model=TokenResponse,
    summary="Paso 2: Verificar código 2FA y obtener token",
)
async def verify_2fa(
    verification: Verify2FARequest,
    db: Session = Depends(get_db),
):
    """
    Verifica el código 2FA y retorna el JWT si es válido.
    """
    # Validar que existe un código pendiente
    if verification.username not in _2fa_codes:
        logger.warning(f"verify-2fa: no hay código pendiente para '{verification.username}'")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No hay código pendiente para este usuario",
        )

    # Validar que el código coincida
    if _2fa_codes[verification.username] != verification.code:
        logger.warning(f"verify-2fa: código incorrecto para '{verification.username}'")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Código de verificación inválido",
        )

    # Obtener usuario por username o email (la clave puede ser cualquiera de los dos)
    user = db.query(User).filter(
        (User.username == verification.username) | (User.email == verification.username)
    ).first()
    if not user:
        logger.error(f"verify-2fa: usuario '{verification.username}' no encontrado en BD")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado",
        )

    # Limpiar código usado (un código solo se puede usar una vez)
    del _2fa_codes[verification.username]
    logger.info(f"✓ Código 2FA verificado correctamente para '{verification.username}'")

    # Generar JWT
    access_token = create_access_token(
        data={"sub": user.username, "role": user.role.value}
    )

    logger.info(f"✓ 2FA exitoso: {user.username} ({user.role.value})")

    return TokenResponse(
        access_token=access_token,
        user=UserResponse.from_user(user),
    )


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Perfil del usuario actual",
    description="Retorna los datos del usuario autenticado.",
)
async def get_me(
    current_user: User = Depends(get_current_active_user),
):
    """Retorna el perfil del usuario autenticado."""
    return UserResponse.from_user(current_user)


# ============================================================================
# Recuperación de contraseña
# ============================================================================

@router.post(
    "/forgot-password",
    summary="Paso 1: Enviar código de recuperación al email",
)
async def forgot_password(
    data: dict,
    db: Session = Depends(get_db),
):
    """Enviar código de recuperación al email."""
    email = data.get("email", "").strip().lower()

    if not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email requerido",
        )

    # Buscar usuario por email
    user = db.query(User).filter(User.email == email).first()

    if not user:
        # No revelar si el email existe o no (seguridad)
        return {"message": "Si el email existe, recibirás un código de recuperación"}

    # Generar código de 6 dígitos
    code = ''.join(random.choices(string.digits, k=6))

    # Guardar código con expiración de 15 minutos
    _password_reset_codes[email] = {
        "code": code,
        "user_id": user.id,
        "expires_at": datetime.now() + timedelta(minutes=15),
        "attempts": 0,
    }

    # Enviar email con el código
    try:
        await email_service.send_password_reset_email(
            to_email=email,
            username=user.username,
            code=code,
        )
    except Exception as e:
        logger.error(f"Error enviando email de recuperación: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al enviar el email de recuperación",
        )

    return {"message": "Si el email existe, recibirás un código de recuperación"}


@router.post(
    "/verify-reset-code",
    summary="Paso 2: Verificar código de recuperación",
)
async def verify_reset_code(
    data: dict,
    db: Session = Depends(get_db),
):
    """Verificar código de recuperación."""
    email = data.get("email", "").strip().lower()
    code = data.get("code", "").strip()

    if not email or not code:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email y código son requeridos",
        )

    # Verificar si existe el código
    reset_data = _password_reset_codes.get(email)

    if not reset_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No se encontró solicitud de recuperación para este email",
        )

    # Verificar expiración
    if datetime.now() > reset_data["expires_at"]:
        del _password_reset_codes[email]
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El código ha expirado. Solicita uno nuevo",
        )

    # Verificar intentos (máximo 5)
    if reset_data["attempts"] >= 5:
        del _password_reset_codes[email]
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Demasiados intentos. Solicita un nuevo código",
        )

    # Verificar código
    if reset_data["code"] != code:
        _password_reset_codes[email]["attempts"] += 1
        remaining = 5 - _password_reset_codes[email]["attempts"]
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Código incorrecto. Te quedan {remaining} intentos",
        )

    # Código válido — generar token temporal para el reset
    reset_token = ''.join(random.choices(string.ascii_letters + string.digits, k=32))
    _password_reset_codes[email]["reset_token"] = reset_token

    return {
        "message": "Código verificado correctamente",
        "reset_token": reset_token,
    }


@router.post(
    "/reset-password",
    summary="Paso 3: Establecer nueva contraseña",
)
async def reset_password(
    data: dict,
    db: Session = Depends(get_db),
):
    """Establecer nueva contraseña tras verificar código."""
    email = data.get("email", "").strip().lower()
    reset_token = data.get("reset_token", "")
    new_password = data.get("new_password", "")

    if not email or not reset_token or not new_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Todos los campos son requeridos",
        )

    # Verificar token
    reset_data = _password_reset_codes.get(email)

    if not reset_data or reset_data.get("reset_token") != reset_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token de recuperación inválido",
        )

    # Verificar expiración
    if datetime.now() > reset_data["expires_at"]:
        del _password_reset_codes[email]
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La sesión ha expirado. Inicia el proceso nuevamente",
        )

    # Validar política de contraseña
    if len(new_password) < 8:
        raise HTTPException(400, "La contraseña debe tener al menos 8 caracteres")
    if not re.search(r'[A-Z]', new_password):
        raise HTTPException(400, "La contraseña debe contener al menos una mayúscula")
    if not re.search(r'[a-z]', new_password):
        raise HTTPException(400, "La contraseña debe contener al menos una minúscula")
    if not re.search(r'\d', new_password):
        raise HTTPException(400, "La contraseña debe contener al menos un número")
    if not re.search(r'[@#$!%*?&]', new_password):
        raise HTTPException(400, "La contraseña debe contener al menos un carácter especial (@#$!%*?&)")

    # Actualizar contraseña
    user = db.query(User).filter(User.id == reset_data["user_id"]).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado",
        )

    user.hashed_password = hash_password(new_password)
    db.commit()

    # Limpiar código usado
    del _password_reset_codes[email]

    # Enviar email de confirmación (no bloquear si falla)
    try:
        await email_service.send_password_changed_email(
            to_email=email,
            username=user.username,
        )
    except Exception:
        pass

    return {"message": "Contraseña actualizada exitosamente"}
