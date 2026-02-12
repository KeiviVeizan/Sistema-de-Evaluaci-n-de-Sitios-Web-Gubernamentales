"""
Generador de informes PDF para evaluaciones de cumplimiento web.

Usa ReportLab para crear PDFs completos y profesionales con los resultados
de evaluación, incluyendo portada, resumen ejecutivo, resultados por dimensión,
criterios no cumplidos y recomendaciones generales.
"""

import io
from collections import defaultdict
from datetime import datetime
from sqlalchemy.orm import Session

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, PageBreak, KeepTogether
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
from reportlab.graphics.shapes import Drawing, Rect, String as GString
from reportlab.graphics import renderPDF
from reportlab.platypus.flowables import Flowable

from app.models.database_models import (
    Evaluation, CriteriaResult, Website, Institution, NLPAnalysis
)

import logging

logger = logging.getLogger(__name__)

# ── Colores institucionales ───────────────────────────────────────────────────
COLOR_HEADER       = colors.HexColor('#1a3a5c')   # Azul oscuro
COLOR_SUBHEADER    = colors.HexColor('#2c5f8a')   # Azul medio
COLOR_ACCENT       = colors.HexColor('#e8f0f7')   # Azul muy claro
COLOR_PASS         = colors.HexColor('#10b981')   # Verde
COLOR_FAIL         = colors.HexColor('#ef4444')   # Rojo
COLOR_PARTIAL      = colors.HexColor('#f59e0b')   # Amarillo/ámbar
COLOR_NA           = colors.HexColor('#95a5a6')   # Gris
COLOR_TABLE_HEADER = colors.HexColor('#1a3a5c')
COLOR_ROW_ODD      = colors.HexColor('#f0f5fa')
COLOR_ROW_EVEN     = colors.white
COLOR_SECTION_BG   = colors.HexColor('#1a3a5c')
COLOR_WARNING_BG   = colors.HexColor('#fff8e1')
COLOR_PRIORITY_HIGH   = colors.HexColor('#ef4444')
COLOR_PRIORITY_MED    = colors.HexColor('#f59e0b')
COLOR_PRIORITY_LOW    = colors.HexColor('#10b981')

PAGE_W, PAGE_H = A4

# Etiquetas de dimensiones
DIMENSION_LABELS = {
    'accesibilidad':     'Accesibilidad',
    'usabilidad':        'Usabilidad',
    'semantica_tecnica': 'Semántica Técnica',
    'semantica_nlp':     'Semántica NLP',
    'soberania':         'Soberanía Digital',
}

STATUS_LABELS = {
    'pass':    'CUMPLE',
    'fail':    'NO CUMPLE',
    'partial': 'PARCIAL',
    'na':      'N/A',
}

STATUS_COLORS = {
    'pass':    COLOR_PASS,
    'fail':    COLOR_FAIL,
    'partial': COLOR_PARTIAL,
    'na':      COLOR_NA,
}

PRIORITY_MAP = {
    'accesibilidad':     'Alta',
    'soberania':         'Alta',
    'usabilidad':        'Media',
    'semantica_tecnica': 'Media',
    'semantica_nlp':     'Baja',
}

PRIORITY_COLOR = {
    'Alta':  COLOR_PRIORITY_HIGH,
    'Media': COLOR_PRIORITY_MED,
    'Baja':  COLOR_PRIORITY_LOW,
}

RECOMMENDATIONS_BY_DIMENSION = {
    'accesibilidad': [
        "Agregar atributos alt descriptivos en todas las imágenes.",
        "Asegurar contraste de color mínimo 4.5:1 (WCAG AA).",
        "Implementar navegación por teclado completa.",
        "Añadir etiquetas ARIA donde corresponda.",
        "Proveer transcripciones para contenido multimedia.",
    ],
    'usabilidad': [
        "Simplificar la estructura de navegación principal.",
        "Asegurar que todos los formularios tengan etiquetas claras.",
        "Incluir mapa del sitio y buscador interno.",
        "Optimizar tiempos de carga (meta: < 3 segundos).",
        "Garantizar diseño responsivo para dispositivos móviles.",
    ],
    'semantica_tecnica': [
        "Completar metadatos Open Graph y Schema.org.",
        "Usar etiquetas semánticas HTML5 (header, main, footer, nav).",
        "Declarar el idioma del documento con lang='es'.",
        "Implementar datos estructurados para contenido institucional.",
        "Validar el HTML con el validador W3C.",
    ],
    'semantica_nlp': [
        "Usar lenguaje claro y accesible para ciudadanos.",
        "Evitar tecnicismos sin definición previa.",
        "Estructurar el contenido con encabezados jerárquicos.",
        "Incluir resúmenes en documentos extensos.",
    ],
    'soberania': [
        "Migrar recursos estáticos a servidores .gob.bo.",
        "Eliminar dependencias de CDN externos no nacionales.",
        "Usar fuentes tipográficas alojadas localmente.",
        "Revisar scripts de terceros y evaluar alternativas nacionales.",
    ],
}

RESOURCES = [
    "WCAG 2.1 – https://www.w3.org/TR/WCAG21/",
    "D.S. 3925 – Decreto Supremo sobre gobierno electrónico Bolivia",
    "Validador W3C – https://validator.w3.org/",
    "Herramienta WAVE – https://wave.webaim.org/",
    "Google Lighthouse – https://developer.chrome.com/docs/lighthouse/",
]


# ── Estilos ───────────────────────────────────────────────────────────────────

