"""
Rutas de perfil de usuario.

Permite a los usuarios autenticados ver y editar su perfil,
y cambiar su contraseña con validación robusta de política.
"""

import re
import logging
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, validator
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.database_models import User
from app.auth.dependencies import get_current_active_user
from app.auth.security import hash_password, verify_password
from app.services.email_service import email_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/profile", tags=["profile"])


class ProfileUpdate(BaseModel):
    full_name: str
    position: str = None


class PasswordChange(BaseModel):
    current_password: str
    new_password: str

    @validator('new_password')
    def validate_password(cls, v):
        """Validar política de contraseñas."""
        if len(v) < 8:
            raise ValueError('La contraseña debe tener al menos 8 caracteres')
        if not re.search(r'[A-Z]', v):
            raise ValueError('La contraseña debe contener al menos una mayúscula')
        if not re.search(r'[a-z]', v):
            raise ValueError('La contraseña debe contener al menos una minúscula')
        if not re.search(r'\d', v):
            raise ValueError('La contraseña debe contener al menos un número')
        if not re.search(r'[@#$!%*?&]', v):
            raise ValueError('La contraseña debe contener al menos un carácter especial (@#$!%*?&)')
        return v


@router.get("/me")
async def get_profile(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Obtener perfil del usuario actual."""
    profile = {
        "id": current_user.id,
        "username": current_user.username,
        "email": current_user.email,
        "full_name": current_user.full_name,
        "position": current_user.position,
        "role": current_user.role,
        "institution_id": current_user.institution_id,
        "is_active": current_user.is_active,
        "created_at": current_user.created_at,
    }

    # Si tiene institución, incluir datos
    if current_user.institution_id:
        from app.models.database_models import Institution
        institution = db.query(Institution).filter(
            Institution.id == current_user.institution_id
        ).first()
        if institution:
            profile["institution_name"] = institution.name

    return profile


@router.patch("/me")
async def update_profile(
    data: ProfileUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Actualizar perfil del usuario."""
    current_user.full_name = data.full_name
    if data.position is not None:
        current_user.position = data.position

    db.commit()
    db.refresh(current_user)

    return {"message": "Perfil actualizado exitosamente"}


@router.post("/change-password")
async def change_password(
    data: PasswordChange,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Cambiar contraseña del usuario."""
    username = current_user.username or current_user.email

    # Verificar contraseña actual
    if not verify_password(data.current_password, current_user.hashed_password):
        logger.warning(f"Cambio de contraseña fallido para {username}: contraseña actual incorrecta")
        raise HTTPException(status_code=400, detail="Contraseña actual incorrecta")

    # Actualizar contraseña
    logger.info(f"Actualizando contraseña para {username}...")
    current_user.hashed_password = hash_password(data.new_password)

    # COMMIT ANTES del email para evitar ROLLBACK si el email falla
    try:
        db.commit()
        # Expulsar objeto del identity map para forzar recarga desde BD en próxima consulta
        db.expire(current_user)
        db.refresh(current_user)
        logger.info(f"✓ Contraseña actualizada y commit exitoso para {username}")
    except Exception as e:
        db.rollback()
        logger.error(f"✗ Error al guardar contraseña para {username}: {e}")
        raise HTTPException(status_code=500, detail="Error al actualizar la contraseña")

    # Enviar email de confirmación (después del commit, el error NO revierte el cambio)
    try:
        await email_service.send_password_changed_email(
            to_email=current_user.email,
            username=username
        )
        logger.info(f"✓ Email de confirmación enviado a {current_user.email}")
    except Exception as e:
        logger.warning(f"No se pudo enviar email de confirmación de cambio de contraseña: {e}")

    return {
        "message": "Contraseña actualizada exitosamente",
        "logout_required": True,
    }
