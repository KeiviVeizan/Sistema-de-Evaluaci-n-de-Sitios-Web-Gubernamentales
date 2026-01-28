"""
Evaluador de Soberania Digital segun D.S. 3925

Evalua 4 criterios de soberania digital para sitios gubernamentales bolivianos:
- PROH-01: Sin trackers publicitarios
- PROH-02: Sin CDNs externos no autorizados
- PROH-03: Hosting en dominio nacional (.gob.bo)
- PROH-04: Sin widgets invasivos de redes sociales

Este evaluador representa el 10% del score total de la evaluacion.
"""
import logging
from typing import Dict, List, Any, Optional
from urllib.parse import urlparse

from .base_evaluator import BaseEvaluator, CriteriaEvaluation

logger = logging.getLogger(__name__)


class EvaluadorSoberania(BaseEvaluator):
    """
    Evaluador de criterios de soberania digital segun D.S. 3925.

    Evalua 4 criterios relacionados con:
    - Ausencia de trackers publicitarios (Google Analytics, Facebook Pixel)
    - Independencia de CDNs externos no gubernamentales
    - Hosting en dominio nacional boliviano
    - Sin widgets invasivos de redes sociales

    Peso en evaluacion total: 10%
    """

    # Dominios de trackers prohibidos
    TRACKING_DOMAINS = [
        'google-analytics.com',
        'googletagmanager.com',
        'analytics.google.com',
        'gtag',
        'ga.js',
        'gtm.js',
        'facebook.net',
        'connect.facebook.net',
        'facebook.com/tr',
        'doubleclick.net',
        'googleadservices.com',
        'hotjar.com',
        'crazyegg.com',
        'mixpanel.com',
        'segment.io',
        'heap.io',
        'amplitude.com',
        'clarity.ms',
        'newrelic.com',
        'nr-data.net',
        'pixel',
        'tracker'
    ]

    # CDNs externos permitidos (excepciones justificadas)
    ALLOWED_CDNS = [
        'fonts.googleapis.com',
        'fonts.gstatic.com',
    ]

    # Widgets invasivos de redes sociales
    SOCIAL_WIDGETS = [
        'facebook.com/plugins',
        'platform.twitter.com',
        'twitter.com/widgets',
        'instagram.com/embed',
        'youtube.com/embed',
        'linkedin.com/embed',
        'tiktok.com/embed',
        'pinterest.com/pin',
        'connect.facebook.net',
        'platform-api.sharethis',
    ]

    # CDNs comunmente usados (para deteccion)
    COMMON_CDNS = [
        'jquery.com',
        'jsdelivr.net',
        'bootstrapcdn.com',
        'cloudflare.com',
        'cdnjs.cloudflare.com',
        'unpkg.com',
        'amazonaws.com',
        'akamaihd.net',
        'fastly.net',
        'maxcdn.com'
    ]

    def __init__(self):
        super().__init__(dimension='sovereignty')

        # Definicion de criterios
        self.criterios = {
            'PROH-01': {
                'name': 'Sin trackers publicitarios',
                'lineamiento': 'D.S. 3925 Art. 7 - Proteccion de datos ciudadanos',
                'max_score': 10.0
            },
            'PROH-02': {
                'name': 'Sin CDNs externos no autorizados',
                'lineamiento': 'D.S. 3925 Art. 5 - Soberania tecnologica',
                'max_score': 10.0
            },
            'PROH-03': {
                'name': 'Hosting nacional (.gob.bo)',
                'lineamiento': 'D.S. 3925 Art. 4 - Dominio gubernamental boliviano',
                'max_score': 10.0
            },
            'PROH-04': {
                'name': 'Sin widgets invasivos de redes sociales',
                'lineamiento': 'D.S. 3925 Art. 8 - Privacidad de usuarios',
                'max_score': 10.0
            }
        }

    def evaluate(self, extracted_content: Dict[str, Any]) -> List[CriteriaEvaluation]:
        """
        Evalua todos los criterios de soberania digital.

        Args:
            extracted_content: Contenido extraido por el crawler con:
                - external_resources: {
                    trackers: {found: List, count: int},
                    cdn: {external: List, count: int},
                    iframes: {external: List, count: int}
                  }
                - url: str (URL del sitio)
                - metadata: {domain: str}

        Returns:
            List[CriteriaEvaluation]: Lista de evaluaciones por criterio
        """
        self.clear_results()

        # Evaluar cada criterio
        self.add_result(self._evaluar_proh01(extracted_content))
        self.add_result(self._evaluar_proh02(extracted_content))
        self.add_result(self._evaluar_proh03(extracted_content))
        self.add_result(self._evaluar_proh04(extracted_content))

        return self.results

    # ========================================================================
    # PROH-01: Sin trackers publicitarios
    # ========================================================================

    def _evaluar_proh01(self, content: Dict) -> CriteriaEvaluation:
        """
        PROH-01: Sin trackers publicitarios

        Verifica que el sitio NO use:
        - Google Analytics / Google Tag Manager
        - Facebook Pixel / Meta Pixel
        - Otros trackers publicitarios

        Score: 10.0 si cumple (sin trackers), 0.0 si tiene trackers
        """
        external_resources = content.get('external_resources', {})
        trackers_data = external_resources.get('trackers', {})

        trackers_found = trackers_data.get('found', [])
        tracker_count = trackers_data.get('count', 0)

        # Clasificar trackers por severidad
        critical_trackers = []
        other_trackers = []

        for tracker in trackers_found:
            tracker_name = tracker.get('tracker', '') if isinstance(tracker, dict) else str(tracker)
            tracker_lower = tracker_name.lower()

            if any(critical in tracker_lower for critical in ['google-analytics', 'googletagmanager', 'gtag', 'facebook', 'doubleclick']):
                critical_trackers.append(tracker_name)
            else:
                other_trackers.append(tracker_name)

        # Calcular score
        has_trackers = tracker_count > 0

        if not has_trackers:
            status = 'pass'
            score = 10.0
            message = 'Sin trackers publicitarios detectados'
        elif len(critical_trackers) > 0:
            status = 'fail'
            score = 0.0
            message = f'Trackers criticos detectados: {len(critical_trackers)}'
        else:
            status = 'fail'
            score = 2.0
            message = f'Trackers menores detectados: {len(other_trackers)}'

        # Generar recomendacion educativa
        recomendacion = self._generar_recomendacion_trackers(
            critical_trackers, other_trackers, tracker_count
        )

        return CriteriaEvaluation(
            criteria_id='PROH-01',
            criteria_name=self.criterios['PROH-01']['name'],
            dimension=self.dimension,
            lineamiento=self.criterios['PROH-01']['lineamiento'],
            status=status,
            score=score,
            max_score=10.0,
            details={
                'trackers_found': trackers_found,
                'critical_trackers': critical_trackers,
                'other_trackers': other_trackers,
                'total_count': tracker_count,
                'compliant': not has_trackers,
                'message': message
            },
            evidence={
                'trackers_detectados': [t.get('tracker', str(t)) if isinstance(t, dict) else str(t) for t in trackers_found] or ['Ninguno'],
                'recomendacion': recomendacion
            }
        )

    def _generar_recomendacion_trackers(
        self,
        critical: List[str],
        other: List[str],
        total: int
    ) -> Dict[str, Any]:
        """Genera recomendacion educativa para trackers"""
        if total == 0:
            return {
                'estado': 'CUMPLE',
                'mensaje': 'El sitio respeta la privacidad de los ciudadanos al no usar trackers publicitarios.'
            }

        return {
            'estado': 'NO CUMPLE',
            'problema': f'Se detectaron {total} tracker(s) publicitario(s) que recopilan datos de ciudadanos sin consentimiento.',
            'por_que_mal': '''Los trackers publicitarios (Google Analytics, Facebook Pixel):
1. Recopilan datos personales de ciudadanos sin consentimiento explicito
2. Envian informacion a servidores extranjeros (violando soberania de datos)
3. Permiten perfilamiento de ciudadanos por empresas privadas
4. Incumplen el D.S. 3925 sobre proteccion de datos gubernamentales''',
            'como_corregir': [
                '1. ELIMINAR inmediatamente Google Analytics y scripts de googletagmanager.com',
                '2. ELIMINAR Facebook Pixel y cualquier script de facebook.net/connect.facebook.net',
                '3. ALTERNATIVA: Usar Matomo (https://matomo.org) instalado en servidor propio .gob.bo',
                '4. ALTERNATIVA: Usar analisis de logs del servidor Apache/Nginx (GoAccess, AWStats)',
                '5. Si necesita metricas, usar herramientas de ADSIB o AGETIC'
            ],
            'ejemplo_antes': '''<!-- INCORRECTO: Trackers que violan privacidad -->
<script async src="https://www.googletagmanager.com/gtag/js?id=UA-XXXXX"></script>
<script>
  gtag('config', 'UA-XXXXX');
</script>
<script>
  fbq('init', '123456789');  <!-- Facebook Pixel -->
</script>''',
            'ejemplo_despues': '''<!-- CORRECTO: Sin trackers externos -->
<!-- Opcion 1: Matomo auto-hospedado -->
<script src="https://analytics.midominio.gob.bo/matomo.js"></script>

<!-- Opcion 2: Sin tracking (analizar logs del servidor) -->
<!-- No se requiere ningun script de tracking -->''',
            'referencias': [
                'D.S. 3925 Art. 7: Proteccion de datos de ciudadanos',
                'RGPD Art. 6: Consentimiento para tratamiento de datos',
                'Matomo: https://matomo.org/free-software/'
            ],
            'trackers_criticos': critical,
            'trackers_otros': other
        }

    # ========================================================================
    # PROH-02: Sin CDNs externos no autorizados
    # ========================================================================

    def _evaluar_proh02(self, content: Dict) -> CriteriaEvaluation:
        """
        PROH-02: Sin CDNs externos no autorizados

        Verifica que el sitio no dependa de CDNs externos para recursos criticos.

        PERMITIDO:
        - fonts.googleapis.com (fuentes)
        - fonts.gstatic.com (fuentes)

        PROHIBIDO:
        - CDNs de terceros para recursos propios
        - Dependencias criticas en servidores externos

        Score: 10.0 si 0 externos, 7.0 si 1-2, 4.0 si 3-5, 0.0 si >5
        """
        external_resources = content.get('external_resources', {})
        cdn_data = external_resources.get('cdn', {})

        external_cdns = cdn_data.get('external', [])

        # Filtrar CDNs no permitidos
        unauthorized_cdns = []
        allowed_cdns_used = []

        for cdn in external_cdns:
            domain = cdn.get('domain', '') if isinstance(cdn, dict) else str(cdn)
            domain_lower = domain.lower()

            # Verificar si esta en lista de permitidos
            is_allowed = any(allowed in domain_lower for allowed in self.ALLOWED_CDNS)

            if is_allowed:
                allowed_cdns_used.append(domain)
            else:
                is_common_cdn = any(cdn_name in domain_lower for cdn_name in self.COMMON_CDNS)
                unauthorized_cdns.append({
                    'domain': domain,
                    'type': cdn.get('type', 'unknown') if isinstance(cdn, dict) else 'unknown',
                    'is_common_cdn': is_common_cdn
                })

        # Calcular score
        cdn_count = len(unauthorized_cdns)

        if cdn_count == 0:
            status = 'pass'
            score = 10.0
            message = 'Sin dependencias de CDNs externos no autorizados'
        elif cdn_count <= 2:
            status = 'partial'
            score = 7.0
            message = f'Pocas dependencias externas ({cdn_count} CDNs)'
        elif cdn_count <= 5:
            status = 'partial'
            score = 4.0
            message = f'Varias dependencias externas ({cdn_count} CDNs)'
        else:
            status = 'fail'
            score = 0.0
            message = f'Demasiadas dependencias externas ({cdn_count} CDNs)'

        # Generar recomendacion educativa
        recomendacion = self._generar_recomendacion_cdns(
            unauthorized_cdns, allowed_cdns_used, cdn_count
        )

        return CriteriaEvaluation(
            criteria_id='PROH-02',
            criteria_name=self.criterios['PROH-02']['name'],
            dimension=self.dimension,
            lineamiento=self.criterios['PROH-02']['lineamiento'],
            status=status,
            score=score,
            max_score=10.0,
            details={
                'unauthorized_cdns': unauthorized_cdns,
                'allowed_cdns_used': list(set(allowed_cdns_used)),
                'unauthorized_count': cdn_count,
                'message': message
            },
            evidence={
                'cdns_no_autorizados': [c['domain'] for c in unauthorized_cdns] or ['Ninguno'],
                'cdns_permitidos_usados': list(set(allowed_cdns_used)) or ['Ninguno'],
                'recomendacion': recomendacion
            }
        )

    def _generar_recomendacion_cdns(
        self,
        unauthorized: List[Dict],
        allowed: List[str],
        count: int
    ) -> Dict[str, Any]:
        """Genera recomendacion educativa para CDNs"""
        if count == 0:
            return {
                'estado': 'CUMPLE',
                'mensaje': 'El sitio es independiente de CDNs externos no autorizados.'
            }

        domains = [c['domain'] for c in unauthorized]

        return {
            'estado': 'NO CUMPLE' if count > 5 else 'PARCIAL',
            'problema': f'El sitio depende de {count} CDN(s) externo(s): {", ".join(domains[:5])}',
            'por_que_mal': '''Depender de CDNs externos causa:
1. DISPONIBILIDAD: Si el CDN cae, su sitio deja de funcionar
2. SEGURIDAD: El CDN puede ser comprometido e inyectar malware
3. PRIVACIDAD: Los CDNs rastrean a los usuarios de su sitio
4. SOBERANIA: Datos y recursos dependen de infraestructura extranjera
5. RENDIMIENTO: Latencia adicional por servidores lejanos''',
            'como_corregir': [
                '1. DESCARGAR los archivos JS/CSS de los CDNs externos',
                '2. HOSPEDAR localmente en su servidor .gob.bo',
                '3. ACTUALIZAR las referencias en el HTML:',
                '   - Cambiar src="https://cdn.example.com/lib.js"',
                '   - Por src="/assets/js/lib.js"',
                '4. CONFIGURAR cache apropiado para archivos estaticos',
                '5. USAR un CDN gubernamental si disponible (AGETIC/ADSIB)'
            ],
            'ejemplo_antes': '''<!-- INCORRECTO: Dependencias externas -->
<script src="https://code.jquery.com/jquery-3.6.0.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.min.js"></script>
<link href="https://cdn.example.com/styles.css" rel="stylesheet">''',
            'ejemplo_despues': '''<!-- CORRECTO: Recursos locales -->
<script src="/assets/js/jquery-3.6.0.min.js"></script>
<script src="/assets/js/bootstrap.min.js"></script>
<link href="/assets/css/styles.css" rel="stylesheet">

<!-- Las fuentes de Google SI estan permitidas -->
<link href="https://fonts.googleapis.com/css2?family=Roboto&display=swap" rel="stylesheet">''',
            'referencias': [
                'D.S. 3925 Art. 5: Soberania tecnologica',
                'OWASP: Third-Party JavaScript Management',
                'Web.dev: Loading Third-Party JavaScript'
            ],
            'cdns_problematicos': domains
        }

    # ========================================================================
    # PROH-03: Hosting nacional (.gob.bo)
    # ========================================================================

    def _evaluar_proh03(self, content: Dict) -> CriteriaEvaluation:
        """
        PROH-03: Hosting en dominio nacional

        Verifica que el sitio use dominio .gob.bo

        Score:
        - 10.0 si .gob.bo
        - 5.0 si .bo (boliviano pero no gubernamental)
        - 0.0 si otro dominio
        """
        url = content.get('url', '')
        metadata = content.get('metadata', {})
        domain = metadata.get('domain', '')

        # Si no hay domain en metadata, extraerlo de la URL
        if not domain and url:
            parsed = urlparse(url)
            domain = parsed.netloc.lower()

        domain_lower = domain.lower()
        url_lower = url.lower()

        # Verificar tipo de dominio
        if '.gob.bo' in domain_lower or '.gob.bo' in url_lower:
            status = 'pass'
            score = 10.0
            tipo_dominio = 'gubernamental_boliviano'
            message = 'Dominio gubernamental boliviano (.gob.bo)'
        elif '.bo' in domain_lower or '.bo' in url_lower:
            status = 'partial'
            score = 5.0
            tipo_dominio = 'boliviano_no_gubernamental'
            message = 'Dominio boliviano (.bo) pero no gubernamental'
        else:
            status = 'fail'
            score = 0.0
            tipo_dominio = 'extranjero'
            message = f'Dominio no boliviano ({domain})'

        # Generar recomendacion
        recomendacion = self._generar_recomendacion_hosting(status, domain, tipo_dominio)

        return CriteriaEvaluation(
            criteria_id='PROH-03',
            criteria_name=self.criterios['PROH-03']['name'],
            dimension=self.dimension,
            lineamiento=self.criterios['PROH-03']['lineamiento'],
            status=status,
            score=score,
            max_score=10.0,
            details={
                'url': url,
                'domain': domain,
                'tipo_dominio': tipo_dominio,
                'message': message,
                'nota': 'Verificacion de IP/geolocalizacion no implementada'
            },
            evidence={
                'dominio_detectado': domain or 'No detectado',
                'tipo': tipo_dominio,
                'recomendacion': recomendacion
            }
        )

    def _generar_recomendacion_hosting(
        self,
        status: str,
        domain: str,
        tipo: str
    ) -> Dict[str, Any]:
        """Genera recomendacion educativa para hosting"""
        if status == 'pass':
            return {
                'estado': 'CUMPLE',
                'mensaje': f'El sitio usa correctamente el dominio gubernamental boliviano: {domain}'
            }

        if status == 'partial':
            return {
                'estado': 'PARCIAL',
                'problema': f'El sitio usa dominio .bo pero no .gob.bo: {domain}',
                'como_corregir': [
                    '1. Solicitar dominio .gob.bo a traves de AGETIC',
                    '2. Configurar redireccion del dominio actual al nuevo .gob.bo',
                    '3. Actualizar referencias internas al nuevo dominio'
                ],
                'referencias': ['D.S. 3925 Art. 4: Uso obligatorio de dominio .gob.bo para entidades gubernamentales']
            }

        return {
            'estado': 'NO CUMPLE',
            'problema': f'CRITICO: El sitio usa dominio extranjero: {domain}',
            'por_que_mal': '''Usar dominio no gubernamental boliviano causa:
1. LEGAL: Incumplimiento del D.S. 3925 (obligatorio .gob.bo)
2. CONFIANZA: Los ciudadanos no pueden verificar autenticidad
3. SOBERANIA: El dominio esta controlado por entidad extranjera
4. SEGURIDAD: Mayor riesgo de phishing y suplantacion''',
            'como_corregir': [
                '1. URGENTE: Solicitar dominio .gob.bo a AGETIC',
                '2. Migrar el sitio al nuevo dominio',
                '3. Configurar SSL/TLS para el nuevo dominio',
                '4. Establecer redirecciones 301 desde el dominio antiguo',
                '5. Actualizar todas las referencias y enlaces'
            ],
            'referencias': [
                'D.S. 3925 Art. 4: Dominio gubernamental boliviano obligatorio',
                'NB/ISO 27001: Control de activos de informacion',
                'AGETIC: Procedimiento de solicitud de dominios .gob.bo'
            ]
        }

    # ========================================================================
    # PROH-04: Sin widgets invasivos de redes sociales
    # ========================================================================

    def _evaluar_proh04(self, content: Dict) -> CriteriaEvaluation:
        """
        PROH-04: Sin widgets invasivos de redes sociales

        Verifica que el sitio NO use widgets pesados que:
        - Rastrean usuarios
        - Cargan scripts externos de redes sociales
        - Afectan rendimiento

        PERMITIDO: Enlaces simples a redes sociales
        PROHIBIDO: Embeds de Facebook, Twitter widgets, YouTube embeds, etc.

        Score:
        - 10.0 si solo links simples (sin embeds)
        - 5.0 si embeds ligeros (1-2)
        - 0.0 si widgets pesados (>2)
        """
        external_resources = content.get('external_resources', {})
        iframes_data = external_resources.get('iframes', {})
        cdn_data = external_resources.get('cdn', {})

        external_iframes = iframes_data.get('external', [])
        external_cdns = cdn_data.get('external', [])

        # Buscar widgets de redes sociales en iframes
        social_widgets_found = []

        for iframe in external_iframes:
            src = iframe.get('absolute_src', '') if isinstance(iframe, dict) else str(iframe)
            domain = iframe.get('domain', '') if isinstance(iframe, dict) else ''
            src_lower = src.lower()

            for widget_pattern in self.SOCIAL_WIDGETS:
                if widget_pattern in src_lower:
                    social_widgets_found.append({
                        'type': 'iframe',
                        'source': src,
                        'domain': domain,
                        'widget': widget_pattern
                    })
                    break

        # Buscar widgets en scripts (SDKs de redes sociales)
        for cdn in external_cdns:
            src = cdn.get('absolute_src', '') if isinstance(cdn, dict) else str(cdn)
            cdn_type = cdn.get('type', '') if isinstance(cdn, dict) else ''

            if cdn_type == 'script':
                src_lower = src.lower()
                for widget_pattern in self.SOCIAL_WIDGETS:
                    if widget_pattern in src_lower:
                        social_widgets_found.append({
                            'type': 'script',
                            'source': src,
                            'widget': widget_pattern
                        })
                        break

        # Calcular score
        widget_count = len(social_widgets_found)

        if widget_count == 0:
            status = 'pass'
            score = 10.0
            message = 'Sin widgets invasivos de redes sociales'
        elif widget_count <= 2:
            status = 'partial'
            score = 5.0
            message = f'Algunos widgets sociales detectados ({widget_count})'
        else:
            status = 'fail'
            score = 0.0
            message = f'Demasiados widgets sociales ({widget_count})'

        # Generar recomendacion educativa
        recomendacion = self._generar_recomendacion_widgets(
            social_widgets_found, widget_count
        )

        return CriteriaEvaluation(
            criteria_id='PROH-04',
            criteria_name=self.criterios['PROH-04']['name'],
            dimension=self.dimension,
            lineamiento=self.criterios['PROH-04']['lineamiento'],
            status=status,
            score=score,
            max_score=10.0,
            details={
                'widgets_found': social_widgets_found,
                'widget_count': widget_count,
                'message': message,
                'nota': 'Enlaces simples a redes sociales SI estan permitidos'
            },
            evidence={
                'widgets_detectados': [w.get('widget', 'unknown') for w in social_widgets_found] or ['Ninguno'],
                'fuentes': [w.get('source', '')[:100] for w in social_widgets_found] or ['N/A'],
                'recomendacion': recomendacion
            }
        )

    def _generar_recomendacion_widgets(
        self,
        widgets: List[Dict],
        count: int
    ) -> Dict[str, Any]:
        """Genera recomendacion educativa para widgets sociales"""
        if count == 0:
            return {
                'estado': 'CUMPLE',
                'mensaje': 'El sitio usa enlaces simples a redes sociales sin widgets invasivos.'
            }

        widget_types = list(set(w.get('widget', 'unknown') for w in widgets))

        return {
            'estado': 'NO CUMPLE' if count > 2 else 'PARCIAL',
            'problema': f'Se detectaron {count} widget(s) invasivo(s) de redes sociales: {", ".join(widget_types)}',
            'por_que_mal': '''Los widgets de redes sociales (Facebook Like, Twitter Feed, YouTube embed):
1. PRIVACIDAD: Rastrean a todos los visitantes, incluso sin interactuar
2. RENDIMIENTO: Cargan megabytes de JavaScript externo
3. DEPENDENCIA: Si la red social tiene problemas, afecta su sitio
4. SEGURIDAD: Pueden inyectar contenido no controlado
5. ACCESIBILIDAD: Muchos widgets no son accesibles para personas con discapacidad''',
            'como_corregir': [
                '1. REEMPLAZAR embeds de YouTube por enlaces simples:',
                '   <a href="https://youtube.com/watch?v=ID">Ver video en YouTube</a>',
                '',
                '2. REEMPLAZAR widgets de Facebook por enlaces:',
                '   <a href="https://facebook.com/pagina">Siguenos en Facebook</a>',
                '',
                '3. REEMPLAZAR Twitter widgets por enlaces:',
                '   <a href="https://twitter.com/cuenta">@cuenta en Twitter</a>',
                '',
                '4. Si necesita mostrar contenido, usar capturas de pantalla estaticas',
                '5. Agrupar enlaces sociales en una seccion "Redes Sociales"'
            ],
            'ejemplo_antes': '''<!-- INCORRECTO: Widgets invasivos -->
<iframe src="https://www.facebook.com/plugins/page.php?href=..." width="340"></iframe>
<iframe src="https://www.youtube.com/embed/VIDEO_ID" frameborder="0"></iframe>
<a class="twitter-timeline" href="https://twitter.com/cuenta">Tweets</a>
<script src="https://platform.twitter.com/widgets.js"></script>''',
            'ejemplo_despues': '''<!-- CORRECTO: Enlaces simples -->
<section class="redes-sociales">
  <h2>Siguenos en redes sociales</h2>
  <ul>
    <li><a href="https://facebook.com/institucion" target="_blank" rel="noopener">
      Facebook</a></li>
    <li><a href="https://twitter.com/institucion" target="_blank" rel="noopener">
      Twitter</a></li>
    <li><a href="https://youtube.com/channel/ID" target="_blank" rel="noopener">
      Canal de YouTube</a></li>
  </ul>
</section>''',
            'referencias': [
                'D.S. 3925 Art. 8: Privacidad de usuarios en sitios gubernamentales',
                'WCAG 2.1: Third-party content accessibility',
                'Web.dev: Loading Third-Party JavaScript'
            ],
            'widgets_problematicos': widget_types
        }


# Funcion de conveniencia para uso directo
def evaluar_soberania(extracted_content: Dict[str, Any]) -> Dict[str, Any]:
    """
    Funcion de conveniencia para evaluar soberania digital.

    Args:
        extracted_content: Contenido extraido por el crawler

    Returns:
        Dict con resultados de evaluacion
    """
    evaluador = EvaluadorSoberania()
    results = evaluador.evaluate(extracted_content)
    dimension_score = evaluador.get_dimension_score()

    return {
        'dimension': 'sovereignty',
        'score': dimension_score['percentage'],
        'total_score': dimension_score['total_score'],
        'max_score': dimension_score['max_score'],
        'criteria_results': [r.to_dict() for r in results],
        'summary': {
            'passed': dimension_score['passed'],
            'failed': dimension_score['failed'],
            'partial': dimension_score['partial']
        }
    }