def _build_styles() -> dict:
    base = getSampleStyleSheet()

    def ps(name, **kw):
        parent = kw.pop('parent', base['Normal'])
        return ParagraphStyle(name, parent=parent, **kw)

    return {
        'cover_title': ps('CoverTitle',
            fontSize=22, textColor=colors.white,
            alignment=TA_CENTER, fontName='Helvetica-Bold',
            spaceAfter=8, leading=28),
        'cover_sub': ps('CoverSub',
            fontSize=13, textColor=colors.HexColor('#cce0f5'),
            alignment=TA_CENTER, fontName='Helvetica', spaceAfter=4),
        'cover_meta': ps('CoverMeta',
            fontSize=10, textColor=colors.HexColor('#b0c8e0'),
            alignment=TA_CENTER, fontName='Helvetica', spaceAfter=3),
        'title': ps('ReportTitle',
            parent=base['Title'],
            fontSize=18, textColor=COLOR_HEADER,
            spaceAfter=4, alignment=TA_CENTER, fontName='Helvetica-Bold'),
        'subtitle': ps('ReportSubtitle',
            fontSize=11, textColor=COLOR_SUBHEADER,
            spaceAfter=2, alignment=TA_CENTER, fontName='Helvetica'),
        'section': ps('SectionHeader',
            parent=base['Heading2'],
            fontSize=13, textColor=colors.white,
            spaceBefore=12, spaceAfter=8,
            fontName='Helvetica-Bold', backColor=COLOR_SECTION_BG,
            borderPad=6, leading=18),
        'dim_header': ps('DimHeader',
            fontSize=11, textColor=COLOR_HEADER,
            spaceBefore=10, spaceAfter=4,
            fontName='Helvetica-Bold', leading=15),
        'body': ps('BodyText',
            fontSize=9, textColor=colors.HexColor('#2c3e50'),
            spaceAfter=3, fontName='Helvetica', leading=13),
        'body_justify': ps('BodyJustify',
            fontSize=9, textColor=colors.HexColor('#2c3e50'),
            spaceAfter=3, fontName='Helvetica', leading=13,
            alignment=TA_JUSTIFY),
        'body_bold': ps('BodyBold',
            fontSize=9, textColor=colors.HexColor('#2c3e50'),
            fontName='Helvetica-Bold'),
        'footer': ps('Footer',
            fontSize=7.5, textColor=colors.HexColor('#7f8c8d'),
            alignment=TA_CENTER, fontName='Helvetica'),
        'criteria_text': ps('CriteriaText',
            fontSize=8, textColor=colors.HexColor('#2c3e50'),
            fontName='Helvetica', wordWrap='CJK', leading=11),
        'obs_text': ps('ObsText',
            fontSize=7.5, textColor=colors.HexColor('#555'),
            fontName='Helvetica-Oblique', wordWrap='CJK', leading=11),
        'th_white': ps('ThWhite',
            fontSize=8, textColor=colors.white,
            fontName='Helvetica-Bold', alignment=TA_CENTER),
        'cell_center': ps('CellCenter',
            fontSize=8, alignment=TA_CENTER, fontName='Helvetica'),
        'cell_bold_center': ps('CellBoldCenter',
            fontSize=8, alignment=TA_CENTER, fontName='Helvetica-Bold'),
        'score_big': ps('ScoreBig',
            fontSize=36, fontName='Helvetica-Bold',
            alignment=TA_CENTER, leading=42),
        'score_label': ps('ScoreLabel',
            fontSize=10, textColor=COLOR_SUBHEADER,
            alignment=TA_CENTER, fontName='Helvetica'),
        'rec_title': ps('RecTitle',
            fontSize=9, textColor=COLOR_HEADER,
            fontName='Helvetica-Bold', spaceAfter=2),
        'bullet': ps('Bullet',
            fontSize=8.5, textColor=colors.HexColor('#2c3e50'),
            fontName='Helvetica', leftIndent=12, spaceAfter=2, leading=13),
    }


# ── Helpers ───────────────────────────────────────────────────────────────────

def _score_color(pct: float) -> colors.Color:
    if pct >= 80:
        return COLOR_PASS
    elif pct >= 50:
        return COLOR_PARTIAL
    return COLOR_FAIL


def _hex(c: colors.Color) -> str:
    """Retorna hex sin '#' compatible con ReportLab."""
    try:
        h = c.hexval()
        return h[2:] if h.startswith('0x') else h
    except Exception:
        return '000000'


def _status_badge(label: str, color: colors.Color, style: ParagraphStyle) -> Paragraph:
    return Paragraph(
        f'<font color="#{_hex(color)}"><b>{label}</b></font>',
        style
    )


def _th(text: str, styles: dict) -> Paragraph:
    return Paragraph(f"<b>{text}</b>", styles['th_white'])


def _extract_observations(details: dict | None) -> str:
    if not details:
        return ""
    for key in ('observations', 'message', 'error', 'description'):
        val = details.get(key)
        if val:
            if isinstance(val, list):
                val = "; ".join(str(v) for v in val[:3])
            return str(val)[:250]
    return ""


def _extract_recommendations(details: dict | None) -> str:
    if not details:
        return ""
    val = details.get('recommendations') or details.get('recommendation') or details.get('fix')
    if not val:
        return ""
    if isinstance(val, list):
        return "; ".join(str(v) for v in val[:3])
    return str(val)[:250]


