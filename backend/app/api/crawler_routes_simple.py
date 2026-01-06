"""
Rutas API simplificadas para el crawler (sin base de datos).
Versión para pruebas sin PostgreSQL.
"""

from typing import Optional
from datetime import datetime
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, HttpUrl, Field
import logging

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
                "url": "https://www.minedu.gob.bo",
                "institution_name": "Ministerio de Educación"
            }
        }


class CrawlResponse(BaseModel):
    """Response del endpoint de crawling."""
    url: str
    institution_name: str
    status: str
    message: str
    crawled_at: datetime
    data: dict  # Todo el contenido extraído

    class Config:
        from_attributes = True


# ============================================================================
# Endpoints
# ============================================================================

@router.post(
    "/crawl",
    response_model=CrawlResponse,
    status_code=status.HTTP_200_OK,
    summary="Crawlear sitio web .gob.bo",
    description="Realiza crawling de un sitio web gubernamental boliviano (versión sin base de datos)"
)
def crawl_website(request: CrawlRequest) -> CrawlResponse:
    """
    Crawlea un sitio web .gob.bo y retorna el contenido extraído.

    Args:
        request: Datos del sitio a crawlear (url, institution_name)

    Returns:
        CrawlResponse: Resultado del crawling completo

    Raises:
        HTTPException 400: Si la URL no es .gob.bo válido
        HTTPException 500: Si ocurre un error durante el crawling
    """
    url = str(request.url)
    logger.info(f"Iniciando crawling de {url}")

    # Validar dominio .gob.bo
    if not url.endswith('.gob.bo') and '.gob.bo/' not in url:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"La URL debe ser un dominio .gob.bo válido"
        )

    try:
        # Ejecutar crawler
        crawler = GobBoCrawler(timeout=30)
        extracted_data = crawler.crawl(url)

        logger.info(f"Crawling completado para {url}")

        return CrawlResponse(
            url=url,
            institution_name=request.institution_name,
            status="completed",
            message="Crawling completado exitosamente",
            crawled_at=datetime.utcnow(),
            data=extracted_data
        )

    except ValueError as e:
        logger.error(f"Error de validación: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error durante crawling de {url}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error durante el crawling: {str(e)}"
        )


@router.get(
    "/health",
    summary="Health check del crawler",
    description="Verifica que el crawler esté funcionando"
)
def crawler_health():
    """Verifica el estado del crawler."""
    return {
        "status": "healthy",
        "crawler": "GobBoCrawler",
        "version": "1.0.0",
        "timestamp": datetime.utcnow()
    }
