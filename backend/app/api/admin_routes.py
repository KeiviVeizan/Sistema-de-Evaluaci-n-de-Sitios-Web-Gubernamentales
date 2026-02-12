"""
Rutas administrativas protegidas por roles (RBAC).

Endpoints para gestión de usuarios, instituciones y métricas del sistema.
"""

import logging
import secrets
import string

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.email_service import email_service
from app.models.database_models import (
    Evaluation,
    EvaluationStatus,
    Institution,
    User,
    UserRole,
    Website,
)
from app.auth.security import hash_password
from app.auth.dependencies import (
    get_current_user,
    allow_admin_secretary,
    allow_admin_evaluator,
    allow_superadmin,
)
from app.schemas.auth_schemas import (
    AdminStatsResponse,
    InstitutionCreate,
    InstitutionDetailResponse,
    InstitutionListResponse,
    InstitutionResponse,
    InstitutionUpdate,
    InstitutionWithUser,
    UserCreate,
    UserListResponse,
    UserResponse,
    UserUpdate,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin", tags=["Admin"])


def _generate_password(length: int = 12) -> str:
    """Genera una contraseña aleatoria segura."""
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
    return "".join(secrets.choice(alphabet) for _ in range(length))


# ============================================================================
# User Endpoints
# ============================================================================

@router.post(
    "/users",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Crear usuario (solo Superadmin)",
)
async def create_user(
    user_data: UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(allow_superadmin),
):
    """
    Crea un nuevo usuario interno (superadmin, secretary o evaluator).
    Genera una contraseña aleatoria y envía las credenciales por email.
    Solo accesible por superadmin.
    """
    # Verificar unicidad de username y email
    existing = db.query(User).filter(
        (User.username == user_data.username) | (User.email == user_data.email)
    ).first()
    if existing:
        field = "username" if existing.username == user_data.username else "email"
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Ya existe un usuario con ese {field}",
        )

    # Usar la contraseña provista o generar una automáticamente
    plain_password = user_data.password if user_data.password else _generate_password()

    db_user = User(
        username=user_data.username,
        email=user_data.email,
        hashed_password=hash_password(plain_password),
        full_name=user_data.full_name,
        role=user_data.role,
        is_active=True,
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    logger.info(
        f"Usuario creado: {db_user.username} ({db_user.role.value}) por {current_user.username}"
    )

    # Enviar email de bienvenida con credenciales
    await email_service.send_welcome_email(
        email=db_user.email,
        password=plain_password,
        role=db_user.role.value,
    )

    return UserResponse.from_user(db_user)


@router.get(
    "/users",
    response_model=UserListResponse,
    summary="Listar usuarios (Superadmin o Secretary)",
)
def list_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=1000),
    search: str = Query(None, description="Buscar por nombre o email"),
    db: Session = Depends(get_db),
    current_user: User = Depends(allow_admin_secretary),
):
    """Lista paginada de todos los usuarios del sistema."""
    query = db.query(User)

    if search:
        search_term = f"%{search}%"
        query = query.filter(
            (User.username.ilike(search_term)) |
            (User.email.ilike(search_term)) |
            (User.full_name.ilike(search_term))
        )

    total = query.count()
    users = query.offset(skip).limit(limit).all()

    return UserListResponse(
        total=total,
        items=[UserResponse.from_user(u) for u in users],
    )


@router.patch("/users/{user_id}", response_model=UserResponse, summary="Actualizar usuario (solo Superadmin)")
@router.put("/users/{user_id}", response_model=UserResponse, summary="Actualizar usuario (solo Superadmin)", include_in_schema=False)
def update_user(
    user_id: int,
    user_data: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(allow_superadmin),
):
    """
    Actualiza los datos de un usuario existente (rol, estado, email, nombre).
    Solo accesible por superadmin.
    """
    db_user = db.query(User).filter(User.id == user_id).first()
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado",
        )

    update_data = user_data.model_dump(exclude_unset=True)

    if "email" in update_data:
        existing_email = db.query(User).filter(
            User.email == update_data["email"],
            User.id != user_id,
        ).first()
        if existing_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Ya existe un usuario con ese email",
            )

    for field, value in update_data.items():
        setattr(db_user, field, value)

    db.commit()
    db.refresh(db_user)

    logger.info(f"Usuario actualizado: {db_user.username} (ID: {db_user.id}) por {current_user.username}")
    return UserResponse.from_user(db_user)