def _bar_chart(dim_scores: dict, width_pts: float = 430, bar_h: int = 18, gap: int = 6) -> Drawing:
    """Gráfico de barras horizontal simple con ReportLab Graphics."""
    items = [(DIMENSION_LABELS.get(k, k), float(v or 0)) for k, v in dim_scores.items()]
    n = len(items)
    label_w = 130
    bar_area = width_pts - label_w - 50  # 50 para texto %
    total_h = n * (bar_h + gap) + 20

    d = Drawing(width_pts, total_h)

    for i, (label, pct) in enumerate(items):
        y = total_h - 15 - i * (bar_h + gap)
        bar_color = _score_color(pct)

        # Fondo gris
        bg = Rect(label_w, y, bar_area, bar_h,
                  fillColor=colors.HexColor('#e5e7eb'), strokeColor=None)
        d.add(bg)

        # Barra coloreada
        fill_w = (pct / 100.0) * bar_area
        if fill_w > 0:
            bar = Rect(label_w, y, fill_w, bar_h,
                       fillColor=bar_color, strokeColor=None)
            d.add(bar)

        # Etiqueta dimensión
        lbl = GString(label_w - 4, y + bar_h / 2 + 3, label,
                      fontName='Helvetica', fontSize=8,
                      fillColor=colors.HexColor('#374151'),
                      textAnchor='end')
        d.add(lbl)

        # Porcentaje
        pct_lbl = GString(label_w + fill_w + 5, y + bar_h / 2 + 3,
                          f"{pct:.1f}%",
                          fontName='Helvetica-Bold', fontSize=8,
                          fillColor=_hex_rgb(bar_color),
                          textAnchor='start')
        d.add(pct_lbl)

    return d


def _hex_rgb(c: colors.Color):
    """Retorna el color como objeto para GString."""
    return c


# ── Secciones del PDF ─────────────────────────────────────────────────────────

def _build_cover(story: list, styles: dict,
                 institution_name: str, domain: str,
                 eval_date: datetime, evaluator_name: str,
                 total_score: float):
    """Portada del informe."""
    # Bloque azul superior simulado con tabla de fondo
    cover_data = [[
        Paragraph(
            "INFORME DE EVALUACIÓN DE CUMPLIMIENTO WEB",
            styles['cover_title']
        )
    ]]
    cover_table = Table(cover_data, colWidths=['100%'])
    cover_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), COLOR_HEADER),
        ('TOPPADDING', (0, 0), (-1, -1), 28),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 28),
        ('LEFTPADDING', (0, 0), (-1, -1), 12),
        ('RIGHTPADDING', (0, 0), (-1, -1), 12),
    ]))
    story.append(cover_table)
    story.append(Spacer(1, 0.5 * cm))

    story.append(Paragraph("Estado Plurinacional de Bolivia", styles['subtitle']))
    story.append(Paragraph("Agencia para el Desarrollo de la Sociedad de la Información en Bolivia", styles['subtitle']))
    story.append(Spacer(1, 0.4 * cm))
    story.append(HRFlowable(width="100%", thickness=2, color=COLOR_HEADER))
    story.append(Spacer(1, 0.6 * cm))

    # Datos de portada
    meta_data = [
        [Paragraph("<b>Institución evaluada:</b>", styles['body']),
         Paragraph(institution_name, styles['body'])],
        [Paragraph("<b>Dominio:</b>", styles['body']),
         Paragraph(domain or "N/D", styles['body'])],
        [Paragraph("<b>Fecha de evaluación:</b>", styles['body']),
         Paragraph(eval_date.strftime("%d de %B de %Y"), styles['body'])],
        [Paragraph("<b>Evaluador responsable:</b>", styles['body']),
         Paragraph(evaluator_name, styles['body'])],
        [Paragraph("<b>Puntaje global:</b>", styles['body']),
         Paragraph(
             f'<font color="#{_hex(_score_color(total_score))}"><b>{total_score:.1f}%</b></font>',
             styles['body_bold']
         )],
    ]
    meta_table = Table(meta_data, colWidths=[5.5 * cm, None])
    meta_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), COLOR_ACCENT),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#d0dce8')),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 0.6 * cm))

    # Nota legal
    story.append(Paragraph(
        "<i>Este documento es generado automáticamente por el Sistema de Evaluación "
        "de Cumplimiento Web GOB.BO y constituye un informe oficial de auditoría digital.</i>",
        styles['body_justify']
    ))
    story.append(PageBreak())


