"""
Motor de evaluacion que orquesta todos los evaluadores.

Este motor coordina la ejecucion de los evaluadores:
- Accesibilidad (30%): 10 criterios WCAG
- Usabilidad (30%): 9 criterios de navegacion/identidad
- Semantica Tecnica (15%): 10 criterios HTML5
- Semantica Contenido NLP (15%): 3 criterios BETO
- Soberania (10%): 4 criterios D.S. 3925

Total: 36 criterios (33 heuristicos + 3 NLP)
"""
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timezone, timedelta

# Bolivia timezone (UTC-4)
_TZ_BOT = timezone(timedelta(hours=-4))

# Imports condicionales para uso con/sin BD
try:
    from sqlalchemy.orm import Session
    from app.models.database_models import (
        Evaluation, ExtractedContent, CriteriaResult, NLPAnalysis
    )
    HAS_DATABASE = True
except ImportError:
    HAS_DATABASE = False
    Session = None
    NLPAnalysis = None

# Importar evaluadores REALES
from .accesibilidad_evaluator import EvaluadorAccesibilidad
from .usabilidad_evaluator import EvaluadorUsabilidad
from .semantica_evaluator import EvaluadorSemantica
from .soberania_evaluator import EvaluadorSoberania

# Importar modulo NLP
try:
    from app.nlp.analyzer import NLPAnalyzer
    from app.nlp.adapter import NLPDataAdapter
    HAS_NLP = True
except ImportError:
    HAS_NLP = False
    NLPAnalyzer = None
    NLPDataAdapter = None

# Crawler (opcional para testing directo)
try:
    from app.crawler.html_crawler import GobBoCrawler
    HAS_CRAWLER = True
except ImportError:
    HAS_CRAWLER = False
    GobBoCrawler = None

logger = logging.getLogger(__name__)


# ============================================================================
# ENRIQUECIMIENTO DE EVIDENCIA: genera issues/recomendaciones para TODOS
# los criterios que fallen o sean parciales, asegurando que el frontend
# siempre tenga datos ricos para mostrar.
# ============================================================================

