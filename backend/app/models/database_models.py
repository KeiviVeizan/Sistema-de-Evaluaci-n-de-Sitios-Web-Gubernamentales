"""
Modelos de base de datos usando SQLAlchemy ORM.

Define las tablas para usuarios, instituciones, sitios web, evaluaciones,
resultados de criterios y análisis NLP.
"""

from datetime import datetime
from typing import List, Optional
from sqlalchemy import (
    String, Float, Boolean, DateTime,
    ForeignKey, Text, JSON, Enum as SQLEnum, ARRAY
)
from sqlalchemy.orm import relationship, Mapped, mapped_column
import enum

from app.database import Base


class UserRole(str, enum.Enum):
    """Roles de usuario en el sistema."""
    SUPERADMIN = "superadmin"
    SECRETARY = "secretary"
    EVALUATOR = "evaluator"
    ENTITY_USER = "entity_user"


class CrawlStatus(str, enum.Enum):
    """Estado del proceso de crawling."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class EvaluationStatus(str, enum.Enum):
    """Estado del proceso de evaluación."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class CriteriaStatus(str, enum.Enum):
    """Estado de cumplimiento de un criterio."""
    PASS = "pass"
    FAIL = "fail"
    NOT_APPLICABLE = "na"


class Institution(Base):
    """
    Modelo para instituciones gubernamentales.

    Cada institución tiene un dominio .gob.bo y puede tener
    múltiples usuarios asociados.
    """

    __tablename__ = "institutions"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    domain: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relaciones
    users: Mapped[List["User"]] = relationship(back_populates="institution", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Institution(id={self.id}, name={self.name}, domain={self.domain})>"


class User(Base):
    """
    Modelo para usuarios del sistema.

    Soporta roles: superadmin, secretary, evaluator.
    Los usuarios pueden estar asociados a una institución.
    """

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    position: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    role: Mapped[UserRole] = mapped_column(
        SQLEnum(UserRole),
        default=UserRole.EVALUATOR,
        nullable=False
    )
    institution_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("institutions.id", ondelete="SET NULL"),
        nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Campos 2FA
    two_factor_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, server_default="false")
    two_factor_secret: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    two_factor_backup_codes: Mapped[Optional[list]] = mapped_column(ARRAY(String), nullable=True)

    # Relaciones
    institution: Mapped[Optional["Institution"]] = relationship(back_populates="users")

    def __repr__(self) -> str:
        return f"<User(id={self.id}, username={self.username}, role={self.role})>"


class Website(Base):
    """
    Modelo para sitios web gubernamentales.

    Almacena información básica de cada sitio web a evaluar,
    incluyendo URL, dominio, institución y estado de crawling.
    """

    __tablename__ = "websites"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    url: Mapped[str] = mapped_column(String(500), unique=True, nullable=False, index=True)
    domain: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    institution_name: Mapped[str] = mapped_column(String(255), nullable=False)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    last_crawled_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Estado
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    crawl_status: Mapped[CrawlStatus] = mapped_column(
        SQLEnum(CrawlStatus),
        default=CrawlStatus.PENDING,
        nullable=False
    )

    # Relaciones
    evaluations: Mapped[List["Evaluation"]] = relationship(
        back_populates="website",
        cascade="all, delete-orphan"
    )
    extracted_content: Mapped[Optional["ExtractedContent"]] = relationship(
        back_populates="website",
        cascade="all, delete-orphan",
        uselist=False
    )

    def __repr__(self) -> str:
        return f"<Website(id={self.id}, domain={self.domain}, institution={self.institution_name})>"