def _build_executive_summary(story: list, styles: dict,
                              total_score: float,
                              passed: int, partial: int, failed: int, na: int,
                              total_c: int,
                              dimension_scores: dict):
    """Sección 1 – Resumen Ejecutivo."""
    story.append(Paragraph("1. RESUMEN EJECUTIVO", styles['section']))
    story.append(Spacer(1, 0.2 * cm))

    # Puntaje global destacado
    score_color = _score_color(total_score)
    nivel_text = ("Satisfactorio" if total_score >= 80
                  else "En proceso" if total_score >= 50
                  else "Insatisfactorio")

    score_block = [
        [
            Paragraph(
                f'<font color="#{_hex(score_color)}"><b>{total_score:.1f}%</b></font>',
                styles['score_big']
            ),
        ],
        [
            Paragraph(f"Puntaje Global de Cumplimiento — Nivel: {nivel_text}", styles['score_label']),
        ],
    ]
    score_t = Table(score_block, colWidths=['100%'])
    score_t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), COLOR_ACCENT),
        ('BOX', (0, 0), (-1, -1), 1.5, COLOR_SUBHEADER),
        ('TOPPADDING', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    story.append(score_t)
    story.append(Spacer(1, 0.4 * cm))

    # Tabla resumen estadístico
    story.append(Paragraph("Resumen de Criterios Evaluados", styles['dim_header']))
    th_style = ParagraphStyle('th2', fontSize=8, textColor=colors.white,
                               fontName='Helvetica-Bold', alignment=TA_CENTER)
    sum_header = [
        Paragraph("<b>Total criterios</b>", th_style),
        Paragraph("<b>Aprobados</b>", th_style),
        Paragraph("<b>Parciales</b>", th_style),
        Paragraph("<b>Fallidos</b>", th_style),
        Paragraph("<b>N/A</b>", th_style),
    ]
    pct_pass = (passed / total_c * 100) if total_c else 0

    def _num(v, c):
        return Paragraph(
            f'<font color="#{_hex(c)}"><b>{v}</b></font>',
            ParagraphStyle('n', fontSize=14, alignment=TA_CENTER, fontName='Helvetica-Bold')
        )

    sum_vals = [
        _num(total_c, COLOR_HEADER),
        _num(passed, COLOR_PASS),
        _num(partial, COLOR_PARTIAL),
        _num(failed, COLOR_FAIL),
        _num(na, COLOR_NA),
    ]
    sum_table = Table([sum_header, sum_vals], colWidths=[None] * 5)
    sum_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), COLOR_TABLE_HEADER),
        ('BACKGROUND', (0, 1), (-1, 1), COLOR_ACCENT),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#d0dce8')),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(sum_table)
    story.append(Spacer(1, 0.4 * cm))

    # Gráfico de barras por dimensión
    story.append(Paragraph("Puntajes por Dimensión", styles['dim_header']))
    chart = _bar_chart(dimension_scores, width_pts=430)
    story.append(chart)
    story.append(Spacer(1, 0.3 * cm))

    # Tabla de puntajes por dimensión
    dim_h = [
        _th("Dimensión", styles),
        _th("Puntaje", styles),
        _th("Nivel", styles),
    ]
    dim_rows = [dim_h]
    for dim_key, dim_label in DIMENSION_LABELS.items():
        pct = float(dimension_scores.get(dim_key) or 0)
        if isinstance(pct, dict):
            pct = pct.get('percentage', 0)
        nivel = ("Satisfactorio" if pct >= 80
                 else "En proceso" if pct >= 50
                 else "Insatisfactorio")
        c = _score_color(pct)
        dim_rows.append([
            Paragraph(dim_label, styles['body']),
            Paragraph(f'<font color="#{_hex(c)}"><b>{pct:.1f}%</b></font>',
                      styles['cell_bold_center']),
            Paragraph(f'<font color="#{_hex(c)}"><b>{nivel}</b></font>',
                      styles['cell_bold_center']),
        ])
    dim_table = Table(dim_rows, colWidths=[8 * cm, 4 * cm, 5 * cm])
    dim_ts = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), COLOR_TABLE_HEADER),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#d0dce8')),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
    ])
    for i in range(1, len(dim_rows)):
        bg = COLOR_ROW_ODD if i % 2 == 1 else COLOR_ROW_EVEN
        dim_ts.add('BACKGROUND', (0, i), (-1, i), bg)
    dim_table.setStyle(dim_ts)
    story.append(dim_table)
    story.append(PageBreak())


