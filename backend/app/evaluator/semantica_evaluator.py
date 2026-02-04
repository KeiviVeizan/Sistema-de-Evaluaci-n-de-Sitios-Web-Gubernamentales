"""
Evaluador de Semántica Web (15%)
Evalúa 10 criterios técnicos según Tabla 12:
- SEM-01 a SEM-04: Semántica HTML5 (4 criterios, 44 pts)
- SEO-01 a SEO-04: Optimización SEO (4 criterios, 38 pts)
- FMT-01 a FMT-02: Formato técnico (2 criterios, 18 pts)

Total: 100 puntos
Ponderación WCAG: A > AA > AAA (mayor puntaje a mayor prioridad)
"""
import logging
from typing import Dict, List
from .base_evaluator import BaseEvaluator, CriteriaEvaluation
from .buenas_practicas_html5 import (
    detectar_violaciones,
    calcular_penalizacion_total,
    generar_recomendaciones
)
from .recomendaciones_semanticas import RecomendacionesSemanticas

logger = logging.getLogger(__name__)


class EvaluadorSemantica(BaseEvaluator):
    """
    Evaluador de criterios de semántica web técnica.

    Evalúa 10 criterios en 3 grupos (según Tabla 12):
    - SEM: HTML5 semántico (4 criterios) = 44 pts
    - SEO: Optimización SEO (4 criterios) = 38 pts
    - FMT: Formato técnico (2 criterios) = 18 pts

    Ponderación basada en prioridad WCAG: A > AA > AAA
    Total: 100 puntos
    """

    # Tags HTML5 semanticos esperados
    SEMANTIC_TAGS = ['header', 'nav', 'main', 'article', 'section', 'aside', 'footer']

    # Extensiones de documentos para FMT-01
    FORMATOS_DOC_ABIERTOS = {
        '.pdf', '.odt', '.ods', '.odp', '.odf', '.csv', '.json',
        '.xml', '.txt', '.epub', '.html', '.htm'
    }
    FORMATOS_DOC_PROPIETARIOS = {
        '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx'
    }

    # Extensiones de imagen para FMT-02
    FORMATOS_IMG_OPTIMIZADOS = {'.webp', '.avif', '.svg'}
    FORMATOS_IMG_PESADOS = {'.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.tif', '.gif'}

    def __init__(self):
        super().__init__(dimension="semantica")

        # Pesos según Tabla 12 de la tesis
        # Ponderación WCAG: A > AA > AAA (mayor puntaje a mayor prioridad)
        self.criterios = {
            # Grupo SEM - Semántica HTML5 (44 pts)
            "SEM-01": {"name": "Uso de DOCTYPE HTML5", "points": 10, "lineamiento": "W3C HTML5 Standard"},
            "SEM-02": {"name": "Codificación UTF-8", "points": 10, "lineamiento": "W3C Encoding Standards"},
            "SEM-03": {"name": "Elementos semánticos HTML5", "points": 14, "lineamiento": "WCAG 1.3.1 (A) / W3C HTML5"},
            "SEM-04": {"name": "Separación contenido-presentación", "points": 10, "lineamiento": "D.S. 3925 (BP-05) / WCAG 1.3.1 (A)"},
            # Grupo SEO - Optimización (38 pts)
            "SEO-01": {"name": "Meta descripción", "points": 8, "lineamiento": "SEO Best Practices"},
            "SEO-02": {"name": "Meta Keywords", "points": 4, "lineamiento": "SEO Best Practices"},
            "SEO-03": {"name": "Meta viewport", "points": 12, "lineamiento": "WCAG 1.4.4 (AA) / Mobile-First"},
            "SEO-04": {"name": "Jerarquía de headings válida", "points": 14, "lineamiento": "WCAG 1.3.1 (A) / H42"},
            # Grupo FMT - Formato técnico (18 pts)
            "FMT-01": {"name": "Uso de formatos abiertos", "points": 10, "lineamiento": "D.S. 3925 / Acceso universal"},
            "FMT-02": {"name": "Imágenes optimizadas", "points": 8, "lineamiento": "WCAG 1.4.5 (AA) / Performance"},
        }

    def evaluate(self, extracted_content: Dict) -> List[CriteriaEvaluation]:
        """Evalúa todos los criterios de semántica técnica"""
        self.clear_results()

        # Extraer datos relevantes
        metadata = extracted_content.get('metadata', {})
        structure = extracted_content.get('structure', {})
        semantic_elements = extracted_content.get('semantic_elements', {})
        headings = extracted_content.get('headings', {})
        links = extracted_content.get('links', {})
        images = extracted_content.get('images', {})

        # Extraer document_hierarchy del structure (datos de buenas prácticas)
        document_hierarchy = structure.get('document_hierarchy', {})
        structure_analysis = document_hierarchy.get('structure_analysis', {})

        # Grupo SEM - Semántica HTML5 (44 pts)
        self.add_result(self._evaluar_sem01_doctype(structure))
        self.add_result(self._evaluar_sem02_utf8(structure))
        self.add_result(self._evaluar_sem03_elementos_semanticos(semantic_elements, structure_analysis))
        self.add_result(self._evaluar_sem04(extracted_content))

        # Grupo SEO - Optimización (38 pts)
        self.add_result(self._evaluar_seo01_meta_descripcion(metadata))
        self.add_result(self._evaluar_seo02_meta_keywords(metadata))
        self.add_result(self._evaluar_seo03_viewport(metadata))
        self.add_result(self._evaluar_seo04_headings(headings))

        # Grupo FMT - Formato técnico (18 pts)
        self.add_result(self._evaluar_fmt01_formatos_abiertos(links))
        self.add_result(self._evaluar_fmt02_imagenes_optimizadas(images))

        return self.results

    # ========================================================================
    # GRUPO SEM - Semántica HTML5 (44 pts)
    # ========================================================================

    def _evaluar_sem01_doctype(self, structure: Dict) -> CriteriaEvaluation:
        """
        SEM-01: Uso de DOCTYPE HTML5 (10 pts)
        W3C HTML5 Standard
        Verificar que el HTML declare <!DOCTYPE html>
        Score: 10.0 si existe, 0 si no
        """
        has_doctype = structure.get('has_html5_doctype', False)
        doctype_text = structure.get('doctype_text', '')

        if has_doctype:
            status = "pass"
            score = 10.0
            message = "DOCTYPE HTML5 declarado correctamente"
        else:
            status = "fail"
            score = 0.0
            message = "DOCTYPE HTML5 no declarado o incorrecto"

        return CriteriaEvaluation(
            criteria_id="SEM-01",
            criteria_name=self.criterios["SEM-01"]["name"],
            dimension=self.dimension,
            lineamiento=self.criterios["SEM-01"]["lineamiento"],
            status=status,
            score=score,
            max_score=10,
            details={
                "has_html5_doctype": has_doctype,
                "doctype_found": doctype_text if doctype_text else "No detectado",
                "message": message
            },
            evidence={
                "expected": "<!DOCTYPE html>",
                "found": doctype_text
            }
        )

    def _evaluar_sem02_utf8(self, structure: Dict) -> CriteriaEvaluation:
        """
        SEM-02: Codificación UTF-8 (10 pts)
        W3C Encoding Standards
        Verificar <meta charset="UTF-8"> o equivalente
        Score: 10 si existe, 5 si otro charset, 0 si no declarado
        """
        has_utf8 = structure.get('has_utf8_charset', False)
        charset_declared = structure.get('charset_declared', '')

        if has_utf8 or (charset_declared and charset_declared.lower() == 'utf-8'):
            status = "pass"
            score = 10.0
            message = "Encoding UTF-8 declarado correctamente"
        elif charset_declared:
            status = "partial"
            score = 5.0
            message = f"Encoding declarado pero no es UTF-8: {charset_declared}"
        else:
            status = "fail"
            score = 0.0
            message = "No se declaró encoding de caracteres"

        return CriteriaEvaluation(
            criteria_id="SEM-02",
            criteria_name=self.criterios["SEM-02"]["name"],
            dimension=self.dimension,
            lineamiento=self.criterios["SEM-02"]["lineamiento"],
            status=status,
            score=score,
            max_score=10,
            details={
                "has_utf8": has_utf8,
                "charset_declared": charset_declared if charset_declared else "No declarado",
                "expected": "UTF-8",
                "message": message
            },
            evidence={
                "declaration": f'<meta charset="{charset_declared}">' if charset_declared else "No encontrado"
            }
        )

    def _evaluar_sem03_elementos_semanticos(self, semantic_elements: Dict, structure_analysis: Dict) -> CriteriaEvaluation:
        """
        SEM-03: Elementos semánticos HTML5 (14 pts, WCAG 1.3.1 Level A)
        Según Tabla 12 - Interpretación correcta de estructura

        Evalúa:
        - Presencia de elementos semánticos (header, nav, main, footer, etc.)
        - Jerarquía correcta según estándares W3C
        - Sin violaciones estructurales (incluyendo divitis)
        - Uso apropiado de cada tag

        Score máximo: 14 puntos
        """
        issues = []
        scores = []

        # Verificar si tenemos datos de structure_analysis
        has_structure_data = bool(structure_analysis)

        if not has_structure_data:
            logger.warning("SEM-03: No hay datos de structure_analysis del crawler")
            # Fallback: solo verificar existencia (comportamiento anterior)
            return self._evaluar_sem03_fallback(semantic_elements)

        # ================================================================
        # 1. EVALUACION DE <main> (critico - 3 puntos)
        # ================================================================
        main_count = structure_analysis.get('main_count', 0)
        main_inside_section = structure_analysis.get('main_inside_section', False)

        if main_count == 1 and not main_inside_section:
            scores.append(3.0)  # Perfecto
        elif main_count == 1:
            scores.append(1.5)  # Existe pero mal ubicado
            issues.append(f"<main> esta dentro de <section> (incorrecto segun W3C)")
        elif main_count > 1:
            scores.append(0.5)
            issues.append(f"Multiples <main> ({main_count}), debe ser unico")
        else:
            scores.append(0.0)
            issues.append("Falta <main> para contenido principal")

        # ================================================================
        # 2. EVALUACION DE <header> (importante - 2 puntos)
        # ================================================================
        header_count = structure_analysis.get('header_count', 0)
        if header_count >= 1:
            scores.append(2.0)
        else:
            scores.append(0.0)
            issues.append("Falta <header> para contenido introductorio")

        # ================================================================
        # 3. EVALUACION DE <footer> (importante - 2 puntos)
        # ================================================================
        footer_count = structure_analysis.get('footer_count', 0)
        if footer_count >= 1:
            scores.append(2.0)
        else:
            scores.append(0.0)
            issues.append("Falta <footer> para informacion de cierre")

        # ================================================================
        # 4. EVALUACION DE <nav> (importante - 2 puntos)
        # ================================================================
        nav_count = structure_analysis.get('nav_count', 0)
        navs_in_header = structure_analysis.get('navs_in_header', 0)
        navs_floating = structure_analysis.get('navs_floating', 0)

        if nav_count >= 1:
            if navs_in_header >= 1 or navs_floating == 0:
                scores.append(2.0)  # Nav bien ubicado
            else:
                scores.append(1.5)  # Nav existe pero mal ubicado
                issues.append(f"<nav> fuera de <header>/<footer> ({navs_floating} flotantes)")
        else:
            scores.append(0.0)
            issues.append("Falta <nav> para navegacion")

        # ================================================================
        # 5. EVALUACION DE <article> (recomendado - 1.5 puntos)
        # ================================================================
        article_present = self.extract_present(semantic_elements.get('article', {}))
        if article_present:
            scores.append(1.5)
        else:
            scores.append(0.0)
            issues.append("Sin <article> (recomendado para contenido autonomo)")

        # ================================================================
        # 6. EVALUACION DE <section> (recomendado - 1.5 puntos)
        # ================================================================
        section_present = self.extract_present(semantic_elements.get('section', {}))
        if section_present:
            scores.append(1.5)
        else:
            scores.append(0.0)
            issues.append("Sin <section> (recomendado para agrupar contenido)")

        # ================================================================
        # 7. EVALUACION DE <aside> (opcional - 2 puntos)
        # ================================================================
        aside_present = self.extract_present(semantic_elements.get('aside', {}))
        if aside_present:
            scores.append(2.0)
        else:
            scores.append(0.0)
            issues.append("Sin <aside> (recomendado para contenido relacionado)")

        # ================================================================
        # PENALIZACION POR VIOLACIONES ESTRUCTURALES (incluye divitis)
        # ================================================================
        violaciones = detectar_violaciones(structure_analysis)
        penalizacion = calcular_penalizacion_total(violaciones)

        # Incluir TODAS las violaciones (incluyendo divitis)
        # Divitis ahora se evalúa aquí junto con la estructura semántica
        for v in violaciones:
            issues.append(f"VIOLACION: {v['mensaje']}")

        # Calcular score final
        total_score = sum(scores) - penalizacion
        total_score = max(0.0, min(14.0, total_score))

        # Determinar status
        if total_score >= 11:
            status = "pass"
            message = f"Buen uso de HTML5 semantico ({total_score:.1f}/14)"
        elif total_score >= 7:
            status = "partial"
            message = f"Uso parcial de HTML5 semantico ({total_score:.1f}/14)"
        else:
            status = "fail"
            message = f"Uso deficiente de HTML5 semantico ({total_score:.1f}/14)"

        # Generar recomendaciones EDUCATIVAS detalladas (incluye divitis)
        recomendaciones_basicas = generar_recomendaciones(violaciones, structure_analysis)
        recomendacion_detallada = None

        # Determinar cual recomendacion detallada mostrar (prioridad)
        if main_count == 0:
            # Falta estructura basica
            elementos_faltantes = []
            if main_count == 0:
                elementos_faltantes.append('main')
            if header_count == 0:
                elementos_faltantes.append('header')
            if footer_count == 0:
                elementos_faltantes.append('footer')
            if nav_count == 0:
                elementos_faltantes.append('nav')
            recomendacion_detallada = RecomendacionesSemanticas.falta_estructura_base(elementos_faltantes)
        elif main_count > 1 or main_inside_section:
            # Main mal ubicado
            recomendacion_detallada = RecomendacionesSemanticas.main_mal_ubicado(main_count, main_inside_section)
        elif navs_floating > 0 and nav_count > 0:
            # Nav fuera de header
            recomendacion_detallada = RecomendacionesSemanticas.nav_mal_ubicado(navs_floating, nav_count)

        return CriteriaEvaluation(
            criteria_id="SEM-03",
            criteria_name=self.criterios["SEM-03"]["name"],
            dimension=self.dimension,
            lineamiento=self.criterios["SEM-03"]["lineamiento"],
            status=status,
            score=round(total_score, 2),
            max_score=14,
            details={
                "main_count": main_count,
                "main_inside_section": main_inside_section,
                "header_count": header_count,
                "footer_count": footer_count,
                "nav_count": nav_count,
                "navs_in_header": navs_in_header,
                "navs_floating": navs_floating,
                "article_present": article_present,
                "section_present": section_present,
                "aside_present": aside_present,
                "violations_count": len(violaciones),
                "penalty_applied": round(penalizacion, 2),
                "issues": issues,
                "message": message
            },
            evidence={
                "recomendaciones": recomendaciones_basicas[:5],
                "recomendacion_detallada": recomendacion_detallada,
                "structure_analysis_available": has_structure_data
            }
        )

    def _evaluar_sem03_fallback(self, semantic_elements: Dict) -> CriteriaEvaluation:
        """
        Fallback para SEM-03 cuando no hay datos de structure_analysis.
        Solo verifica existencia de tags (comportamiento anterior).
        """
        logger.warning("SEM-03: Usando evaluacion fallback (solo existencia)")

        tags_found = []
        tags_missing = []

        for tag in self.SEMANTIC_TAGS:
            tag_data = semantic_elements.get(tag, {})
            is_present = self.extract_present(tag_data)
            if is_present:
                tags_found.append(tag)
            else:
                tags_missing.append(tag)

        tags_count = len(tags_found)
        score = min(tags_count * 2.0, 14.0)

        if tags_count >= 5:
            status = "pass"
        elif tags_count >= 3:
            status = "partial"
        else:
            status = "fail"

        return CriteriaEvaluation(
            criteria_id="SEM-03",
            criteria_name=self.criterios["SEM-03"]["name"],
            dimension=self.dimension,
            lineamiento=self.criterios["SEM-03"]["lineamiento"],
            status=status,
            score=score,
            max_score=14,
            details={
                "tags_found": tags_found,
                "tags_missing": tags_missing,
                "tags_count": tags_count,
                "note": "Evaluación básica (sin datos de jerarquía)",
                "message": f"Tags presentes: {tags_count}/7 (evaluación básica)"
            },
            evidence={
                "warning": "Actualizar crawler para obtener structure_analysis"
            }
        )

    def _evaluar_sem04(self, content: Dict) -> CriteriaEvaluation:
        """
        SEM-04: Separación contenido-presentación (10 pts, WCAG 1.3.1 Level A)
        D.S. 3925 (BP-05) / WCAG 1.3.1

        Verifica ausencia de elementos HTML obsoletos que mezclan
        contenido con presentación.

        Elementos obsoletos detectados:
        - Tags: <font>, <center>, <marquee>, <blink>, <big>, <strike>, <s>, <u>
        - Atributos: align, bgcolor, color, border en elementos semánticos

        Score:
        - 10 puntos: 0 elementos obsoletos
        - 5 puntos: 1-5 elementos obsoletos
        - 0 puntos: >5 elementos obsoletos
        """
        max_score = 10.0

        # Intentar obtener BeautifulSoup y raw_html
        try:
            from bs4 import BeautifulSoup
            raw_html = content.get('raw_html', '')

            if not raw_html:
                return CriteriaEvaluation(
                    criteria_id="SEM-04",
                    criteria_name=self.criterios["SEM-04"]["name"],
                    dimension=self.dimension,
                    lineamiento=self.criterios["SEM-04"]["lineamiento"],
                    status="na",
                    score=0.0,
                    max_score=max_score,
                    details={
                        "error": "raw_html no proporcionado por crawler",
                        "message": "HTML no disponible para análisis"
                    },
                    evidence={
                        "recommendation": "Crawler debe proporcionar raw_html"
                    }
                )

            soup = BeautifulSoup(raw_html, 'html.parser')

        except ImportError:
            return CriteriaEvaluation(
                criteria_id="SEM-04",
                criteria_name=self.criterios["SEM-04"]["name"],
                dimension=self.dimension,
                lineamiento=self.criterios["SEM-04"]["lineamiento"],
                status="na",
                score=0.0,
                max_score=max_score,
                details={
                    "error": "BeautifulSoup no disponible",
                    "message": "Instalar: pip install beautifulsoup4"
                },
                evidence={
                    "recommendation": "Instalar beautifulsoup4"
                }
            )

        # Elementos obsoletos a detectar
        tags_obsoletos = ['font', 'center', 'marquee', 'blink', 'big', 'strike', 's', 'u']
        atributos_obsoletos = ['align', 'bgcolor', 'color', 'border']

        # Tags donde los atributos presentacionales son más problemáticos
        tags_prohibidos_attrs = ['div', 'span', 'p', 'section', 'article', 'header', 'footer', 'nav']

        problemas = []

        # 1. Buscar tags obsoletos
        for tag_name in tags_obsoletos:
            tags_encontrados = soup.find_all(tag_name)
            if tags_encontrados:
                problemas.append({
                    'tipo': 'tag_obsoleto',
                    'elemento': f'<{tag_name}>',
                    'cantidad': len(tags_encontrados),
                    'ejemplo': str(tags_encontrados[0])[:100] if tags_encontrados else ''
                })

        # 2. Buscar atributos obsoletos en tags semánticos
        for tag_name in tags_prohibidos_attrs:
            elements = soup.find_all(tag_name)
            for elem in elements:
                for attr in atributos_obsoletos:
                    if elem.has_attr(attr):
                        problemas.append({
                            'tipo': 'atributo_obsoleto',
                            'elemento': f'<{tag_name} {attr}="{elem[attr]}">',
                            'atributo': attr,
                            'valor': str(elem[attr])[:50]
                        })
                        break  # Solo contar una vez por elemento

        # 3. Detectar estilos inline excesivos (>50% de elementos)
        total_elements = len(soup.find_all(True))
        elements_with_style = len(soup.find_all(style=True))

        if total_elements > 0:
            porcentaje_inline = (elements_with_style / total_elements) * 100
        else:
            porcentaje_inline = 0

        if porcentaje_inline > 50:
            problemas.append({
                'tipo': 'estilos_inline_excesivos',
                'elemento': 'style attribute',
                'cantidad': elements_with_style,
                'porcentaje': round(porcentaje_inline, 2)
            })

        # Calcular score
        total_problemas = len(problemas)

        if total_problemas == 0:
            score = max_score
            status = 'pass'
            message = "Cumple: Correcta separación contenido-presentación"
        elif total_problemas <= 5:
            score = max_score * 0.5
            status = 'partial'
            message = f"Parcial: {total_problemas} elemento(s) obsoleto(s) encontrado(s)"
        else:
            score = 0.0
            status = 'fail'
            message = f"No cumple: {total_problemas} violaciones de separación contenido-presentación"

        # Generar recomendación
        if status == 'fail':
            tipos_problemas = list(set([p['tipo'] for p in problemas]))
            recommendation = (
                f"CRÍTICO: Se encontraron {total_problemas} violaciones. "
                f"Tipos: {', '.join(tipos_problemas)}. "
                f"Eliminar <font>, <center> y atributos como align, bgcolor. "
                f"Usar CSS externo para toda la presentación visual. "
                f"Ejemplo: Reemplazar <font color='red'> con <span class='text-danger'> + CSS."
            )
        elif status == 'partial':
            recommendation = (
                f"Se encontraron {total_problemas} elementos obsoletos. "
                f"Migrar gradualmente a HTML5 + CSS moderno para mejor mantenibilidad y accesibilidad."
            )
        else:
            recommendation = "Cumple: HTML moderno sin elementos presentacionales obsoletos"

        # Contar por tipo
        tags_obsoletos_count = sum(1 for p in problemas if p['tipo'] == 'tag_obsoleto')
        attrs_obsoletos_count = sum(1 for p in problemas if p['tipo'] == 'atributo_obsoleto')
        inline_excesivo = any(p['tipo'] == 'estilos_inline_excesivos' for p in problemas)

        return CriteriaEvaluation(
            criteria_id="SEM-04",
            criteria_name=self.criterios["SEM-04"]["name"],
            dimension=self.dimension,
            lineamiento=self.criterios["SEM-04"]["lineamiento"],
            status=status,
            score=round(score, 2),
            max_score=max_score,
            details={
                "total_problemas": total_problemas,
                "tags_obsoletos_encontrados": tags_obsoletos_count,
                "atributos_obsoletos_encontrados": attrs_obsoletos_count,
                "estilos_inline_excesivos": inline_excesivo,
                "porcentaje_estilos_inline": round(porcentaje_inline, 2),
                "problemas_detalle": problemas[:10],  # Primeros 10 para evidencia
                "message": message,
                "recommendation": recommendation
            },
            evidence={
                "problemas_detectados": [f"{p['tipo']}: {p['elemento']}" for p in problemas[:5]],
                "tags_obsoletos_buscados": tags_obsoletos,
                "atributos_obsoletos_buscados": atributos_obsoletos
            }
        )

    # ========================================================================
    # GRUPO SEO - Optimización para Motores de Búsqueda (38 pts)
    # ========================================================================

    def _evaluar_seo01_meta_descripcion(self, metadata: Dict) -> CriteriaEvaluation:
        """
        SEO-01: Meta descripción (8 pts)
        SEO Best Practices
        Verificar <meta name="description"> con contenido adecuado
        Score: 8 si cumple (>=50 chars), 4 si corta, 0 si no existe
        """
        description = metadata.get('description', '')
        description_length = metadata.get('description_length', len(description) if description else 0)
        has_description = metadata.get('has_description', bool(description))

        if has_description and description_length >= 50:
            status = "pass"
            score = 8.0
            message = f"Meta descripción presente ({description_length} caracteres)"
        elif has_description:
            status = "partial"
            score = 4.0
            message = f"Meta descripción muy corta ({description_length} caracteres, mínimo: 50)"
        else:
            status = "fail"
            score = 0.0
            message = "No se encontró meta descripción"

        return CriteriaEvaluation(
            criteria_id="SEO-01",
            criteria_name=self.criterios["SEO-01"]["name"],
            dimension=self.dimension,
            lineamiento=self.criterios["SEO-01"]["lineamiento"],
            status=status,
            score=score,
            max_score=8,
            details={
                "has_description": has_description,
                "description_length": description_length,
                "is_adequate": description_length >= 50,
                "recommended_length": "150-160 caracteres",
                "message": message
            },
            evidence={
                "description": description[:200] if description else "No presente"
            }
        )

    def _evaluar_seo02_meta_keywords(self, metadata: Dict) -> CriteriaEvaluation:
        """
        SEO-02: Meta Keywords (4 pts)
        SEO Best Practices (menor peso por ser deprecated en SEO moderno)
        Verificar <meta name="keywords">
        Score: 4 si existe, 0 si no
        """
        keywords = metadata.get('keywords', '')
        has_keywords = metadata.get('has_keywords', bool(keywords))

        if has_keywords:
            status = "pass"
            score = 4.0
            keyword_list = [k.strip() for k in keywords.split(',') if k.strip()]
            keyword_count = len(keyword_list)
            message = f"Meta keywords presente ({keyword_count} keywords)"
        else:
            status = "fail"
            score = 0.0
            keyword_count = 0
            message = "No se encontró meta keywords (opcional pero recomendado)"

        return CriteriaEvaluation(
            criteria_id="SEO-02",
            criteria_name=self.criterios["SEO-02"]["name"],
            dimension=self.dimension,
            lineamiento=self.criterios["SEO-02"]["lineamiento"],
            status=status,
            score=score,
            max_score=4,
            details={
                "has_keywords": has_keywords,
                "keyword_count": keyword_count,
                "note": "Meta keywords es menos importante en SEO moderno pero aún recomendado",
                "message": message
            },
            evidence={
                "keywords": keywords[:200] if keywords else "No presente"
            }
        )

    def _evaluar_seo03_viewport(self, metadata: Dict) -> CriteriaEvaluation:
        """
        SEO-03: Meta viewport (12 pts, WCAG 1.4.4 Level AA)
        Verificar <meta name="viewport" content="width=device-width">
        Score: 12 si existe y correcto, 6 si parcial, 0 si no existe
        """
        viewport = metadata.get('viewport', '')
        has_viewport = metadata.get('has_viewport', bool(viewport))

        has_device_width = 'width=device-width' in viewport.lower().replace(' ', '') if viewport else False

        if has_viewport and has_device_width:
            status = "pass"
            score = 12.0
            message = "Viewport configurado correctamente para responsive"
        elif has_viewport:
            status = "partial"
            score = 6.0
            message = "Viewport presente pero puede no ser óptimo"
        else:
            status = "fail"
            score = 0.0
            message = "No se encontró meta viewport (sitio no responsive)"

        return CriteriaEvaluation(
            criteria_id="SEO-03",
            criteria_name=self.criterios["SEO-03"]["name"],
            dimension=self.dimension,
            lineamiento=self.criterios["SEO-03"]["lineamiento"],
            status=status,
            score=score,
            max_score=12,
            details={
                "has_viewport": has_viewport,
                "has_device_width": has_device_width,
                "viewport_content": viewport if viewport else "No declarado",
                "recommended": "width=device-width, initial-scale=1",
                "message": message
            },
            evidence={
                "viewport": viewport if viewport else "No encontrado"
            }
        )

    def _evaluar_seo04_headings(self, headings: Dict) -> CriteriaEvaluation:
        """
        SEO-04: Jerarquía de headings válida (14 pts, WCAG 1.3.1 Level A)
        Técnica H42 de WCAG
        - Exactamente 1 <h1>
        - Sin saltos en jerarquía (h1->h3 sin h2)
        Score: 14 si cumple ambos, 7 si cumple uno, 0 si ninguno
        """
        h1_count = headings.get('h1_count', 0)
        has_single_h1 = headings.get('has_single_h1', False)
        hierarchy_valid = headings.get('hierarchy_valid', False)
        hierarchy_errors = headings.get('hierarchy_errors', [])
        by_level = headings.get('by_level', {})

        # Calcular score
        if has_single_h1 and hierarchy_valid:
            status = "pass"
            score = 14.0
            message = "Jerarquía de headings correcta"
        elif has_single_h1 or hierarchy_valid:
            status = "partial"
            score = 7.0
            issues = []
            if not has_single_h1:
                if h1_count == 0:
                    issues.append("Falta <h1>")
                else:
                    issues.append(f"Múltiples <h1> ({h1_count})")
            if not hierarchy_valid:
                issues.append("Saltos en jerarquía")
            message = "Problemas: " + ", ".join(issues)
        else:
            status = "fail"
            score = 0.0
            message = "Jerarquía de headings incorrecta"

        return CriteriaEvaluation(
            criteria_id="SEO-04",
            criteria_name=self.criterios["SEO-04"]["name"],
            dimension=self.dimension,
            lineamiento=self.criterios["SEO-04"]["lineamiento"],
            status=status,
            score=score,
            max_score=14,
            details={
                "h1_count": h1_count,
                "has_single_h1": has_single_h1,
                "hierarchy_valid": hierarchy_valid,
                "hierarchy_errors_count": len(hierarchy_errors),
                "message": message
            },
            evidence={
                "headings_by_level": by_level,
                "hierarchy_errors": hierarchy_errors[:5]
            }
        )

    # ========================================================================
    # GRUPO FMT - Formato Técnico (18 pts)
    # ========================================================================

    def _evaluar_fmt01_formatos_abiertos(self, links: Dict) -> CriteriaEvaluation:
        """
        FMT-01: Uso de formatos abiertos (10 pts)
        D.S. 3925 - Garantiza acceso universal a documentos sin software propietario

        Verifica que los documentos enlazados usen formatos abiertos:
        - Abiertos: PDF, ODF (.odt, .ods, .odp), CSV, JSON, XML, TXT
        - Propietarios: DOC, DOCX, XLS, XLSX, PPT, PPTX

        Score:
        - 10 pts: 0 documentos propietarios (o sin documentos enlazados)
        - 5 pts: ≤30% documentos propietarios
        - 0 pts: >30% documentos propietarios
        """
        max_score = 10.0
        all_links = links.get('all_links', [])

        docs_abiertos = []
        docs_propietarios = []

        for link in all_links:
            href = link.get('href', '').lower().split('?')[0].split('#')[0]

            # Verificar si el enlace apunta a un documento propietario
            es_propietario = False
            for ext in self.FORMATOS_DOC_PROPIETARIOS:
                if href.endswith(ext):
                    docs_propietarios.append({
                        'href': link.get('href', '')[:100],
                        'format': ext,
                        'text': link.get('text', '')[:50]
                    })
                    es_propietario = True
                    break

            if not es_propietario:
                for ext in self.FORMATOS_DOC_ABIERTOS:
                    if href.endswith(ext):
                        docs_abiertos.append({
                            'href': link.get('href', '')[:100],
                            'format': ext,
                            'text': link.get('text', '')[:50]
                        })
                        break

        total_docs = len(docs_abiertos) + len(docs_propietarios)

        if total_docs == 0:
            status = "pass"
            score = max_score
            message = "Sin enlaces a documentos descargables (cumple por defecto)"
        elif len(docs_propietarios) == 0:
            status = "pass"
            score = max_score
            message = f"Cumple: {total_docs} documento(s) en formatos abiertos"
        elif len(docs_propietarios) / total_docs <= 0.3:
            status = "partial"
            score = max_score * 0.5
            formatos_prop = list(set(d['format'] for d in docs_propietarios))
            message = (
                f"Parcial: {len(docs_propietarios)}/{total_docs} documentos en "
                f"formatos propietarios ({', '.join(formatos_prop)})"
            )
        else:
            status = "fail"
            score = 0.0
            formatos_prop = list(set(d['format'] for d in docs_propietarios))
            message = (
                f"No cumple: {len(docs_propietarios)}/{total_docs} documentos en "
                f"formatos propietarios ({', '.join(formatos_prop)})"
            )

        # Recomendación
        if status == 'fail':
            recommendation = (
                f"CRÍTICO: {len(docs_propietarios)} documentos usan formatos propietarios. "
                f"Migrar a formatos abiertos: DOC→ODT/PDF, XLS→ODS/CSV, PPT→ODP/PDF. "
                f"D.S. 3925 requiere acceso universal sin software propietario."
            )
        elif status == 'partial':
            recommendation = (
                f"Se encontraron {len(docs_propietarios)} documentos propietarios. "
                f"Convertir gradualmente a PDF u ODF para garantizar acceso universal."
            )
        else:
            recommendation = "Cumple: Todos los documentos usan formatos abiertos"

        return CriteriaEvaluation(
            criteria_id="FMT-01",
            criteria_name=self.criterios["FMT-01"]["name"],
            dimension=self.dimension,
            lineamiento=self.criterios["FMT-01"]["lineamiento"],
            status=status,
            score=round(score, 2),
            max_score=max_score,
            details={
                "total_documentos": total_docs,
                "documentos_abiertos": len(docs_abiertos),
                "documentos_propietarios": len(docs_propietarios),
                "formatos_propietarios_encontrados": [d['format'] for d in docs_propietarios[:10]],
                "message": message,
                "recommendation": recommendation
            },
            evidence={
                "docs_propietarios": docs_propietarios[:5],
                "docs_abiertos_ejemplo": docs_abiertos[:3],
                "formatos_abiertos_aceptados": list(self.FORMATOS_DOC_ABIERTOS),
                "formatos_propietarios_detectados": list(self.FORMATOS_DOC_PROPIETARIOS)
            }
        )

    def _evaluar_fmt02_imagenes_optimizadas(self, images: Dict) -> CriteriaEvaluation:
        """
        FMT-02: Imágenes optimizadas (8 pts, WCAG 1.4.5 Level AA)
        Verifica que las imágenes usen formatos modernos optimizados.

        - Optimizados: WebP, AVIF, SVG (menor tamaño, mejor rendimiento)
        - Pesados: PNG, JPG/JPEG, BMP, TIFF, GIF (mayor tamaño, más lentos)

        Score:
        - 8 pts: ≥50% de imágenes en formatos optimizados
        - 4 pts: ≥20% en formatos optimizados o todas sin formato detectable
        - 0 pts: <20% en formatos optimizados
        """
        max_score = 8.0
        image_list = images.get('images', [])
        total_images = images.get('total_count', len(image_list))

        if total_images == 0:
            return CriteriaEvaluation(
                criteria_id="FMT-02",
                criteria_name=self.criterios["FMT-02"]["name"],
                dimension=self.dimension,
                lineamiento=self.criterios["FMT-02"]["lineamiento"],
                status="na",
                score=0.0,
                max_score=max_score,
                details={
                    "message": "No se encontraron imágenes para analizar",
                    "total_images": 0
                },
                evidence={}
            )

        optimizadas = []
        pesadas = []
        otras = []

        for img in image_list:
            src = img.get('src', '').lower().split('?')[0].split('#')[0]

            # Detectar extensión
            formato_detectado = None
            for ext in self.FORMATOS_IMG_OPTIMIZADOS:
                if src.endswith(ext):
                    formato_detectado = ext
                    optimizadas.append({'src': img.get('src', '')[:100], 'format': ext})
                    break

            if not formato_detectado:
                for ext in self.FORMATOS_IMG_PESADOS:
                    if src.endswith(ext):
                        formato_detectado = ext
                        pesadas.append({'src': img.get('src', '')[:100], 'format': ext})
                        break

            if not formato_detectado:
                otras.append({'src': img.get('src', '')[:100], 'format': 'desconocido'})

        total_clasificadas = len(optimizadas) + len(pesadas)

        if total_clasificadas == 0:
            # No se pudo determinar formato (data URIs, sin extensión, etc.)
            status = "partial"
            score = max_score * 0.5
            porcentaje_optimizadas = 0
            message = f"No se pudo determinar el formato de {len(otras)} imagen(es)"
        else:
            porcentaje_optimizadas = (len(optimizadas) / total_clasificadas) * 100

            if porcentaje_optimizadas >= 50:
                status = "pass"
                score = max_score
                message = (
                    f"Cumple: {len(optimizadas)}/{total_clasificadas} imágenes "
                    f"({porcentaje_optimizadas:.0f}%) en formatos optimizados"
                )
            elif porcentaje_optimizadas >= 20:
                status = "partial"
                score = max_score * 0.5
                message = (
                    f"Parcial: {len(optimizadas)}/{total_clasificadas} imágenes "
                    f"({porcentaje_optimizadas:.0f}%) en formatos optimizados"
                )
            else:
                status = "fail"
                score = 0.0
                formatos_pesados = list(set(p['format'] for p in pesadas))
                message = (
                    f"No cumple: {len(pesadas)}/{total_clasificadas} imágenes en "
                    f"formatos pesados ({', '.join(formatos_pesados)})"
                )

        # Recomendación
        if status == 'fail':
            recommendation = (
                f"IMPORTANTE: {len(pesadas)} imágenes usan formatos pesados (PNG/JPG). "
                f"Convertir a WebP o AVIF para reducir tiempos de carga. "
                f"WebP ofrece ~30% menos tamaño que JPG y soporta transparencia como PNG. "
                f"Usar SVG para íconos y logos vectoriales."
            )
        elif status == 'partial':
            recommendation = (
                f"Algunas imágenes usan formatos pesados. "
                f"Migrar gradualmente a WebP/AVIF para mejor rendimiento."
            )
        else:
            recommendation = "Cumple: Mayoría de imágenes en formatos optimizados"

        return CriteriaEvaluation(
            criteria_id="FMT-02",
            criteria_name=self.criterios["FMT-02"]["name"],
            dimension=self.dimension,
            lineamiento=self.criterios["FMT-02"]["lineamiento"],
            status=status,
            score=round(score, 2),
            max_score=max_score,
            details={
                "total_images": total_images,
                "imagenes_optimizadas": len(optimizadas),
                "imagenes_pesadas": len(pesadas),
                "imagenes_formato_desconocido": len(otras),
                "porcentaje_optimizadas": round(porcentaje_optimizadas, 1),
                "formatos_pesados_encontrados": list(set(p['format'] for p in pesadas)),
                "message": message,
                "recommendation": recommendation
            },
            evidence={
                "imagenes_pesadas_ejemplo": pesadas[:5],
                "imagenes_optimizadas_ejemplo": optimizadas[:3],
                "formatos_optimizados": list(self.FORMATOS_IMG_OPTIMIZADOS),
                "formatos_pesados": list(self.FORMATOS_IMG_PESADOS)
            }
        )


# Alias para compatibilidad con codigo existente
EvaluadorSemanticaTecnica = EvaluadorSemantica
