"""
Rutas API para el crawler de sitios web .gob.bo.

Define endpoints para iniciar crawling y consultar contenido extraído.
"""

from typing import Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel, HttpUrl, Field
import logging
import tldextract

from app.database import get_db
from app.models.database_models import Website, ExtractedContent, CrawlStatus
from app.crawler.html_crawler import GobBoCrawler

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/crawler", tags=["Crawler"])


# ============================================================================
# Schemas Pydantic
# ============================================================================

class CrawlRequest(BaseModel):
    """Request para iniciar crawling de un sitio web."""
    url: HttpUrl = Field(..., description="URL del sitio web .gob.bo a crawlear")
    institution_name: str = Field(..., min_length=3, max_length=255, description="Nombre de la institución")

    class Config:
        json_schema_extra = {
            "example": {
                "url": "https://www.migracion.gob.bo",
                "institution_name": "Dirección General de Migración"
            }
        }


class CrawlResponse(BaseModel):
    """Response del endpoint de crawling."""
    website_id: int
    url: str
    institution_name: str
    status: str
    message: str
    crawled_at: Optional[datetime] = None
    summary: Optional[dict] = None

    class Config:
        from_attributes = True


class ExtractedContentResponse(BaseModel):
    """Response con contenido extraído."""
    website_id: int
    url: str
    institution_name: str
    crawled_at: datetime
    http_status_code: Optional[int]
    robots_txt: Optional[dict]
    structure: Optional[dict]
    metadata: Optional[dict]
    semantic_elements: Optional[dict]
    headings: Optional[dict]
    images: Optional[dict]
    links: Optional[dict]
    forms: Optional[dict]
    media: Optional[dict]
    external_resources: Optional[dict]
    stylesheets: Optional[dict]
    scripts: Optional[dict]
    text_corpus: Optional[dict]

    class Config:
        from_attributes = True


class WebsiteListItem(BaseModel):
    """Item de lista de sitios web."""
    id: int
    url: str
    domain: str
    institution_name: str
    crawl_status: str
    last_crawled_at: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True


class WebsiteListResponse(BaseModel):
    """Response de lista de sitios web."""
    total: int
    items: list[WebsiteListItem]


# ============================================================================
# Endpoints
# ============================================================================

