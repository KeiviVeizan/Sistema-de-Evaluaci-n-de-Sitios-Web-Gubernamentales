"""
Parser HTML para análisis estructural de páginas web.

Proporciona utilidades para parsear y extraer información
de documentos HTML usando BeautifulSoup.
"""

from typing import List, Dict, Optional
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import re
import logging

logger = logging.getLogger(__name__)


class HTMLParser:
    """
    Parser para analizar estructura HTML de páginas web.

    Proporciona métodos para extraer y analizar elementos HTML
    relevantes para la evaluación de sitios web.
    """

    def __init__(self, html_content: str, base_url: str = ""):
        """
        Inicializa el parser HTML.

        Args:
            html_content: Contenido HTML a parsear
            base_url: URL base para resolver enlaces relativos
        """
        self.html = html_content
        self.base_url = base_url
        self.soup = BeautifulSoup(html_content, 'lxml')

    def get_title(self) -> str:
        """Obtiene el título de la página."""
        title_tag = self.soup.find('title')
        return title_tag.get_text().strip() if title_tag else ""

    def get_meta_description(self) -> str:
        """Obtiene la meta descripción."""
        meta = self.soup.find('meta', attrs={'name': 'description'})
        return meta.get('content', '').strip() if meta else ""

    def get_headings(self) -> Dict[str, List[str]]:
        """
        Obtiene todos los encabezados organizados por nivel.

        Returns:
            dict: Diccionario con listas de encabezados por nivel (h1-h6)
        """
        headings = {}
        for level in range(1, 7):
            tag = f'h{level}'
            headings[tag] = [h.get_text().strip() for h in self.soup.find_all(tag)]
        return headings

    def get_links(self) -> List[Dict[str, str]]:
        """
        Obtiene todos los enlaces de la página.

        Returns:
            list: Lista de diccionarios con información de enlaces
        """
        links = []
        for a_tag in self.soup.find_all('a', href=True):
            href = a_tag.get('href', '')
            absolute_url = urljoin(self.base_url, href) if self.base_url else href

            links.append({
                'text': a_tag.get_text().strip(),
                'href': href,
                'absolute_url': absolute_url,
                'title': a_tag.get('title', ''),
                'is_external': self._is_external_link(absolute_url)
            })
        return links

    def get_images(self) -> List[Dict[str, str]]:
        """
        Obtiene información de todas las imágenes.

        Returns:
            list: Lista de diccionarios con información de imágenes
        """
        images = []
        for img in self.soup.find_all('img'):
            src = img.get('src', '')
            absolute_src = urljoin(self.base_url, src) if self.base_url else src

            images.append({
                'src': src,
                'absolute_src': absolute_src,
                'alt': img.get('alt', ''),
                'title': img.get('title', ''),
                'has_alt': bool(img.get('alt'))
            })
        return images

    def get_forms(self) -> List[Dict]:
        """
        Obtiene información de formularios.

        Returns:
            list: Lista de diccionarios con información de formularios
        """
        forms = []
        for form in self.soup.find_all('form'):
            forms.append({
                'action': form.get('action', ''),
                'method': form.get('method', 'get').upper(),
                'id': form.get('id', ''),
                'fields_count': len(form.find_all(['input', 'select', 'textarea']))
            })
        return forms

    def get_language(self) -> str:
        """Obtiene el idioma declarado en el documento."""
        html_tag = self.soup.find('html')
        return html_tag.get('lang', 'unknown') if html_tag else 'unknown'

    def get_main_text(self, max_length: int = 10000) -> str:
        """
        Extrae el texto principal del documento.

        Args:
            max_length: Longitud máxima del texto a retornar

        Returns:
            str: Texto principal del documento
        """
        # Eliminar scripts, estilos y otros elementos no deseados
        for element in self.soup(['script', 'style', 'nav', 'footer', 'header']):
            element.decompose()

        # Extraer texto
        text = self.soup.get_text(separator=' ', strip=True)

        # Limpiar espacios múltiples
        text = re.sub(r'\s+', ' ', text)

        return text[:max_length]

    def has_semantic_html5(self) -> Dict[str, bool]:
        """
        Verifica el uso de elementos semánticos HTML5.

        Returns:
            dict: Diccionario indicando presencia de elementos semánticos
        """
        semantic_tags = ['header', 'nav', 'main', 'article', 'section', 'aside', 'footer']
        return {
            tag: bool(self.soup.find(tag))
            for tag in semantic_tags
        }

    def get_aria_attributes_count(self) -> int:
        """Cuenta elementos con atributos ARIA para accesibilidad."""
        count = 0
        for tag in self.soup.find_all(True):
            if any(attr.startswith('aria-') for attr in tag.attrs):
                count += 1
        return count

    def get_table_count(self) -> int:
        """Cuenta el número de tablas en el documento."""
        return len(self.soup.find_all('table'))

    def get_doctype(self) -> str:
        """Obtiene la declaración DOCTYPE."""
        if self.soup.contents and hasattr(self.soup.contents[0], 'name'):
            if self.soup.contents[0].name == '[document]':
                return str(self.soup.contents[0])
        return ""

    def _is_external_link(self, url: str) -> bool:
        """
        Determina si un enlace es externo.

        Args:
            url: URL a verificar

        Returns:
            bool: True si es enlace externo
        """
        if not self.base_url or not url:
            return False

        base_domain = urlparse(self.base_url).netloc
        url_domain = urlparse(url).netloc

        return url_domain and url_domain != base_domain

    def validate_structure(self) -> Dict[str, any]:
        """
        Valida la estructura básica del HTML.

        Returns:
            dict: Diccionario con resultados de validación
        """
        return {
            'has_title': bool(self.get_title()),
            'has_meta_description': bool(self.get_meta_description()),
            'has_h1': bool(self.soup.find('h1')),
            'h1_count': len(self.soup.find_all('h1')),
            'has_lang_attribute': self.get_language() != 'unknown',
            'images_without_alt': len([img for img in self.get_images() if not img['has_alt']]),
            'total_images': len(self.get_images()),
            'total_links': len(self.get_links()),
            'total_forms': len(self.get_forms()),
            'has_semantic_html5': any(self.has_semantic_html5().values()),
            'aria_elements_count': self.get_aria_attributes_count()
        }
