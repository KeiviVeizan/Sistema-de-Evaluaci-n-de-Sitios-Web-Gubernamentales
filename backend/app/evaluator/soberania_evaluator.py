"""
Evaluador de Soberania Digital segun D.S. 3925

Evalua 4 criterios de soberania digital para sitios gubernamentales bolivianos:
- PROH-01: Sin iframes externos (evitar dependencia y filtracion de datos)
- PROH-02: Sin CDNs externos no autorizados (soberania tecnologica)
- PROH-03: Sin fuentes externas (tipografias auto-hospedadas)
- PROH-04: Sin trackers externos (proteccion de privacidad ciudadana)

Este evaluador representa el 10% del score total de la evaluacion.
"""
import logging
from typing import Dict, List, Any
from .base_evaluator import BaseEvaluator, CriteriaEvaluation

logger = logging.getLogger(__name__)


class EvaluadorSoberania(BaseEvaluator):
    """
    Evaluador de criterios de soberania digital segun D.S. 3925.

    Evalua 4 criterios relacionados con:
    - Ausencia de iframes externos (dependencia y filtracion)
    - Independencia de CDNs externos no gubernamentales
    - Tipografias auto-hospedadas (sin fuentes externas)
    - Sin trackers externos (privacidad de datos ciudadanos)

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

    # Dominios de fuentes externas (para PROH-03)
    FONT_DOMAINS = [
        'fonts.googleapis.com',
        'fonts.gstatic.com',
        'use.typekit.net',
        'fonts.adobe.com',
        'cloud.typography.com',
        'fast.fonts.net',
        'use.fontawesome.com',
        'cdnjs.cloudflare.com/ajax/libs/font-awesome',
    ]

    # CDNs comunmente usados (para deteccion en PROH-02)
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
                'name': 'Sin iframes externos',
                'lineamiento': 'D.S. 3925 Art. 5 - Independencia y proteccion contra filtracion',
                'max_score': 25.0
            },
            'PROH-02': {
                'name': 'Sin CDNs externos no autorizados',
                'lineamiento': 'D.S. 3925 Art. 5 - Soberania tecnologica',
                'max_score': 25.0
            },
            'PROH-03': {
                'name': 'Sin fuentes externas',
                'lineamiento': 'D.S. 3925 Art. 5 - Recursos tipograficos auto-hospedados',
                'max_score': 20.0
            },
            'PROH-04': {
                'name': 'Sin trackers externos',
                'lineamiento': 'D.S. 3925 Art. 7 - Proteccion de privacidad de datos ciudadanos',
                'max_score': 30.0
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

        Returns:
            List[CriteriaEvaluation]: Lista de evaluaciones por criterio
        """
        self.clear_results()

        self.add_result(self._evaluar_proh01_iframes(extracted_content))
        self.add_result(self._evaluar_proh02_cdns(extracted_content))
        self.add_result(self._evaluar_proh03_fuentes(extracted_content))
        self.add_result(self._evaluar_proh04_trackers(extracted_content))

        return self.results

    # ========================================================================
    # PROH-01: Sin iframes externos
    # ========================================================================

    def _evaluar_proh01_iframes(self, content: Dict) -> CriteriaEvaluation:
        """
        PROH-01: Sin iframes externos

        Verifica que el sitio NO use iframes que carguen contenido de
        dominios externos, ya que:
        - Crean dependencia de servicios terceros
        - Pueden filtrar informacion de ciudadanos
        - Reducen control sobre el contenido mostrado

        Score: 25 si 0 iframes, 12.5 si 1-2, 0 si >2
        """
        max_score = 25.0
        external_resources = content.get('external_resources', {})
        iframes_data = external_resources.get('iframes', {})
        external_iframes = iframes_data.get('external', [])

        # Clasificar iframes por tipo
        iframes_info = []
        for iframe in external_iframes:
            src = iframe.get('absolute_src', '') if isinstance(iframe, dict) else str(iframe)
            domain = iframe.get('domain', '') if isinstance(iframe, dict) else ''
            iframes_info.append({
                'source': src,
                'domain': domain
            })

        iframe_count = len(iframes_info)

        if iframe_count == 0:
            status = 'pass'
            score = max_score
            message = 'Sin iframes externos detectados'
        elif iframe_count <= 2:
            status = 'partial'
            score = max_score * 0.5
            message = f'Pocos iframes externos ({iframe_count})'
        else:
            status = 'fail'
            score = 0.0
            message = f'Demasiados iframes externos ({iframe_count})'

        recomendacion = self._generar_recomendacion_iframes(iframes_info, iframe_count)

        return CriteriaEvaluation(
            criteria_id='PROH-01',
            criteria_name=self.criterios['PROH-01']['name'],
            dimension=self.dimension,
            lineamiento=self.criterios['PROH-01']['lineamiento'],
            status=status,
            score=score,
            max_score=max_score,
            details={
                'iframes_found': iframes_info,
                'iframe_count': iframe_count,
                'compliant': iframe_count == 0,
                'message': message
            },
            evidence={
                'iframes_detectados': [i['domain'] or i['source'][:80] for i in iframes_info] or ['Ninguno'],
                'recomendacion': recomendacion
            }
        )

    def _generar_recomendacion_iframes(self, iframes: List[Dict], count: int) -> Dict[str, Any]:
        """Genera recomendacion educativa para iframes externos"""
        if count == 0:
            return {
                'estado': 'CUMPLE',
                'mensaje': 'El sitio no depende de iframes externos, manteniendo independencia y control del contenido.'
            }

        domains = list(set(i['domain'] for i in iframes if i['domain']))

        return {
            'estado': 'NO CUMPLE' if count > 2 else 'PARCIAL',
            'problema': f'Se detectaron {count} iframe(s) externo(s): {", ".join(domains[:5])}',
            'por_que_mal': '''Los iframes externos causan problemas de soberania digital:
1. DEPENDENCIA: Si el servicio externo cae, parte de su sitio deja de funcionar
2. FILTRACION: El contenido del iframe puede rastrear a los ciudadanos
3. SEGURIDAD: Los iframes pueden ser comprometidos (clickjacking, XSS)
4. RENDIMIENTO: Cargan recursos adicionales de servidores externos
5. CONTROL: No se tiene control sobre el contenido mostrado al ciudadano''',
            'como_corregir': [
                '1. ELIMINAR iframes de servicios externos (YouTube, Google Maps, etc.)',
                '2. REEMPLAZAR videos de YouTube por enlaces directos:',
                '   <a href="https://youtube.com/watch?v=ID">Ver video</a>',
                '3. REEMPLAZAR Google Maps por OpenStreetMap auto-hospedado o imagen estatica',
                '4. Si necesita contenido dinamico, hospedarlo en su servidor .gob.bo',
                '5. Usar enlaces externos en lugar de embeds cuando sea posible'
            ],
            'ejemplo_antes': '''<!-- INCORRECTO: iframes externos -->
<iframe src="https://www.youtube.com/embed/VIDEO_ID"></iframe>
<iframe src="https://www.google.com/maps/embed?pb=..."></iframe>
<iframe src="https://www.facebook.com/plugins/page.php"></iframe>''',
            'ejemplo_despues': '''<!-- CORRECTO: Sin iframes externos -->
<a href="https://youtube.com/watch?v=VIDEO_ID" target="_blank" rel="noopener">
  Ver video informativo</a>
<img src="/assets/img/mapa-ubicacion.png" alt="Ubicacion de la oficina">
<a href="https://facebook.com/institucion" target="_blank" rel="noopener">
  Siguenos en Facebook</a>''',
            'referencias': [
                'D.S. 3925 Art. 5: Soberania tecnologica e independencia',
                'OWASP: Clickjacking Defense Cheat Sheet',
                'CSP frame-ancestors directive'
            ],
            'iframes_problematicos': domains
        }

    # ========================================================================
    # PROH-02: Sin CDNs externos no autorizados
    # ========================================================================

    def _evaluar_proh02_cdns(self, content: Dict) -> CriteriaEvaluation:
        """
        PROH-02: Sin CDNs externos no autorizados

        Verifica que el sitio no dependa de CDNs externos para recursos criticos
        (JS, CSS, imagenes). Las fuentes tipograficas se evaluan en PROH-03.

        Score: 25 si 0 externos, 17.5 si 1-2, 10 si 3-5, 0 si >5
        """
        max_score = 25.0
        external_resources = content.get('external_resources', {})
        cdn_data = external_resources.get('cdn', {})
        external_cdns = cdn_data.get('external', [])

        # Filtrar: separar CDNs de fonts (evaluados en PROH-03) de otros CDNs
        unauthorized_cdns = []
        font_cdns_excluded = []

        for cdn in external_cdns:
            domain = cdn.get('domain', '') if isinstance(cdn, dict) else str(cdn)
            domain_lower = domain.lower()
            src = cdn.get('absolute_src', '') if isinstance(cdn, dict) else str(cdn)
            src_lower = src.lower()

            # Excluir dominios de fuentes (evaluados en PROH-03)
            is_font = any(font_domain in domain_lower or font_domain in src_lower
                          for font_domain in self.FONT_DOMAINS)

            if is_font:
                font_cdns_excluded.append(domain)
            else:
                is_common_cdn = any(cdn_name in domain_lower for cdn_name in self.COMMON_CDNS)
                unauthorized_cdns.append({
                    'domain': domain,
                    'type': cdn.get('type', 'unknown') if isinstance(cdn, dict) else 'unknown',
                    'is_common_cdn': is_common_cdn
                })

        cdn_count = len(unauthorized_cdns)

        if cdn_count == 0:
            status = 'pass'
            score = max_score
            message = 'Sin dependencias de CDNs externos no autorizados'
        elif cdn_count <= 2:
            status = 'partial'
            score = max_score * 0.7  # 17.5
            message = f'Pocas dependencias externas ({cdn_count} CDNs)'
        elif cdn_count <= 5:
            status = 'partial'
            score = max_score * 0.4  # 10
            message = f'Varias dependencias externas ({cdn_count} CDNs)'
        else:
            status = 'fail'
            score = 0.0
            message = f'Demasiadas dependencias externas ({cdn_count} CDNs)'

        recomendacion = self._generar_recomendacion_cdns(unauthorized_cdns, cdn_count)

        return CriteriaEvaluation(
            criteria_id='PROH-02',
            criteria_name=self.criterios['PROH-02']['name'],
            dimension=self.dimension,
            lineamiento=self.criterios['PROH-02']['lineamiento'],
            status=status,
            score=score,
            max_score=max_score,
            details={
                'unauthorized_cdns': unauthorized_cdns,
                'font_cdns_excluded': list(set(font_cdns_excluded)),
                'unauthorized_count': cdn_count,
                'message': message
            },
            evidence={
                'cdns_no_autorizados': [c['domain'] for c in unauthorized_cdns] or ['Ninguno'],
                'cdns_fuentes_excluidos': list(set(font_cdns_excluded)) or ['Ninguno'],
                'recomendacion': recomendacion
            }
        )

    def _generar_recomendacion_cdns(self, unauthorized: List[Dict], count: int) -> Dict[str, Any]:
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
<link href="/assets/css/styles.css" rel="stylesheet">''',
            'referencias': [
                'D.S. 3925 Art. 5: Soberania tecnologica',
                'OWASP: Third-Party JavaScript Management',
                'Web.dev: Loading Third-Party JavaScript'
            ],
            'cdns_problematicos': domains
        }

    # ========================================================================
    # PROH-03: Sin fuentes externas
    # ========================================================================

    def _evaluar_proh03_fuentes(self, content: Dict) -> CriteriaEvaluation:
        """
        PROH-03: Sin fuentes externas

        Verifica que el sitio NO cargue tipografias desde servidores externos
        (Google Fonts, Adobe Fonts, etc.). Las fuentes deben estar
        auto-hospedadas en el servidor .gob.bo.

        Score: 20 si 0 fuentes externas, 10 si 1-2, 0 si >2
        """
        max_score = 20.0
        external_resources = content.get('external_resources', {})
        cdn_data = external_resources.get('cdn', {})
        external_cdns = cdn_data.get('external', [])

        # Buscar fuentes externas en los CDNs
        external_fonts = []

        for cdn in external_cdns:
            domain = cdn.get('domain', '') if isinstance(cdn, dict) else str(cdn)
            domain_lower = domain.lower()
            src = cdn.get('absolute_src', '') if isinstance(cdn, dict) else str(cdn)
            src_lower = src.lower()

            # Verificar si es un dominio de fuentes
            is_font = any(font_domain in domain_lower or font_domain in src_lower
                          for font_domain in self.FONT_DOMAINS)

            if is_font:
                external_fonts.append({
                    'domain': domain,
                    'source': src[:120],
                    'type': cdn.get('type', 'unknown') if isinstance(cdn, dict) else 'unknown'
                })

        font_count = len(external_fonts)

        if font_count == 0:
            status = 'pass'
            score = max_score
            message = 'Sin fuentes tipograficas externas'
        elif font_count <= 2:
            status = 'partial'
            score = max_score * 0.5  # 10
            message = f'Algunas fuentes externas detectadas ({font_count})'
        else:
            status = 'fail'
            score = 0.0
            message = f'Demasiadas fuentes externas ({font_count})'

        recomendacion = self._generar_recomendacion_fuentes(external_fonts, font_count)

        return CriteriaEvaluation(
            criteria_id='PROH-03',
            criteria_name=self.criterios['PROH-03']['name'],
            dimension=self.dimension,
            lineamiento=self.criterios['PROH-03']['lineamiento'],
            status=status,
            score=score,
            max_score=max_score,
            details={
                'external_fonts': external_fonts,
                'font_count': font_count,
                'compliant': font_count == 0,
                'message': message
            },
            evidence={
                'fuentes_externas': [f['domain'] for f in external_fonts] or ['Ninguna'],
                'recomendacion': recomendacion
            }
        )

    def _generar_recomendacion_fuentes(self, fonts: List[Dict], count: int) -> Dict[str, Any]:
        """Genera recomendacion educativa para fuentes externas"""
        if count == 0:
            return {
                'estado': 'CUMPLE',
                'mensaje': 'El sitio usa fuentes auto-hospedadas, manteniendo independencia tipografica.'
            }

        domains = list(set(f['domain'] for f in fonts))

        return {
            'estado': 'NO CUMPLE' if count > 2 else 'PARCIAL',
            'problema': f'Se detectaron {count} fuente(s) tipografica(s) externa(s): {", ".join(domains[:5])}',
            'por_que_mal': '''Usar fuentes de servidores externos causa:
