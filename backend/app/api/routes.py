"""
Rutas de la API REST.

Define todos los endpoints para gestionar sitios web y evaluaciones.
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
import tldextract
import logging

from app.database import get_db
from app.models.database_models import Website, Evaluation, CrawlStatus, EvaluationStatus
from app.schemas.pydantic_schemas import (
    WebsiteCreate,
    WebsiteUpdate,
    WebsiteResponse,
    WebsiteList,
    EvaluationCreate,
    EvaluationResponse,
    EvaluationList,
    EvaluationDetailResponse
)

logger = logging.getLogger(__name__)

router = APIRouter()


# ============================================================================
# Website Endpoints
# ============================================================================

@router.post(
    "/websites",
    response_model=WebsiteResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Websites"]
)
def create_website(
    website: WebsiteCreate,
    db: Session = Depends(get_db)
) -> Website:
    """
    Registra un nuevo sitio web gubernamental para evaluación.

    Args:
        website: Datos del sitio web a registrar
        db: Sesión de base de datos

    Returns:
        Website: Sitio web creado

    Raises:
        HTTPException: Si la URL ya está registrada
    """
    # Verificar si la URL ya existe
    existing = db.query(Website).filter(Website.url == website.url).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"La URL {website.url} ya está registrada"
        )

    # Extraer dominio
    extracted = tldextract.extract(website.url)
    domain = f"{extracted.domain}.{extracted.suffix}"

    # Crear nuevo sitio web
    db_website = Website(
        url=website.url,
        domain=domain,
        institution_name=website.institution_name,
        crawl_status=CrawlStatus.PENDING
    )

    db.add(db_website)
    db.commit()
    db.refresh(db_website)

    logger.info(f"Sitio web creado: {db_website.id} - {db_website.url}")
    return db_website


@router.get(
    "/websites",
    response_model=WebsiteList,
    tags=["Websites"]
)
def list_websites(
    skip: int = Query(0, ge=0, description="Número de registros a saltar"),
    limit: int = Query(100, ge=1, le=500, description="Número máximo de registros"),
    active_only: bool = Query(True, description="Solo sitios activos"),
    db: Session = Depends(get_db)
) -> dict:
    """
    Lista todos los sitios web registrados.

    Args:
        skip: Número de registros a saltar (paginación)
        limit: Número máximo de registros a retornar
        active_only: Filtrar solo sitios activos
        db: Sesión de base de datos

    Returns:
        dict: Total y lista de sitios web
    """
    query = db.query(Website)

    if active_only:
        query = query.filter(Website.is_active == True)

    total = query.count()
    websites = query.offset(skip).limit(limit).all()

    return {
        "total": total,
        "items": websites
    }


@router.get(
    "/websites/{website_id}",
    response_model=WebsiteResponse,
    tags=["Websites"]
)
def get_website(
    website_id: int,
    db: Session = Depends(get_db)
) -> Website:
    """
    Obtiene los detalles de un sitio web específico.

    Args:
        website_id: ID del sitio web
        db: Sesión de base de datos

    Returns:
        Website: Datos del sitio web

    Raises:
        HTTPException: Si el sitio web no existe
    """
    website = db.query(Website).filter(Website.id == website_id).first()

    if not website:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Sitio web {website_id} no encontrado"
        )

    return website


@router.patch(
    "/websites/{website_id}",
    response_model=WebsiteResponse,
    tags=["Websites"]
)
def update_website(
    website_id: int,
    website_update: WebsiteUpdate,
    db: Session = Depends(get_db)
) -> Website:
    """
    Actualiza los datos de un sitio web.

    Args:
        website_id: ID del sitio web
        website_update: Datos a actualizar
        db: Sesión de base de datos

    Returns:
        Website: Sitio web actualizado

    Raises:
        HTTPException: Si el sitio web no existe
    """
    db_website = db.query(Website).filter(Website.id == website_id).first()

    if not db_website:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Sitio web {website_id} no encontrado"
        )

    # Actualizar campos proporcionados
    update_data = website_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_website, field, value)

    db.commit()
    db.refresh(db_website)

    logger.info(f"Sitio web actualizado: {db_website.id}")
    return db_website


@router.delete(
    "/websites/{website_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["Websites"]
)
def delete_website(
    website_id: int,
    db: Session = Depends(get_db)
) -> None:
    """
    Elimina un sitio web y todas sus evaluaciones.

    Args:
        website_id: ID del sitio web
        db: Sesión de base de datos

    Raises:
        HTTPException: Si el sitio web no existe
    """
    db_website = db.query(Website).filter(Website.id == website_id).first()

    if not db_website:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Sitio web {website_id} no encontrado"
        )

    db.delete(db_website)
    db.commit()

    logger.info(f"Sitio web eliminado: {website_id}")


# ============================================================================
# Evaluation Endpoints
# ============================================================================

@router.post(
    "/evaluations",
    response_model=EvaluationResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Evaluations"]
)
def create_evaluation(
    evaluation: EvaluationCreate,
    db: Session = Depends(get_db)
) -> Evaluation:
    """
    Inicia una nueva evaluación para un sitio web.

    Args:
        evaluation: Datos de la evaluación
        db: Sesión de base de datos

    Returns:
        Evaluation: Evaluación creada

    Raises:
        HTTPException: Si el sitio web no existe o hay evaluaciones en progreso
    """
    # Verificar que el sitio web existe
    website = db.query(Website).filter(Website.id == evaluation.website_id).first()
    if not website:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Sitio web {evaluation.website_id} no encontrado"
        )

    # Verificar que no haya una evaluación en progreso
    in_progress = db.query(Evaluation).filter(
        Evaluation.website_id == evaluation.website_id,
        Evaluation.status == EvaluationStatus.IN_PROGRESS
    ).first()

    if in_progress:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Ya existe una evaluación en progreso para este sitio web (ID: {in_progress.id})"
        )

    # Crear nueva evaluación
    db_evaluation = Evaluation(
        website_id=evaluation.website_id,
        status=EvaluationStatus.PENDING
    )

    db.add(db_evaluation)
    db.commit()
    db.refresh(db_evaluation)

    logger.info(f"Evaluación creada: {db_evaluation.id} para sitio {website.url}")

    # TODO: Iniciar proceso de crawling y evaluación en background (Celery)

    return db_evaluation


@router.get(
    "/evaluations",
    response_model=EvaluationList,
    tags=["Evaluations"]
)
def list_evaluations(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    website_id: int = Query(None, description="Filtrar por sitio web"),
    status_filter: str = Query(None, description="Filtrar por estado"),
    db: Session = Depends(get_db)
) -> dict:
    """
    Lista todas las evaluaciones realizadas.

    Args:
        skip: Número de registros a saltar
        limit: Número máximo de registros
        website_id: Filtrar por sitio web específico
        status_filter: Filtrar por estado
        db: Sesión de base de datos

    Returns:
        dict: Total y lista de evaluaciones
    """
    query = db.query(Evaluation)

    if website_id:
        query = query.filter(Evaluation.website_id == website_id)

    if status_filter:
        query = query.filter(Evaluation.status == status_filter)

    total = query.count()
    evaluations = query.order_by(Evaluation.started_at.desc()).offset(skip).limit(limit).all()

    return {
        "total": total,
        "items": evaluations
    }


@router.get(
    "/evaluations/{evaluation_id}",
    response_model=EvaluationDetailResponse,
    tags=["Evaluations"]
)
def get_evaluation(
    evaluation_id: int,
    db: Session = Depends(get_db)
) -> Evaluation:
    """
    Obtiene los resultados detallados de una evaluación.

    Args:
        evaluation_id: ID de la evaluación
        db: Sesión de base de datos

    Returns:
        Evaluation: Evaluación con todos sus resultados

    Raises:
        HTTPException: Si la evaluación no existe
    """
    evaluation = db.query(Evaluation).filter(Evaluation.id == evaluation_id).first()

    if not evaluation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Evaluación {evaluation_id} no encontrada"
        )

    return evaluation


@router.delete(
    "/evaluations/{evaluation_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["Evaluations"]
)
def delete_evaluation(
    evaluation_id: int,
    db: Session = Depends(get_db)
) -> None:
    """
    Elimina una evaluación y todos sus resultados.

    Args:
        evaluation_id: ID de la evaluación
        db: Sesión de base de datos

    Raises:
        HTTPException: Si la evaluación no existe
    """
    db_evaluation = db.query(Evaluation).filter(Evaluation.id == evaluation_id).first()

    if not db_evaluation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Evaluación {evaluation_id} no encontrada"
        )

    db.delete(db_evaluation)
    db.commit()

    logger.info(f"Evaluación eliminada: {evaluation_id}")