# ============================================================================
# Institution Endpoints
# ============================================================================

@router.post(
    "/institutions",
    response_model=InstitutionWithUser,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar institución (Superadmin o Secretary)",
)
async def create_institution(
    data: InstitutionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(allow_admin_secretary),
):
    """
    Registra una nueva institución gubernamental y crea su usuario responsable.
    """
    # Verificar dominio único
    existing_inst = db.query(Institution).filter(Institution.domain == data.domain).first()
    if existing_inst:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Ya existe una institución con el dominio {data.domain}",
        )

    # Verificar email único
    existing_user = db.query(User).filter(User.email == data.contact_email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Ya existe un usuario con el correo {data.contact_email}",
        )

    # Crear institución
    institution = Institution(
        name=data.name,
        domain=data.domain,
        is_active=True,
    )
    db.add(institution)
    db.flush()  # Para obtener el ID

    # Generar contraseña y username para el responsable
    generated_password = _generate_password()
    username = data.contact_email.split("@")[0].lower().replace(".", "_")

    # Verificar unicidad de username
    existing_username = db.query(User).filter(User.username == username).first()
    if existing_username:
        username = f"{username}_{institution.id}"

    # Crear usuario responsable
    user = User(
        username=username,
        email=data.contact_email,
        hashed_password=hash_password(generated_password),
        full_name=data.contact_name,
        position=data.contact_position,
        role=UserRole.ENTITY_USER,
        is_active=True,
        institution_id=institution.id,
    )
    db.add(user)
    db.commit()
    db.refresh(institution)
    db.refresh(user)

    logger.info(f"Institución creada: {institution.name} ({institution.domain}) por {current_user.username}")

    # Enviar email de bienvenida con credenciales al responsable
    await email_service.send_welcome_email(
        email=user.email,
        password=generated_password,
        role=user.role.value,
        institution_name=institution.name,
    )

    return InstitutionWithUser(
        institution=InstitutionResponse.model_validate(institution),
        initial_user=UserResponse.from_user(user),
        generated_password=generated_password,
    )


@router.get(
    "/institutions",
    response_model=InstitutionListResponse,
    summary="Listar instituciones (Superadmin o Secretary)",
)
def list_institutions(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=1000),
    search: str = Query(None, description="Buscar por nombre"),
    letter: str = Query(None, description="Filtrar por letra inicial"),
    domain: str = Query(None, description="Filtrar por dominio exacto"),
    db: Session = Depends(get_db),
    current_user: User = Depends(allow_admin_secretary),
):
    """Lista paginada de instituciones registradas."""
    query = db.query(Institution)

    if search:
        query = query.filter(Institution.name.ilike(f"%{search}%"))

    if letter:
        query = query.filter(Institution.name.ilike(f"{letter}%"))

    if domain:
        # Normalizar: quitar www. para comparación
        normalized = domain.replace("www.", "", 1) if domain.startswith("www.") else domain
        query = query.filter(
            Institution.domain.ilike(normalized) | Institution.domain.ilike(f"www.{normalized}")
        )

    total = query.count()
    institutions = query.offset(skip).limit(limit).all()

    return InstitutionListResponse(
        total=total,
        items=[InstitutionResponse.model_validate(i) for i in institutions],
    )


@router.get(
    "/institutions/{institution_id}",
    summary="Detalle de institución con responsable y evaluaciones",
)
def get_institution_detail(
    institution_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(allow_admin_secretary),
):
    """Obtiene el detalle completo de una institución con responsable y evaluaciones."""
    institution = db.query(Institution).filter(Institution.id == institution_id).first()
    if not institution:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Institución no encontrada",
        )
    
    # Buscar el usuario responsable (ENTITY_USER de esta institución)
    responsible = db.query(User).filter(
        User.institution_id == institution_id,
        User.role == UserRole.ENTITY_USER,
    ).first()
    
    # Buscar evaluaciones relacionadas (a través del dominio de la institución)
    # Se usa domain en lugar de institution_name para evitar desincronizaciones
    # cuando el nombre de la institución cambia o el website fue creado por otra ruta.
    evals_qs = (
        db.query(Evaluation)
        .join(Website, Evaluation.website_id == Website.id)
        .filter(Website.domain == institution.domain)
        .order_by(Evaluation.started_at.desc())
        .all()
    )
    evaluations = []
    for ev in evals_qs:
        evaluations.append({
            "id": ev.id,
            "started_at": ev.started_at.isoformat() if ev.started_at else None,
            "completed_at": ev.completed_at.isoformat() if ev.completed_at else None,
            "status": ev.status.value,
            "score_total": ev.score_total,
            "score_digital_sovereignty": ev.score_digital_sovereignty,
            "score_accessibility": ev.score_accessibility,
            "score_usability": ev.score_usability,
            "score_semantic_web": ev.score_semantic_web,
        })
    
    return {
        "institution": InstitutionResponse.model_validate(institution),
        "responsible": UserResponse.from_user(responsible) if responsible else None,
        "evaluations": evaluations,
    }