1. PRIVACIDAD: Google Fonts y otros rastrean a cada visitante de su sitio
2. DEPENDENCIA: Si el servicio de fuentes cae, el texto se muestra con fuentes genericas
3. RENDIMIENTO: Peticiones DNS adicionales y descarga desde servidores lejanos
4. LEGAL: En la UE, usar Google Fonts sin consentimiento viola el RGPD
5. SOBERANIA: Informacion de los visitantes se envia a servidores extranjeros''',
            'como_corregir': [
                '1. DESCARGAR las fuentes usando https://gwfh.mranftl.com/fonts (Google Webfonts Helper)',
                '2. COPIAR los archivos .woff2 a su servidor: /assets/fonts/',
                '3. CREAR un archivo CSS local con @font-face:',
                '',
                '   @font-face {',
                '     font-family: "Roboto";',
                '     src: url("/assets/fonts/roboto-v30-latin-regular.woff2") format("woff2");',
                '     font-weight: 400;',
                '     font-style: normal;',
                '     font-display: swap;',
                '   }',
                '',
                '4. ELIMINAR el <link> a fonts.googleapis.com del HTML',
                '5. REFERENCIAR el CSS local en su lugar'
            ],
            'ejemplo_antes': '''<!-- INCORRECTO: Fuentes externas -->
