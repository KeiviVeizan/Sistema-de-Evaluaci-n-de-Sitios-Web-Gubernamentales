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

    def __repr__(self) -> str:
        return f"<CriteriaResult(id={self.id}, criteria_id={self.criteria_id}, status={self.status})>"


class NLPAnalysis(Base):
    """
    Modelo para análisis de lenguaje natural (NLP).

    Almacena resultados del análisis NLP usando BETO para evaluar
    la calidad del contenido textual del sitio web gubernamental.

    Evalúa 3 dimensiones principales:
    - Coherencia semántica: Similitud entre headings y contenido (BETO embeddings)
    - Ambigüedades: Detección de textos genéricos/vagos (enlaces, labels, headings)
    - Claridad: Legibilidad del texto (Índice Fernández Huerta)

    Relación: 1:1 con Evaluation (una evaluación tiene un análisis NLP)

    Estructura JSONB esperada:

    coherence_details = {
        "sections_analyzed": int,
        "coherent_sections": int,
        "incoherent_sections": int,
        "average_similarity": float,
        "threshold_used": float,
        "section_scores": [
            {
                "heading": str,
                "heading_level": int,
                "word_count": int,
                "similarity_score": float,
                "is_coherent": bool,
                "recommendation": str | None
            }
        ]
    }

    ambiguity_details = {
        "total_analyzed": int,
        "problematic_count": int,
        "clear_count": int,
        "by_category": {"genérico": int, "ambiguo": int, ...},
        "by_element_type": {"link": int, "label": int, "heading": int},
        "problematic_items": [
            {
                "text": str,
                "element_type": str,
                "category": str,
                "recommendation": str,
                "wcag_criterion": str
            }
        ]
    }

    clarity_details = {
        "total_analyzed": int,
        "clear_count": int,
        "unclear_count": int,
        "avg_fernandez_huerta": float,
        "reading_difficulty": str,
        "avg_sentence_length": float,
        "avg_syllables_per_word": float,
        "complex_words_percentage": float
    }

    wcag_compliance = {
        "ACC-07": bool,  # Labels or Instructions (WCAG 3.3.2)
        "ACC-08": bool,  # Link Purpose (WCAG 2.4.4)
        "ACC-09": bool,  # Headings and Labels (WCAG 2.4.6)
        "total_criteria": int,
        "passed_criteria": int,
        "compliance_percentage": float
    }
    """

    __tablename__ = "nlp_analysis"

    # =========================================================================
    # Identificadores
    # =========================================================================
    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    # Relación 1:1 con evaluación (UNIQUE garantiza unicidad)
    evaluation_id: Mapped[int] = mapped_column(
        ForeignKey("evaluations.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True
    )

    # =========================================================================
    # Scores principales (0-100)
    # =========================================================================
    # Score global: 40% coherencia + 40% ambigüedad + 20% claridad
    nlp_global_score: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        index=True
    )

    # Coherencia semántica (embeddings BETO + similitud coseno)
    coherence_score: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        index=True
    )

    # Claridad de textos (% de textos sin ambigüedades)
    ambiguity_score: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        index=True
    )

    # Legibilidad (Índice Fernández Huerta)
    clarity_score: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        index=True
    )

    # =========================================================================
    # Detalles de análisis (JSONB)
    # =========================================================================
    coherence_details: Mapped[dict] = mapped_column(
        JSON,
        nullable=False,
        default=dict
    )

    ambiguity_details: Mapped[dict] = mapped_column(
        JSON,
        nullable=False,
        default=dict
    )

    clarity_details: Mapped[dict] = mapped_column(
        JSON,
        nullable=False,
        default=dict
    )

    # =========================================================================
    # Recomendaciones priorizadas
    # =========================================================================
    # Lista de strings ordenadas por prioridad
    recommendations: Mapped[list] = mapped_column(
        JSON,
        nullable=False,
        default=list
    )

    # =========================================================================
    # Cumplimiento WCAG
    # =========================================================================
    wcag_compliance: Mapped[dict] = mapped_column(
        JSON,
        nullable=False,
        default=dict
    )

    # =========================================================================
    # Timestamps
    # =========================================================================
    analyzed_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
        index=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )

    # =========================================================================
    # Relaciones
    # =========================================================================
    evaluation: Mapped["Evaluation"] = relationship(back_populates="nlp_analysis")

    def __repr__(self) -> str:
        """Representación string para debugging."""
        return (
            f"<NLPAnalysis(id={self.id}, "
            f"evaluation_id={self.evaluation_id}, "
            f"global_score={self.nlp_global_score:.1f})>"
        )

    def to_dict(self) -> dict:
        """
        Serializa el modelo a diccionario.

        Returns:
            Dict con todos los campos serializados correctamente,
            incluyendo JSONB y arrays.
        """
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

    Almacena todo el contenido HTML extraído por el crawler, incluyendo
    estructura del documento, metadatos, elementos semánticos, imágenes,
    enlaces, formularios, multimedia y recursos externos.
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

    # Robots.txt (Buena práctica SEO)
    robots_txt: Mapped[Optional[dict]] = mapped_column(
        JSON,
        nullable=True,
        comment="exists, accessible, allows_crawling, has_sitemap"
    )

    # Estructura del documento (SEM-01, SEM-02, SEM-04)
    html_structure: Mapped[Optional[dict]] = mapped_column(
        JSON,
        nullable=True,
        comment="DOCTYPE, charset, elementos obsoletos"
    )

    # Metadatos (ACC-02, ACC-03, SEO-01, SEO-02, SEO-03)
    page_metadata: Mapped[Optional[dict]] = mapped_column(
        JSON,
        nullable=True,
        comment="title, lang, description, keywords, viewport"
    )

    # Elementos semánticos HTML5 (SEM-03, NAV-01)
    semantic_elements: Mapped[Optional[dict]] = mapped_column(
        JSON,
        nullable=True,
        comment="header, nav, main, footer, article, section"
    )

    # Headings (ACC-04, ACC-09)
    headings: Mapped[Optional[dict]] = mapped_column(
        JSON,
        nullable=True,
        comment="h1-h6 con texto y jerarquía"
    )

    # Imágenes (ACC-01, FMT-02)
    images: Mapped[Optional[dict]] = mapped_column(
        JSON,
        nullable=True,
        comment="src, alt, dimensiones"
    )

    # Enlaces (ACC-08, PART-01 a PART-05)
    links: Mapped[Optional[dict]] = mapped_column(
        JSON,
        nullable=True,
        comment="clasificados por tipo: social, messaging, email, phone"
    )

    # Formularios (ACC-07)
    forms: Mapped[Optional[dict]] = mapped_column(
        JSON,
        nullable=True,
        comment="inputs con/sin label"
    )

    # Multimedia (ACC-05)
    media: Mapped[Optional[dict]] = mapped_column(
        JSON,
        nullable=True,
        comment="audio, video con/sin autoplay"
    )

    # Recursos externos (PROH-01 a PROH-04)
    external_resources: Mapped[Optional[dict]] = mapped_column(
        JSON,
        nullable=True,
        comment="iframes, CDN, fuentes, trackers"
    )

    # Estilos y scripts
    stylesheets: Mapped[Optional[list]] = mapped_column(
        JSON,
        nullable=True,
        comment="lista de CSS con clasificación"
    )

    scripts: Mapped[Optional[list]] = mapped_column(
        JSON,
        nullable=True,
        comment="lista de JS con clasificación"
    )

    # Corpus textual para análisis NLP
    text_corpus: Mapped[Optional[dict]] = mapped_column(
        JSON,
        nullable=True,
        comment="texto estructurado para análisis de coherencia"
    )

    # Relaciones
    website: Mapped["Website"] = relationship(back_populates="extracted_content")

    def __repr__(self) -> str:
        return f"<ExtractedContent(id={self.id}, website_id={self.website_id})>"
