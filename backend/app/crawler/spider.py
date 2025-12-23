"""
Spider de Scrapy para crawlear sitios web gubernamentales bolivianos.

Este módulo implementa el crawler usando Scrapy para extraer contenido
de sitios .gob.bo respetando políticas de crawling responsable.
"""

import scrapy
from scrapy.http import Response
from typing import Generator, Optional
from urllib.parse import urljoin, urlparse
import logging

from app.config import settings

logger = logging.getLogger(__name__)


class GobBoSpider(scrapy.Spider):
    """
    Spider para crawlear sitios web gubernamentales bolivianos.

    Atributos:
        name: Nombre del spider
        allowed_domains: Dominios permitidos para crawling
        start_urls: URLs iniciales
        custom_settings: Configuraciones personalizadas del spider
    """

    name = "gob_bo_spider"
    allowed_domains = ["gob.bo"]

    custom_settings = {
        'USER_AGENT': settings.crawler_user_agent,
        'DOWNLOAD_DELAY': settings.crawler_delay,
        'CONCURRENT_REQUESTS': 1,
        'DEPTH_LIMIT': settings.crawler_max_depth,
        'CLOSESPIDER_PAGECOUNT': settings.crawler_max_pages,
        'ROBOTSTXT_OBEY': True,
        'COOKIES_ENABLED': False,
        'DOWNLOAD_TIMEOUT': settings.crawler_timeout,
        'RETRY_TIMES': 2,
        'REDIRECT_MAX_TIMES': 3,

        # Evitar crawlear recursos innecesarios
        'IGNORED_EXTENSIONS': [
            'pdf', 'zip', 'rar', 'tar', 'gz', '7z',
            'exe', 'dmg', 'pkg', 'deb', 'rpm',
            'mp4', 'avi', 'mov', 'wmv', 'flv',
            'mp3', 'wav', 'ogg', 'flac',
            'jpg', 'jpeg', 'png', 'gif', 'bmp', 'svg', 'ico',
            'doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx'
        ]
    }

    def __init__(
        self,
        start_url: str,
        max_pages: Optional[int] = None,
        max_depth: Optional[int] = None,
        *args,
        **kwargs
    ):
        """
        Inicializa el spider.

        Args:
            start_url: URL inicial para comenzar el crawling
            max_pages: Máximo número de páginas a crawlear (opcional)
            max_depth: Profundidad máxima de crawling (opcional)
            *args: Argumentos adicionales
            **kwargs: Argumentos de palabra clave adicionales
        """
        super(GobBoSpider, self).__init__(*args, **kwargs)
        self.start_urls = [start_url]

        # Extraer dominio de la URL inicial
        parsed = urlparse(start_url)
        self.allowed_domains = [parsed.netloc]

        # Personalizar límites si se proporcionan
        if max_pages:
            self.custom_settings['CLOSESPIDER_PAGECOUNT'] = max_pages
        if max_depth:
            self.custom_settings['DEPTH_LIMIT'] = max_depth

        # Estadísticas de crawling
        self.pages_crawled = 0
        self.errors_count = 0

        logger.info(f"Spider inicializado para {start_url}")

    def parse(self, response: Response) -> Generator:
        """
        Parsea la respuesta de una página web.

        Extrae contenido relevante y sigue enlaces internos.

        Args:
            response: Respuesta HTTP de Scrapy

        Yields:
            dict: Datos extraídos de la página
        """
        self.pages_crawled += 1
        logger.info(f"Crawleando ({self.pages_crawled}): {response.url}")

        try:
            # Extraer información de la página
            page_data = {
                'url': response.url,
                'status_code': response.status,
                'title': self._extract_title(response),
                'meta_description': self._extract_meta_description(response),
                'headings': self._extract_headings(response),
                'links': self._extract_links(response),
                'images': self._extract_images(response),
                'text_content': self._extract_text_content(response),
                'has_forms': self._has_forms(response),
                'language': self._extract_language(response),
            }

            yield page_data

            # Seguir enlaces internos
            for link in self._get_internal_links(response):
                yield response.follow(link, callback=self.parse)

        except Exception as e:
            self.errors_count += 1
            logger.error(f"Error parseando {response.url}: {e}")

    def _extract_title(self, response: Response) -> str:
        """Extrae el título de la página."""
        title = response.css('title::text').get()
        return title.strip() if title else ""

    def _extract_meta_description(self, response: Response) -> str:
        """Extrae la meta descripción."""
        desc = response.css('meta[name="description"]::attr(content)').get()
        return desc.strip() if desc else ""

    def _extract_headings(self, response: Response) -> dict:
        """Extrae todos los encabezados (h1-h6)."""
        return {
            'h1': response.css('h1::text').getall(),
            'h2': response.css('h2::text').getall(),
            'h3': response.css('h3::text').getall(),
        }

    def _extract_links(self, response: Response) -> list:
        """Extrae todos los enlaces de la página."""
        links = response.css('a::attr(href)').getall()
        return [urljoin(response.url, link) for link in links]

    def _extract_images(self, response: Response) -> list:
        """Extrae información de imágenes."""
        images = []
        for img in response.css('img'):
            images.append({
                'src': img.css('::attr(src)').get(),
                'alt': img.css('::attr(alt)').get() or "",
            })
        return images

    def _extract_text_content(self, response: Response) -> str:
        """Extrae el texto principal de la página."""
        # Extraer texto del body, excluyendo scripts y estilos
        text = response.css('body *::text').getall()
        return ' '.join([t.strip() for t in text if t.strip()])[:5000]  # Limitar a 5000 caracteres

    def _has_forms(self, response: Response) -> bool:
        """Verifica si la página tiene formularios."""
        return len(response.css('form')) > 0

    def _extract_language(self, response: Response) -> str:
        """Extrae el idioma de la página."""
        lang = response.css('html::attr(lang)').get()
        return lang if lang else "unknown"

    def _get_internal_links(self, response: Response) -> list:
        """Obtiene enlaces internos válidos para seguir crawleando."""
        links = []
        for link in response.css('a::attr(href)').getall():
            absolute_url = urljoin(response.url, link)
            parsed = urlparse(absolute_url)

            # Verificar que sea un enlace interno válido
            if (parsed.netloc in self.allowed_domains and
                not self._should_ignore_url(absolute_url)):
                links.append(link)

        return links

    def _should_ignore_url(self, url: str) -> bool:
        """
        Determina si una URL debe ser ignorada.

        Args:
            url: URL a verificar

        Returns:
            bool: True si debe ignorarse
        """
        ignore_patterns = [
            'javascript:', 'mailto:', 'tel:', '#',
            'login', 'logout', 'admin', 'wp-admin',
            'download', 'file', 'attachment'
        ]

        url_lower = url.lower()
        return any(pattern in url_lower for pattern in ignore_patterns)

    def closed(self, reason):
        """
        Callback ejecutado cuando el spider termina.

        Args:
            reason: Razón por la que se cerró el spider
        """
        logger.info(
            f"Spider cerrado. Páginas crawleadas: {self.pages_crawled}, "
            f"Errores: {self.errors_count}, Razón: {reason}"
        )