@router.patch("/institutions/{institution_id}", response_model=InstitutionResponse, summary="Actualizar institución (Superadmin o Secretary)")
@router.put("/institutions/{institution_id}", response_model=InstitutionResponse, summary="Actualizar institución (Superadmin o Secretary)", include_in_schema=False)
def update_institution(
    institution_id: int,
    inst_data: InstitutionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(allow_admin_secretary),
):
    """Actualiza los datos de una institución."""
    institution = db.query(Institution).filter(Institution.id == institution_id).first()
    if not institution:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Institución no encontrada",
        )

    update_data = inst_data.model_dump(exclude_unset=True)

    # Separar campos de institución de los del responsable
    inst_fields = {k: v for k, v in update_data.items() if k in ("name", "domain", "is_active")}
    contact_fields = {k: v for k, v in update_data.items() if k in ("contact_name", "contact_email", "contact_position")}

    for field, value in inst_fields.items():
        setattr(institution, field, value)

    # Actualizar responsable si se proporcionaron datos
    if contact_fields:
        responsible = db.query(User).filter(
            User.institution_id == institution_id,
            User.role == UserRole.ENTITY_USER,
        ).first()
        if responsible:
            if "contact_name" in contact_fields:
                responsible.full_name = contact_fields["contact_name"]
            if "contact_email" in contact_fields:
                responsible.email = contact_fields["contact_email"]
            if "contact_position" in contact_fields:
                responsible.position = contact_fields["contact_position"]

    db.commit()
    db.refresh(institution)

    logger.info(f"Institución actualizada: {institution.name} (ID: {institution_id}) por {current_user.username}")
    return InstitutionResponse.model_validate(institution)


@router.delete(
    "/institutions/{institution_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar institución (Solo Superadmin)",
)
def delete_institution(
    institution_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(allow_superadmin),
):
    """
    Elimina una institución y todos sus datos relacionados.
    
    ADVERTENCIA: Esta operación es irreversible y eliminará:
    - La institución
    - Todos los usuarios asociados (responsables)
    """
    institution = db.query(Institution).filter(Institution.id == institution_id).first()
    if not institution:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Institución no encontrada",
        )
    
    institution_name = institution.name
    
    # Eliminar la institución (cascade eliminará usuarios relacionados)
    db.delete(institution)
    db.commit()
    
    logger.warning(f"Institución ELIMINADA: {institution_name} (ID: {institution_id}) por {current_user.username}")
    return None


# ============================================================================
# Stats Endpoint
# ============================================================================

@router.get(
    "/stats",
    response_model=AdminStatsResponse,
    summary="Métricas globales (Superadmin o Evaluator)",
)
def get_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(allow_admin_evaluator),
):
    """Retorna métricas globales del sistema."""
    total_evaluations = db.query(Evaluation).count()
    total_websites = db.query(Website).count()
    total_users = db.query(User).count()
    total_institutions = db.query(Institution).count()

    # Evaluaciones por estado
    status_counts = (
        db.query(Evaluation.status, func.count(Evaluation.id))
        .group_by(Evaluation.status)
        .all()
    )
    evaluations_by_status = {s.value: count for s, count in status_counts}

    # Promedio de score total (solo evaluaciones completadas)
    avg_result = (
        db.query(func.avg(Evaluation.score_total))
        .filter(Evaluation.status == EvaluationStatus.COMPLETED)
        .scalar()
    )

    return AdminStatsResponse(
        total_evaluations=total_evaluations,
        total_websites=total_websites,
        total_users=total_users,
        total_institutions=total_institutions,
        evaluations_by_status=evaluations_by_status,
        avg_score=round(avg_result, 2) if avg_result else None,
    )
