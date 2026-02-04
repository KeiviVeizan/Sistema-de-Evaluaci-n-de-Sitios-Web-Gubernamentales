"""
Evaluador de Usabilidad (30%)
Evalúa 9 criterios: IDEN-01, IDEN-02, NAV-01, NAV-02, PART-01 a PART-05
"""
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
            "IDEN-01": {"name": "Nombre institución en título", "points": 14, "lineamiento": "D.S. 3925 (CONT-01) / WCAG 2.4.2"},
            "IDEN-02": {"name": "Leyenda 'Bolivia a tu servicio'", "points": 12, "lineamiento": "D.S. 3925 (BATS-01)"},
            "NAV-01": {"name": "Menú de navegación", "points": 16, "lineamiento": "D.S. 3925 (NAV-01)"},
            "NAV-02": {"name": "Buscador interno", "points": 14, "lineamiento": "D.S. 3925 (NAV-02)"},
            "PART-01": {"name": "Enlaces a redes sociales (mín. 2)", "points": 12, "lineamiento": "D.S. 3925 (BATS-02)"},
            "PART-02": {"name": "Enlace a app mensajería", "points": 10, "lineamiento": "D.S. 3925 (BATS-03)"},
            "PART-03": {"name": "Enlace a correo electrónico", "points": 10, "lineamiento": "D.S. 3925 (BATS-04)"},
            "PART-04": {"name": "Enlace a teléfono", "points": 8, "lineamiento": "D.S. 3925 (BATS-05)"},
            "PART-05": {"name": "Botones compartir en RRSS", "points": 4, "lineamiento": "D.S. 3925 (BATS-07)"}
        }

    def evaluate(self, extracted_content: Dict) -> List[CriteriaEvaluation]:
        """Evalúa todos los criterios de usabilidad"""
        self.clear_results()

        # Extraer datos relevantes
        metadata = extracted_content.get('metadata', {})
        semantic_elements = extracted_content.get('semantic_elements', {})
        links = extracted_content.get('links', {})
        forms = extracted_content.get('forms', {})
        text_corpus = extracted_content.get('text_corpus', {})

        # Evaluar cada criterio
        self.add_result(self._evaluar_iden01(metadata))
        self.add_result(self._evaluar_iden02(text_corpus))
        self.add_result(self._evaluar_nav01(semantic_elements, links))
        self.add_result(self._evaluar_nav02(forms))
        self.add_result(self._evaluar_part01(text_corpus, links))
        self.add_result(self._evaluar_part02(links, text_corpus))
        self.add_result(self._evaluar_part03(links))
        self.add_result(self._evaluar_part04(links))
        self.add_result(self._evaluar_part05(links))

        return self.results

    def _evaluar_iden01(self, metadata: Dict) -> CriteriaEvaluation:
        """
        IDEN-01: Nombre institución en título
        D.S. 3925 (CONT-01) / WCAG 2.4.2

        Verifica que el <title> contenga el nombre oficial de la institución.
        Usa enfoque heurístico buscando palabras clave comunes en entidades .gob.bo
        """
        max_score = 14

        # Obtener título del sitio
        title = metadata.get('title', '').strip()

        # Palabras clave que indican institución gubernamental boliviana
        keywords_institucion = [
            'ministerio', 'agencia', 'instituto', 'servicio', 'autoridad',
            'aduana', 'agetic', 'adsib', 'ine', 'ruat',
            'gobierno', 'alcaldía', 'municipio', 'gobernación',
            'departamental', 'nacional', 'dirección', 'secretaría',
            'viceministerio', 'bolivia', 'boliviano', 'gob.bo',
            'estado plurinacional', 'entidad', 'oficina',
            'organismo', 'corporación', 'empresa pública'
        ]

        # Verificar si el título contiene alguna palabra clave
        title_lower = title.lower()
        tiene_nombre = any(keyword in title_lower for keyword in keywords_institucion)

        # Verificar longitud mínima (títulos muy cortos no son descriptivos)
        tiene_longitud = len(title) >= 10

        # Calcular score
        if tiene_nombre and tiene_longitud:
            score = max_score
            status = "pass"
            message = f"Cumple: Título '{title}' identifica la institución"
        elif tiene_longitud:
            score = max_score * 0.5  # 4 puntos
            status = "partial"
            message = f"Título '{title}' tiene longitud adecuada pero no identifica claramente la institución"
        else:
            score = 0
            status = "fail"
            message = "Título ausente o muy corto para identificar la institución"

        # Generar recomendación
        if status == "fail":
            recommendation = (
                "CRÍTICO: El <title> debe contener el nombre oficial de la institución. "
                "D.S. 3925 (CONT-01) y WCAG 2.4.2 requieren título descriptivo. "
                "Ejemplo: <title>Ministerio de Educación - Estado Plurinacional de Bolivia</title>"
            )
        elif status == "partial":
            recommendation = (
                f"El <title> actual es '{title}'. "
                f"Verificar que contenga claramente el nombre de la institución gubernamental."
            )
        else:
            recommendation = f"Cumple: Título descriptivo identifica la institución"

        return CriteriaEvaluation(
            criteria_id="IDEN-01",
            criteria_name=self.criterios["IDEN-01"]["name"],
            dimension=self.dimension,
            lineamiento=self.criterios["IDEN-01"]["lineamiento"],
            status=status,
            score=score,
            max_score=max_score,
            details={
                "title": title,
                "title_length": len(title),
                "tiene_nombre_institucion": tiene_nombre,
                "tiene_longitud_minima": tiene_longitud,
                "message": message,
                "recommendation": recommendation
            },
            evidence={
                "title_found": title if title else "Título ausente o vacío"
            }
        )

    def _evaluar_iden02(self, text_corpus: Dict) -> CriteriaEvaluation:
        """
        IDEN-02: Leyenda "Bolivia a tu servicio"
        D.S. 3925 (BATS-01) - Identificación visual obligatoria del Estado

        CRÍTICO: El texto "Bolivia a tu servicio" DEBE estar en el <header>.
        - Si está en header: PASS (10 pts)
        - Si está en otra parte (body, footer): PARTIAL (5 pts)
        - Si no existe: FAIL (0 pts)
        """
        max_score = 12
        leyenda = "bolivia a tu servicio"

        # Obtener textos de diferentes secciones
        header_text = text_corpus.get('header_text', '').lower()
        footer_text = text_corpus.get('footer_text', '').lower()
        # Usar full_text para verificar en el resto del body (excluye header/footer ya verificados)
        full_text = text_corpus.get('full_text', '').lower()

        # Flag general del crawler
        has_bolivia_service = text_corpus.get('has_bolivia_service_text', False)

        # Verificar ubicación de la leyenda
        en_header = leyenda in header_text
        en_footer = leyenda in footer_text
        en_body = leyenda in full_text  # full_text contiene todo el texto visible del body

        # Determinar score según ubicación
        if en_header:
            # Caso ideal: leyenda en header
            status = "pass"
            score = max_score
            message = "Cumple: Leyenda 'Bolivia a tu servicio' presente en <header>"
            ubicacion = "header"
        elif en_footer or en_body or has_bolivia_service:
            # Leyenda existe pero NO está en header (penalización)
            status = "partial"
            score = max_score * 0.5  # 5 puntos
            ubicaciones = []
            if en_footer:
                ubicaciones.append("footer")
            if en_body:
                ubicaciones.append("body")
            if has_bolivia_service and not (en_footer or en_body):
                ubicaciones.append("detectada por crawler")
            ubicacion = ', '.join(ubicaciones)
            message = f"Parcial: Leyenda encontrada en {ubicacion}, pero DEBE estar en <header>"
        else:
            # Leyenda no encontrada
            status = "fail"
            score = 0
            message = "No se encontró la leyenda 'Bolivia a tu servicio'"
            ubicacion = "no encontrada"

        # Generar recomendación
        if status == "fail":
            recommendation = (
                "CRÍTICO: Agregar la leyenda 'Bolivia a tu servicio' en el <header>. "
                "D.S. 3925 (BATS-01) lo requiere como identificación visual obligatoria. "
                "Ejemplo: <header><span class='leyenda'>Bolivia a tu servicio</span>...</header>"
            )
        elif status == "partial":
            recommendation = (
                f"La leyenda existe pero está en {ubicacion}. "
                f"MOVER al <header> para cumplir completamente D.S. 3925 (BATS-01). "
                f"La leyenda DEBE ser visible en la cabecera del sitio."
            )
        else:
            recommendation = "Cumple: Leyenda 'Bolivia a tu servicio' correctamente ubicada en header"

        return CriteriaEvaluation(
            criteria_id="IDEN-02",
            criteria_name=self.criterios["IDEN-02"]["name"],
            dimension=self.dimension,
            lineamiento=self.criterios["IDEN-02"]["lineamiento"],
            status=status,
            score=score,
            max_score=max_score,
            details={
                "leyenda_buscada": "Bolivia a tu servicio",
                "en_header": en_header,
                "en_footer": en_footer,
                "en_body": en_body,
                "ubicacion_detectada": ubicacion,
                "message": message,
                "recommendation": recommendation
            },
            evidence={
                "header_has_leyenda": en_header,
                "ubicacion": ubicacion,
                "has_bolivia_service_flag": has_bolivia_service
            }
        )

    def _evaluar_nav01(self, semantic_elements: Dict, links: Dict) -> CriteriaEvaluation:
        """
        NAV-01: Menú de navegación
        Debe existir elemento <nav> con enlaces
        """
        nav_count = self.extract_count(semantic_elements.get('nav', 0))
        total_links = links.get('total_count', 0)

        if nav_count > 0 and total_links >= 3:
            status = "pass"
            score = 16
            message = f"Menú de navegación presente con {nav_count} elemento(s) <nav>"
        elif nav_count > 0:
            status = "partial"
            score = 8
            message = "Elemento <nav> presente pero pocos enlaces"
        elif total_links >= 5:
            status = "partial"
            score = 6
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
            max_score=16,
            details={
                "nav_count": nav_count,
                "total_links": total_links,
                "message": message
            },
            evidence={
                "semantic_nav": nav_count > 0
            }
        )

    def _evaluar_nav02(self, forms: Dict) -> CriteriaEvaluation:
        """
        NAV-02: Buscador interno
        D.S. 3925 (NAV-02) - Facilita la búsqueda de contenido en el sitio
        """
        max_score = 14
        forms_list = forms.get('forms', [])
        has_search = False
        search_details = None

        for form in forms_list:
            # Verificar el action del formulario
            form_action = form.get('action', '').lower()

            if 'search' in form_action or 'buscar' in form_action or 'busqueda' in form_action:
                has_search = True
                search_details = {'type': 'form_action', 'action': form.get('action')}
                break

            inputs = form.get('inputs', [])
            for inp in inputs:
                input_type = inp.get('type', '').lower()
                input_name = inp.get('name', '').lower()
                input_placeholder = inp.get('placeholder', '').lower()
                input_id = inp.get('id', '').lower()

                if input_type == 'search':
                    has_search = True
                    search_details = {'type': 'input_search', 'name': inp.get('name')}
                    break
                if 'search' in input_name or 'buscar' in input_name or 'busqueda' in input_name or 'query' in input_name or input_name == 'q':
                    has_search = True
                    search_details = {'type': 'input_name', 'name': inp.get('name')}
                    break
                if 'buscar' in input_placeholder or 'search' in input_placeholder:
                    has_search = True
                    search_details = {'type': 'placeholder', 'placeholder': inp.get('placeholder')}
                    break
                if 'search' in input_id or 'buscar' in input_id:
                    has_search = True
                    search_details = {'type': 'input_id', 'id': inp.get('id')}
                    break

            if has_search:
                break

        if has_search:
            status = "pass"
            score = max_score
            message = "Buscador interno presente"
        else:
            status = "fail"
            score = 0
            message = "No se encontró buscador interno"

        # Generar recomendación
        if status == "fail":
            recommendation = (
                "No se encontró buscador interno. "
                "Agregar: <form action='/buscar'><input type='search' name='q' placeholder='Buscar...'></form>"
            )
        else:
            recommendation = "Cumple: Buscador interno disponible"

        return CriteriaEvaluation(
            criteria_id="NAV-02",
            criteria_name=self.criterios["NAV-02"]["name"],
            dimension=self.dimension,
            lineamiento=self.criterios["NAV-02"]["lineamiento"],
            status=status,
            score=score,
            max_score=max_score,
            details={
                "has_search": has_search,
                "search_details": search_details,
                "forms_analyzed": len(forms_list),
                "message": message,
                "recommendation": recommendation
            },
            evidence={
                "forms_count": forms.get('total_forms', 0),
                "search_found": has_search
            }
        )

    def _evaluar_part01(self, text_corpus: Dict, links: Dict) -> CriteriaEvaluation:
        """
        PART-01: Enlaces a redes sociales (mínimo 2)
        D.S. 3925 (BATS-02) - Obligatorio para participación ciudadana digital
        """
        max_score = 12

        # Dominios de redes sociales reconocidas
        social_domains = {
            'facebook': ['facebook.com', 'fb.com', 'fb.me'],
            'twitter': ['twitter.com', 'x.com', 't.co'],
            'instagram': ['instagram.com', 'instagr.am'],
            'youtube': ['youtube.com', 'youtu.be'],
            'tiktok': ['tiktok.com'],
            'linkedin': ['linkedin.com'],
            'pinterest': ['pinterest.com'],
            'mastodon': ['mastodon.social', 'mastodon'],
            'diaspora': ['diaspora']
        }

        # Buscar enlaces a redes sociales
        redes_encontradas = set()
        enlaces_rrss = []

        # Buscar en links['social']['links'] (categoría específica del crawler)
        social_links = links.get('social', {}).get('links', [])

        for link in social_links:
            href = link.get('href', '').lower()
            text = link.get('text', '')

            for red, domains in social_domains.items():
                if any(domain in href for domain in domains):
                    redes_encontradas.add(red)
                    enlaces_rrss.append({
                        'red': red.capitalize(),
                        'href': link.get('href'),
                        'text': text
                    })
                    break

        # También buscar en todos los enlaces por si el crawler no los categorizó
        all_links = links.get('links', [])
        for link in all_links:
            href = link.get('href', '').lower()
            text = link.get('text', '')

            for red, domains in social_domains.items():
                if red not in redes_encontradas:  # Solo si no se encontró ya
                    if any(domain in href for domain in domains):
                        redes_encontradas.add(red)
                        enlaces_rrss.append({
                            'red': red.capitalize(),
                            'href': link.get('href'),
                            'text': text
                        })
                        break

        # Calcular score
        count = len(redes_encontradas)

        if count >= 2:
            score = max_score
            status = "pass"
            message = f"Cumple: {count} redes sociales encontradas"
        elif count == 1:
            score = max_score * 0.5  # 4 puntos
            status = "partial"
            red_actual = list(redes_encontradas)[0].capitalize()
            message = f"Solo 1 red social ({red_actual}). Requiere mínimo 2"
        else:
            score = 0
            status = "fail"
            message = "No se encontraron enlaces a redes sociales"

        # Generar recomendación
        if status == "fail":
            recommendation = (
                "CRÍTICO: No se encontraron enlaces a redes sociales. "
                "D.S. 3925 (BATS-02) requiere MÍNIMO 2 redes sociales para participación ciudadana. "
                "Recomendado: Facebook + Twitter/X"
            )
        elif status == "partial":
            red_actual = list(redes_encontradas)[0].capitalize()
            recommendation = (
                f"Solo se encontró 1 red social ({red_actual}). "
                f"Agregar al menos 1 red social más para cumplir D.S. 3925 (BATS-02). "
                f"Sugerencias: Twitter/X, Instagram, YouTube"
            )
        else:
            redes_list = ', '.join([r.capitalize() for r in sorted(redes_encontradas)])
            recommendation = f"Cumple: {count} redes sociales ({redes_list})"

        return CriteriaEvaluation(
            criteria_id="PART-01",
            criteria_name=self.criterios["PART-01"]["name"],
            dimension=self.dimension,
            lineamiento=self.criterios["PART-01"]["lineamiento"],
            status=status,
            score=score,
            max_score=max_score,
            details={
                "redes_encontradas": list(redes_encontradas),
                "total_redes": count,
                "minimo_requerido": 2,
                "enlaces_detectados": enlaces_rrss[:5],  # Primeros 5 como evidencia
                "message": message,
                "recommendation": recommendation
            },
            evidence={
                "found_networks": [r.capitalize() for r in sorted(redes_encontradas)] if redes_encontradas else ['Ninguna red social detectada']
            }
        )

    def _evaluar_part02(self, links: Dict, text_corpus: Dict) -> CriteriaEvaluation:
        """
        PART-02: Enlace a app mensajería
        D.S. 3925 (BATS-03) - Facilita comunicación directa ciudadano-Estado
        """
        max_score = 10

        # Dominios de apps de mensajería reconocidas
        messaging_domains = {
            'whatsapp': ['wa.me', 'api.whatsapp.com', 'web.whatsapp.com', 'whatsapp.com/send'],
            'telegram': ['t.me', 'telegram.me', 'telegram.org'],
            'riot': ['riot.im', 'matrix.org'],
            'signal': ['signal.me', 'signal.org']
        }

        # Detectar apps de mensajería
        apps_encontradas = set()
        enlaces_mensajeria = []

        # Buscar en links['social']['links'] (algunas pueden estar categorizadas ahí)
        social_links = links.get('social', {}).get('links', [])

        for link in social_links:
            href = link.get('href', '').lower()
            text = link.get('text', '')

            for app, domains in messaging_domains.items():
                if any(domain in href for domain in domains):
                    apps_encontradas.add(app)
                    enlaces_mensajeria.append({
                        'app': app.capitalize(),
                        'href': link.get('href'),
                        'text': text
                    })
                    break

        # También buscar en todos los enlaces
        all_links = links.get('links', [])
        for link in all_links:
            href = link.get('href', '').lower()
            text = link.get('text', '')

            for app, domains in messaging_domains.items():
                if app not in apps_encontradas:  # Solo si no se encontró ya
                    if any(domain in href for domain in domains):
                        apps_encontradas.add(app)
                        enlaces_mensajeria.append({
                            'app': app.capitalize(),
                            'href': link.get('href'),
                            'text': text
                        })
                        break

        # Calcular score
        count = len(apps_encontradas)

        if count >= 1:
            score = max_score
            status = "pass"
            apps_list = ', '.join([a.capitalize() for a in sorted(apps_encontradas)])
            message = f"Cumple: Enlace a {apps_list} disponible"
        else:
            score = 0
            status = "fail"
            message = "No se encontró enlace a app de mensajería"

        # Generar recomendación
        if status == "fail":
            recommendation = (
                "CRÍTICO: No se encontró enlace a app de mensajería. "
                "D.S. 3925 (BATS-03) requiere WhatsApp o Telegram para comunicación directa. "
                "Ejemplo: <a href='https://wa.me/59170000000'>WhatsApp</a>"
            )
        else:
            apps_list = ', '.join([a.capitalize() for a in sorted(apps_encontradas)])
            recommendation = f"Cumple: Enlace a {apps_list} disponible"

        return CriteriaEvaluation(
            criteria_id="PART-02",
            criteria_name=self.criterios["PART-02"]["name"],
            dimension=self.dimension,
            lineamiento=self.criterios["PART-02"]["lineamiento"],
            status=status,
            score=score,
            max_score=max_score,
            details={
                "apps_encontradas": list(apps_encontradas),
                "total_apps": count,
                "minimo_requerido": 1,
                "enlaces_detectados": enlaces_mensajeria,
                "message": message,
                "recommendation": recommendation
            },
            evidence={
                "found_apps": [a.capitalize() for a in sorted(apps_encontradas)] if apps_encontradas else ['Ninguna app de mensajería detectada']
            }
        )

    def _evaluar_part03(self, links: Dict) -> CriteriaEvaluation:
        """
        PART-03: Enlace a correo electrónico
        D.S. 3925 (BATS-04) - Canal de contacto formal institucional
        """
        max_score = 10

        # Buscar enlaces mailto: en la categoría 'email' del crawler
        email_links = links.get('email', {}).get('links', [])
        emails_encontrados = []

        for link in email_links:
            href = link.get('href', '').lower()
            if 'mailto:' in href:
                # Limpiar el email (remover mailto: y query params)
                email_clean = href.replace('mailto:', '').split('?')[0].strip()
                emails_encontrados.append({
                    'email': email_clean,
                    'text': link.get('text', ''),
                    'href': link.get('href')
                })

        # También buscar en todos los enlaces por si no están categorizados
        all_links = links.get('links', [])
        for link in all_links:
            href = link.get('href', '').lower()
            if 'mailto:' in href:
                email_clean = href.replace('mailto:', '').split('?')[0].strip()
                # Evitar duplicados
                if not any(e['email'] == email_clean for e in emails_encontrados):
                    emails_encontrados.append({
                        'email': email_clean,
                        'text': link.get('text', ''),
                        'href': link.get('href')
                    })

        # Calcular score
        count = len(emails_encontrados)

        if count >= 1:
            score = max_score
            status = "pass"
            emails_list = ', '.join([e['email'] for e in emails_encontrados[:3]])
            message = f"Cumple: {count} enlace(s) mailto: ({emails_list})"
        else:
            score = 0
            status = "fail"
            message = "No se encontró enlace a correo electrónico"

        # Generar recomendación
        if status == "fail":
            recommendation = (
                "CRÍTICO: No se encontró enlace de correo electrónico institucional. "
                "D.S. 3925 (BATS-04) requiere enlace mailto: para contacto formal. "
                "Ejemplo: <a href='mailto:contacto@institucion.gob.bo'>Contáctenos</a>"
            )
        else:
            emails_list = ', '.join([e['email'] for e in emails_encontrados[:3]])
            recommendation = f"Cumple: {count} enlace(s) de email ({emails_list})"

        return CriteriaEvaluation(
            criteria_id="PART-03",
            criteria_name=self.criterios["PART-03"]["name"],
            dimension=self.dimension,
            lineamiento=self.criterios["PART-03"]["lineamiento"],
            status=status,
            score=score,
            max_score=max_score,
            details={
                "emails_encontrados": count,
                "minimo_requerido": 1,
                "ejemplos_detectados": emails_encontrados[:3],
                "message": message,
                "recommendation": recommendation
            },
            evidence={
                "found_emails": [e['email'] for e in emails_encontrados[:3]] if emails_encontrados else ['Ningún enlace mailto: detectado']
            }
        )

    def _evaluar_part04(self, links: Dict) -> CriteriaEvaluation:
        """
        PART-04: Enlace a teléfono
        D.S. 3925 (BATS-05) - Canal directo, especialmente para adultos mayores
        """
        max_score = 8

        # Buscar enlaces tel: en la categoría 'phone' del crawler
        phone_links = links.get('phone', {}).get('links', [])
        telefonos_encontrados = []

        for link in phone_links:
            href = link.get('href', '').lower()
            if 'tel:' in href:
                # Limpiar el teléfono (remover tel: y espacios)
                phone_clean = href.replace('tel:', '').strip()
                telefonos_encontrados.append({
                    'telefono': phone_clean,
                    'text': link.get('text', ''),
                    'href': link.get('href')
                })

        # También buscar en todos los enlaces por si no están categorizados
        all_links = links.get('links', [])
        for link in all_links:
            href = link.get('href', '').lower()
            if 'tel:' in href:
                phone_clean = href.replace('tel:', '').strip()
                # Evitar duplicados
                if not any(t['telefono'] == phone_clean for t in telefonos_encontrados):
                    telefonos_encontrados.append({
                        'telefono': phone_clean,
                        'text': link.get('text', ''),
                        'href': link.get('href')
                    })

        # Calcular score
        count = len(telefonos_encontrados)

        if count >= 1:
            score = max_score
            status = "pass"
            phones_list = ', '.join([t['telefono'] for t in telefonos_encontrados[:3]])
            message = f"Cumple: {count} enlace(s) tel: ({phones_list})"
        else:
            score = 0
            status = "fail"
            message = "No se encontró enlace a teléfono"

        # Generar recomendación
        if status == "fail":
            recommendation = (
                "CRÍTICO: No se encontró enlace telefónico institucional. "
                "D.S. 3925 (BATS-05) requiere enlace tel: para contacto directo. "
                "Ejemplo: <a href='tel:+59122000000'>Llámenos: (2) 2000000</a>"
            )
        else:
            phones_list = ', '.join([t['telefono'] for t in telefonos_encontrados[:3]])
            recommendation = f"Cumple: {count} enlace(s) telefónico(s) ({phones_list})"

        return CriteriaEvaluation(
            criteria_id="PART-04",
            criteria_name=self.criterios["PART-04"]["name"],
            dimension=self.dimension,
            lineamiento=self.criterios["PART-04"]["lineamiento"],
            status=status,
            score=score,
            max_score=max_score,
            details={
                "telefonos_encontrados": count,
                "minimo_requerido": 1,
                "ejemplos_detectados": telefonos_encontrados[:3],
                "message": message,
                "recommendation": recommendation
            },
            evidence={
                "found_phones": [t['telefono'] for t in telefonos_encontrados[:3]] if telefonos_encontrados else ['Ningún enlace tel: detectado']
            }
        )

    def _evaluar_part05(self, links: Dict) -> CriteriaEvaluation:
        """
        PART-05: Botones compartir en RRSS
        D.S. 3925 (BATS-07) - Facilita difusión de información pública
        """
        max_score = 4

        # URLs de compartir en redes sociales
        share_url_patterns = [
            'facebook.com/sharer',
            'twitter.com/intent/tweet',
            'twitter.com/share',
            'x.com/intent/tweet',
            'linkedin.com/shareArticle',
            'linkedin.com/share',
            'pinterest.com/pin/create',
            'wa.me',
            'api.whatsapp.com/send',
            't.me/share',
            'reddit.com/submit',
            'addthis.com',
            'sharethis.com'
        ]

        # Buscar botones de compartir en enlaces
        botones_compartir = []

        # Buscar en links['social']['links']
        social_links = links.get('social', {}).get('links', [])
        for link in social_links:
            href = link.get('href', '').lower()
            text = link.get('text', '').lower()

            if any(pattern in href for pattern in share_url_patterns):
                botones_compartir.append({
                    'tipo': 'share_url',
                    'href': link.get('href'),
                    'text': link.get('text', '')
                })
                continue

            if any(word in text for word in ['compartir', 'share', 'difundir']):
                botones_compartir.append({
                    'tipo': 'share_text',
                    'href': link.get('href'),
                    'text': link.get('text', '')
                })

        # También buscar en todos los enlaces
        all_links = links.get('links', [])
        for link in all_links:
            href = link.get('href', '').lower()
            text = link.get('text', '').lower()

            # Evitar duplicados
            if any(b['href'] == link.get('href') for b in botones_compartir):
                continue

            if any(pattern in href for pattern in share_url_patterns):
                botones_compartir.append({
                    'tipo': 'share_url',
                    'href': link.get('href'),
                    'text': link.get('text', '')
                })
                continue

            if any(word in text for word in ['compartir', 'share']):
                # Verificar que no sea un enlace normal
                if 'facebook' in href or 'twitter' in href or 'linkedin' in href:
                    botones_compartir.append({
                        'tipo': 'share_text',
                        'href': link.get('href'),
                        'text': link.get('text', '')
                    })

        # Calcular score
        count = len(botones_compartir)

        if count >= 1:
            score = max_score
            status = "pass"
            message = f"Cumple: {count} botón(es) de compartir encontrado(s)"
        else:
            score = 0
            status = "fail"
            message = "No se encontraron botones para compartir en RRSS"

        # Generar recomendación
        if status == "fail":
            recommendation = (
                "Agregar botones para compartir contenido en redes sociales. "
                "D.S. 3925 (BATS-07) facilita la difusión de información pública. "
                "Ejemplo: <a href='https://facebook.com/sharer/sharer.php?u={URL}'>Compartir</a>"
            )
        else:
            tipos = list(set([b['tipo'] for b in botones_compartir]))
            recommendation = f"Cumple: {count} botón(es) de compartir ({', '.join(tipos)})"

        return CriteriaEvaluation(
            criteria_id="PART-05",
            criteria_name=self.criterios["PART-05"]["name"],
            dimension=self.dimension,
            lineamiento=self.criterios["PART-05"]["lineamiento"],
            status=status,
            score=score,
            max_score=max_score,
            details={
                "botones_encontrados": count,
                "tipos_detectados": list(set([b['tipo'] for b in botones_compartir])),
                "ejemplos": botones_compartir[:3],
                "message": message,
                "recommendation": recommendation
            },
            evidence={
                "found_share_buttons": [f"{b['tipo']}: {b.get('text', '')[:30]}" for b in botones_compartir[:3]] if botones_compartir else ['Ningún botón de compartir detectado']
            }
        )

    # =========================================================================
    # CÓDIGO COMENTADO - Formularios de contacto (guardado por si se necesita)
    # =========================================================================
    # def _evaluar_formularios_contacto(self, forms: Dict) -> CriteriaEvaluation:
    #     """
    #     Criterio removido de Tabla 12 - Guardado como referencia
    #     Evalúa presencia de formularios de contacto
    #     """
    #     forms_list = forms.get('forms', [])
    #     total_forms = forms.get('total_forms', 0)
    #     has_contact_form = False
    #
    #     for form in forms_list:
    #         inputs = form.get('inputs', [])
    #         has_name = False
    #         has_email = False
    #         has_message = False
    #
    #         for inp in inputs:
    #             input_type = inp.get('type', '').lower()
    #             input_name = inp.get('name', '').lower()
    #
    #             if 'name' in input_name or 'nombre' in input_name:
    #                 has_name = True
    #             if input_type == 'email' or 'email' in input_name or 'correo' in input_name:
    #                 has_email = True
    #             if 'message' in input_name or 'mensaje' in input_name or 'consulta' in input_name:
    #                 has_message = True
    #
    #         if (has_name or has_email) and has_message:
    #             has_contact_form = True
    #             break
    #
    #     # Scoring: pass=8pts, partial=4pts, fail=0pts
    #     # ... resto de la implementación ...