def _build_dimension_results(story: list, styles: dict,
                              criteria_by_dim: dict,
                              dimension_scores: dict,
                              nlp=None):
    """Sección 2 – Resultados por Dimensión."""
    story.append(Paragraph("2. RESULTADOS POR DIMENSIÓN", styles['section']))
    story.append(Spacer(1, 0.2 * cm))

    for dim_key, dim_label in DIMENSION_LABELS.items():
        results = criteria_by_dim.get(dim_key, [])
        if not results:
            continue

        pct = float(dimension_scores.get(dim_key) or 0)
        color = _score_color(pct)

        # Encabezado dimensión
        dim_title_data = [[
            Paragraph(
                f'<b>{dim_label}</b>',
                ParagraphStyle('dt', fontSize=11, textColor=colors.white,
                               fontName='Helvetica-Bold', leading=15)
            ),
            Paragraph(
                f'<font color="white"><b>{pct:.1f}%</b></font>',
                ParagraphStyle('dp', fontSize=14, textColor=colors.white,
                               fontName='Helvetica-Bold', alignment=TA_RIGHT, leading=18)
            ),
        ]]
        dim_title_t = Table(dim_title_data, colWidths=['75%', '25%'])
        dim_title_t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), color),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('LEFTPADDING', (0, 0), (-1, -1), 10),
            ('RIGHTPADDING', (0, 0), (-1, -1), 10),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        story.append(dim_title_t)
        story.append(Spacer(1, 0.15 * cm))

        # Sub-sección especial para Análisis Semántico (IA)
        if dim_key == 'semantica_nlp' and nlp is not None:
            # Encabezado sub-sección
            story.append(Paragraph(
                "<b>Métricas de Calidad del Contenido (Análisis IA)</b>",
                ParagraphStyle('nlp_sub', fontSize=10, textColor=COLOR_SUBHEADER,
                               fontName='Helvetica-Bold', leading=14,
                               spaceBefore=4, spaceAfter=2)
            ))
            story.append(Paragraph(
                "El modelo de IA analiza el contenido textual del sitio y produce las "
                "siguientes métricas independientes de los criterios WCAG:",
                ParagraphStyle('nlp_sub_note', fontSize=8, textColor=colors.HexColor('#555'),
                               fontName='Helvetica-Oblique', leading=11, spaceAfter=4)
            ))

            # Métricas principales: columnas con nombre + descripción + valor
            coherence_pct = float(nlp.coherence_score or 0)
            ambiguity_pct = float(nlp.ambiguity_score or 0)
            clarity_pct   = float(nlp.clarity_score or 0)

            metrics_data = [
                [
                    _th("Métrica", styles),
                    _th("Descripción", styles),
                    _th("Valor", styles),
                ],
                [
                    Paragraph("<b>Coherencia</b>", styles['criteria_text']),
                    Paragraph("Consistencia semántica del contenido", styles['obs_text']),
                    Paragraph(
                        f'<font color="#{_hex(_score_color(coherence_pct))}"><b>{coherence_pct:.1f}%</b></font>',
                        styles['cell_bold_center']
                    ),
                ],
                [
                    Paragraph("<b>Ambigüedad</b>", styles['criteria_text']),
                    Paragraph("Porcentaje de textos sin ambigüedad", styles['obs_text']),
                    Paragraph(
                        f'<font color="#{_hex(_score_color(ambiguity_pct))}"><b>{ambiguity_pct:.1f}%</b></font>',
                        styles['cell_bold_center']
                    ),
                ],
                [
                    Paragraph("<b>Claridad</b>", styles['criteria_text']),
                    Paragraph("Legibilidad y comprensión del lenguaje", styles['obs_text']),
                    Paragraph(
                        f'<font color="#{_hex(_score_color(clarity_pct))}"><b>{clarity_pct:.1f}%</b></font>',
                        styles['cell_bold_center']
                    ),
                ],
            ]
            metrics_t = Table(metrics_data, colWidths=[3.5 * cm, 9.5 * cm, 4.0 * cm])
            metrics_ts = TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), COLOR_TABLE_HEADER),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#d0dce8')),
                ('TOPPADDING', (0, 0), (-1, -1), 5),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
                ('LEFTPADDING', (0, 0), (-1, -1), 6),
                ('RIGHTPADDING', (0, 0), (-1, -1), 6),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ])
            for i in range(1, 4):
                bg = COLOR_ROW_ODD if i % 2 == 1 else COLOR_ROW_EVEN
                metrics_ts.add('BACKGROUND', (0, i), (-1, i), bg)
            metrics_t.setStyle(metrics_ts)
            story.append(metrics_t)
            story.append(Spacer(1, 0.2 * cm))

            # Recomendaciones del análisis IA
            nlp_recs = nlp.recommendations or []
            if nlp_recs:
                story.append(Paragraph(
                    "<b>Recomendaciones del análisis IA:</b>",
                    styles['body_bold']
                ))
                for rec in nlp_recs:
                    story.append(Paragraph(f"• {rec}", styles['bullet']))
                story.append(Spacer(1, 0.2 * cm))

            # Separador visual antes de criterios WCAG
            story.append(HRFlowable(width="100%", thickness=0.5,
                                    color=colors.HexColor('#d0dce8')))
            story.append(Spacer(1, 0.1 * cm))

            # Título y nota explicativa de criterios WCAG
            story.append(Paragraph(
                "<b>Criterios de Cumplimiento WCAG (NLP):</b>",
                ParagraphStyle('nlp_crit_title', fontSize=9, textColor=COLOR_HEADER,
                               fontName='Helvetica-Bold', leading=13,
                               spaceBefore=4, spaceAfter=2)
            ))
            story.append(Paragraph(
                "Los siguientes criterios evalúan el cumplimiento de estándares WCAG mediante "
                "análisis de procesamiento de lenguaje natural (NLP). Son independientes de "
                "las métricas IA mostradas arriba.",
                ParagraphStyle('nlp_wcag_note', fontSize=8, textColor=colors.HexColor('#555'),
                               fontName='Helvetica-Oblique', leading=11, spaceAfter=4)
            ))

        # Para semantica_nlp: mostrar solo criterios -NLP (sin duplicados)
        NLP_NAME_OVERRIDES = {
            'ACC-07-NLP': 'Etiquetas e instrucciones de formularios',
            'ACC-08-NLP': 'Propósito descriptivo de enlaces',
            'ACC-09-NLP': 'Encabezados y estructura del documento',
        }
        if dim_key == 'semantica_nlp':
            nlp_suffixed = [r for r in results if (r.criteria_id or '').endswith('-NLP')]
            if nlp_suffixed:
                display_results = nlp_suffixed
            else:
                # Fallback: sin sufijo, excluir duplicados usando los base ACC-07/08/09
                seen = set()
                display_results = []
                for r in results:
                    key = r.criteria_id or ''
                    if key not in seen:
                        seen.add(key)
                        display_results.append(r)
        else:
            display_results = results

        # Tabla de criterios
        crit_header = [
            _th("Código", styles),
            _th("Criterio / Lineamiento", styles),
            _th("Estado", styles),
            _th("Observaciones", styles),
        ]
        crit_rows = [crit_header]

        for i, cr in enumerate(display_results):
            s = cr.status or 'na'
            st_color = STATUS_COLORS.get(s, COLOR_NA)
            st_label = STATUS_LABELS.get(s, s.upper())

            obs = _extract_observations(cr.details)

            # Nombre mejorado para criterios NLP si existe override
            crit_name = NLP_NAME_OVERRIDES.get(cr.criteria_id, cr.criteria_name or '—')

            crit_rows.append([
                Paragraph(cr.criteria_id or "—", styles['criteria_text']),
                Paragraph(
                    f"<b>{crit_name}</b><br/>"
                    f"<font color='#6b7280' size='7'>{cr.lineamiento or ''}</font>",
                    styles['criteria_text']
                ),
                Paragraph(
                    f'<font color="#{_hex(st_color)}"><b>{st_label}</b></font>',
                    styles['cell_bold_center']
                ),
                Paragraph(obs or "—", styles['obs_text']),
            ])

        crit_t = Table(
            crit_rows,
            colWidths=[1.8 * cm, 6.0 * cm, 2.5 * cm, 6.7 * cm],
            repeatRows=1,
        )
        crit_ts = TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), COLOR_TABLE_HEADER),
            ('GRID', (0, 0), (-1, -1), 0.4, colors.HexColor('#d0dce8')),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
            ('LEFTPADDING', (0, 0), (-1, -1), 5),
            ('RIGHTPADDING', (0, 0), (-1, -1), 5),
        ])
        for i in range(1, len(crit_rows)):
            bg = COLOR_ROW_ODD if i % 2 == 1 else COLOR_ROW_EVEN
            crit_ts.add('BACKGROUND', (0, i), (-1, i), bg)
        crit_t.setStyle(crit_ts)

        story.append(crit_t)
        story.append(Spacer(1, 0.5 * cm))

    story.append(PageBreak())