# Diccionario de explicaciones detalladas por criterio (para los que no las generan nativamente)
_CRITERIA_ENRICHMENT = {
    'ACC-01': {
        'por_que_mal': 'Las imágenes sin atributo alt son invisibles para lectores de pantalla y buscadores. '
                       'Usuarios con discapacidad visual no pueden entender el contenido visual.',
        'como_corregir': [
            'Agregar atributo alt descriptivo a cada imagen: <img src="foto.jpg" alt="Descripción de la imagen">',
            'Para imágenes decorativas, usar alt vacío: <img src="decoracion.png" alt="">',
            'Evitar textos genéricos como "imagen" o "foto". Describir el contenido real.',
        ],
        'referencias': ['WCAG 1.1.1 - Contenido no textual', 'https://www.w3.org/WAI/tutorials/images/']
    },
    'ACC-02': {
        'por_que_mal': 'Sin declaración de idioma, los lectores de pantalla no pueden pronunciar correctamente el contenido. '
                       'Afecta la accesibilidad y el SEO del sitio.',
        'como_corregir': [
            'Agregar atributo lang al elemento <html>: <html lang="es">',
            'Usar códigos ISO 639-1 (es, en, pt, etc.)',
        ],
        'referencias': ['WCAG 3.1.1 - Idioma de la página']
    },
    'ACC-03': {
        'por_que_mal': 'Un título de página vacío o genérico dificulta la navegación entre pestañas '
                       'y perjudica el posicionamiento en buscadores.',
        'como_corregir': [
            'Agregar un <title> descriptivo dentro de <head>',
            'El título debe describir el propósito de la página',
            'Incluir el nombre de la institución en el título',
        ],
        'referencias': ['WCAG 2.4.2 - Titulado de páginas']
    },
    'ACC-04': {
        'por_que_mal': 'Una jerarquía de encabezados incorrecta (saltos de nivel, falta de h1) '
                       'dificulta la navegación con lectores de pantalla y la comprensión de la estructura.',
        'como_corregir': [
            'Asegurar que exista exactamente un <h1> por página',
            'Mantener jerarquía secuencial: h1 → h2 → h3 (sin saltar niveles)',
            'No usar encabezados solo por estilo visual; usar CSS para eso',
        ],
        'referencias': ['WCAG 1.3.1 - Información y relaciones', 'WCAG 2.4.6 - Encabezados y etiquetas']
    },
    'ACC-05': {
        'por_que_mal': 'La reproducción automática de audio/video es intrusiva y problemática para '
                       'usuarios con discapacidades cognitivas o auditivas.',
        'como_corregir': [
            'Eliminar el atributo autoplay de elementos <audio> y <video>',
            'Si es necesario autoplay, asegurar que el audio esté silenciado (muted)',
            'Proveer controles visibles para pausar/detener la reproducción',
        ],
        'referencias': ['WCAG 1.4.2 - Control del audio']
    },
    'ACC-07': {
        'por_que_mal': 'Los campos de formulario sin etiquetas (<label>) son inaccesibles para lectores de pantalla. '
                       'Los usuarios no pueden saber qué información se les solicita.',
        'como_corregir': [
            'Asociar un <label> a cada campo usando el atributo for: <label for="email">Email</label> <input id="email">',
            'Alternativamente, envolver el campo dentro del label: <label>Email <input></label>',
            'Usar aria-label o aria-labelledby como alternativa cuando no sea posible un <label> visible',
        ],
        'referencias': ['WCAG 3.3.2 - Etiquetas o instrucciones', 'WCAG 1.3.1']
    },
    'ACC-08': {
        'por_que_mal': 'Enlaces con textos genéricos como "clic aquí", "ver más" o "leer más" no informan '
                       'al usuario sobre el destino del enlace fuera de contexto.',
        'como_corregir': [
            'Usar textos descriptivos: en lugar de "clic aquí", usar "Descargar el formulario de inscripción"',
            'Si el enlace abre un PDF, indicarlo: "Informe anual 2024 (PDF)"',
            'Evitar URLs desnudas como texto del enlace',
        ],
        'referencias': ['WCAG 2.4.4 - Propósito de los enlaces']
    },
    'ACC-09': {
        'por_que_mal': 'Encabezados y etiquetas vacías o sin contenido descriptivo no proveen información '
                       'útil para la navegación con lectores de pantalla.',
        'como_corregir': [
            'Asegurar que todos los encabezados (h1-h6) tengan texto descriptivo',
            'Eliminar encabezados vacíos o que contengan solo espacios',
            'Los encabezados deben describir la sección que les sigue',
        ],
        'referencias': ['WCAG 2.4.6 - Encabezados y etiquetas']
    },
    'ACC-10': {
        'por_que_mal': 'Cuando hay contenido en otros idiomas sin marcado lang, los lectores de pantalla '
                       'lo pronuncian incorrectamente.',
        'como_corregir': [
            'Marcar secciones en otros idiomas con el atributo lang: <span lang="en">Welcome</span>',
            'Usar códigos ISO 639-1 correctos',
        ],
        'referencias': ['WCAG 3.1.2 - Idioma de las partes']
    },
    'IDEN-01': {
        'por_que_mal': 'El D.S. 3925 requiere que el nombre de la institución sea visible en el título '
                       'para identificación institucional y transparencia.',
        'como_corregir': [
            'Incluir el nombre completo o sigla oficial de la institución en el <title>',
            'Formato recomendado: "Nombre Institución - Descripción de la página"',
        ],
        'referencias': ['D.S. 3925 (CONT-01)', 'WCAG 2.4.2']
    },
    'IDEN-02': {
        'por_que_mal': 'El D.S. 3925 (BATS-01) requiere la leyenda "Bolivia a tu servicio" como '
                       'identificador de sitios gubernamentales bolivianos.',
        'como_corregir': [
            'Agregar la leyenda "Bolivia a tu servicio" en el header o footer del sitio',
            'Asegurar que sea visible y legible para todos los usuarios',
        ],
        'referencias': ['D.S. 3925 (BATS-01)']
    },
    'NAV-01': {
        'por_que_mal': 'Un menú de navegación es fundamental para que los usuarios puedan explorar '
                       'el contenido del sitio de manera estructurada.',
        'como_corregir': [
            'Implementar un elemento <nav> con enlaces a las secciones principales',
            'Usar listas (<ul>/<li>) dentro del <nav> para estructura semántica',
            'Agregar aria-label="Navegación principal" al elemento <nav>',
        ],
        'referencias': ['D.S. 3925 (NAV-01)', 'WCAG 2.4.5']
    },
    'NAV-02': {
        'por_que_mal': 'Un buscador interno permite a los usuarios encontrar información rápidamente '
                       'sin tener que navegar por toda la estructura del sitio.',
        'como_corregir': [
            'Agregar un formulario de búsqueda con <input type="search"> o role="search"',
            'Ubicar el buscador en una posición visible (header o barra de navegación)',
            'Incluir un botón de envío claro y un placeholder descriptivo',
        ],
        'referencias': ['D.S. 3925 (NAV-02)']
    },
    'PART-01': {
        'por_que_mal': 'El D.S. 3925 (BATS-02) requiere enlaces a al menos 2 redes sociales '
                       'como canales de comunicación institucional con la ciudadanía.',
        'como_corregir': [
            'Agregar enlaces a las redes sociales oficiales de la institución (Facebook, Twitter/X, etc.)',
            'Se requiere un mínimo de 2 redes sociales diferentes',
            'Usar iconos reconocibles y enlaces directos a los perfiles institucionales',
        ],
        'referencias': ['D.S. 3925 (BATS-02)']
    },
    'PART-02': {
        'por_que_mal': 'El D.S. 3925 (BATS-03) requiere enlace a aplicación de mensajería '
                       'para contacto directo e inmediato con la ciudadanía.',
        'como_corregir': [
            'Agregar enlace a WhatsApp: <a href="https://wa.me/59170000000">WhatsApp</a>',
            'Alternativamente, enlazar a Telegram u otra app de mensajería',
            'Incluir el número de contacto institucional',
        ],
        'referencias': ['D.S. 3925 (BATS-03)']
    },
    'PART-03': {
        'por_que_mal': 'El D.S. 3925 (BATS-04) requiere enlace mailto: para contacto formal '
                       'por correo electrónico institucional.',
        'como_corregir': [
            'Agregar enlace mailto: <a href="mailto:contacto@institucion.gob.bo">Contáctenos</a>',
            'Usar la dirección de correo electrónico institucional oficial',
            'Colocar el enlace en un lugar visible (footer o página de contacto)',
        ],
        'referencias': ['D.S. 3925 (BATS-04)']
    },
    'PART-04': {
        'por_que_mal': 'El D.S. 3925 (BATS-05) requiere enlace tel: para contacto telefónico directo, '
                       'especialmente importante para adultos mayores y personas con discapacidad.',
        'como_corregir': [
            'Agregar enlace tel: <a href="tel:+59122000000">Llámenos: (2) 2000000</a>',
            'Usar el formato internacional del número (+591...)',
            'Colocar el enlace en el header, footer o página de contacto',
        ],
        'referencias': ['D.S. 3925 (BATS-05)']
    },
    'PART-05': {
        'por_que_mal': 'El D.S. 3925 (BATS-07) requiere botones para compartir contenido en redes sociales, '
                       'facilitando la difusión de información pública.',
        'como_corregir': [
            'Agregar botones para compartir en redes sociales (Facebook, Twitter/X, etc.)',
            'Ejemplo: <a href="https://facebook.com/sharer/sharer.php?u={URL}">Compartir</a>',
            'Ubicar los botones en artículos y páginas de contenido informativo',
        ],
        'referencias': ['D.S. 3925 (BATS-07)']
    },
    'SEO-01': {
        'por_que_mal': 'La meta descripción es crucial para el posicionamiento en buscadores. '
                       'Sin ella, Google genera un snippet automático que puede no ser representativo.',
        'como_corregir': [
            'Agregar <meta name="description" content="Descripción clara del sitio en 150-160 caracteres">',
            'La descripción debe resumir el propósito del sitio institucional',
        ],
        'referencias': ['WCAG 2.4.2', 'Google SEO Starter Guide']
    },
    'SEO-02': {
        'por_que_mal': 'Las meta keywords, aunque tienen menor peso en SEO moderno, son parte del '
                       'estándar de metadatos recomendado para sitios gubernamentales.',
        'como_corregir': [
            'Agregar <meta name="keywords" content="institución, gobierno, bolivia, servicio">',
            'Usar palabras clave relevantes al contenido del sitio',
        ],
        'referencias': ['Buenas prácticas de metadatos web']
    },
    'SEO-03': {
        'por_que_mal': 'Sin la meta viewport, el sitio no se adapta correctamente a dispositivos móviles, '
                       'afectando a la mayoría de usuarios que navegan desde celulares.',
        'como_corregir': [
            'Agregar <meta name="viewport" content="width=device-width, initial-scale=1">',
            'No usar user-scalable=no ya que impide el zoom para accesibilidad',
        ],
        'referencias': ['WCAG 1.4.4 - Cambio de tamaño del texto', 'Google Mobile-Friendly']
    },
    'SEO-04': {
        'por_que_mal': 'Una jerarquía de headings inválida afecta la estructura semántica del documento, '
                       'perjudicando la accesibilidad y el posicionamiento en buscadores.',
        'como_corregir': [
            'Asegurar un único <h1> que describa el contenido principal de la página',
            'Mantener la jerarquía h1 → h2 → h3 sin saltos',
            'No usar headings solo por estilo visual',
        ],
        'referencias': ['WCAG 1.3.1', 'WCAG 2.4.6']
    },
    'FMT-01': {
        'por_que_mal': 'El uso de formatos propietarios (docx, xlsx, pptx) limita el acceso '
                       'a la información pública para quienes no tienen software comercial.',
        'como_corregir': [
            'Preferir formatos abiertos: PDF, ODF (.odt, .ods), CSV, HTML',
            'Si se requiere un documento editable, usar formato ODF',
            'Proveer alternativa en formato abierto junto al formato propietario',
        ],
        'referencias': ['D.S. 3925 - Soberanía tecnológica', 'ISO 26300 (ODF)']
    },
    'FMT-02': {
        'por_que_mal': 'Las imágenes en formatos pesados (.bmp, .tiff) o sin optimizar aumentan '
                       'los tiempos de carga y el consumo de datos, especialmente en conexiones lentas.',
        'como_corregir': [
            'Convertir imágenes a formatos web optimizados: WebP, AVIF, o PNG/JPEG optimizado',
            'Comprimir imágenes manteniendo calidad aceptable',
            'Usar lazy loading para imágenes fuera del viewport',
        ],
        'referencias': ['Web Performance Best Practices', 'Google PageSpeed']
    },
    'ACC-06': {
        'por_que_mal': 'Un contraste insuficiente entre el texto y el fondo dificulta la lectura para '
                       'personas con baja visión, daltonismo o que usan el sitio en condiciones de mucha luz.',
        'como_corregir': [
            'Asegurar una relación de contraste mínima de 4.5:1 para texto normal',
            'Para texto grande (18px+ o 14px+ negrita), el mínimo es 3:1',
            'Usar herramientas como WebAIM Contrast Checker para verificar',
            'Evitar texto gris claro sobre fondo blanco o combinaciones de bajo contraste',
        ],
        'referencias': ['WCAG 1.4.3 - Contraste mínimo', 'https://webaim.org/resources/contrastchecker/']
    },
    'SEM-01': {
        'por_que_mal': 'Sin la declaración <!DOCTYPE html>, el navegador puede renderizar la página en modo quirks, '
                       'causando inconsistencias visuales y de comportamiento.',
        'como_corregir': [
            'Agregar <!DOCTYPE html> como primera línea del documento HTML',
            'Verificar que no haya espacios o caracteres antes del DOCTYPE',
        ],
        'referencias': ['Estándar HTML5', 'W3C HTML Validator']
    },
    'SEM-02': {
        'por_que_mal': 'Sin declaración de codificación UTF-8, los caracteres especiales (tildes, eñes) '
                       'pueden mostrarse incorrectamente.',
        'como_corregir': [
            'Agregar <meta charset="UTF-8"> dentro de <head>',
            'Asegurar que el archivo HTML esté guardado con codificación UTF-8',
            'El meta charset debe ser uno de los primeros elementos dentro de <head>',
        ],
        'referencias': ['Estándar HTML5', 'W3C - Declaración de codificación']
    },
    'SEM-03': {
        'por_que_mal': 'No usar elementos semánticos HTML5 (<header>, <nav>, <main>, <footer>, <article>, <section>) '
                       'dificulta la interpretación del contenido por buscadores y tecnologías asistivas.',
        'como_corregir': [
            'Usar <header> para el encabezado del sitio',
            'Usar <nav> para menús de navegación',
            'Usar <main> para el contenido principal (uno por página)',
            'Usar <footer> para el pie de página',
            'Usar <article> y <section> para organizar el contenido',
        ],
        'referencias': ['HTML5 Semantics', 'WCAG 1.3.1 - Información y relaciones']
    },
    'SEM-04': {
        'por_que_mal': 'Mezclar contenido con presentación (estilos inline, atributos de estilo en HTML) '
                       'dificulta el mantenimiento y afecta la accesibilidad.',
        'como_corregir': [
            'Mover estilos inline a hojas de estilo CSS externas',
            'Evitar atributos como bgcolor, align, font en elementos HTML',
            'Usar clases CSS en lugar de estilos directos en los elementos',
        ],
        'referencias': ['Buenas prácticas de desarrollo web', 'WCAG 1.3.1']
    },
    'PROH-01': {
        'por_que_mal': 'Los iframes externos cargan contenido de servidores fuera del control institucional, '
                       'exponiendo a los usuarios a riesgos de seguridad y privacidad.',
        'como_corregir': [
            'Eliminar iframes que cargan contenido de dominios externos no autorizados',
            'Si es necesario un iframe, usar los atributos sandbox y allow para restringir permisos',
            'Considerar alojar el contenido localmente en lugar de usar iframes',
        ],
        'referencias': ['D.S. 3925 - Soberanía tecnológica', 'OWASP - Clickjacking']
    },
    'PROH-02': {
        'por_que_mal': 'Cargar recursos desde CDNs externos (JavaScript, CSS) crea dependencias de servidores '
                       'fuera del control institucional y puede comprometer la seguridad.',
        'como_corregir': [
            'Alojar localmente las librerías JavaScript y CSS que se usan',
            'Si se requiere un CDN, usar solo los autorizados por la institución',
            'Implementar Subresource Integrity (SRI) para recursos externos críticos',
        ],
        'referencias': ['D.S. 3925 - Soberanía tecnológica', 'Mozilla SRI']
    },
    'PROH-03': {
        'por_que_mal': 'Cargar fuentes desde servidores externos (como Google Fonts) envía datos del '
                       'visitante a terceros sin su consentimiento.',
        'como_corregir': [
            'Descargar las fuentes y alojarlas localmente en el servidor institucional',
            'Usar la directiva @font-face con archivos locales',
            'Considerar usar fuentes del sistema para mejorar rendimiento',
        ],
        'referencias': ['D.S. 3925 - Soberanía tecnológica', 'GDPR/Privacidad']
    },
    'PROH-04': {
        'por_que_mal': 'Los trackers externos (Google Analytics, Facebook Pixel, etc.) envían datos de '
                       'navegación de los ciudadanos a empresas extranjeras sin consentimiento.',
        'como_corregir': [
            'Reemplazar Google Analytics por alternativas de código abierto como Matomo o Plausible',
            'Eliminar pixels de seguimiento de redes sociales',
            'Si se requiere analítica, usar soluciones auto-alojadas en servidores institucionales',
        ],
        'referencias': ['D.S. 3925 - Soberanía tecnológica', 'Ley de Protección de Datos']
    },
}


