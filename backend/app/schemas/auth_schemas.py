"""
Schemas Pydantic para autenticación, usuarios e instituciones.
"""

from datetime import datetime
from typing import Dict, List, Optional

from pydantic import BaseModel, EmailStr, Field, field_validator

from app.models.database_models import UserRole


# ============================================================================
# Auth / Login
# ============================================================================

class TokenResponse(BaseModel):
    """Respuesta de login exitoso."""
    access_token: str
    token_type: str = "bearer"
    user: "UserResponse"


# ============================================================================
# User
# ============================================================================

class UserCreate(BaseModel):
    """Schema para crear un usuario interno."""
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: Optional[str] = Field(None, min_length=8)
    full_name: Optional[str] = None
    role: UserRole
    position: Optional[str] = Field(None, max_length=100)
    institution_id: Optional[int] = None

    @field_validator("username")
    @classmethod
    def validate_username(cls, v: str) -> str:
        if not v.replace("_", "").replace(".", "").isalnum():
            raise ValueError("El username solo puede contener letras, números, puntos y guiones bajos")
        return v.lower()


class UserResponse(BaseModel):
    """Respuesta con datos de usuario (sin password)."""
    id: int
    username: str
    email: str
    full_name: Optional[str] = None
    position: Optional[str] = None
    is_active: bool
    role: str
    institution_id: Optional[int] = None
    institution_name: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

    @classmethod
    def from_user(cls, user) -> "UserResponse":
        return cls(
            id=user.id,
            username=user.username,
            email=user.email,
            full_name=user.full_name,
            position=user.position,
            is_active=user.is_active,
            role=user.role.value,
            institution_id=user.institution_id,
            institution_name=user.institution.name if user.institution else None,
            created_at=user.created_at,
        )


class UserListResponse(BaseModel):
    """Lista paginada de usuarios."""
    total: int
    items: List[UserResponse]


# ============================================================================
# Institution
# ============================================================================

class InstitutionCreate(BaseModel):
    """Schema para crear una institución con su usuario responsable."""
    # Datos de la institución
    name: str = Field(..., min_length=3, max_length=255)
    domain: str = Field(..., min_length=5, max_length=255)

    # Datos del responsable (usuario EVALUATOR)
    contact_name: str = Field(..., min_length=3, max_length=100)
    contact_email: EmailStr
    contact_position: Optional[str] = Field(None, max_length=100)

    @field_validator("domain")
    @classmethod
    def validate_domain(cls, v: str) -> str:
        v = v.lower().strip()
        if not v.endswith(".gob.bo"):
            raise ValueError("El dominio debe terminar en .gob.bo")
        return v

    @field_validator("contact_email")
    @classmethod
    def validate_contact_email(cls, v: str) -> str:
        return v.lower().strip()


class InstitutionResponse(BaseModel):
    """Respuesta con datos de institución."""
    id: int
    name: str
    domain: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class InstitutionWithUser(BaseModel):
    """Respuesta al crear institución: incluye usuario generado y password temporal."""
    institution: InstitutionResponse
    initial_user: UserResponse
    generated_password: str = Field(
        ..., description="Contraseña generada. Solo se muestra una vez."
    )


class InstitutionListResponse(BaseModel):
    """Lista paginada de instituciones."""
    total: int
    items: List[InstitutionResponse]


class InstitutionUpdate(BaseModel):
    """Schema para actualizar una institución y su responsable."""
    # Datos de la institución (todos opcionales)
    name: Optional[str] = Field(None, min_length=3, max_length=255)
    domain: Optional[str] = Field(None, min_length=5, max_length=255)
    is_active: Optional[bool] = None

    # Datos del responsable (todos opcionales)
    contact_name: Optional[str] = Field(None, min_length=3, max_length=100)
    contact_email: Optional[EmailStr] = None
    contact_position: Optional[str] = Field(None, max_length=100)

    @field_validator("domain")
    @classmethod
    def validate_domain(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            v = v.lower().strip()
            if not v.endswith(".gob.bo"):
                raise ValueError("El dominio debe terminar en .gob.bo")
        return v


class InstitutionDetailResponse(BaseModel):
    """Respuesta detallada de institución con responsable y evaluaciones."""
    institution: InstitutionResponse
    responsible: Optional[UserResponse] = None
    evaluations: List[dict] = Field(default_factory=list)


class UserUpdate(BaseModel):
    """Schema para actualizar un usuario."""
    full_name: Optional[str] = None
    username: Optional[str] = Field(None, min_length=3, max_length=50)
    email: Optional[EmailStr] = None
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None
    position: Optional[str] = Field(None, max_length=100)
    institution_id: Optional[int] = None
    new_password: Optional[str] = Field(None, min_length=8)

    @field_validator("username")
    @classmethod
    def validate_username(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            if not v.replace("_", "").replace(".", "").isalnum():
                raise ValueError("El username solo puede contener letras, números, puntos y guiones bajos")
            return v.lower()
        return v


# ============================================================================
# Admin Stats
# ============================================================================

class AdminStatsResponse(BaseModel):
    """Métricas globales del sistema."""
    total_evaluations: int
    total_websites: int
    total_users: int
    total_institutions: int
    evaluations_by_status: Dict[str, int]
    avg_score: Optional[float] = None


# Resolver forward references
TokenResponse.model_rebuild()