def _build_non_compliant(story: list, styles: dict, non_compliant: list):
    """Sección 3 – Criterios No Cumplidos (detalle)."""
    story.append(Paragraph("3. CRITERIOS NO CUMPLIDOS — DETALLE", styles['section']))

    if not non_compliant:
        story.append(Spacer(1, 0.2 * cm))
        story.append(Paragraph(
            "Todos los criterios evaluados han sido cumplidos satisfactoriamente. "
            "No se registran incumplimientos en esta evaluación.",
            styles['body']
        ))
        story.append(PageBreak())
        return

    story.append(Paragraph(
        "Los siguientes criterios requieren atención prioritaria para alcanzar "
        "el nivel de cumplimiento exigido por la normativa vigente:",
        styles['body_justify']
    ))
    story.append(Spacer(1, 0.3 * cm))

    for i, cr in enumerate(non_compliant, 1):
        s = cr.status or 'fail'
        st_color = STATUS_COLORS.get(s, COLOR_FAIL)
        st_label = STATUS_LABELS.get(s, s.upper())
        priority = PRIORITY_MAP.get(cr.dimension, 'Media')
        p_color = PRIORITY_COLOR[priority]
        dim_label = DIMENSION_LABELS.get(cr.dimension, cr.dimension or "")

        obs = _extract_observations(cr.details)
        rec = _extract_recommendations(cr.details)

        # Bloque por criterio
        block = []

        # Encabezado del criterio
        hdr_data = [[
            Paragraph(
                f'<b>{i}. [{cr.criteria_id or "?"}] {cr.criteria_name or "Criterio sin nombre"}</b>',
                ParagraphStyle('ch', fontSize=9, textColor=colors.white,
                               fontName='Helvetica-Bold', leading=13)
            ),
            Paragraph(
                f'<font color="white"><b>{st_label}</b></font>',
                ParagraphStyle('cs', fontSize=9, textColor=colors.white,
                               fontName='Helvetica-Bold', alignment=TA_RIGHT, leading=13)
            ),
        ]]
        hdr_t = Table(hdr_data, colWidths=['75%', '25%'])
        hdr_t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), st_color),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('RIGHTPADDING', (0, 0), (-1, -1), 8),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        block.append(hdr_t)

        # Detalle
        detail_rows = [
            [Paragraph("<b>Dimensión:</b>", styles['body']),
             Paragraph(dim_label, styles['body']),
             Paragraph("<b>Prioridad:</b>", styles['body']),
             Paragraph(f'<font color="#{_hex(p_color)}"><b>{priority}</b></font>', styles['body'])],
            [Paragraph("<b>Lineamiento:</b>", styles['body']),
             Paragraph(cr.lineamiento or "—", styles['criteria_text']),
             Paragraph("<b>Puntaje:</b>", styles['body']),
             Paragraph(f"{cr.score:.1f} / {cr.max_score:.1f}", styles['body'])],
        ]
        detail_t = Table(detail_rows, colWidths=[2.5 * cm, 6.5 * cm, 2.0 * cm, 6.0 * cm])
        detail_t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f9fafb')),
            ('GRID', (0, 0), (-1, -1), 0.4, colors.HexColor('#e5e7eb')),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))
        block.append(detail_t)

        # Observaciones y recomendaciones
        obs_rec_rows = [
            [Paragraph("<b>¿Por qué falló?</b>", styles['body']),
             Paragraph(obs or "Sin observaciones detalladas registradas.", styles['obs_text'])],
            [Paragraph("<b>¿Cómo corregirlo?</b>", styles['body']),
             Paragraph(rec or "Ver recomendaciones generales de la dimensión.", styles['obs_text'])],
        ]
        obs_rec_t = Table(obs_rec_rows, colWidths=[3.5 * cm, None])
        obs_rec_t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), COLOR_ACCENT),
            ('BACKGROUND', (1, 0), (1, -1), colors.white),
            ('GRID', (0, 0), (-1, -1), 0.4, colors.HexColor('#e5e7eb')),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))
        block.append(obs_rec_t)
        block.append(Spacer(1, 0.35 * cm))

        story.append(KeepTogether(block))

    story.append(PageBreak())