@router.post(
    "/crawl",
    response_model=CrawlResponse,
    status_code=status.HTTP_200_OK,
    summary="Crawlear sitio web .gob.bo",
    description="Realiza crawling de un sitio web gubernamental boliviano y almacena el contenido extraído"
)
def crawl_website(
    request: CrawlRequest,
    db: Session = Depends(get_db)
) -> CrawlResponse:
    """
    Crawlea un sitio web .gob.bo y almacena el contenido extraído.

    Proceso:
    1. Valida que sea dominio .gob.bo
    2. Crea/actualiza registro de Website
    3. Ejecuta crawler para extraer contenido
    4. Guarda ExtractedContent en base de datos
    5. Retorna resumen del crawling

    Args:
        request: Datos del sitio a crawlear (url, institution_name)
        db: Sesión de base de datos

    Returns:
        CrawlResponse: Resultado del crawling con resumen

    Raises:
        HTTPException 400: Si la URL no es .gob.bo válido
        HTTPException 500: Si ocurre un error durante el crawling
    """
    url = str(request.url)
    logger.info(f"Iniciando crawling de {url}")

    # Validar dominio .gob.bo
    extracted = tldextract.extract(url)
    domain = f"{extracted.domain}.{extracted.suffix}"

    if not domain.endswith('.gob.bo'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"La URL debe ser un dominio .gob.bo válido. Dominio recibido: {domain}"
        )

    try:
        # Buscar o crear Website
        website = db.query(Website).filter(Website.url == url).first()

        if website:
            logger.info(f"Website existente encontrado (ID: {website.id}), actualizando...")
            website.institution_name = request.institution_name
            website.crawl_status = CrawlStatus.IN_PROGRESS
        else:
            logger.info(f"Creando nuevo Website para {url}")
            website = Website(
                url=url,
                domain=domain,
                institution_name=request.institution_name,
                crawl_status=CrawlStatus.IN_PROGRESS
            )
            db.add(website)
            db.flush()  # Para obtener el ID

        # Ejecutar crawler
        crawler = GobBoCrawler(timeout=30)
        extracted_data = crawler.crawl(url)

        logger.info(f"Crawling completado para {url}, guardando contenido...")

        # Buscar o crear ExtractedContent
        content = db.query(ExtractedContent).filter(
            ExtractedContent.website_id == website.id
        ).first()

        if content:
            # Actualizar contenido existente
            content.crawled_at = datetime.utcnow()
            content.http_status_code = extracted_data.get('http_status_code')
            content.robots_txt = extracted_data.get('robots_txt')
            content.html_structure = extracted_data.get('structure')
            content.page_metadata = extracted_data.get('metadata')
            content.semantic_elements = extracted_data.get('semantic_elements')
            content.headings = extracted_data.get('headings')
            content.images = extracted_data.get('images')
            content.links = extracted_data.get('links')
            content.forms = extracted_data.get('forms')
            content.media = extracted_data.get('media')
            content.external_resources = extracted_data.get('external_resources')
            content.stylesheets = extracted_data.get('stylesheets')
            content.scripts = extracted_data.get('scripts')
            content.text_corpus = extracted_data.get('text_corpus')
        else:
            # Crear nuevo registro
            content = ExtractedContent(
                website_id=website.id,
                crawled_at=datetime.utcnow(),
                http_status_code=extracted_data.get('http_status_code'),
                robots_txt=extracted_data.get('robots_txt'),
                html_structure=extracted_data.get('structure'),
                page_metadata=extracted_data.get('metadata'),
                semantic_elements=extracted_data.get('semantic_elements'),
                headings=extracted_data.get('headings'),
                images=extracted_data.get('images'),
                links=extracted_data.get('links'),
                forms=extracted_data.get('forms'),
                media=extracted_data.get('media'),
                external_resources=extracted_data.get('external_resources'),
                stylesheets=extracted_data.get('stylesheets'),
                scripts=extracted_data.get('scripts'),
                text_corpus=extracted_data.get('text_corpus')
            )
            db.add(content)

        # Actualizar estado del website
        website.crawl_status = CrawlStatus.COMPLETED
        website.last_crawled_at = datetime.utcnow()

        db.commit()
        db.refresh(website)

        logger.info(f"Contenido guardado exitosamente para Website ID: {website.id}")

        # Generar resumen
        summary = _generate_summary(extracted_data)

        return CrawlResponse(
            website_id=website.id,
            url=website.url,
            institution_name=website.institution_name,
            status="completed",
            message="Crawling completado exitosamente",
            crawled_at=website.last_crawled_at,
            summary=summary
        )

    except ValueError as e:
        # Error de validación del crawler
        logger.error(f"Error de validación: {e}")
        if website:
            website.crawl_status = CrawlStatus.FAILED
            db.commit()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

    except Exception as e:
        # Error general
        logger.error(f"Error durante crawling de {url}: {e}", exc_info=True)
        if website:
            website.crawl_status = CrawlStatus.FAILED
            db.commit()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error durante el crawling: {str(e)}"
        )


@router.get(
    "/websites/{website_id}",
    response_model=ExtractedContentResponse,
    summary="Obtener contenido extraído",
    description="Retorna el contenido extraído de un sitio web específico"
)
def get_extracted_content(
    website_id: int,
    db: Session = Depends(get_db)
) -> ExtractedContentResponse:
    """
    Obtiene el contenido extraído de un sitio web.

    Args:
        website_id: ID del sitio web
        db: Sesión de base de datos

    Returns:
        ExtractedContentResponse: Contenido extraído completo

    Raises:
        HTTPException 404: Si el sitio web o contenido no existe
    """
    website = db.query(Website).filter(Website.id == website_id).first()

    if not website:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Sitio web {website_id} no encontrado"
        )

    content = db.query(ExtractedContent).filter(
        ExtractedContent.website_id == website_id
    ).first()

    if not content:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No se encontró contenido extraído para el sitio web {website_id}. Ejecute crawling primero."
        )

    return ExtractedContentResponse(
        website_id=website.id,
        url=website.url,
        institution_name=website.institution_name,
        crawled_at=content.crawled_at,
        http_status_code=content.http_status_code,
        robots_txt=content.robots_txt,
        structure=content.html_structure,
        metadata=content.page_metadata,
        semantic_elements=content.semantic_elements,
        headings=content.headings,
        images=content.images,
        links=content.links,
        forms=content.forms,
        media=content.media,
        external_resources=content.external_resources,
        stylesheets=content.stylesheets,
        scripts=content.scripts,
        text_corpus=content.text_corpus
    )