class Evaluation(Base):
    """
    Modelo para evaluaciones de sitios web.

    Almacena los resultados de cada evaluación realizada a un sitio web,
    incluyendo puntajes por categoría y estado general.
    """

    __tablename__ = "evaluations"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    website_id: Mapped[int] = mapped_column(ForeignKey("websites.id", ondelete="CASCADE"), nullable=False)

    # Timestamps
    started_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Puntajes
    score_digital_sovereignty: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    score_accessibility: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    score_usability: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    score_semantic_web: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    score_total: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Estado
    status: Mapped[EvaluationStatus] = mapped_column(
        SQLEnum(EvaluationStatus),
        default=EvaluationStatus.PENDING,
        nullable=False
    )
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relaciones
    website: Mapped["Website"] = relationship(back_populates="evaluations")
    criteria_results: Mapped[List["CriteriaResult"]] = relationship(
        back_populates="evaluation",
        cascade="all, delete-orphan"
    )
    # Relación 1:1 con análisis NLP (uselist=False)
    nlp_analysis: Mapped[Optional["NLPAnalysis"]] = relationship(
        back_populates="evaluation",
        cascade="all, delete-orphan",
        uselist=False
    )
    followups: Mapped[List["Followup"]] = relationship(
        back_populates="evaluation",
        cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Evaluation(id={self.id}, website_id={self.website_id}, status={self.status})>"


class CriteriaResult(Base):
    """
    Modelo para resultados de criterios individuales.

    Almacena el resultado de cada criterio evaluado (D.S. 3925 o WCAG),
    incluyendo estado, puntaje y detalles específicos.
    """

    __tablename__ = "criteria_results"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    evaluation_id: Mapped[int] = mapped_column(
        ForeignKey("evaluations.id", ondelete="CASCADE"),
        nullable=False
    )

    # Identificación del criterio
    criteria_id: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    criteria_name: Mapped[str] = mapped_column(String(255), nullable=False)
    dimension: Mapped[str] = mapped_column(String(50), nullable=False)
    lineamiento: Mapped[str] = mapped_column(String(255), nullable=False)

    # Resultado
    status: Mapped[str] = mapped_column(String(20), nullable=False)  # pass, fail, partial, na
    score: Mapped[float] = mapped_column(Float, nullable=False)
    max_score: Mapped[float] = mapped_column(Float, nullable=False)
    details: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    evidence: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    # Timestamp
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    # Relaciones
    evaluation: Mapped["Evaluation"] = relationship(back_populates="criteria_results")
    followups: Mapped[List["Followup"]] = relationship(back_populates="criteria_result")

    def __repr__(self) -> str:
        return f"<CriteriaResult(id={self.id}, criteria_id={self.criteria_id}, status={self.status})>"


class Followup(Base):
    """
    Modelo para seguimientos de criterios no cumplidos.

    Permite agendar y gestionar el seguimiento de correcciones
    para criterios con estado fail o partial.

    Flujo de estados:
      pending   → La institución aún no ha reportado corrección
      corrected → La institución marcó como corregido (pendiente de validación)
      validated → El admin/secretaría validó la corrección
      rejected  → El admin/secretaría rechazó la corrección
      cancelled → Seguimiento cancelado
    """

    __tablename__ = "followups"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    evaluation_id: Mapped[int] = mapped_column(
        ForeignKey("evaluations.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    criteria_result_id: Mapped[int] = mapped_column(
        ForeignKey("criteria_results.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    due_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    # pending, corrected, validated, rejected, cancelled
    status: Mapped[str] = mapped_column(String(20), default="pending", nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    # Campos de corrección (institución)
    corrected_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    corrected_by_user_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id"),
        nullable=True
    )

    # Campos de validación (admin/secretaría)
    validated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    validated_by_user_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id"),
        nullable=True
    )
    validation_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relaciones
    evaluation: Mapped["Evaluation"] = relationship(back_populates="followups")
    criteria_result: Mapped["CriteriaResult"] = relationship(back_populates="followups")
    corrected_by: Mapped[Optional["User"]] = relationship(
        foreign_keys=[corrected_by_user_id]
    )
    validated_by: Mapped[Optional["User"]] = relationship(
        foreign_keys=[validated_by_user_id]
    )

    def __repr__(self) -> str:
        return f"<Followup(id={self.id}, evaluation_id={self.evaluation_id}, status={self.status})>"


class NLPAnalysis(Base):
    """
    Modelo para análisis de lenguaje natural (NLP).

    Almacena resultados del análisis NLP usando BETO para evaluar
    la calidad del contenido textual del sitio web gubernamental.
    """

    __tablename__ = "nlp_analysis"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    evaluation_id: Mapped[int] = mapped_column(
        ForeignKey("evaluations.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True
    )

    # Scores principales (0-100)
    nlp_global_score: Mapped[float] = mapped_column(Float, nullable=False, index=True)
    coherence_score: Mapped[float] = mapped_column(Float, nullable=False, index=True)
    ambiguity_score: Mapped[float] = mapped_column(Float, nullable=False, index=True)
    clarity_score: Mapped[float] = mapped_column(Float, nullable=False, index=True)

    # Detalles de análisis (JSON)
    coherence_details: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    ambiguity_details: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    clarity_details: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)

    # Recomendaciones priorizadas
    recommendations: Mapped[Optional[list]] = mapped_column(ARRAY(String), nullable=True, default=list)

    # Cumplimiento WCAG
    wcag_compliance: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)

    # Timestamps
    analyzed_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relaciones
    evaluation: Mapped["Evaluation"] = relationship(back_populates="nlp_analysis")

    def __repr__(self) -> str:
        return (
            f"<NLPAnalysis(id={self.id}, "
            f"evaluation_id={self.evaluation_id}, "
            f"global_score={self.nlp_global_score:.1f})>"
        )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "evaluation_id": self.evaluation_id,
            "scores": {
                "global": self.nlp_global_score,
                "coherence": self.coherence_score,
                "ambiguity": self.ambiguity_score,
                "clarity": self.clarity_score
            },
            "coherence_details": self.coherence_details or {},
            "ambiguity_details": self.ambiguity_details or {},
            "clarity_details": self.clarity_details or {},
            "recommendations": self.recommendations or [],
            "wcag_compliance": self.wcag_compliance or {},
            "analyzed_at": self.analyzed_at.isoformat() if self.analyzed_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }


class ExtractedContent(Base):
    """
    Modelo para contenido extraído del sitio web.

    Almacena todo el contenido HTML extraído por el crawler.
    """

    __tablename__ = "extracted_content"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    website_id: Mapped[int] = mapped_column(
        ForeignKey("websites.id", ondelete="CASCADE"),
        unique=True,
        nullable=False
    )

    # Información básica
    crawled_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    http_status_code: Mapped[Optional[int]] = mapped_column(nullable=True)

    # Robots.txt
    robots_txt: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    # Estructura del documento
    html_structure: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    # Metadatos
    page_metadata: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    # Elementos semánticos HTML5
    semantic_elements: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    # Headings
    headings: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    # Imágenes
    images: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    # Enlaces
    links: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    # Formularios
    forms: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    # Multimedia
    media: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    # Recursos externos
    external_resources: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    # Estilos y scripts
    stylesheets: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    scripts: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)

    # Corpus textual para análisis NLP
    text_corpus: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    # Relaciones
    website: Mapped["Website"] = relationship(back_populates="extracted_content")

    def __repr__(self) -> str:
        return f"<ExtractedContent(id={self.id}, website_id={self.website_id})>"