def _build_recommendations(story: list, styles: dict,
                            non_compliant: list,
                            dimension_scores: dict):
    """Sección 4 – Recomendaciones Generales."""
    story.append(Paragraph("4. RECOMENDACIONES GENERALES", styles['section']))
    story.append(Spacer(1, 0.2 * cm))

    story.append(Paragraph(
        "A continuación se presentan las acciones prioritarias recomendadas para mejorar "
        "el nivel de cumplimiento del sitio evaluado:",
        styles['body_justify']
    ))
    story.append(Spacer(1, 0.3 * cm))

    # Dimensiones afectadas (ordenadas por puntaje ascendente)
    dims_affected = sorted(
        [(k, float(v or 0)) for k, v in dimension_scores.items()],
        key=lambda x: x[1]
    )

    for dim_key, pct in dims_affected:
        if pct >= 80:
            continue  # dimensión satisfactoria, sin recomendaciones urgentes
        dim_label = DIMENSION_LABELS.get(dim_key, dim_key)
        recs = RECOMMENDATIONS_BY_DIMENSION.get(dim_key, [])
        priority = PRIORITY_MAP.get(dim_key, 'Media')
        p_color = PRIORITY_COLOR[priority]

        story.append(Paragraph(
            f'■ {dim_label} '
            f'(<font color="#{_hex(p_color)}"><b>Prioridad {priority}</b></font> — '
            f'Puntaje actual: {pct:.1f}%)',
            styles['rec_title']
        ))
        for rec in recs:
            story.append(Paragraph(f"• {rec}", styles['bullet']))
        story.append(Spacer(1, 0.2 * cm))

    # Plazo sugerido
    story.append(Spacer(1, 0.1 * cm))
    story.append(Paragraph("Plazo Sugerido de Corrección", styles['dim_header']))

    plazo_data = [
        [Paragraph("<b>Prioridad</b>", styles['th_white']),
         Paragraph("<b>Plazo recomendado</b>", styles['th_white']),
         Paragraph("<b>Criterio</b>", styles['th_white'])],
        [Paragraph(f'<font color="#{_hex(COLOR_PRIORITY_HIGH)}"><b>Alta</b></font>', styles['body']),
         Paragraph("30 días hábiles", styles['body']),
         Paragraph("Accesibilidad, Soberanía Digital", styles['body'])],
        [Paragraph(f'<font color="#{_hex(COLOR_PRIORITY_MED)}"><b>Media</b></font>', styles['body']),
         Paragraph("60 días hábiles", styles['body']),
         Paragraph("Usabilidad, Semántica Técnica", styles['body'])],
        [Paragraph(f'<font color="#{_hex(COLOR_PRIORITY_LOW)}"><b>Baja</b></font>', styles['body']),
         Paragraph("90 días hábiles", styles['body']),
         Paragraph("Semántica NLP", styles['body'])],
    ]
    plazo_t = Table(plazo_data, colWidths=[3 * cm, 5 * cm, None])
    plazo_ts = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), COLOR_TABLE_HEADER),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#d0dce8')),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ])
    for i in range(1, 4):
        bg = COLOR_ROW_ODD if i % 2 == 1 else COLOR_ROW_EVEN
        plazo_ts.add('BACKGROUND', (0, i), (-1, i), bg)
    plazo_t.setStyle(plazo_ts)
    story.append(plazo_t)
    story.append(Spacer(1, 0.4 * cm))

    # Recursos útiles
    story.append(Paragraph("Recursos Útiles", styles['dim_header']))
    for res in RESOURCES:
        story.append(Paragraph(f"• {res}", styles['bullet']))


# ── Función principal ─────────────────────────────────────────────────────────