def _enrich_criteria_results(results: list) -> list:
    """
    Enriquece los resultados de criterios que fallan o son parciales
    para asegurar que TODOS tengan issues, recomendaciones y recomendación detallada.

    Opera tanto sobre objetos CriteriaEvaluation como sobre dicts.
    """
    logger.info(f"_enrich_criteria_results: procesando {len(results)} criterios")
    enriched_count = 0
    for result in results:
        # Obtener datos según tipo (objeto o dict)
        if hasattr(result, 'status'):
            status = result.status
            details = result.details or {}
            evidence = result.evidence or {}
            criteria_id = result.criteria_id
        else:
            status = result.get('status', '')
            details = result.get('details') or {}
            evidence = result.get('evidence') or {}
            criteria_id = result.get('criteria_id', '')

        # Solo enriquecer criterios que fallan o son parciales
        if status not in ('fail', 'partial'):
            continue

        # 1. Generar issues si no existen
        if not details.get('issues'):
            issues = []
            msg = details.get('message', '')
            rec = details.get('recommendation', '')
            if msg:
                issues.append(msg)
            if rec and rec != msg:
                issues.append(rec)
            if issues:
                details['issues'] = issues

        # 2. Generar recomendaciones en evidence si no existen
        if not evidence.get('recomendaciones'):
            enrichment = _CRITERIA_ENRICHMENT.get(criteria_id, {})
            if enrichment.get('como_corregir'):
                evidence['recomendaciones'] = enrichment['como_corregir']
            elif details.get('recommendation'):
                evidence['recomendaciones'] = [details['recommendation']]

        # 3. Generar recomendacion_detallada si no existe
        if not evidence.get('recomendacion_detallada') and not evidence.get('recomendacion'):
            enrichment = _CRITERIA_ENRICHMENT.get(criteria_id, {})
            if enrichment:
                rec_detallada = {}
                msg = details.get('message', '')
                if msg:
                    rec_detallada['problema'] = msg
                if enrichment.get('por_que_mal'):
                    rec_detallada['por_que_mal'] = enrichment['por_que_mal']
                if enrichment.get('como_corregir'):
                    rec_detallada['como_corregir'] = enrichment['como_corregir']
                if enrichment.get('referencias'):
                    rec_detallada['referencias'] = enrichment['referencias']
                if rec_detallada:
                    evidence['recomendacion_detallada'] = rec_detallada

        # Actualizar references back
        if hasattr(result, 'details'):
            result.details = details
            result.evidence = evidence
        else:
            result['details'] = details
            result['evidence'] = evidence
        enriched_count += 1
        logger.debug(f"  Enriquecido {criteria_id} (status={status}): "
                     f"issues={bool(details.get('issues'))}, "
                     f"recs={bool(evidence.get('recomendaciones'))}, "
                     f"detallada={bool(evidence.get('recomendacion_detallada'))}")

    logger.info(f"_enrich_criteria_results: {enriched_count}/{len(results)} criterios enriquecidos")
    return results


