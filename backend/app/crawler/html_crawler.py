import re
import logging
import time
from typing import Dict, List, Optional, Any
from datetime import datetime
from urllib.parse import urlparse, urljoin
from bs4 import BeautifulSoup, Doctype
import requests
from requests.exceptions import RequestException, Timeout, SSLError
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout

logger = logging.getLogger(__name__)


class GobBoCrawler:
    """
    Crawler especializado para sitios web gubernamentales bolivianos.

    Extrae información estructurada del HTML para evaluar:
    - Accesibilidad (30%): 10 criterios WCAG 2.0
    - Usabilidad (30%): 8 criterios de navegación/identidad
    - Semántica Web (30%): 10 criterios técnicos + análisis NLP
    - Soberanía Digital (10%): 4 criterios de recursos externos
    """

    # Dominios de redes sociales conocidas
    SOCIAL_DOMAINS = [
        'facebook.com', 'fb.com', 'twitter.com', 'x.com', 'instagram.com',
        'youtube.com', 'youtu.be', 'linkedin.com', 'tiktok.com', 'pinterest.com'
    ]

    # Dominios de mensajería
    MESSAGING_DOMAINS = ['wa.me', 'api.whatsapp.com', 't.me', 'telegram.me']

    # Trackers conocidos
    TRACKER_PATTERNS = [
        'google-analytics.com', 'googletagmanager.com', 'analytics.google.com',
        'facebook.net', 'connect.facebook.net', 'facebook.com/tr',
        'doubleclick.net', 'googleadservices.com', 'pixel', 'tracker'
    ]

    # Fuentes externas conocidas
    FONT_DOMAINS = ['fonts.googleapis.com', 'fonts.gstatic.com', 'use.typekit.net', 'cloud.typography.com']

    # Elementos HTML obsoletos
    OBSOLETE_ELEMENTS = ['font', 'center', 'marquee', 'blink', 'big', 'strike']
    OBSOLETE_ATTRIBUTES = ['align', 'bgcolor', 'border', 'height', 'width']  # cuando se usan para presentación

    # Textos genéricos de enlaces
    GENERIC_LINK_TEXTS = [
        'clic aquí', 'click aquí', 'haga clic aquí', 'pulse aquí',
        'aquí', 'ver más', 'leer más', 'más', 'más información',
        'más info', 'continuar', 'siguiente', 'anterior'
    ]

    def __init__(self, timeout: int = 30, user_agent: Optional[str] = None):
        """
        Inicializa el crawler.

        Args:
            timeout: Timeout en segundos para las peticiones HTTP
            user_agent: User-Agent personalizado para las peticiones
        """
        self.timeout = timeout
        self.user_agent = user_agent or "GOB.BO-Evaluator/1.0 (ADSIB)"
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': self.user_agent})

    def _fetch_page_with_playwright(self, url: str) -> Optional[str]:
        """
        Obtiene el HTML de una URL usando Playwright (ejecuta JavaScript).

        Esto permite extraer contenido de sitios web que cargan contenido dinámicamente
        con JavaScript (SPAs como React, Vue, Angular).

        Args:
            url: URL del sitio web a cargar

        Returns:
            str: HTML completamente renderizado, o None si hay error
        """
        try:
            logger.info(f"Usando Playwright para cargar {url}")

            with sync_playwright() as p:
                # Lanzar navegador Chromium en modo headless
                browser = p.chromium.launch(
                    headless=True,
                    args=[
                        '--disable-dev-shm-usage',  # Evitar problemas de memoria compartida
                        '--no-sandbox',              # Necesario en algunos entornos
                        '--disable-web-security'     # Para sitios con CORS estricto
                    ]
                )

                # Crear contexto de navegación con configuración
                context = browser.new_context(
                    user_agent=self.user_agent,
                    viewport={'width': 1920, 'height': 1080},
                    ignore_https_errors=True  # Manejar certificados SSL inválidos
                )

                # Crear nueva página
                page = context.new_page()
                page.set_default_timeout(self.timeout * 1000)  # Convertir a milisegundos

                # Navegar a la URL y esperar a que la red esté inactiva
                logger.info(f"Navegando a {url} y esperando carga de JavaScript...")
                page.goto(url, wait_until='networkidle')

                # Esperar adicional para contenido dinámico
                time.sleep(3)

                # Scroll para activar lazy loading de imágenes y contenido
                logger.info("Simulando scroll para activar lazy loading...")
                page.evaluate('window.scrollTo(0, document.body.scrollHeight / 2);')
                time.sleep(1)
                page.evaluate('window.scrollTo(0, document.body.scrollHeight);')
                time.sleep(1)
                page.evaluate('window.scrollTo(0, 0);')  # Volver arriba
                time.sleep(1)

                # Obtener HTML completamente renderizado
                html = page.content()

                # Cerrar navegador
                browser.close()

                logger.info(f"HTML obtenido exitosamente ({len(html)} caracteres)")
                return html

        except PlaywrightTimeout as e:
            logger.error(f"Timeout de Playwright al cargar {url}: {e}")
            return None
        except Exception as e:
            logger.error(f"Error con Playwright al cargar {url}: {e}")
            return None

    def _validate_content_loaded(self, soup: BeautifulSoup) -> bool:
        """
        Valida que el contenido se haya cargado correctamente.

        Verifica que el HTML tenga elementos básicos que indiquen
        que el JavaScript se ejecutó y cargó contenido.

        Args:
            soup: Objeto BeautifulSoup con el HTML parseado

        Returns:
            bool: True si el contenido parece cargado correctamente
        """
        # Verificar que haya al menos algunos elementos básicos
        has_links = len(soup.find_all('a')) > 0
        has_images = len(soup.find_all('img')) > 0
        has_text = len(soup.get_text(strip=True)) > 100

        # Al menos debe tener texto o algunos elementos
        return has_text or has_links or has_images

    def crawl(self, url: str) -> Dict[str, Any]:
        """
        Crawlea un sitio web y extrae toda la información necesaria.

        Args:
            url: URL del sitio web a crawlear

        Returns:
            dict: Diccionario con toda la información extraída

        Raises:
            ValueError: Si la URL no es un dominio .gob.bo válido
            RequestException: Si ocurre un error en la petición HTTP
        """
        # Validar que sea dominio .gob.bo
        if not self._is_gob_bo_domain(url):
            raise ValueError(f"La URL {url} no es un dominio .gob.bo válido")

        logger.info(f"Iniciando crawling de {url}")

        try:
            # Usar Playwright para obtener HTML con JavaScript ejecutado
            html = self._fetch_page_with_playwright(url)

            if not html:
                logger.error(f"No se pudo obtener el HTML de {url}")
                return {
                    'error': 'No se pudo cargar el sitio web',
                    'url': url,
                    'crawled_at': datetime.utcnow().isoformat()
                }

            # Parsear HTML con lxml (más rápido que html.parser)
            soup = BeautifulSoup(html, 'lxml')

            # Validar que el contenido se cargó correctamente
            if not self._validate_content_loaded(soup):
                logger.warning(f"El sitio {url} parece no haber cargado contenido dinámico correctamente")
                # Continuar de todos modos, puede ser un sitio estático

            # Verificar robots.txt
            robots_info = self._check_robots_txt(url)

            # Extraer toda la información
            extracted_data = {
                'url': url,
                'final_url': url,  # Playwright maneja redirecciones internamente
                'crawled_at': datetime.utcnow().isoformat(),
                'http_status_code': 200,  # Asumimos 200 si Playwright cargó correctamente
                'robots_txt': robots_info,
                'structure': self._extract_structure(soup, html),
                'metadata': self._extract_metadata(soup),
                'semantic_elements': self._extract_semantic_elements(soup),
                'headings': self._extract_headings(soup),
                'images': self._extract_images(soup, url),
                'links': self._extract_links(soup, url),
                'forms': self._extract_forms(soup),
                'media': self._extract_media(soup),
                'external_resources': self._extract_external_resources(soup, url),
                'stylesheets': self._extract_stylesheets(soup, url),
                'scripts': self._extract_scripts(soup, url),
                'text_corpus': self._extract_text_corpus(soup)
            }

            logger.info(f"Crawling completado exitosamente para {url}")
            return extracted_data

        except Timeout:
            logger.error(f"Timeout al crawlear {url}")
            raise
        except SSLError as e:
            logger.error(f"Error SSL al crawlear {url}: {e}")
            raise
        except RequestException as e:
            logger.error(f"Error en petición HTTP para {url}: {e}")
            raise
        except Exception as e:
            logger.error(f"Error inesperado al crawlear {url}: {e}")
            raise

    def _is_gob_bo_domain(self, url: str) -> bool:
        """
        Verifica que la URL sea un dominio .gob.bo válido.

        Args:
            url: URL a verificar

        Returns:
            bool: True si es dominio .gob.bo, False en caso contrario
        """
        try:
            parsed = urlparse(url)
            domain = parsed.netloc.lower()
            return domain.endswith('.gob.bo') or domain == 'gob.bo'
        except Exception:
            return False

    def _check_robots_txt(self, url: str) -> Dict[str, Any]:
        """
        Verifica la existencia y contenido del archivo robots.txt.

        Buena práctica SEO y crawling responsable.

        Args:
            url: URL base del sitio

        Returns:
            dict: Información sobre robots.txt
        """
        parsed = urlparse(url)
        base_url = f"{parsed.scheme}://{parsed.netloc}"
        robots_url = urljoin(base_url, '/robots.txt')

        result = {
            'exists': False,
            'url': robots_url,
            'accessible': False,
            'allows_crawling': None,
            'has_sitemap': False,
            'sitemap_urls': [],
            'content_preview': None,
            'error': None
        }

        try:
            response = self.session.get(
                robots_url,
                timeout=10,
                verify=False,
                allow_redirects=True
            )

            if response.status_code == 200:
                result['exists'] = True
                result['accessible'] = True

                content = response.text
                result['content_preview'] = content[:500]  # Primeros 500 caracteres

                # Analizar contenido
                lines = content.lower().split('\n')

                # Buscar User-agent: * y Disallow:
                current_user_agent = None
                disallow_all = False

                for line in lines:
                    line = line.strip()

                    if line.startswith('user-agent:'):
                        user_agent = line.split(':', 1)[1].strip()
                        if user_agent == '*' or 'gob.bo-evaluator' in user_agent.lower():
                            current_user_agent = user_agent

                    elif line.startswith('disallow:') and current_user_agent:
                        disallow_value = line.split(':', 1)[1].strip()
                        if disallow_value == '/':
                            disallow_all = True

                    elif line.startswith('sitemap:'):
                        sitemap_url = line.split(':', 1)[1].strip()
                        result['has_sitemap'] = True
                        result['sitemap_urls'].append(sitemap_url)

                # Determinar si permite crawling
                result['allows_crawling'] = not disallow_all

            elif response.status_code == 404:
                result['exists'] = False
                result['error'] = 'Archivo robots.txt no encontrado (404)'
            else:
                result['exists'] = True
                result['accessible'] = False
                result['error'] = f'Error al acceder: HTTP {response.status_code}'

        except Timeout:
            result['error'] = 'Timeout al intentar acceder a robots.txt'
        except Exception as e:
            result['error'] = f'Error al verificar robots.txt: {str(e)}'

        return result

    def _extract_structure(self, soup: BeautifulSoup, raw_html: str) -> Dict[str, Any]:
        """
        Extrae la estructura del documento HTML.

        Evalúa criterios:
        - SEM-01: Uso de DOCTYPE HTML5
        - SEM-02: Codificación UTF-8
        - SEM-04: Separación contenido-presentación (ausencia de elementos obsoletos)

        Args:
            soup: Objeto BeautifulSoup con el HTML parseado
            raw_html: HTML raw como string

        Returns:
            dict: Información sobre la estructura del documento
        """
        # SEM-01: Verificar DOCTYPE HTML5
        has_html5_doctype = False
        doctype_text = ""
        for item in soup.contents:
            if isinstance(item, Doctype):
                doctype_text = str(item).strip().lower()
                has_html5_doctype = doctype_text == 'html'
                break

        # SEM-02: Verificar charset UTF-8
        charset = None
        meta_charset = soup.find('meta', charset=True)
        if meta_charset:
            charset = meta_charset.get('charset', '').lower()
        else:
            # Buscar en meta http-equiv
            meta_http_equiv = soup.find('meta', {'http-equiv': 'Content-Type'})
            if meta_http_equiv:
                content = meta_http_equiv.get('content', '')
                charset_match = re.search(r'charset=([^;]+)', content, re.IGNORECASE)
                if charset_match:
                    charset = charset_match.group(1).strip().lower()

        has_utf8 = charset == 'utf-8' if charset else False

        # SEM-04: Detectar elementos y atributos obsoletos
        obsolete_elements_found = []
        for tag_name in self.OBSOLETE_ELEMENTS:
            tags = soup.find_all(tag_name)
            if tags:
                obsolete_elements_found.extend([{
                    'tag': tag_name,
                    'count': len(tags)
                }])

        # Detectar atributos obsoletos en elementos comunes
        obsolete_attributes_found = []
        for tag in soup.find_all(['table', 'td', 'tr', 'th', 'img', 'div', 'p']):
            for attr in self.OBSOLETE_ATTRIBUTES:
                if tag.has_attr(attr):
                    # Excepciones: width/height en img son válidos
                    if tag.name == 'img' and attr in ['width', 'height']:
                        continue
                    obsolete_attributes_found.append({
                        'tag': tag.name,
                        'attribute': attr,
                        'value': tag[attr]
                    })

        # FMT-02: Verificar elementos básicos de estructura HTML
        has_html = soup.find('html') is not None
        has_head = soup.find('head') is not None
        has_body = soup.find('body') is not None

        return {
            'has_html5_doctype': has_html5_doctype,
            'doctype_text': doctype_text,
            'has_utf8_charset': has_utf8,
            'charset_declared': charset,
            'obsolete_elements': obsolete_elements_found,
            'obsolete_attributes': obsolete_attributes_found[:20],  # Limitar a 20 ejemplos
            'has_obsolete_code': len(obsolete_elements_found) > 0 or len(obsolete_attributes_found) > 0,
            # FMT-02: Estructura básica HTML
            'has_html': has_html,
            'has_head': has_head,
            'has_body': has_body
        }

    def _extract_metadata(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """
        Extrae metadatos del documento.

        Evalúa criterios:
        - ACC-02: Idioma de la página (<html lang="es">)
        - ACC-03: Título descriptivo de página
        - SEO-01: Meta descripción
        - SEO-02: Meta keywords
        - SEO-03: Meta viewport (responsive)
        - IDEN-01: Nombre institución en título

        Args:
            soup: Objeto BeautifulSoup con el HTML parseado

        Returns:
            dict: Metadatos del documento
        """
        # ACC-03 / IDEN-01: Title
        title_tag = soup.find('title')
        title = title_tag.get_text().strip() if title_tag else None
        title_length = len(title) if title else 0

        # ACC-02: Idioma
        html_tag = soup.find('html')
        lang = html_tag.get('lang', '').strip() if html_tag else None

        # SEO-01: Meta description
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        description = meta_desc.get('content', '').strip() if meta_desc else None
        description_length = len(description) if description else 0

        # SEO-02: Meta keywords
        meta_keywords = soup.find('meta', attrs={'name': 'keywords'})
        keywords = meta_keywords.get('content', '').strip() if meta_keywords else None

        # SEO-03: Meta viewport
        meta_viewport = soup.find('meta', attrs={'name': 'viewport'})
        viewport = meta_viewport.get('content', '').strip() if meta_viewport else None

        return {
            'title': title,
            'title_length': title_length,
            'has_title': title is not None and title_length > 0,
            'lang': lang,
            'has_lang': lang is not None and len(lang) > 0,
            'description': description,
            'description_length': description_length,
            'has_description': description is not None,
            'keywords': keywords,
            'has_keywords': keywords is not None,
            'viewport': viewport,
            'has_viewport': viewport is not None
        }

    def _extract_semantic_elements(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """
        Extrae elementos semánticos HTML5.

        Evalúa criterios:
        - SEM-03: Elementos semánticos HTML5
        - NAV-01: Menú de navegación

        Args:
            soup: Objeto BeautifulSoup con el HTML parseado

        Returns:
            dict: Información sobre elementos semánticos
        """
        semantic_tags = ['header', 'nav', 'main', 'footer', 'article', 'section', 'aside']

        result = {}
        for tag_name in semantic_tags:
            tags = soup.find_all(tag_name)
            result[tag_name] = {
                'count': len(tags),
                'present': len(tags) > 0
            }

        # Calcular resumen
        result['summary'] = {
            'total_semantic_elements': sum(result[tag]['count'] for tag in semantic_tags),
            'types_used': sum(1 for tag in semantic_tags if result[tag]['present']),
            'has_basic_structure': (
                result['header']['present'] and
                result['nav']['present'] and
                result['main']['present'] and
                result['footer']['present']
            )
        }

        return result

    def _extract_headings(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """
        Extrae información de encabezados (headings).

        Evalúa criterios:
        - ACC-04: Estructura de encabezados (jerarquía correcta)
        - ACC-09: Encabezados descriptivos

        Args:
            soup: Objeto BeautifulSoup con el HTML parseado

        Returns:
            dict: Información sobre los encabezados
        """
        headings_list = []

        for level in range(1, 7):
            tag_name = f'h{level}'
            for heading in soup.find_all(tag_name):
                text = heading.get_text().strip()
                headings_list.append({
                    'level': level,
                    'tag': tag_name,
                    'text': text,
                    'length': len(text),
                    'is_empty': len(text) == 0
                })

        # Validar jerarquía (sin saltos de nivel)
        hierarchy_valid = True
        hierarchy_errors = []

        if headings_list:
            levels_used = [h['level'] for h in headings_list]
            previous_level = 0

            for i, level in enumerate(levels_used):
                if level > previous_level + 1:
                    hierarchy_valid = False
                    hierarchy_errors.append({
                        'position': i,
                        'expected_max': previous_level + 1,
                        'found': level
                    })
                previous_level = max(previous_level, level)

        # Contar h1
        h1_count = sum(1 for h in headings_list if h['level'] == 1)

        return {
            'headings': headings_list[:50],  # Limitar a 50 para no saturar la BD
            'total_count': len(headings_list),
            'by_level': {
                f'h{i}': sum(1 for h in headings_list if h['level'] == i)
                for i in range(1, 7)
            },
            'h1_count': h1_count,
            'has_single_h1': h1_count == 1,
            'hierarchy_valid': hierarchy_valid,
            'hierarchy_errors': hierarchy_errors,
            'empty_headings': sum(1 for h in headings_list if h['is_empty'])
        }

    def _extract_images(self, soup: BeautifulSoup, base_url: str) -> Dict[str, Any]:
        """
        Extrae información de imágenes.

        Evalúa criterios:
        - ACC-01: Texto alternativo en imágenes
        - FMT-02: Imágenes optimizadas (dimensiones razonables)

        Args:
            soup: Objeto BeautifulSoup con el HTML parseado
            base_url: URL base para resolver URLs relativas

        Returns:
            dict: Información sobre las imágenes
        """
        images_list = []

        for img in soup.find_all('img'):
            src = img.get('src', '')
            alt = img.get('alt', '')
            width = img.get('width', '')
            height = img.get('height', '')

            # Convertir dimensiones a números si es posible
            try:
                width_num = int(width) if width else None
            except (ValueError, TypeError):
                width_num = None

            try:
                height_num = int(height) if height else None
            except (ValueError, TypeError):
                height_num = None

            images_list.append({
                'src': src,
                'absolute_src': urljoin(base_url, src) if src else '',
                'alt': alt,
                'has_alt': 'alt' in img.attrs,
                'alt_empty': alt == '',
                'alt_length': len(alt),
                'width': width_num,
                'height': height_num,
                'has_dimensions': width_num is not None and height_num is not None
            })

        # Calcular estadísticas
        total_images = len(images_list)
        images_with_alt = sum(1 for img in images_list if img['has_alt'] and not img['alt_empty'])
        images_without_alt = total_images - images_with_alt

        return {
            'images': images_list[:100],  # Limitar a 100
            'total_count': total_images,
            'with_alt': images_with_alt,
            'without_alt': images_without_alt,
            'alt_compliance_percentage': (images_with_alt / total_images * 100) if total_images > 0 else 0
        }

    def _extract_links(self, soup: BeautifulSoup, base_url: str) -> Dict[str, Any]:
        """
        Extrae y clasifica enlaces.

        Evalúa criterios:
        - ACC-08: Enlaces descriptivos (detecta enlaces vacíos y textos genéricos)
        - PART-01: Enlaces a redes sociales (mín. 2)
        - PART-02: Enlace a app mensajería
        - PART-03: Enlace a correo electrónico
        - PART-04: Enlace a teléfono
        - PART-05: Botones compartir en RRSS

        Args:
            soup: Objeto BeautifulSoup con el HTML parseado
            base_url: URL base para resolver URLs relativas

        Returns:
            dict: Información clasificada sobre los enlaces
        """
        all_links = []
        social_links = []
        messaging_links = []
        email_links = []
        phone_links = []
        share_buttons = []
        generic_text_links = []
        empty_links = []  # Enlaces sin texto

        for link in soup.find_all('a', href=True):
            href = link.get('href', '').strip()
            text = link.get_text().strip()
            title = link.get('title', '').strip()

            absolute_url = urljoin(base_url, href) if href else ''
            parsed = urlparse(absolute_url.lower())

            # Detectar enlaces vacíos (ACC-08)
            is_empty = len(text) == 0 and len(title) == 0

            link_data = {
                'href': href,
                'text': text,
                'title': title,
                'absolute_url': absolute_url,
                'is_empty': is_empty
            }

            all_links.append(link_data)

            # Clasificar enlaces vacíos
            if is_empty:
                empty_links.append(link_data)

            # Clasificar enlaces
            # PART-03: Email
            if href.startswith('mailto:'):
                email_links.append(link_data)

            # PART-04: Teléfono
            elif href.startswith('tel:'):
                phone_links.append(link_data)

            # PART-01: Redes sociales
            elif any(domain in parsed.netloc for domain in self.SOCIAL_DOMAINS):
                social_links.append(link_data)

            # PART-02: Mensajería
            elif any(domain in parsed.netloc for domain in self.MESSAGING_DOMAINS):
                messaging_links.append(link_data)

            # ACC-08: Textos genéricos
            if text.lower() in self.GENERIC_LINK_TEXTS:
                generic_text_links.append(link_data)

            # PART-05: Botones compartir (buscar en atributos y clases)
            link_attrs = ' '.join([str(v) for v in link.attrs.values()]).lower()
            if 'share' in link_attrs or 'compartir' in link_attrs:
                share_buttons.append(link_data)

        return {
            'all_links': all_links[:200],  # Limitar a 200
            'total_count': len(all_links),
            'empty_links': {
                'links': empty_links[:20],  # Limitar a 20 ejemplos
                'count': len(empty_links)
            },
            'social': {
                'links': social_links,
                'count': len(social_links),
                'unique_platforms': len(set(urlparse(l['absolute_url']).netloc for l in social_links))
            },
            'messaging': {
                'links': messaging_links,
                'count': len(messaging_links)
            },
            'email': {
                'links': email_links,
                'count': len(email_links)
            },
            'phone': {
                'links': phone_links,
                'count': len(phone_links)
            },
            'share_buttons': {
                'links': share_buttons,
                'count': len(share_buttons)
            },
            'generic_text': {
                'links': generic_text_links[:20],
                'count': len(generic_text_links)
            }
        }

    def _extract_forms(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """
        Extrae información de formularios.

        Evalúa criterios:
        - ACC-07: Etiquetas en formularios (<label> asociado a <input>)

        Args:
            soup: Objeto BeautifulSoup con el HTML parseado

        Returns:
            dict: Información sobre formularios
        """
        forms_list = []
        total_inputs = 0
        inputs_with_label = 0

        for form in soup.find_all('form'):
            # FIX: Buscar inputs tanto dentro como alrededor del form
            inputs = form.find_all(['input', 'select', 'textarea'])
            form_inputs = []

            for input_elem in inputs:
                input_id = input_elem.get('id', '')
                input_type = input_elem.get('type', 'text')
                input_name = input_elem.get('name', '')
                input_placeholder = input_elem.get('placeholder', '')

                # Ignorar inputs hidden y submit/button
                if input_type in ['hidden', 'submit', 'button', 'reset', 'image']:
                    continue

                # Buscar label asociado
                has_label = False
                label_text = None

                # Método 1: Buscar por atributo 'for' en todo el documento
                if input_id:
                    label = soup.find('label', attrs={'for': input_id})
                    if label:
                        has_label = True
                        label_text = label.get_text(strip=True)

                # Método 2: Buscar si el input está dentro de un label
                if not has_label:
                    parent = input_elem.parent
                    if parent and parent.name == 'label':
                        has_label = True
                        label_text = parent.get_text(strip=True)

                # Método 3: Buscar label hermano anterior (común en algunos frameworks)
                if not has_label:
                    prev_sibling = input_elem.find_previous_sibling('label')
                    if prev_sibling:
                        has_label = True
                        label_text = prev_sibling.get_text(strip=True)

                # Método 4: Si tiene placeholder descriptivo, considerar como label implícito
                if not has_label and input_placeholder and len(input_placeholder) > 3:
                    has_label = True
                    label_text = f"[placeholder: {input_placeholder}]"

                form_inputs.append({
                    'type': input_type,
                    'id': input_id,
                    'name': input_name,
                    'placeholder': input_placeholder,
                    'has_label': has_label,
                    'label_text': label_text
                })

                total_inputs += 1
                if has_label:
                    inputs_with_label += 1

            # Solo agregar el formulario si tiene inputs válidos
            if form_inputs:
                forms_list.append({
                    'action': form.get('action', ''),
                    'method': form.get('method', 'get').upper(),
                    'inputs': form_inputs
                })

        return {
            'forms': forms_list,
            'total_forms': len(forms_list),
            'total_inputs': total_inputs,
            'inputs_with_label': inputs_with_label,
            'inputs_without_label': total_inputs - inputs_with_label,
            'label_compliance_percentage': (inputs_with_label / total_inputs * 100) if total_inputs > 0 else 0
        }

    def _extract_media(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """
        Extrae información de elementos multimedia.

        Evalúa criterios:
        - ACC-05: Sin auto reproducción multimedia

        Args:
            soup: Objeto BeautifulSoup con el HTML parseado

        Returns:
            dict: Información sobre elementos multimedia
        """
        audio_elements = []
        video_elements = []

        for audio in soup.find_all('audio'):
            audio_elements.append({
                'src': audio.get('src', ''),
                'has_autoplay': audio.has_attr('autoplay')
            })

        for video in soup.find_all('video'):
            video_elements.append({
                'src': video.get('src', ''),
                'has_autoplay': video.has_attr('autoplay')
            })

        audio_with_autoplay = sum(1 for a in audio_elements if a['has_autoplay'])
        video_with_autoplay = sum(1 for v in video_elements if v['has_autoplay'])

        return {
            'audio': {
                'elements': audio_elements,
                'count': len(audio_elements),
                'with_autoplay': audio_with_autoplay
            },
            'video': {
                'elements': video_elements,
                'count': len(video_elements),
                'with_autoplay': video_with_autoplay
            },
            'has_autoplay_media': audio_with_autoplay > 0 or video_with_autoplay > 0
        }

    def _extract_external_resources(self, soup: BeautifulSoup, base_url: str) -> Dict[str, Any]:
        """
        Extrae información de recursos externos.

        Evalúa criterios:
        - PROH-01: Sin iframes externos
        - PROH-02: Sin CDN externos
        - PROH-03: Sin fuentes externas
        - PROH-04: Sin trackers externos

        Args:
            soup: Objeto BeautifulSoup con el HTML parseado
            base_url: URL base del sitio

        Returns:
            dict: Información sobre recursos externos
        """
        base_domain = urlparse(base_url).netloc.lower()

        # PROH-01: iframes externos
        external_iframes = []
        for iframe in soup.find_all('iframe', src=True):
            src = iframe.get('src', '')
            absolute_src = urljoin(base_url, src)
            iframe_domain = urlparse(absolute_src).netloc.lower()

            is_external = iframe_domain and not iframe_domain.endswith('.gob.bo')

            if is_external:
                external_iframes.append({
                    'src': src,
                    'absolute_src': absolute_src,
                    'domain': iframe_domain
                })

        # PROH-02: CDN externos (en scripts y links)
        external_cdn = []

        for link in soup.find_all('link', href=True):
            href = link.get('href', '')
            absolute_href = urljoin(base_url, href)
            link_domain = urlparse(absolute_href).netloc.lower()

            is_external = link_domain and link_domain != base_domain and not link_domain.endswith('.gob.bo')

            if is_external:
                external_cdn.append({
                    'src': href,
                    'absolute_src': absolute_href,
                    'domain': link_domain,
                    'type': 'link',
                    'rel': link.get('rel', [])
                })

        for script in soup.find_all('script', src=True):
            src = script.get('src', '')
            absolute_src = urljoin(base_url, src)
            script_domain = urlparse(absolute_src).netloc.lower()

            is_external = script_domain and script_domain != base_domain and not script_domain.endswith('.gob.bo')

            if is_external:
                external_cdn.append({
                    'src': src,
                    'absolute_src': absolute_src,
                    'domain': script_domain,
                    'type': 'script'
                })

        # PROH-03: Fuentes externas
        external_fonts = []
        for link in soup.find_all('link', href=True):
            href = link.get('href', '')
            absolute_href = urljoin(base_url, href)

            if any(font_domain in absolute_href.lower() for font_domain in self.FONT_DOMAINS):
                external_fonts.append({
                    'src': href,
                    'absolute_src': absolute_href
                })

        # PROH-04: Trackers
        trackers_found = []

        for script in soup.find_all('script'):
            src = script.get('src', '')
            script_content = script.string or ''

            # Verificar en src
            if src and any(tracker in src.lower() for tracker in self.TRACKER_PATTERNS):
                trackers_found.append({
                    'type': 'script_src',
                    'src': src,
                    'tracker': next(t for t in self.TRACKER_PATTERNS if t in src.lower())
                })

            # Verificar en contenido inline
            elif any(tracker in script_content.lower() for tracker in self.TRACKER_PATTERNS):
                tracker_match = next(t for t in self.TRACKER_PATTERNS if t in script_content.lower())
                trackers_found.append({
                    'type': 'inline_script',
                    'tracker': tracker_match,
                    'snippet': script_content[:200]
                })

        return {
            'iframes': {
                'external': external_iframes,
                'count': len(external_iframes)
            },
            'cdn': {
                'external': external_cdn[:50],  # Limitar a 50
                'count': len(external_cdn),
                'unique_domains': len(set(cdn['domain'] for cdn in external_cdn))
            },
            'fonts': {
                'external': external_fonts,
                'count': len(external_fonts)
            },
            'trackers': {
                'found': trackers_found,
                'count': len(trackers_found)
            }
        }

    def _extract_stylesheets(self, soup: BeautifulSoup, base_url: str) -> List[Dict[str, Any]]:
        """
        Extrae información de hojas de estilo.

        Args:
            soup: Objeto BeautifulSoup con el HTML parseado
            base_url: URL base del sitio

        Returns:
            list: Lista de hojas de estilo con clasificación
        """
        base_domain = urlparse(base_url).netloc.lower()
        stylesheets = []

        for link in soup.find_all('link', rel='stylesheet'):
            href = link.get('href', '')
            absolute_href = urljoin(base_url, href)
            css_domain = urlparse(absolute_href).netloc.lower()

            is_external = css_domain and css_domain != base_domain
            is_gob_bo = css_domain.endswith('.gob.bo')

            stylesheets.append({
                'href': href,
                'absolute_href': absolute_href,
                'domain': css_domain,
                'is_external': is_external,
                'is_gob_bo': is_gob_bo,
                'media': link.get('media', 'all')
            })

        # Contar estilos inline
        inline_styles_count = len(soup.find_all('style'))

        return {
            'stylesheets': stylesheets,
            'count': len(stylesheets),
            'inline_styles_count': inline_styles_count,
            'external_count': sum(1 for s in stylesheets if s['is_external'])
        }

    def _extract_scripts(self, soup: BeautifulSoup, base_url: str) -> List[Dict[str, Any]]:
        """
        Extrae información de scripts.

        Args:
            soup: Objeto BeautifulSoup con el HTML parseado
            base_url: URL base del sitio

        Returns:
            list: Lista de scripts con clasificación
        """
        base_domain = urlparse(base_url).netloc.lower()
        scripts = []

        for script in soup.find_all('script', src=True):
            src = script.get('src', '')
            absolute_src = urljoin(base_url, src)
            script_domain = urlparse(absolute_src).netloc.lower()

            is_external = script_domain and script_domain != base_domain
            is_gob_bo = script_domain.endswith('.gob.bo')

            scripts.append({
                'src': src,
                'absolute_src': absolute_src,
                'domain': script_domain,
                'is_external': is_external,
                'is_gob_bo': is_gob_bo,
                'type': script.get('type', 'text/javascript'),
                'async': script.has_attr('async'),
                'defer': script.has_attr('defer')
            })

        # Contar scripts inline
        inline_scripts_count = len(soup.find_all('script', src=False))

        return {
            'scripts': scripts,
            'count': len(scripts),
            'inline_scripts_count': inline_scripts_count,
            'external_count': sum(1 for s in scripts if s['is_external'])
        }

    def _extract_text_corpus(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """
        Extrae corpus textual completo para análisis NLP.

        Necesario para:
        - IDEN-02: Buscar "Bolivia a tu servicio"
        - Coherencia: ¿El contenido bajo un heading corresponde al título?
        - Claridad: ¿El texto es comprensible?
        - Ambigüedades: ¿Hay instrucciones confusas o enlaces genéricos?

        Args:
            soup: Objeto BeautifulSoup con el HTML parseado

        Returns:
            dict: Corpus textual estructurado para análisis NLP
        """
        # 1. TEXTO DEL HEADER (para IDEN-02)
        header_text = ""
        header = soup.find('header')
        if header:
            header_text = header.get_text(separator=' ', strip=True)

        # Buscar "Bolivia a tu servicio"
        has_bolivia_service = 'bolivia a tu servicio' in header_text.lower()

        # 1.5. TEXTO DEL FOOTER (para PART-01 datos de contacto)
        footer_text = ""
        footer = soup.find('footer')
        if footer:
            footer_text = footer.get_text(separator=' ', strip=True)

        # 2. TÍTULO DE LA PÁGINA
        title_text = ''
        title_tag = soup.find('title')
        if title_tag:
            title_text = title_tag.get_text(strip=True)

        # 3. META DESCRIPTION
        meta_desc = ''
        head = soup.find('head')
        if head:
            meta_tag = head.find('meta', {'name': 'description'})
            if meta_tag:
                meta_desc = meta_tag.get('content', '')

        # 4. SECCIONES CON HEADINGS Y CONTENIDO
        # Para análisis de coherencia: ¿el contenido corresponde al título de la sección?
        sections = []
        processed_headings = set()  # Para evitar duplicados

        for heading in soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
            heading_text = heading.get_text(strip=True)

            # Evitar duplicados
            if heading_text in processed_headings or len(heading_text) < 3:
                continue

            processed_headings.add(heading_text)
            heading_level = heading.name

            # ESTRATEGIA MEJORADA: Extraer TODO el texto asociado al heading
            paragraphs = []
            found_content = False

            # Estrategia 1: Buscar en hermanos directos
            current = heading.find_next_sibling()

            while current and len(paragraphs) < 10:
                if current.name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
                    current_level = int(current.name[1])
                    heading_level_num = int(heading_level[1])
                    if current_level <= heading_level_num:
                        break

                # Extraer de párrafos
                if current.name == 'p':
                    p_text = current.get_text(strip=True)
                    if len(p_text) > 20:
                        paragraphs.append(p_text)
                        found_content = True

                # Extraer de listas
                elif current.name in ['ul', 'ol']:
                    for li in current.find_all('li'):
                        li_text = li.get_text(strip=True)
                        if len(li_text) > 10:
                            paragraphs.append(li_text)
                            found_content = True

                # NUEVO: Extraer de divs
                elif current.name == 'div':
                    # Buscar párrafos dentro del div
                    for p in current.find_all('p', recursive=True):
                        p_text = p.get_text(strip=True)
                        if len(p_text) > 20:
                            paragraphs.append(p_text)
                            found_content = True

                    # Si no hay párrafos, tomar texto directo del div
                    if not found_content:
                        div_text = current.get_text(strip=True)
                        if len(div_text) > 20 and len(div_text) < 800:
                            paragraphs.append(div_text)
                            found_content = True

                current = current.find_next_sibling()

            # Estrategia 2: Si no encontramos nada, buscar en el contenedor padre
            if not found_content:
                parent = heading.parent
                if parent:
                    # Obtener todo el texto del padre excluyendo el heading mismo
                    parent_text = parent.get_text(separator=' ', strip=True)
                    heading_start = parent_text.find(heading_text)
                    if heading_start != -1:
                        content_after_heading = parent_text[heading_start + len(heading_text):].strip()
                        if len(content_after_heading) > 20:
                            # Dividir en fragmentos de ~200 caracteres
                            words = content_after_heading.split()
                            chunk = []
                            for word in words:
                                chunk.append(word)
                                if len(' '.join(chunk)) > 200:
                                    paragraphs.append(' '.join(chunk))
                                    chunk = []
                                if len(paragraphs) >= 3:
                                    break
                            if chunk and len(paragraphs) < 3:
                                paragraphs.append(' '.join(chunk))

            if paragraphs:
                content = ' '.join(paragraphs)
                sections.append({
                    'heading': heading_text,
                    'heading_level': heading_level,
                    'paragraphs': paragraphs[:5],
                    'content': content[:1000],
                    'word_count': len(content.split())
                })

        # 5. TEXTO DE NAVEGACIÓN
        nav_texts = []
        for nav in soup.find_all('nav'):
            for link in nav.find_all('a'):
                text = link.get_text(strip=True)
                if text and len(text) > 0:
                    nav_texts.append(text)

        # 6. TEXTO DE ENLACES (para detectar textos genéricos - claridad)
        link_texts = []
        generic_phrases = [
            'clic aquí', 'haz clic', 'click aquí', 'aquí',
            'ver más', 'leer más', 'más información', 'continuar',
            'siguiente', 'anterior', 'atrás', 'más', 'click here',
            'here', 'read more', 'more'
        ]

        for a in soup.find_all('a', href=True):
            text = a.get_text(strip=True)
            href = a.get('href', '')

            if text:
                is_generic = any(phrase in text.lower() for phrase in generic_phrases)
                link_texts.append({
                    'text': text,
                    'href': href[:100],  # Limitar URL
                    'is_generic': is_generic,
                    'length': len(text)
                })

        # 7. TEXTO DE BOTONES
        button_texts = []
        for button in soup.find_all(['button', 'input']):
            if button.name == 'input' and button.get('type') not in ['button', 'submit']:
                continue

            text = button.get_text(strip=True) or button.get('value', '')
            if text:
                button_texts.append(text)

        # 8. ETIQUETAS DE FORMULARIOS
        label_texts = []
        for label in soup.find_all('label'):
            text = label.get_text(strip=True)
            if text:
                label_texts.append(text)

        # 9. TODO EL TEXTO VISIBLE (para análisis general)
        # Crear una copia para no modificar el original
        soup_copy = BeautifulSoup(str(soup), 'html.parser')

        # Eliminar scripts y estilos
        for element in soup_copy(['script', 'style', 'noscript']):
            element.decompose()

        body = soup_copy.find('body')
        full_text = ''
        if body:
            full_text = body.get_text(separator=' ', strip=True)

        # 10. ESTADÍSTICAS
        total_words = len(full_text.split())

        return {
            # Textos específicos
            'header_text': header_text[:500],
            'footer_text': footer_text[:1000],  # AGREGADO: Texto del footer para contacto
            'has_bolivia_service_text': has_bolivia_service,
            'title': title_text,
            'meta_description': meta_desc[:300],

            # Secciones para análisis de coherencia
            'sections': sections[:20],  # Limitar a 20 secciones
            'total_sections': len(sections),
            'sections_with_content': len([s for s in sections if len(s['paragraphs']) > 0]),

            # Navegación
            'navigation_texts': nav_texts[:50],  # Limitar a 50
            'total_nav_items': len(nav_texts),

            # Enlaces (para análisis de claridad)
            'link_texts': link_texts[:100],  # Limitar a 100
            'total_links': len(link_texts),
            'generic_links': len([l for l in link_texts if l['is_generic']]),
            'generic_link_examples': [l['text'] for l in link_texts if l['is_generic']][:10],

            # Botones
            'button_texts': button_texts[:30],
            'total_buttons': len(button_texts),

            # Formularios
            'label_texts': label_texts[:50],
            'total_labels': len(label_texts),

            # Texto completo
            'full_text': full_text[:5000],  # Primeros 5000 caracteres
            'total_words': total_words,
            'total_characters': len(full_text)
        }
