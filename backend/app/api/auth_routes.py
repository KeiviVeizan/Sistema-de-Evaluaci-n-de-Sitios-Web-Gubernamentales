"""
Rutas de autenticación: login con 2FA y perfil del usuario actual.
"""

import logging
import random
from typing import Dict

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.database_models import User
from app.auth.security import verify_password, create_access_token
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
    user = db.query(User).filter(User.username == credentials.username).first()

    if not user or not verify_password(credentials.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales incorrectas",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuario desactivado",
        )

    # Generar código de 6 dígitos
    code = str(random.randint(100000, 999999))
    _2fa_codes[user.username] = code

    # Enviar código por correo electrónico (en segundo plano)
    background_tasks.add_task(
        email_service.send_2fa_code,
        email=user.email,
        code=code,
        username=user.username,
    )

    logger.info(f"Código 2FA generado para {user.username}")

    return {
        "message": "Código de verificación enviado a tu correo electrónico.",
        "username": user.username,
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
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No hay código pendiente para este usuario",
        )

    # Validar que el código coincida
    if _2fa_codes[verification.username] != verification.code:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Código de verificación inválido",
        )

    # Obtener usuario
    user = db.query(User).filter(User.username == verification.username).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado",
        )

    # Limpiar código usado (un código solo se puede usar una vez)
    del _2fa_codes[verification.username]

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