class EvaluationEngine:
    """
    Motor principal de evaluacion.

    Ejecuta los evaluadores heuristicos + NLP y calcula scores finales.
    Soporta dos modos:
    - Con BD: Para uso en produccion (requiere Session)
    - Sin BD: Para testing directo con URLs

    Pesos actualizados:
    - Accesibilidad: 30%
    - Usabilidad: 30%
    - Semantica Tecnica: 15%
    - Semantica Contenido (NLP): 15%
    - Soberania: 10%
    """

    # Pesos de cada dimension en el score final
    PESOS = {
        "accesibilidad": 0.30,
        "usabilidad": 0.30,
        "semantica_tecnica": 0.15,
        "semantica_nlp": 0.15,
        "soberania": 0.10
    }

    def __init__(self, db: Optional[Session] = None):
        """
        Inicializa el motor de evaluacion.

        Args:
            db: Session de SQLAlchemy (opcional, para modo con BD)
        """
        self.db = db

        # Inicializar evaluadores REALES (33 criterios heuristicos)
        self.evaluadores = {
            "accesibilidad": EvaluadorAccesibilidad(),
            "usabilidad": EvaluadorUsabilidad(),
            "semantica": EvaluadorSemantica(),
            "soberania": EvaluadorSoberania()
        }

        # Inicializar NLPAnalyzer (3 criterios NLP)
        if HAS_NLP:
            self.nlp_analyzer = NLPAnalyzer()
            self.nlp_adapter = NLPDataAdapter()
        else:
            self.nlp_analyzer = None
            self.nlp_adapter = None

        # Inicializar crawler para modo sin BD
        if HAS_CRAWLER:
            self.crawler = GobBoCrawler(timeout=45)
        else:
            self.crawler = None

        logger.info("EvaluationEngine inicializado con evaluadores REALES:")
        logger.info("  - EvaluadorAccesibilidad (10 criterios)")
        logger.info("  - EvaluadorUsabilidad (9 criterios)")
        logger.info("  - EvaluadorSemantica (10 criterios)")
        logger.info("  - EvaluadorSoberania (4 criterios)")
        if HAS_NLP:
            logger.info("  - NLPAnalyzer (3 criterios: coherencia, ambiguedad, claridad)")
        logger.info(f"  Total: {33 + (3 if HAS_NLP else 0)} criterios")

    def evaluar_sitio(self, website_id: int) -> Dict:
        """
        Evalúa un sitio completo con evaluadores heuristicos + NLP.

        1. Obtiene el contenido extraído
        2. Ejecuta evaluadores heuristicos (33 criterios)
        3. Ejecuta análisis NLP (3 criterios)
        4. Guarda resultados en BD (criteria_results + nlp_analysis)
        5. Calcula scores finales ponderados
        """
        # 1. Obtener contenido extraído más reciente
        extracted = self.db.query(ExtractedContent).filter(
            ExtractedContent.website_id == website_id
        ).order_by(ExtractedContent.crawled_at.desc()).first()

        if not extracted:
            raise ValueError(f"No hay contenido extraído para website_id={website_id}")

        # Convertir a dict
        extracted_data = {
            'metadata': extracted.page_metadata or {},
            'structure': extracted.html_structure or {},
            'semantic_elements': extracted.semantic_elements or {},
            'headings': extracted.headings or {},
            'images': extracted.images or {},
            'links': extracted.links or {},
            'forms': extracted.forms or {},
            'media': extracted.media or {},
            'external_resources': extracted.external_resources or {},
            'text_corpus': extracted.text_corpus or {}
        }

        # 2. Crear registro de evaluación
        evaluation = Evaluation(
            website_id=website_id,
            status='in_progress'
        )
        self.db.add(evaluation)
        self.db.commit()
        self.db.refresh(evaluation)

        try:
            all_results = []

            # 3. Ejecutar evaluadores heuristicos (33 criterios)
            for dimension_name, evaluador in self.evaluadores.items():
                results = evaluador.evaluate(extracted_data)

                # Enriquecer evidencia antes de guardar
                _enrich_criteria_results(results)

                # Guardar cada resultado
                for result in results:
                    criteria_result = CriteriaResult(
                        evaluation_id=evaluation.id,
                        criteria_id=result.criteria_id,
                        criteria_name=result.criteria_name,
                        dimension=result.dimension,
                        lineamiento=result.lineamiento,
                        status=result.status,
                        score=result.score,
                        max_score=result.max_score,
                        details=result.details,
                        evidence=result.evidence
                    )
                    self.db.add(criteria_result)
                    all_results.append(result)

            self.db.commit()

            # 4. Calcular scores por dimensión heuristica
            scores_por_dimension = {}
            for dimension_name, evaluador in self.evaluadores.items():
                scores_por_dimension[dimension_name] = evaluador.get_dimension_score()

            # 5. Ejecutar análisis NLP (3 criterios)
            nlp_result = None
            if self.nlp_analyzer:
                nlp_result = self._run_nlp_analysis(extracted_data)

                # 6. Guardar resultados NLP en BD
                self._save_nlp_to_database(evaluation.id, nlp_result)

                # Agregar criterios NLP a los resultados
                nlp_criteria = self._create_nlp_criteria_results(
                    evaluation.id, nlp_result
                )
                for criteria in nlp_criteria:
                    self.db.add(criteria)
                    all_results.append(criteria)

                self.db.commit()

            # 7. Calcular score final ponderado (30-30-15-15-10)
            score_final = self._calculate_final_score(
                scores_por_dimension,
                nlp_result
            )

            # 8. Actualizar evaluación
            evaluation.score_digital_sovereignty = scores_por_dimension['soberania']['percentage']
            evaluation.score_accessibility = scores_por_dimension['accesibilidad']['percentage']
            evaluation.score_usability = scores_por_dimension['usabilidad']['percentage']
            # Combinación: técnica (15%) + NLP (15%)
            semantica_tecnica = scores_por_dimension['semantica']['percentage']
            semantica_nlp = nlp_result['global_score'] if nlp_result else 0
            evaluation.score_semantic_web = (semantica_tecnica + semantica_nlp) / 2
            evaluation.score_total = score_final
            evaluation.status = 'completed'
            evaluation.completed_at = datetime.now(_TZ_BOT).replace(tzinfo=None)

            self.db.commit()

            return {
                "evaluation_id": evaluation.id,
                "website_id": website_id,
                "status": "completed",
                "scores": {
                    "accesibilidad": scores_por_dimension['accesibilidad'],
                    "usabilidad": scores_por_dimension['usabilidad'],
                    "semantica_tecnica": scores_por_dimension['semantica'],
                    "semantica_nlp": {
                        "percentage": nlp_result['global_score'] if nlp_result else 0,
                        "coherence": nlp_result['coherence_score'] if nlp_result else 0,
                        "ambiguity": nlp_result['ambiguity_score'] if nlp_result else 0,
                        "clarity": nlp_result['clarity_score'] if nlp_result else 0
                    } if nlp_result else None,
                    "soberania": scores_por_dimension['soberania'],
                    "total": score_final
                },
                "nlp_analysis": nlp_result,
                "total_criteria": len(all_results),
                "passed": len([r for r in all_results if getattr(r, 'status', r.get('status', '')) == "pass"]),
                "failed": len([r for r in all_results if getattr(r, 'status', r.get('status', '')) == "fail"]),
                "partial": len([r for r in all_results if getattr(r, 'status', r.get('status', '')) == "partial"]),
                "not_applicable": len([r for r in all_results if getattr(r, 'status', r.get('status', '')) == "na"])
            }

        except Exception as e:
            evaluation.status = 'failed'
            evaluation.error_message = str(e)
            self.db.commit()
            raise

    def _run_nlp_analysis(self, extracted_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Ejecuta análisis NLP sobre el contenido extraído.

        Args:
            extracted_data: Datos del crawler

        Returns:
            Resultado del análisis NLP o None si falla
        """
        if not self.nlp_analyzer:
            logger.warning("NLPAnalyzer no disponible")
            return None

        try:
            # Verificar que text_corpus tenga datos
            text_corpus = extracted_data.get('text_corpus', {})
            tc_sections = text_corpus.get('sections', []) if text_corpus else []
            logger.info(
                f"NLP: text_corpus tiene {len(tc_sections)} secciones, "
                f"keys={list(text_corpus.keys()) if text_corpus else '(vacío)'}"
            )

            # Adaptar datos al formato NLP
            nlp_data = self.nlp_adapter.adapt(extracted_data)

            nlp_sections = nlp_data.get('sections', [])
            logger.info(
                f"NLP: Datos adaptados - {len(nlp_sections)} secciones, "
                f"{len(nlp_data.get('links', []))} enlaces"
            )

            # Ejecutar análisis
            result = self.nlp_analyzer.analyze_website(nlp_data)

            logger.info(
                f"NLP completado: global={result['global_score']:.1f}, "
                f"coherencia={result['coherence_score']:.1f}, "
                f"ambiguedad={result['ambiguity_score']:.1f}, "
                f"claridad={result['clarity_score']:.1f}"
            )
            return result

        except Exception as e:
            logger.error(f"Error en análisis NLP: {e}", exc_info=True)
            return None

    def _save_nlp_to_database(
        self,
        evaluation_id: int,
        nlp_result: Dict[str, Any]
    ) -> Optional[int]:
        """
        Persiste resultados NLP en la tabla nlp_analysis.

        Args:
            evaluation_id: ID de la evaluación
            nlp_result: Resultado del NLPAnalyzer

        Returns:
            ID del registro NLP creado o None
        """
        if not HAS_DATABASE or not nlp_result:
            return None

        try:
            nlp_analysis = NLPAnalysis(
                evaluation_id=evaluation_id,
                nlp_global_score=nlp_result['global_score'],
                coherence_score=nlp_result['coherence_score'],
                ambiguity_score=nlp_result['ambiguity_score'],
                clarity_score=nlp_result['clarity_score'],
                coherence_details=nlp_result['details'].get('coherence', {}),
                ambiguity_details=nlp_result['details'].get('ambiguity', {}),
                clarity_details=nlp_result['details'].get('clarity', {}),
                recommendations=nlp_result.get('recommendations', []),
                wcag_compliance=nlp_result.get('wcag_compliance', {}),
                analyzed_at=datetime.now(_TZ_BOT).replace(tzinfo=None)
            )

            self.db.add(nlp_analysis)
            self.db.flush()  # Obtener ID sin commit

            logger.info(f"NLP guardado en BD: nlp_analysis.id={nlp_analysis.id}")
            return nlp_analysis.id

        except Exception as e:
            logger.error(f"Error guardando NLP en BD: {e}")
            return None

    def _create_nlp_criteria_results(
        self,
        evaluation_id: int,
        nlp_result: Dict[str, Any]
    ) -> List[CriteriaResult]:
        """
        Crea CriteriaResult para los 3 criterios NLP.

        Criterios:
        - ACC-07: Labels or Instructions (WCAG 3.3.2)
        - ACC-08: Link Purpose (WCAG 2.4.4)
        - ACC-09: Headings and Labels (WCAG 2.4.6)

        Args:
            evaluation_id: ID de la evaluación
            nlp_result: Resultado del NLPAnalyzer

        Returns:
            Lista de CriteriaResult para NLP
        """
        criteria = []
        wcag = nlp_result.get('wcag_compliance', {})

        # ACC-07: Labels or Instructions
        acc07_pass = wcag.get('ACC-07', False)
        criteria.append(CriteriaResult(
            evaluation_id=evaluation_id,
            criteria_id='ACC-07',
            criteria_name='Labels or Instructions (NLP)',
            dimension='semantica_nlp',
            lineamiento='WCAG 3.3.2 - Level A',
            status='pass' if acc07_pass else 'fail',
            score=1.0 if acc07_pass else 0.0,
            max_score=1.0,
            details={
                'source': 'NLP Analysis',
                'wcag_criterion': '3.3.2',
                'wcag_level': 'A',
                'analysis': 'Análisis de claridad en labels y textos de formularios'
            },
            evidence={'nlp_score': nlp_result['ambiguity_score']}
        ))

        # ACC-08: Link Purpose
        acc08_pass = wcag.get('ACC-08', False)
        criteria.append(CriteriaResult(
            evaluation_id=evaluation_id,
            criteria_id='ACC-08',
            criteria_name='Link Purpose (NLP)',
            dimension='semantica_nlp',
            lineamiento='WCAG 2.4.4 - Level A',
            status='pass' if acc08_pass else 'fail',
            score=1.0 if acc08_pass else 0.0,
            max_score=1.0,
            details={
                'source': 'NLP Analysis',
                'wcag_criterion': '2.4.4',
                'wcag_level': 'A',
                'analysis': 'Detección de enlaces con texto genérico o ambiguo'
            },
            evidence={'nlp_score': nlp_result['ambiguity_score']}
        ))

        # ACC-09: Headings and Labels
        acc09_pass = wcag.get('ACC-09', False)
        criteria.append(CriteriaResult(
            evaluation_id=evaluation_id,
            criteria_id='ACC-09',
            criteria_name='Headings and Labels (NLP)',
            dimension='semantica_nlp',
            lineamiento='WCAG 2.4.6 - Level AA',
            status='pass' if acc09_pass else 'fail',
            score=1.0 if acc09_pass else 0.0,
            max_score=1.0,
            details={
                'source': 'NLP Analysis',
                'wcag_criterion': '2.4.6',
                'wcag_level': 'AA',
                'analysis': 'Coherencia semántica entre headings y contenido'
            },
            evidence={'nlp_score': nlp_result['coherence_score']}
        ))

        return criteria

    def _calculate_final_score(
        self,
        scores_por_dimension: Dict[str, Dict],
        nlp_result: Optional[Dict[str, Any]]
    ) -> float:
        """
        Calcula score final ponderado.

        Pesos:
        - Accesibilidad: 30%
        - Usabilidad: 30%
        - Semántica Técnica: 15%
        - Semántica NLP: 15%
        - Soberanía: 10%

        Args:
            scores_por_dimension: Scores de evaluadores heuristicos
            nlp_result: Resultado NLP (opcional)

        Returns:
            Score final [0-100]
        """
        score = 0.0

        # Scores heuristicos
        score += scores_por_dimension['accesibilidad']['percentage'] * self.PESOS['accesibilidad']
        score += scores_por_dimension['usabilidad']['percentage'] * self.PESOS['usabilidad']
        score += scores_por_dimension['semantica']['percentage'] * self.PESOS['semantica_tecnica']
        score += scores_por_dimension['soberania']['percentage'] * self.PESOS['soberania']

        # Score NLP
        if nlp_result:
            score += nlp_result['global_score'] * self.PESOS['semantica_nlp']
        else:
            # Si no hay NLP, redistribuir peso a semántica técnica
            score += scores_por_dimension['semantica']['percentage'] * self.PESOS['semantica_nlp']

        return round(score, 2)

    # ========================================================================
    # MODO SIN BASE DE DATOS (para testing directo)
    # ========================================================================

    def evaluate_url(self, url: str) -> Dict[str, Any]:
        """
        Evalua una URL directamente sin usar base de datos (SYNC).

        Este metodo es SYNC y sera ejecutado en un ThreadPoolExecutor
        desde el endpoint async de FastAPI.

        Ejecuta:
        - 33 criterios heuristicos (ACC, USA, SEM, SOB)
        - Analisis NLP complementario (coherencia, ambiguedad, claridad)
        - Total: 33 criterios + 3 criterios NLP = 36 resultados

        Args:
            url: URL del sitio a evaluar

        Returns:
            Dict con resultados completos incluyendo:
            - url, status, timestamp
            - scores (por dimension + total)
            - criteria_results (lista de criterios evaluados)
            - nlp_analysis (analisis NLP completo)
            - summary (estadisticas)
        """
        if not self.crawler:
            raise RuntimeError("Crawler no disponible. Instalar dependencias.")

        logger.info(f"Iniciando evaluacion de: {url}")
        logger.info("=" * 60)

        # 1. Crawlear el sitio (SYNC)
        logger.info("[1/3] Extrayendo contenido...")
        extracted_content = self.crawler.crawl(url)

        if 'error' in extracted_content:
            raise RuntimeError(f"Error al crawlear: {extracted_content['error']}")

        logger.info(f"      Contenido extraido correctamente")

        # 2. Ejecutar evaluadores heuristicos
        logger.info("[2/3] Ejecutando evaluadores heuristicos...")
        all_results = []
        scores_por_dimension = {}

        for dimension_name, evaluador in self.evaluadores.items():
            logger.info(f"      Evaluando {dimension_name}...")
            try:
                results = evaluador.evaluate(extracted_content)
                dimension_score = evaluador.get_dimension_score()
                scores_por_dimension[dimension_name] = dimension_score
                all_results.extend(results)
                logger.info(f"      {dimension_name}: {dimension_score['percentage']:.1f}%")
            except Exception as e:
                logger.error(f"      Error en {dimension_name}: {e}")
                scores_por_dimension[dimension_name] = {
                    'percentage': 0,
                    'total_score': 0,
                    'max_score': 0,
                    'passed': 0,
                    'failed': 0,
                    'partial': 0
                }

        # 3. Ejecutar análisis NLP
        logger.info("[3/3] Ejecutando análisis NLP...")
        nlp_result = None
        if self.nlp_analyzer:
            try:
                nlp_result = self._run_nlp_analysis(extracted_content)
                if nlp_result:
                    logger.info(f"      NLP Global: {nlp_result['global_score']:.1f}%")
                    logger.info(f"      - Coherencia: {nlp_result['coherence_score']:.1f}%")
                    logger.info(f"      - Ambiguedad: {nlp_result['ambiguity_score']:.1f}%")
                    logger.info(f"      - Claridad: {nlp_result['clarity_score']:.1f}%")

                    # Crear resultados de criterios NLP (sin ID de evaluation)
                    nlp_criteria_dicts = self._create_nlp_criteria_dicts(nlp_result)
                    all_results.extend(nlp_criteria_dicts)
            except Exception as e:
                logger.error(f"      Error en NLP: {e}")
        else:
            logger.warning("      NLP no disponible")

        # 4. Calcular score final ponderado
        score_final = self._calculate_final_score(scores_por_dimension, nlp_result)

        logger.info("=" * 60)
        logger.info(f"SCORE FINAL: {score_final:.1f}%")
        logger.info(f"  Accesibilidad (30%): {scores_por_dimension.get('accesibilidad', {}).get('percentage', 0):.1f}%")
        logger.info(f"  Usabilidad (30%): {scores_por_dimension.get('usabilidad', {}).get('percentage', 0):.1f}%")
        logger.info(f"  Semantica Tecnica (15%): {scores_por_dimension.get('semantica', {}).get('percentage', 0):.1f}%")
        if nlp_result:
            logger.info(f"  Semantica NLP (15%): {nlp_result['global_score']:.1f}%")
        logger.info(f"  Soberania (10%): {scores_por_dimension.get('soberania', {}).get('percentage', 0):.1f}%")
        logger.info("=" * 60)

        # Contar resultados
        def get_status(r):
            if hasattr(r, 'status'):
                return r.status
            return r.get('status', '')

        return {
            "url": url,
            "status": "completed",
            "timestamp": datetime.now(_TZ_BOT).replace(tzinfo=None).isoformat(),
            "scores": {
                "accesibilidad": scores_por_dimension.get('accesibilidad', {}),
                "usabilidad": scores_por_dimension.get('usabilidad', {}),
                "semantica_tecnica": scores_por_dimension.get('semantica', {}),
                "semantica_nlp": {
                    "percentage": nlp_result['global_score'] if nlp_result else 0,
                    "coherence": nlp_result['coherence_score'] if nlp_result else 0,
                    "ambiguity": nlp_result['ambiguity_score'] if nlp_result else 0,
                    "clarity": nlp_result['clarity_score'] if nlp_result else 0,
                    "wcag_compliance": nlp_result.get('wcag_compliance', {}) if nlp_result else {}
                } if nlp_result else None,
                "soberania": scores_por_dimension.get('soberania', {}),
                "total": score_final
            },
            "nlp_analysis": nlp_result,
            "criteria_results": _enrich_criteria_results([
                r.to_dict() if hasattr(r, 'to_dict') else r
                for r in all_results
            ]),
            "summary": {
                "total_criteria": len(all_results),
                "heuristic_criteria": 32,
                "nlp_criteria": 3 if nlp_result else 0,
                "passed": len([r for r in all_results if get_status(r) == "pass"]),
                "failed": len([r for r in all_results if get_status(r) == "fail"]),
                "partial": len([r for r in all_results if get_status(r) == "partial"]),
                "not_applicable": len([r for r in all_results if get_status(r) == "na"])
            }
        }

    def _create_nlp_criteria_dicts(self, nlp_result: Dict[str, Any]) -> List[Dict]:
        """
        Crea diccionarios de criterios NLP para modo sin BD.

        Args:
            nlp_result: Resultado del NLPAnalyzer

        Returns:
            Lista de dicts con criterios NLP
        """
        criteria = []
        wcag = nlp_result.get('wcag_compliance', {})

        # ACC-07: Labels or Instructions
        acc07_pass = wcag.get('ACC-07', False)
        criteria.append({
            'criteria_id': 'ACC-07-NLP',
            'criteria_name': 'Labels or Instructions (NLP)',
            'dimension': 'semantica_nlp',
            'lineamiento': 'WCAG 3.3.2 - Level A',
            'status': 'pass' if acc07_pass else 'fail',
            'score': 1.0 if acc07_pass else 0.0,
            'max_score': 1.0,
            'details': {
                'source': 'NLP Analysis',
                'wcag_criterion': '3.3.2',
                'analysis': 'Análisis de claridad en labels'
            }
        })

        # ACC-08: Link Purpose
        acc08_pass = wcag.get('ACC-08', False)
        criteria.append({
            'criteria_id': 'ACC-08-NLP',
            'criteria_name': 'Link Purpose (NLP)',
            'dimension': 'semantica_nlp',
            'lineamiento': 'WCAG 2.4.4 - Level A',
            'status': 'pass' if acc08_pass else 'fail',
            'score': 1.0 if acc08_pass else 0.0,
            'max_score': 1.0,
            'details': {
                'source': 'NLP Analysis',
                'wcag_criterion': '2.4.4',
                'analysis': 'Detección de enlaces genéricos'
            }
        })

        # ACC-09: Headings and Labels
        acc09_pass = wcag.get('ACC-09', False)
        criteria.append({
            'criteria_id': 'ACC-09-NLP',
            'criteria_name': 'Headings and Labels (NLP)',
            'dimension': 'semantica_nlp',
            'lineamiento': 'WCAG 2.4.6 - Level AA',
            'status': 'pass' if acc09_pass else 'fail',
            'score': 1.0 if acc09_pass else 0.0,
            'max_score': 1.0,
            'details': {
                'source': 'NLP Analysis',
                'wcag_criterion': '2.4.6',
                'analysis': 'Coherencia semántica heading-contenido'
            }
        })

        return criteria


# ============================================================================
# FUNCION DE CONVENIENCIA PARA USO DIRECTO
# ============================================================================

def evaluar_url(url: str) -> Dict[str, Any]:
    """
    Funcion de conveniencia para evaluar una URL directamente (SYNC).

    Esta funcion es SYNC y sera ejecutada en un ThreadPoolExecutor
    desde el endpoint async de FastAPI.

    Ejemplo de uso:
        from app.evaluator.evaluation_engine import evaluar_url
        resultado = evaluar_url('https://www.aduana.gob.bo')
        print(f"Score total: {resultado['scores']['total']}%")

    Args:
        url: URL del sitio a evaluar

    Returns:
        Dict con resultados completos
    """
    engine = EvaluationEngine()
    return engine.evaluate_url(url)