@router.get(
    "/websites",
    response_model=WebsiteListResponse,
    summary="Listar sitios web crawleados",
    description="Retorna lista paginada de todos los sitios web registrados"
)
def list_crawled_websites(
    skip: int = Query(0, ge=0, description="Número de registros a saltar"),
    limit: int = Query(100, ge=1, le=500, description="Número máximo de registros"),
    status_filter: Optional[str] = Query(None, description="Filtrar por estado de crawling"),
    db: Session = Depends(get_db)
) -> WebsiteListResponse:
    """
    Lista todos los sitios web crawleados.

    Args:
        skip: Offset para paginación
        limit: Límite de resultados
        status_filter: Filtro opcional por estado (pending, in_progress, completed, failed)
        db: Sesión de base de datos

    Returns:
        WebsiteListResponse: Lista paginada de sitios web
    """
    query = db.query(Website)

    if status_filter:
        try:
            crawl_status = CrawlStatus(status_filter)
            query = query.filter(Website.crawl_status == crawl_status)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Estado inválido: {status_filter}. Valores válidos: pending, in_progress, completed, failed"
            )

    total = query.count()
    websites = query.order_by(Website.last_crawled_at.desc().nullslast()).offset(skip).limit(limit).all()

    return WebsiteListResponse(
        total=total,
        items=[WebsiteListItem.model_validate(w) for w in websites]
    )


# ============================================================================
# Funciones auxiliares
# ============================================================================

def _generate_summary(extracted_data: dict) -> dict:
    """
    Genera un resumen del contenido extraído.

    Args:
        extracted_data: Datos extraídos por el crawler

    Returns:
        dict: Resumen con estadísticas principales
    """
    robots_txt = extracted_data.get('robots_txt', {})
    structure = extracted_data.get('structure', {})
    metadata = extracted_data.get('metadata', {})
    semantic = extracted_data.get('semantic_elements', {})
    headings = extracted_data.get('headings', {})
    images = extracted_data.get('images', {})
    links = extracted_data.get('links', {})
    forms = extracted_data.get('forms', {})
    media = extracted_data.get('media', {})
    external = extracted_data.get('external_resources', {})
    text_corpus = extracted_data.get('text_corpus', {})

    summary = {
        'robots_txt': {
            'exists': robots_txt.get('exists', False),
            'accessible': robots_txt.get('accessible', False),
            'allows_crawling': robots_txt.get('allows_crawling'),
            'has_sitemap': robots_txt.get('has_sitemap', False),
            'sitemap_count': len(robots_txt.get('sitemap_urls', [])),
            'error': robots_txt.get('error')
        },
        'structure': {
            'has_html5_doctype': structure.get('has_html5_doctype', False),
            'has_utf8_charset': structure.get('has_utf8_charset', False),
            'has_obsolete_code': structure.get('has_obsolete_code', False)
        },
        'metadata': {
            'has_title': metadata.get('has_title', False),
            'has_lang': metadata.get('has_lang', False),
            'has_description': metadata.get('has_description', False),
            'has_viewport': metadata.get('has_viewport', False)
        },
        'semantic_elements': {
            'types_used': semantic.get('summary', {}).get('types_used', 0),
            'has_basic_structure': semantic.get('summary', {}).get('has_basic_structure', False)
        },
        'headings': {
            'total': headings.get('total_count', 0),
            'h1_count': headings.get('h1_count', 0),
            'hierarchy_valid': headings.get('hierarchy_valid', True)
        },
        'images': {
            'total': images.get('total_count', 0),
            'alt_compliance_percentage': round(images.get('alt_compliance_percentage', 0), 2)
        },
        'links': {
            'total': links.get('total_count', 0),
            'empty_links': links.get('empty_links', {}).get('count', 0),
            'generic_text': links.get('generic_text', {}).get('count', 0),
            'social': links.get('social', {}).get('count', 0),
            'email': links.get('email', {}).get('count', 0),
            'phone': links.get('phone', {}).get('count', 0),
            'messaging': links.get('messaging', {}).get('count', 0)
        },
        'forms': {
            'total': forms.get('total_forms', 0),
            'label_compliance_percentage': round(forms.get('label_compliance_percentage', 0), 2)
        },
        'media': {
            'has_autoplay': media.get('has_autoplay_media', False)
        },
        'external_resources': {
            'iframes': external.get('iframes', {}).get('count', 0),
            'cdn': external.get('cdn', {}).get('count', 0),
            'fonts': external.get('fonts', {}).get('count', 0),
            'trackers': external.get('trackers', {}).get('count', 0)
        },
        'text_corpus': {
            'total_sections': text_corpus.get('total_sections', 0),
            'sections_with_content': text_corpus.get('sections_with_content', 0),
            'has_bolivia_service': text_corpus.get('has_bolivia_service_text', False),
            'total_words': text_corpus.get('total_words', 0),
            'total_characters': text_corpus.get('total_characters', 0),
            'generic_links_found': text_corpus.get('generic_links', 0),
            'generic_link_examples': text_corpus.get('generic_link_examples', [])
        }
    }

    return summary
