"""
Tipos definidos para estructuras de datos extraídas por el crawler.

Define TypedDict para todas las estructuras de datos que retorna el crawler,
mejorando la consistencia y facilitando el type checking.
"""

from typing import TypedDict, List, Optional, Any, Dict


# ============================================================================
# Tipos para Semantic Elements
# ============================================================================

class SemanticElementData(TypedDict):
    """Datos de un elemento semántico individual."""
    count: int
    present: bool


class SemanticElements(TypedDict):
    """Estructura de elementos semánticos HTML5."""
    header: SemanticElementData
    nav: SemanticElementData
    main: SemanticElementData
    footer: SemanticElementData
    article: SemanticElementData
    section: SemanticElementData
    aside: SemanticElementData
    summary: Dict[str, Any]


# ============================================================================
# Tipos para Document Hierarchy
# ============================================================================

class StructureAnalysis(TypedDict):
    """Análisis de la estructura del documento."""
    header_count: int
    main_count: int
    footer_count: int
    nav_count: int
    navs_in_header: int
    navs_in_footer: int
    navs_floating: int
    main_inside_section: bool
    total_divs: int
    total_semantic: int
    div_ratio: float
    has_divitis: bool


class HierarchyNode(TypedDict):
    """Nodo de jerarquía de elementos."""
    tag: str
    depth: int
    id: Optional[str]
    class_attr: Optional[List[str]]  # 'class' es palabra reservada
    parent: str
    children: List['HierarchyNode']


class DocumentHierarchy(TypedDict):
    """Jerarquía completa del documento."""
    hierarchy: List[HierarchyNode]
    structure_analysis: StructureAnalysis


# ============================================================================
# Tipos para HTML Structure
# ============================================================================

class HTMLStructure(TypedDict, total=False):
    """Estructura del documento HTML."""
    has_html5_doctype: bool
    has_utf8_charset: bool
    has_obsolete_code: bool
    has_html: bool
    has_head: bool
    has_body: bool
    charset: Optional[str]
    doctype: Optional[str]
    obsolete_elements: List[Dict[str, Any]]
    obsolete_attributes: List[Dict[str, Any]]
    table_count: int
    document_hierarchy: DocumentHierarchy


# ============================================================================
# Tipos para Metadata
# ============================================================================

class PageMetadata(TypedDict, total=False):
    """Metadatos de la página."""
    title: str
    title_length: int
    has_title: bool
    lang: Optional[str]
    has_lang: bool
    description: Optional[str]
    has_description: bool
    keywords: Optional[str]
    has_keywords: bool
    viewport: Optional[str]
    has_viewport: bool
    author: Optional[str]
    robots: Optional[str]


# ============================================================================
# Tipos para Images
# ============================================================================

class ImageData(TypedDict):
    """Datos de una imagen."""
    src: str
    alt: Optional[str]
    has_alt: bool
    width: Optional[str]
    height: Optional[str]
    is_external: bool


class ImagesInfo(TypedDict):
    """Información de imágenes."""
    images: List[ImageData]
    total_count: int
    with_alt: int
    without_alt: int
    alt_compliance_percentage: float


# ============================================================================
# Tipos para Links
# ============================================================================

class LinkData(TypedDict):
    """Datos de un enlace."""
    href: str
    text: str
    is_external: bool
    has_text: bool


class LinksCategory(TypedDict):
    """Categoría de enlaces."""
    count: int
    links: List[LinkData]


class LinksInfo(TypedDict):
    """Información de enlaces."""
    links: List[LinkData]
    total_count: int
    internal_count: int
    external_count: int
    social: LinksCategory
    messaging: LinksCategory
    email: LinksCategory
    phone: LinksCategory
    generic_text: LinksCategory
    empty_links: LinksCategory


# ============================================================================
# Tipos para Forms
# ============================================================================

class InputData(TypedDict):
    """Datos de un input de formulario."""
    type: str
    name: Optional[str]
    id: Optional[str]
    placeholder: Optional[str]
    required: bool
    has_label: bool
    label_text: Optional[str]


class FormData(TypedDict):
    """Datos de un formulario."""
    action: Optional[str]
    method: Optional[str]
    inputs: List[InputData]
    has_submit: bool


class FormsInfo(TypedDict):
    """Información de formularios."""
    forms: List[FormData]
    total_forms: int
    total_inputs: int
    inputs_with_label: int
    inputs_without_label: int
    label_compliance_percentage: float


# ============================================================================
# Tipos para Media
# ============================================================================

class MediaElement(TypedDict):
    """Elemento multimedia."""
    tag: str
    src: Optional[str]
    has_autoplay: bool
    has_controls: bool


class MediaInfo(TypedDict):
    """Información multimedia."""
    audio: List[MediaElement]
    video: List[MediaElement]
    audio_count: int
    video_count: int
    has_autoplay: bool
    has_autoplay_media: bool


# ============================================================================
# Tipos para External Resources
# ============================================================================

class ExternalResources(TypedDict):
    """Recursos externos."""
    iframes: Dict[str, Any]
    cdn: Dict[str, Any]
    fonts: Dict[str, Any]
    trackers: Dict[str, Any]
    scripts: List[str]
    stylesheets: List[str]


# ============================================================================
# Tipos para Headings
# ============================================================================

class HeadingData(TypedDict):
    """Datos de un heading."""
    level: int
    text: str
    tag: str


class HeadingsInfo(TypedDict):
    """Información de headings."""
    headings: List[HeadingData]
    total_count: int
    h1_count: int
    h2_count: int
    h3_count: int
    h4_count: int
    h5_count: int
    h6_count: int
    hierarchy_valid: bool
    has_single_h1: bool


# ============================================================================
# Tipos para Text Corpus
# ============================================================================

class TextSection(TypedDict):
    """Sección de texto."""
    heading: str
    paragraphs: List[str]
    content: str


class LinkTextData(TypedDict):
    """Datos de texto de enlace."""
    text: str
    href: str
    is_generic: bool


class TextCorpus(TypedDict):
    """Corpus textual para análisis NLP."""
    header_text: str
    footer_text: str
    main_text: str
    has_bolivia_service_text: bool
    sections: List[TextSection]
    total_sections: int
    sections_with_content: int
    link_texts: List[LinkTextData]
    button_texts: List[str]
    label_texts: List[str]
    full_text: str
    total_words: int
    total_characters: int
    generic_links: int
    generic_link_examples: List[str]


# ============================================================================
# Tipos para Robots.txt
# ============================================================================

class RobotsTxtInfo(TypedDict):
    """Información de robots.txt."""
    exists: bool
    url: str
    accessible: bool
    allows_crawling: Optional[bool]
    has_sitemap: bool
    sitemap_urls: List[str]
    content_preview: Optional[str]
    error: Optional[str]


# ============================================================================
# Tipo Principal: ExtractedContent
# ============================================================================

class ExtractedContent(TypedDict):
    """
    Estructura completa de datos extraídos por el crawler.

    Esta es la estructura principal que retorna el método crawl().
    """
    url: str
    final_url: str
    crawled_at: str
    http_status_code: int
    robots_txt: RobotsTxtInfo
    structure: HTMLStructure
    metadata: PageMetadata
    semantic_elements: SemanticElements
    headings: HeadingsInfo
    images: ImagesInfo
    links: LinksInfo
    forms: FormsInfo
    media: MediaInfo
    external_resources: ExternalResources
    stylesheets: Dict[str, Any]
    scripts: Dict[str, Any]
    text_corpus: TextCorpus