<link href="https://fonts.googleapis.com/css2?family=Roboto:wght@400;700&display=swap"
      rel="stylesheet">''',
            'ejemplo_despues': '''<!-- CORRECTO: Fuentes auto-hospedadas -->
<link href="/assets/css/fonts.css" rel="stylesheet">

<!-- En /assets/css/fonts.css: -->
<!-- @font-face { font-family: "Roboto"; -->
<!--   src: url("/assets/fonts/roboto-regular.woff2") format("woff2"); } -->''',
            'referencias': [
                'D.S. 3925 Art. 5: Soberania tecnologica',
                'RGPD/Privacidad: Google Fonts tracking concerns',
                'Google Webfonts Helper: https://gwfh.mranftl.com/fonts'
            ],
            'fuentes_problematicas': domains
        }

    # ========================================================================
    # PROH-04: Sin trackers externos (CRITICO)
    # ========================================================================

    def _evaluar_proh04_trackers(self, content: Dict) -> CriteriaEvaluation:
        """
        PROH-04: Sin trackers externos

        CRITERIO CRITICO: Verifica que el sitio NO use trackers que recopilen
        datos de ciudadanos:
        - Google Analytics / Google Tag Manager
        - Facebook Pixel / Meta Pixel
        - Otros trackers publicitarios

        Score: 30 si cumple (sin trackers), 5 si trackers menores, 0 si criticos
        """
        max_score = 30.0
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

        has_trackers = tracker_count > 0

        if not has_trackers:
            status = 'pass'
            score = max_score
            message = 'Sin trackers externos detectados'
        elif len(critical_trackers) > 0:
            status = 'fail'
            score = 0.0
            message = f'Trackers criticos detectados: {len(critical_trackers)}'
        else:
            status = 'fail'
            score = 5.0
            message = f'Trackers menores detectados: {len(other_trackers)}'

        recomendacion = self._generar_recomendacion_trackers(
            critical_trackers, other_trackers, tracker_count
        )

        return CriteriaEvaluation(
            criteria_id='PROH-04',
            criteria_name=self.criterios['PROH-04']['name'],
            dimension=self.dimension,
            lineamiento=self.criterios['PROH-04']['lineamiento'],
            status=status,
            score=score,
            max_score=max_score,
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
                'mensaje': 'El sitio respeta la privacidad de los ciudadanos al no usar trackers externos.'
            }

        return {
            'estado': 'NO CUMPLE',
            'problema': f'Se detectaron {total} tracker(s) que recopilan datos de ciudadanos sin consentimiento.',
            'por_que_mal': '''Los trackers externos (Google Analytics, Facebook Pixel):
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
