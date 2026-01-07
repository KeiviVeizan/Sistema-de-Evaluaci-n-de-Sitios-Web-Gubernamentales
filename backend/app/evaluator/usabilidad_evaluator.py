"""
Evaluador de Usabilidad (30%)
Evalúa 8 criterios: IDEN-01, IDEN-02, NAV-01, PART-01 a PART-05
"""
import re
from typing import Dict, List
from .base_evaluator import BaseEvaluator, CriteriaEvaluation


class EvaluadorUsabilidad(BaseEvaluator):
    """
    Evaluador de criterios de usabilidad
    """

    def __init__(self):
        super().__init__(dimension="usabilidad")

        # Pesos según tabla_final.xlsx
        self.criterios = {
            "IDEN-01": {"name": "Escudo de Bolivia", "points": 15, "lineamiento": "D.S. 3925 (IDEN-01)"},
            "IDEN-02": {"name": "Nombre de la institución", "points": 15, "lineamiento": "D.S. 3925 (IDEN-02)"},
            "NAV-01": {"name": "Menú de navegación", "points": 12, "lineamiento": "D.S. 3925 (NAV-01)"},
            "PART-01": {"name": "Datos de contacto", "points": 10, "lineamiento": "D.S. 3925 (PART-01)"},
            "PART-02": {"name": "Redes sociales oficiales", "points": 8, "lineamiento": "D.S. 3925 (PART-02)"},
            "PART-03": {"name": "Buscador interno", "points": 12, "lineamiento": "D.S. 3925 (PART-03)"},
            "PART-04": {"name": "Mapa del sitio", "points": 10, "lineamiento": "D.S. 3925 (PART-04)"},
            "PART-05": {"name": "Formularios de contacto", "points": 8, "lineamiento": "D.S. 3925 (PART-05)"}
        }

    def evaluate(self, extracted_content: Dict) -> List[CriteriaEvaluation]:
        """Evalúa todos los criterios de usabilidad"""
        self.clear_results()

        # Extraer datos relevantes
        metadata = extracted_content.get('metadata', {})
        structure = extracted_content.get('structure', {})
        semantic_elements = extracted_content.get('semantic_elements', {})
        images = extracted_content.get('images', {})
        links = extracted_content.get('links', {})
        forms = extracted_content.get('forms', {})
        text_corpus = extracted_content.get('text_corpus', {})

        # Evaluar cada criterio
        self.add_result(self._evaluar_iden01(images, text_corpus))
        self.add_result(self._evaluar_iden02(metadata, text_corpus))
        self.add_result(self._evaluar_nav01(semantic_elements, links))
        self.add_result(self._evaluar_part01(text_corpus, links))
        self.add_result(self._evaluar_part02(links, text_corpus))
        self.add_result(self._evaluar_part03(forms, structure))
        self.add_result(self._evaluar_part04(links, text_corpus))
        self.add_result(self._evaluar_part05(forms))

        return self.results

    def _evaluar_iden01(self, images: Dict, text_corpus: Dict) -> CriteriaEvaluation:
        """
        IDEN-01: Escudo de Bolivia
        Debe estar presente en el sitio (imagen o texto "escudo de bolivia")
        """
        # Buscar en imágenes
        images_list = images.get('images', [])
        escudo_found_in_images = False
        for img in images_list:
            alt = img.get('alt', '').lower()
            src = img.get('src', '').lower()
            if 'escudo' in alt or 'escudo' in src or 'bolivia' in alt:
                escudo_found_in_images = True
                break

        # Buscar en texto
        sections = text_corpus.get('sections', [])
        escudo_found_in_text = False
        for section in sections:
            heading = section.get('heading', '').lower()
            paragraphs = section.get('paragraphs', [])
            if 'escudo' in heading:
                escudo_found_in_text = True
                break
            for p in paragraphs:
                if 'escudo' in p.lower() and 'bolivia' in p.lower():
                    escudo_found_in_text = True
                    break

        if escudo_found_in_images or escudo_found_in_text:
            status = "pass"
            score = 15
            message = "Escudo de Bolivia presente en el sitio"
        else:
            status = "fail"
            score = 0
            message = "No se detectó el Escudo de Bolivia"

        return CriteriaEvaluation(
            criteria_id="IDEN-01",
            criteria_name=self.criterios["IDEN-01"]["name"],
            dimension=self.dimension,
            lineamiento=self.criterios["IDEN-01"]["lineamiento"],
            status=status,
            score=score,
            max_score=15,
            details={
                "found_in_images": escudo_found_in_images,
                "found_in_text": escudo_found_in_text,
                "message": message
            },
            evidence={
                "images_checked": len(images_list),
                "sections_checked": len(sections)
            }
        )

    def _evaluar_iden02(self, metadata: Dict, text_corpus: Dict) -> CriteriaEvaluation:
        """
        IDEN-02: Nombre de la institución
        Debe estar presente en título, headings o texto prominente
        """
        title = metadata.get('title', '').lower()
        has_bolivia_service = text_corpus.get('has_bolivia_service_text', False)

        # Buscar en secciones
        sections = text_corpus.get('sections', [])
        institution_found = False

        # Palabras clave de instituciones gubernamentales
        keywords = ['ministerio', 'gobierno', 'bolivia', 'servicio', 'agencia', 'dirección']

        for section in sections:
            heading = section.get('heading', '').lower()
            for keyword in keywords:
                if keyword in heading:
                    institution_found = True
                    break
            if institution_found:
                break

        # Verificar en título
        title_has_institution = any(keyword in title for keyword in keywords)

        if title_has_institution or institution_found or has_bolivia_service:
            status = "pass"
            score = 15
            message = "Nombre de la institución identificado"
        else:
            status = "fail"
            score = 0
            message = "No se identificó claramente el nombre de la institución"

        return CriteriaEvaluation(
            criteria_id="IDEN-02",
            criteria_name=self.criterios["IDEN-02"]["name"],
            dimension=self.dimension,
            lineamiento=self.criterios["IDEN-02"]["lineamiento"],
            status=status,
            score=score,
            max_score=15,
            details={
                "in_title": title_has_institution,
                "in_headings": institution_found,
                "has_bolivia_service": has_bolivia_service,
                "message": message
            },
            evidence={
                "title": metadata.get('title', ''),
                "sections_count": len(sections)
            }
        )

    def _evaluar_nav01(self, semantic_elements: Dict, links: Dict) -> CriteriaEvaluation:
        """
        NAV-01: Menú de navegación
        Debe existir elemento <nav> con enlaces
        """
        nav_data = semantic_elements.get('nav', 0)
        # FIX: nav_data es un dict con 'count', no un int
        nav_count = nav_data.get('count', 0) if isinstance(nav_data, dict) else (nav_data if isinstance(nav_data, int) else 0)
        total_links = links.get('total_count', 0)

        if nav_count > 0 and total_links >= 3:
            status = "pass"
            score = 12
            message = f"Menú de navegación presente con {nav_count} elemento(s) <nav>"
        elif nav_count > 0:
            status = "partial"
            score = 6
            message = "Elemento <nav> presente pero pocos enlaces"
        elif total_links >= 5:
            status = "partial"
            score = 4
            message = "No hay <nav> pero hay enlaces de navegación"
        else:
            status = "fail"
            score = 0
            message = "No se detectó menú de navegación"

        return CriteriaEvaluation(
            criteria_id="NAV-01",
            criteria_name=self.criterios["NAV-01"]["name"],
            dimension=self.dimension,
            lineamiento=self.criterios["NAV-01"]["lineamiento"],
            status=status,
            score=score,
            max_score=12,
            details={
                "nav_count": nav_count,
                "total_links": total_links,
                "message": message
            },
            evidence={
                "semantic_nav": nav_count > 0
            }
        )

    def _evaluar_part01(self, text_corpus: Dict, links: Dict) -> CriteriaEvaluation:
        """
        PART-01: Datos de contacto
        Debe tener teléfono, email o dirección
        """
        sections = text_corpus.get('sections', [])

        # Buscar patrones de contacto
        has_phone = False
        has_email = False
        has_address = False

        contact_keywords = ['contacto', 'teléfono', 'email', 'dirección', 'ubicación']

        for section in sections:
            heading = section.get('heading', '').lower()
            paragraphs = section.get('paragraphs', [])

            # Verificar si es sección de contacto
            if any(keyword in heading for keyword in contact_keywords):
                for p in paragraphs:
                    p_lower = p.lower()
                    if '@' in p or 'email' in p_lower or 'correo' in p_lower:
                        has_email = True
                    if 'tel' in p_lower or 'teléfono' in p_lower or any(c.isdigit() for c in p):
                        has_phone = True
                    if 'calle' in p_lower or 'avenida' in p_lower or 'zona' in p_lower or 'dirección' in p_lower:
                        has_address = True

        # FIX: Buscar en enlaces mailto: y tel: usando las categorías correctas
        email_links = links.get('email', {}).get('links', [])
        phone_links = links.get('phone', {}).get('links', [])

        if email_links:
            has_email = True
        if phone_links:
            has_phone = True

        # También buscar en footer_text si existe
        footer_text = text_corpus.get('footer_text', '').lower()
        if footer_text:
            if not has_email and re.search(r'\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b', footer_text):
                has_email = True
            if not has_phone and re.search(r'(\+?591|tel|teléfono|telefono|celular).*\d{7,}', footer_text):
                has_phone = True
            if not has_address and re.search(r'\b(calle|avenida|av\.|zona|edificio|piso|dirección|direccion|plaza)\b', footer_text):
                has_address = True

        contact_methods = sum([has_phone, has_email, has_address])

        if contact_methods >= 2:
            status = "pass"
            score = 10
            message = f"Datos de contacto completos ({contact_methods} métodos encontrados)"
        elif contact_methods == 1:
            status = "partial"
            score = 5
            message = "Datos de contacto parciales"
        else:
            status = "fail"
            score = 0
            message = "No se encontraron datos de contacto"

        return CriteriaEvaluation(
            criteria_id="PART-01",
            criteria_name=self.criterios["PART-01"]["name"],
            dimension=self.dimension,
            lineamiento=self.criterios["PART-01"]["lineamiento"],
            status=status,
            score=score,
            max_score=10,
            details={
                "has_phone": has_phone,
                "has_email": has_email,
                "has_address": has_address,
                "contact_methods": contact_methods,
                "message": message
            },
            evidence={
                "sections_analyzed": len(sections)
            }
        )

    def _evaluar_part02(self, links: Dict, text_corpus: Dict) -> CriteriaEvaluation:
        """
        PART-02: Redes sociales oficiales
        Enlaces a Facebook, Twitter, Instagram, etc.
        """
        # FIX: Buscar en links['social']['links'] en lugar de links['links']
        social_links = links.get('social', {}).get('links', [])

        social_networks = {
            'facebook': False,
            'twitter': False,
            'instagram': False,
            'youtube': False,
            'linkedin': False,
            'tiktok': False  # Agregar TikTok
        }

        for link in social_links:
            href = link.get('href', '').lower()
            # También revisar 'x.com' para Twitter/X
            if 'facebook.com' in href or 'fb.com' in href:
                social_networks['facebook'] = True
            elif 'twitter.com' in href or 'x.com' in href:
                social_networks['twitter'] = True
            elif 'instagram.com' in href:
                social_networks['instagram'] = True
            elif 'youtube.com' in href or 'youtu.be' in href:
                social_networks['youtube'] = True
            elif 'linkedin.com' in href:
                social_networks['linkedin'] = True
            elif 'tiktok.com' in href:
                social_networks['tiktok'] = True

        count = sum(social_networks.values())

        if count >= 2:
            status = "pass"
            score = 8
            message = f"Enlaces a {count} redes sociales encontrados"
        elif count == 1:
            status = "partial"
            score = 4
            message = "Solo 1 red social encontrada"
        else:
            status = "fail"
            score = 0
            message = "No se encontraron enlaces a redes sociales"

        return CriteriaEvaluation(
            criteria_id="PART-02",
            criteria_name=self.criterios["PART-02"]["name"],
            dimension=self.dimension,
            lineamiento=self.criterios["PART-02"]["lineamiento"],
            status=status,
            score=score,
            max_score=8,
            details={
                "social_networks": social_networks,
                "count": count,
                "message": message
            },
            evidence={
                "found_networks": [net for net, found in social_networks.items() if found]
            }
        )

    def _evaluar_part03(self, forms: Dict, structure: Dict) -> CriteriaEvaluation:
        """
        PART-03: Buscador interno
        Debe tener input type="search" o form con input para búsqueda
        """
        forms_list = forms.get('forms', [])
        has_search = False

        for form in forms_list:
            # FIX: También verificar el action del formulario
            form_action = form.get('action', '').lower()

            # Verificar si el action contiene palabras clave de búsqueda
            if 'search' in form_action or 'buscar' in form_action or 'busqueda' in form_action:
                has_search = True
                break

            inputs = form.get('inputs', [])
            for inp in inputs:
                input_type = inp.get('type', '').lower()
                input_name = inp.get('name', '').lower()
                input_placeholder = inp.get('placeholder', '').lower()
                input_id = inp.get('id', '').lower()

                if input_type == 'search':
                    has_search = True
                    break
                if 'search' in input_name or 'buscar' in input_name or 'busqueda' in input_name or 'query' in input_name or 'q' == input_name:
                    has_search = True
                    break
                if 'buscar' in input_placeholder or 'search' in input_placeholder or 'busqueda' in input_placeholder:
                    has_search = True
                    break
                if 'search' in input_id or 'buscar' in input_id or 'busqueda' in input_id:
                    has_search = True
                    break

            if has_search:
                break

        if has_search:
            status = "pass"
            score = 12
            message = "Buscador interno presente"
        else:
            status = "fail"
            score = 0
            message = "No se encontró buscador interno"

        return CriteriaEvaluation(
            criteria_id="PART-03",
            criteria_name=self.criterios["PART-03"]["name"],
            dimension=self.dimension,
            lineamiento=self.criterios["PART-03"]["lineamiento"],
            status=status,
            score=score,
            max_score=12,
            details={
                "has_search": has_search,
                "forms_analyzed": len(forms_list),
                "message": message
            },
            evidence={
                "forms_count": forms.get('total_forms', 0)
            }
        )

    def _evaluar_part04(self, links: Dict, text_corpus: Dict) -> CriteriaEvaluation:
        """
        PART-04: Mapa del sitio
        Enlace a sitemap.xml o página de mapa del sitio
        """
        links_list = links.get('links', [])
        has_sitemap = False

        for link in links_list:
            href = link.get('href', '').lower()
            text = link.get('text', '').lower()

            if 'sitemap' in href or 'mapa' in href:
                has_sitemap = True
                break
            if 'mapa del sitio' in text or 'sitemap' in text or 'mapa de sitio' in text:
                has_sitemap = True
                break

        # Buscar en texto
        sections = text_corpus.get('sections', [])
        for section in sections:
            heading = section.get('heading', '').lower()
            if 'mapa' in heading and 'sitio' in heading:
                has_sitemap = True
                break

        if has_sitemap:
            status = "pass"
            score = 10
            message = "Mapa del sitio encontrado"
        else:
            status = "fail"
            score = 0
            message = "No se encontró mapa del sitio"

        return CriteriaEvaluation(
            criteria_id="PART-04",
            criteria_name=self.criterios["PART-04"]["name"],
            dimension=self.dimension,
            lineamiento=self.criterios["PART-04"]["lineamiento"],
            status=status,
            score=score,
            max_score=10,
            details={
                "has_sitemap": has_sitemap,
                "links_analyzed": len(links_list),
                "message": message
            },
            evidence={}
        )

    def _evaluar_part05(self, forms: Dict) -> CriteriaEvaluation:
        """
        PART-05: Formularios de contacto
        Debe tener al menos un formulario con campos de contacto
        """
        forms_list = forms.get('forms', [])
        total_forms = forms.get('total_forms', 0)

        has_contact_form = False

        for form in forms_list:
            inputs = form.get('inputs', [])

            # Buscar campos típicos de contacto
            has_name = False
            has_email = False
            has_message = False

            for inp in inputs:
                input_type = inp.get('type', '').lower()
                input_name = inp.get('name', '').lower()

                if 'name' in input_name or 'nombre' in input_name:
                    has_name = True
                if input_type == 'email' or 'email' in input_name or 'correo' in input_name:
                    has_email = True
                if 'message' in input_name or 'mensaje' in input_name or 'consulta' in input_name:
                    has_message = True

            if (has_name or has_email) and has_message:
                has_contact_form = True
                break

        if has_contact_form:
            status = "pass"
            score = 8
            message = "Formulario de contacto presente"
        elif total_forms > 0:
            status = "partial"
            score = 4
            message = "Hay formularios pero no claramente de contacto"
        else:
            status = "fail"
            score = 0
            message = "No se encontró formulario de contacto"

        return CriteriaEvaluation(
            criteria_id="PART-05",
            criteria_name=self.criterios["PART-05"]["name"],
            dimension=self.dimension,
            lineamiento=self.criterios["PART-05"]["lineamiento"],
            status=status,
            score=score,
            max_score=8,
            details={
                "has_contact_form": has_contact_form,
                "total_forms": total_forms,
                "message": message
            },
            evidence={
                "forms_analyzed": len(forms_list)
            }
        )