def generate_evaluation_report(evaluation_id: int, db: Session) -> bytes:
    """
    Genera un informe PDF completo y profesional con los resultados de una evaluación.

    Args:
        evaluation_id: ID de la evaluación en la base de datos.
        db: Sesión de SQLAlchemy.

    Returns:
        Bytes del PDF generado.

    Raises:
        ValueError: Si la evaluación no existe.
    """
    # ── 1. Consultar datos ────────────────────────────────────────────────────
    evaluation = db.query(Evaluation).filter(Evaluation.id == evaluation_id).first()
    if not evaluation:
        raise ValueError(f"Evaluación con id={evaluation_id} no encontrada")

    website = db.query(Website).filter(Website.id == evaluation.website_id).first()

    institution = None
    if website and website.domain:
        institution = db.query(Institution).filter(
            Institution.domain == website.domain
        ).first()

    criteria_results = db.query(CriteriaResult).filter(
        CriteriaResult.evaluation_id == evaluation_id
    ).order_by(CriteriaResult.dimension, CriteriaResult.criteria_id).all()

    # ── 2. Preparar datos derivados ───────────────────────────────────────────
    institution_name = (
        institution.name if institution
        else (website.institution_name if website else "Institución no identificada")
    )
    domain = (website.domain if website else "N/D") or "N/D"
    eval_date = evaluation.completed_at or evaluation.started_at or datetime.utcnow()
    generation_date = datetime.utcnow()

    # Evaluador: el modelo Evaluation no tiene FK a User; se indica sistema
    evaluator_name = "Sistema de Evaluación Automática GOB.BO"

    # Puntajes por dimensión
    dimension_scores: dict = {
        'accesibilidad':     float(evaluation.score_accessibility or 0),
        'usabilidad':        float(evaluation.score_usability or 0),
        'semantica_tecnica': float(evaluation.score_semantic_web or 0),
        'semantica_nlp':     0.0,
        'soberania':         float(evaluation.score_digital_sovereignty or 0),
    }

    # Intentar cargar puntaje NLP
    nlp = db.query(NLPAnalysis).filter(
        NLPAnalysis.evaluation_id == evaluation_id
    ).first()
    if nlp:
        dimension_scores['semantica_nlp'] = float(nlp.nlp_global_score or 0)

    total_score = float(evaluation.score_total or 0)

    # Estadísticas
    passed  = sum(1 for c in criteria_results if c.status == 'pass')
    failed  = sum(1 for c in criteria_results if c.status == 'fail')
    partial = sum(1 for c in criteria_results if c.status == 'partial')
    na      = sum(1 for c in criteria_results if c.status == 'na')
    total_c = len(criteria_results)

    failed_criteria  = [c for c in criteria_results if c.status == 'fail']
    partial_criteria = [c for c in criteria_results if c.status == 'partial']
    non_compliant    = failed_criteria + partial_criteria

    # Agrupar por dimensión
    criteria_by_dim: dict[str, list] = defaultdict(list)
    for cr in criteria_results:
        criteria_by_dim[cr.dimension or 'unknown'].append(cr)

    # ── 3. Construir PDF ──────────────────────────────────────────────────────
    buffer = io.BytesIO()

    # Función para pie de página con número de página
    def _add_footer(canvas, doc):
        canvas.saveState()
        canvas.setFont('Helvetica', 7.5)
        canvas.setFillColor(colors.HexColor('#7f8c8d'))
        footer_text = (
            f"Documento oficial — Sistema de Evaluación GOB.BO  |  "
            f"Generado el {generation_date.strftime('%d/%m/%Y %H:%M')} UTC"
        )
        canvas.drawCentredString(PAGE_W / 2, 1.2 * cm, footer_text)
        canvas.drawRightString(PAGE_W - 2 * cm, 1.2 * cm, f"Página {doc.page}")
        canvas.restoreState()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=2 * cm,
        leftMargin=2 * cm,
        topMargin=2.5 * cm,
        bottomMargin=2.5 * cm,
        title=f"Informe de Evaluación — {institution_name}",
        author="Sistema de Evaluación de Cumplimiento Web GOB.BO",
        subject=f"Evaluación #{evaluation_id} — {domain}",
    )

    styles = _build_styles()
    story = []

    # ── PORTADA ───────────────────────────────────────────────────────────────
    _build_cover(story, styles,
                 institution_name, domain,
                 eval_date, evaluator_name, total_score)

    # ── RESUMEN EJECUTIVO ─────────────────────────────────────────────────────
    _build_executive_summary(story, styles,
                             total_score,
                             passed, partial, failed, na, total_c,
                             dimension_scores)

    # ── RESULTADOS POR DIMENSIÓN ──────────────────────────────────────────────
    _build_dimension_results(story, styles, criteria_by_dim, dimension_scores, nlp=nlp)

    # ── CRITERIOS NO CUMPLIDOS ────────────────────────────────────────────────
    _build_non_compliant(story, styles, non_compliant)

    # ── RECOMENDACIONES GENERALES ─────────────────────────────────────────────
    _build_recommendations(story, styles, non_compliant, dimension_scores)

    # ── PIE DE PÁGINA FINAL ───────────────────────────────────────────────────
    story.append(Spacer(1, 0.8 * cm))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#d0dce8')))
    story.append(Spacer(1, 0.2 * cm))
    story.append(Paragraph(
        f"Informe de Evaluación #{evaluation_id} — {institution_name} — {domain}  |  "
        f"Generado el {generation_date.strftime('%d/%m/%Y %H:%M')} UTC  |  "
        "Sistema de Evaluación de Cumplimiento Web — Estado Plurinacional de Bolivia",
        styles['footer']
    ))

    # ── Generar PDF ───────────────────────────────────────────────────────────
    doc.build(story, onFirstPage=_add_footer, onLaterPages=_add_footer)
    pdf_bytes = buffer.getvalue()
    buffer.close()

    logger.info(
        "PDF generado para evaluación %d: %d bytes, institución='%s'",
        evaluation_id, len(pdf_bytes), institution_name
    )
    return pdf_bytes


def get_report_filename(evaluation_id: int, db: Session) -> str:
    """
    Retorna el nombre de archivo sugerido para el PDF.

    Formato: Informe_Evaluacion_{Institucion}_{YYYYMMDD}.pdf
    """
    evaluation = db.query(Evaluation).filter(Evaluation.id == evaluation_id).first()
    if not evaluation:
        return f"Informe_Evaluacion_{evaluation_id}.pdf"

    website = db.query(Website).filter(Website.id == evaluation.website_id).first()
    institution = None
    if website and website.domain:
        institution = db.query(Institution).filter(
            Institution.domain == website.domain
        ).first()

    inst_name = (
        institution.name if institution
        else (website.institution_name if website else "Institucion")
    )
    # Limpiar nombre para filename
    safe_name = (
        inst_name
        .replace(" ", "_")
        .replace("/", "-")
        .replace("\\", "-")
        .replace(":", "")
        .replace(".", "")
    )[:40]

    eval_date = evaluation.completed_at or evaluation.started_at or datetime.utcnow()
    date_str = eval_date.strftime("%Y%m%d")

    return f"Informe_Evaluacion_{safe_name}_{date_str}.pdf"
