"""
Modelos de base de datos usando SQLAlchemy ORM.

Define las tablas para sitios web, evaluaciones, resultados de criterios
y análisis NLP.
"""

from datetime import datetime
from typing import List, Optional
from sqlalchemy import (
    String, Float, Boolean, DateTime,
    ForeignKey, Text, JSON, Enum as SQLEnum
)
from sqlalchemy.orm import relationship, Mapped, mapped_column
import enum

from app.database import Base


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
    nlp_analyses: Mapped[List["NLPAnalysis"]] = relationship(
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

    # Tipo de criterio
    criteria_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    criteria_code: Mapped[str] = mapped_column(String(50), nullable=False)
    criteria_name: Mapped[str] = mapped_column(String(255), nullable=False)

    # Resultado
    status: Mapped[CriteriaStatus] = mapped_column(SQLEnum(CriteriaStatus), nullable=False)
    score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    details: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    # Relaciones
    evaluation: Mapped["Evaluation"] = relationship(back_populates="criteria_results")

    def __repr__(self) -> str:
        return f"<CriteriaResult(id={self.id}, code={self.criteria_code}, status={self.status})>"


class NLPAnalysis(Base):
    """
    Modelo para análisis de lenguaje natural.

    Almacena resultados del análisis NLP usando BETO para evaluar
    la calidad del contenido textual del sitio web.
    """

    __tablename__ = "nlp_analyses"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    evaluation_id: Mapped[int] = mapped_column(
        ForeignKey("evaluations.id", ondelete="CASCADE"),
        nullable=False
    )

    # Muestra de texto analizada
    text_sample: Mapped[str] = mapped_column(Text, nullable=False)

    # Puntajes
    ambiguity_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    clarity_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Problemas detectados
    issues_detected: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    # Timestamp
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    # Relaciones
    evaluation: Mapped["Evaluation"] = relationship(back_populates="nlp_analyses")

    def __repr__(self) -> str:
        return f"<NLPAnalysis(id={self.id}, evaluation_id={self.evaluation_id})>"
