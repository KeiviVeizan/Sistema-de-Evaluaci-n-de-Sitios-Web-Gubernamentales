"""
Evaluador de Semantica Web (15%)
Evalua 10 criterios tecnicos: SEM-01 a SEM-04, SEO-01 a SEO-04, FMT-01 a FMT-02

MEJORADO: Evalua BUENAS PRACTICAS HTML5, no solo existencia de tags.
"""
import re
import logging
from typing import Dict, List
from urllib.parse import urlparse, parse_qs
from .base_evaluator import BaseEvaluator, CriteriaEvaluation
from .buenas_practicas_html5 import (
    BUENAS_PRACTICAS,
    DIVITIS_RULES,
    detectar_violaciones,
    calcular_penalizacion_total,
    generar_recomendaciones
)
from .recomendaciones_semanticas import RecomendacionesSemanticas

logger = logging.getLogger(__name__)


class EvaluadorSemantica(BaseEvaluator):
    """
    Evaluador de criterios de semantica web tecnica.

    Evalua 10 criterios en 3 grupos:
    - SEM: HTML5 semantico (4 criterios)
    - SEO: Optimizacion SEO (4 criterios)
    - FMT: Formato tecnico (2 criterios)

    IMPORTANTE: Evalua BUENAS PRACTICAS, no solo existencia de tags.
    """

    # Tags HTML5 semanticos esperados
    SEMANTIC_TAGS = ['header', 'nav', 'main', 'article', 'section', 'aside', 'footer']

    def __init__(self):
        super().__init__(dimension="semantica")

        # Pesos segun especificacion
        self.criterios = {
            # Grupo SEM - Semantica HTML5
            "SEM-01": {"name": "Etiquetas HTML5 semanticas (buenas practicas)", "points": 14, "lineamiento": "W3C HTML5 / MDN Best Practices"},
            "SEM-02": {"name": "DOCTYPE HTML5", "points": 10, "lineamiento": "HTML5 DOCTYPE Declaration"},
            "SEM-03": {"name": "Jerarquia de headings valida", "points": 10, "lineamiento": "WCAG 1.3.1 / H42"},
            "SEM-04": {"name": "Evitar divitis (anti-patron)", "points": 10, "lineamiento": "W3C Semantic Web / MDN"},
            # Grupo SEO - Optimizacion
            "SEO-01": {"name": "Titulo de pagina descriptivo", "points": 10, "lineamiento": "SEO Best Practices"},
            "SEO-02": {"name": "Meta descripcion presente", "points": 10, "lineamiento": "SEO Best Practices"},
            "SEO-03": {"name": "Meta keywords (opcional)", "points": 10, "lineamiento": "SEO Best Practices"},
            "SEO-04": {"name": "URLs amigables", "points": 10, "lineamiento": "SEO Best Practices"},
            # Grupo FMT - Formato tecnico
            "FMT-01": {"name": "Encoding UTF-8 declarado", "points": 10, "lineamiento": "W3C Encoding Standards"},
            "FMT-02": {"name": "Viewport para responsive", "points": 10, "lineamiento": "Mobile-First Design"}
        }

    def evaluate(self, extracted_content: Dict) -> List[CriteriaEvaluation]:
        """Evalua todos los criterios de semantica tecnica"""
        self.clear_results()

        # Extraer datos relevantes
        metadata = extracted_content.get('metadata', {})
        structure = extracted_content.get('structure', {})
        semantic_elements = extracted_content.get('semantic_elements', {})
        headings = extracted_content.get('headings', {})
        url = extracted_content.get('url', '')

        # Extraer document_hierarchy del structure (datos de buenas practicas)
        document_hierarchy = structure.get('document_hierarchy', {})
        structure_analysis = document_hierarchy.get('structure_analysis', {})

        # Grupo SEM - Semantica HTML5 (con buenas practicas)
        self.add_result(self._evaluar_sem01_buenas_practicas(semantic_elements, structure_analysis))
        self.add_result(self._evaluar_sem02(structure))
        self.add_result(self._evaluar_sem03(headings))
        self.add_result(self._evaluar_sem04_antidivitis(structure_analysis))

        # Grupo SEO - Optimizacion
        self.add_result(self._evaluar_seo01(metadata))
        self.add_result(self._evaluar_seo02(metadata))
        self.add_result(self._evaluar_seo03(metadata))
        self.add_result(self._evaluar_seo04(url))

        # Grupo FMT - Formato tecnico
        self.add_result(self._evaluar_fmt01(structure))
        self.add_result(self._evaluar_fmt02(metadata))

        return self.results

    # ========================================================================
    # GRUPO SEM - Semantica HTML5 (con buenas practicas)
    # ========================================================================

    def _evaluar_sem01_buenas_practicas(self, semantic_elements: Dict, structure_analysis: Dict) -> CriteriaEvaluation:
        """
        SEM-01: Etiquetas HTML5 semanticas CORRECTAMENTE USADAS

        No solo verifica existencia, tambien:
        - Jerarquia correcta segun estandares W3C
        - Sin violaciones estructurales
        - Uso apropiado de cada tag

        Score maximo: 14 puntos
        """
        issues = []
        scores = []

        # Verificar si tenemos datos de structure_analysis
        has_structure_data = bool(structure_analysis)

        if not has_structure_data:
            logger.warning("SEM-01: No hay datos de structure_analysis del crawler")
            # Fallback: solo verificar existencia (comportamiento anterior)
            return self._evaluar_sem01_fallback(semantic_elements)

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
        # PENALIZACION POR VIOLACIONES ESTRUCTURALES
        # ================================================================
        violaciones = detectar_violaciones(structure_analysis)
        penalizacion = calcular_penalizacion_total(violaciones)

        # Filtrar violaciones que no sean de divitis (esas van en SEM-04)
        violaciones_estructura = [v for v in violaciones
                                  if 'divitis' not in v.get('mensaje', '').lower()]

        # Agregar violaciones a issues
        for v in violaciones_estructura:
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

        # Generar recomendaciones EDUCATIVAS detalladas
        recomendaciones_basicas = generar_recomendaciones(violaciones_estructura, structure_analysis)
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
            criteria_id="SEM-01",
            criteria_name=self.criterios["SEM-01"]["name"],
            dimension=self.dimension,
            lineamiento=self.criterios["SEM-01"]["lineamiento"],
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
                "violations_count": len(violaciones_estructura),
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

    def _evaluar_sem01_fallback(self, semantic_elements: Dict) -> CriteriaEvaluation:
        """
        Fallback para SEM-01 cuando no hay datos de structure_analysis.
        Solo verifica existencia de tags (comportamiento anterior).
        """
        logger.warning("SEM-01: Usando evaluacion fallback (solo existencia)")

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
            criteria_id="SEM-01",
            criteria_name=self.criterios["SEM-01"]["name"],
            dimension=self.dimension,
            lineamiento=self.criterios["SEM-01"]["lineamiento"],
            status=status,
            score=score,
            max_score=14,
            details={
                "tags_found": tags_found,
                "tags_missing": tags_missing,
                "tags_count": tags_count,
                "note": "Evaluacion basica (sin datos de jerarquia)",
                "message": f"Tags presentes: {tags_count}/7 (evaluacion basica)"
            },
            evidence={
                "warning": "Actualizar crawler para obtener structure_analysis"
            }
        )

    def _evaluar_sem02(self, structure: Dict) -> CriteriaEvaluation:
        """
        SEM-02: DOCTYPE HTML5
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
            criteria_id="SEM-02",
            criteria_name=self.criterios["SEM-02"]["name"],
            dimension=self.dimension,
            lineamiento=self.criterios["SEM-02"]["lineamiento"],
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

    def _evaluar_sem03(self, headings: Dict) -> CriteriaEvaluation:
        """
        SEM-03: Jerarquia de headings valida
        - Exactamente 1 <h1>
        - Sin saltos en jerarquia (h1->h3 sin h2)
        Score: 10 si cumple ambos, 5 si cumple uno, 0 si ninguno
        """
        h1_count = headings.get('h1_count', 0)
        has_single_h1 = headings.get('has_single_h1', False)
        hierarchy_valid = headings.get('hierarchy_valid', False)
        hierarchy_errors = headings.get('hierarchy_errors', [])
        by_level = headings.get('by_level', {})

        # Calcular score
        if has_single_h1 and hierarchy_valid:
            status = "pass"
            score = 10.0
            message = "Jerarquia de headings correcta"
        elif has_single_h1 or hierarchy_valid:
            status = "partial"
            score = 5.0
            issues = []
            if not has_single_h1:
                if h1_count == 0:
                    issues.append("Falta <h1>")
                else:
                    issues.append(f"Multiples <h1> ({h1_count})")
            if not hierarchy_valid:
                issues.append("Saltos en jerarquia")
            message = "Problemas: " + ", ".join(issues)
        else:
            status = "fail"
            score = 0.0
            message = "Jerarquia de headings incorrecta"

        return CriteriaEvaluation(
            criteria_id="SEM-03",
            criteria_name=self.criterios["SEM-03"]["name"],
            dimension=self.dimension,
            lineamiento=self.criterios["SEM-03"]["lineamiento"],
            status=status,
            score=score,
            max_score=10,
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

    def _evaluar_sem04_antidivitis(self, structure_analysis: Dict) -> CriteriaEvaluation:
        """
        SEM-04: Evitar divitis (exceso de <div>)

        Evalua:
        - Ratio divs vs tags semanticos
        - Profundidad de anidamiento
        - Patron divitis detectado

        Score maximo: 10 puntos
        """
        # Verificar si tenemos datos
        if not structure_analysis:
            logger.warning("SEM-04: No hay datos de structure_analysis del crawler")
            return CriteriaEvaluation(
                criteria_id="SEM-04",
                criteria_name=self.criterios["SEM-04"]["name"],
                dimension=self.dimension,
                lineamiento=self.criterios["SEM-04"]["lineamiento"],
                status="na",
                score=0.0,
                max_score=10,
                details={
                    "error": "Datos de divitis no disponibles",
                    "message": "Actualizar crawler para analisis de divitis"
                },
                evidence={
                    "warning": "Crawler debe proporcionar structure_analysis"
                }
            )

        # Extraer datos
        total_divs = structure_analysis.get('total_divs', 0)
        total_semantic = structure_analysis.get('total_semantic', 0)
        div_ratio = structure_analysis.get('div_ratio', 0.0)
        has_divitis = structure_analysis.get('has_divitis', False)

        # Calcular score
        score = 10.0
        issues = []

        # Penalizacion por divitis severa
        if has_divitis or div_ratio > DIVITIS_RULES['ratio_threshold_fail']:
            score -= 5.0
            severity = "CRITICO" if div_ratio > 0.8 else "SEVERO"
            issues.append(f"{severity}: Divitis detectada ({int(div_ratio*100)}% divs vs semanticos)")
        elif div_ratio > DIVITIS_RULES['ratio_threshold_warning']:
            score -= 2.5
            issues.append(f"Uso excesivo de divs ({int(div_ratio*100)}% del contenido)")

        # Penalizacion por ratio muy pobre de semantica
        if total_semantic > 0:
            semantic_ratio = total_semantic / (total_divs + total_semantic) if (total_divs + total_semantic) > 0 else 0
            if semantic_ratio < 0.2:  # Menos del 20% semantico
                score -= 3.0
                issues.append(f"Muy pocos elementos semanticos ({total_semantic} vs {total_divs} divs)")
            elif semantic_ratio < 0.3:
                score -= 1.5
                issues.append(f"Pocos elementos semanticos (ratio: {semantic_ratio:.2f})")
        else:
            score -= 4.0
            issues.append("Sin elementos semanticos detectados")

        # Penalizacion por total excesivo de divs
        if total_divs > 100:
            score -= 1.0
            issues.append(f"Exceso de divs totales ({total_divs})")

        score = max(0.0, score)

        # Determinar status
        if score >= 8:
            status = "pass"
            message = "Estructura HTML limpia (sin divitis)"
        elif score >= 5:
            status = "partial"
            message = "Estructura HTML aceptable (divitis moderada)"
        else:
            status = "fail"
            message = "Estructura HTML problematica (divitis severa)"

        # Recomendaciones EDUCATIVAS detalladas
        recomendaciones = []
        recomendacion_educativa = None

        if has_divitis or div_ratio > DIVITIS_RULES['ratio_threshold_warning']:
            # Generar recomendacion educativa con ejemplos de codigo
            recomendacion_educativa = RecomendacionesSemanticas.divitis_severa(
                div_ratio=div_ratio,
                total_divs=total_divs,
                total_semantic=total_semantic
            )
            # Mantener tambien las recomendaciones simples para compatibilidad
            recomendaciones.append("Reemplazar <div> wrappers por elementos semanticos: <section>, <article>, <aside>")
            recomendaciones.append("Usar <figure> para imagenes con caption en lugar de <div>")

        return CriteriaEvaluation(
            criteria_id="SEM-04",
            criteria_name=self.criterios["SEM-04"]["name"],
            dimension=self.dimension,
            lineamiento=self.criterios["SEM-04"]["lineamiento"],
            status=status,
            score=round(score, 2),
            max_score=10,
            details={
                "total_divs": total_divs,
                "total_semantic": total_semantic,
                "div_ratio": round(div_ratio, 2),
                "has_divitis": has_divitis,
                "issues": issues,
                "message": message,
                "recomendacion_educativa": recomendacion_educativa
            },
            evidence={
                "recomendaciones": recomendaciones,
                "recomendacion_detallada": RecomendacionesSemanticas.formatear_recomendacion(recomendacion_educativa) if recomendacion_educativa else None,
                "threshold_warning": DIVITIS_RULES['ratio_threshold_warning'],
                "threshold_fail": DIVITIS_RULES['ratio_threshold_fail']
            }
        )

    # ========================================================================
    # GRUPO SEO - Optimizacion para Motores de Busqueda
    # ========================================================================

    def _evaluar_seo01(self, metadata: Dict) -> CriteriaEvaluation:
        """
        SEO-01: Titulo de pagina descriptivo
        - Existe <title>
        - Tiene >10 caracteres (descriptivo)
        Score: 10 si cumple, 5 si solo existe pero corto, 0 si no existe
        """
        title = metadata.get('title', '')
        title_length = metadata.get('title_length', len(title) if title else 0)
        has_title = metadata.get('has_title', bool(title))

        if has_title and title_length >= 10:
            status = "pass"
            score = 10.0
            message = f"Titulo descriptivo presente ({title_length} caracteres)"
        elif has_title:
            status = "partial"
            score = 5.0
            message = f"Titulo muy corto ({title_length} caracteres, minimo recomendado: 10)"
        else:
            status = "fail"
            score = 0.0
            message = "No se encontro titulo de pagina"

        return CriteriaEvaluation(
            criteria_id="SEO-01",
            criteria_name=self.criterios["SEO-01"]["name"],
            dimension=self.dimension,
            lineamiento=self.criterios["SEO-01"]["lineamiento"],
            status=status,
            score=score,
            max_score=10,
            details={
                "has_title": has_title,
                "title_length": title_length,
                "is_descriptive": title_length >= 10,
                "recommended_length": "50-60 caracteres",
                "message": message
            },
            evidence={
                "title": title[:100] if title else "No presente"
            }
        )

    def _evaluar_seo02(self, metadata: Dict) -> CriteriaEvaluation:
        """
        SEO-02: Meta descripcion presente
        - Existe <meta name="description">
        - Tiene >50 caracteres
        Score: 10 si cumple, 5 si corta, 0 si no existe
        """
        description = metadata.get('description', '')
        description_length = metadata.get('description_length', len(description) if description else 0)
        has_description = metadata.get('has_description', bool(description))

        if has_description and description_length >= 50:
            status = "pass"
            score = 10.0
            message = f"Meta descripcion presente ({description_length} caracteres)"
        elif has_description:
            status = "partial"
            score = 5.0
            message = f"Meta descripcion muy corta ({description_length} caracteres, minimo: 50)"
        else:
            status = "fail"
            score = 0.0
            message = "No se encontro meta descripcion"

        return CriteriaEvaluation(
            criteria_id="SEO-02",
            criteria_name=self.criterios["SEO-02"]["name"],
            dimension=self.dimension,
            lineamiento=self.criterios["SEO-02"]["lineamiento"],
            status=status,
            score=score,
            max_score=10,
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

    def _evaluar_seo03(self, metadata: Dict) -> CriteriaEvaluation:
        """
        SEO-03: Meta keywords (opcional pero recomendado)
        - Verificar <meta name="keywords">
        Score: 10 si existe, 0 si no
        Nota: Es un criterio menos critico en SEO moderno
        """
        keywords = metadata.get('keywords', '')
        has_keywords = metadata.get('has_keywords', bool(keywords))

        if has_keywords:
            status = "pass"
            score = 10.0
            keyword_list = [k.strip() for k in keywords.split(',') if k.strip()]
            keyword_count = len(keyword_list)
            message = f"Meta keywords presente ({keyword_count} keywords)"
        else:
            status = "fail"
            score = 0.0
            keyword_count = 0
            message = "No se encontro meta keywords (opcional pero recomendado)"

        return CriteriaEvaluation(
            criteria_id="SEO-03",
            criteria_name=self.criterios["SEO-03"]["name"],
            dimension=self.dimension,
            lineamiento=self.criterios["SEO-03"]["lineamiento"],
            status=status,
            score=score,
            max_score=10,
            details={
                "has_keywords": has_keywords,
                "keyword_count": keyword_count,
                "note": "Meta keywords es menos importante en SEO moderno pero aun recomendado",
                "message": message
            },
            evidence={
                "keywords": keywords[:200] if keywords else "No presente"
            }
        )

    def _evaluar_seo04(self, url: str) -> CriteriaEvaluation:
        """
        SEO-04: URLs amigables
        - URL no tiene >2 parametros query (?var1=&var2=)
        - No tiene IDs numericos largos
        Score: 10 si URL limpia, 5 si tiene 1-2 params, 0 si >2
        """
        if not url:
            return CriteriaEvaluation(
                criteria_id="SEO-04",
                criteria_name=self.criterios["SEO-04"]["name"],
                dimension=self.dimension,
                lineamiento=self.criterios["SEO-04"]["lineamiento"],
                status="na",
                score=10.0,
                max_score=10,
                details={"message": "URL no disponible para analisis"},
                evidence={}
            )

        try:
            parsed = urlparse(url)
            query_params = parse_qs(parsed.query)
            param_count = len(query_params)

            path = parsed.path
            has_long_numeric_id = bool(re.search(r'/\d{5,}/', path)) or bool(re.search(r'/\d{5,}$', path))

            issues = []

            if param_count == 0 and not has_long_numeric_id:
                status = "pass"
                score = 10.0
                message = "URL amigable y limpia"
            elif param_count <= 2 and not has_long_numeric_id:
                status = "partial"
                score = 5.0
                if param_count > 0:
                    issues.append(f"{param_count} parametros query")
                message = "URL aceptable: " + ", ".join(issues) if issues else "URL aceptable"
            else:
                status = "fail"
                score = 0.0
                if param_count > 2:
                    issues.append(f"Demasiados parametros ({param_count})")
                if has_long_numeric_id:
                    issues.append("IDs numericos largos en URL")
                message = "URL no amigable: " + ", ".join(issues)

        except Exception as e:
            status = "partial"
            score = 5.0
            param_count = 0
            has_long_numeric_id = False
            message = f"Error analizando URL: {str(e)}"

        return CriteriaEvaluation(
            criteria_id="SEO-04",
            criteria_name=self.criterios["SEO-04"]["name"],
            dimension=self.dimension,
            lineamiento=self.criterios["SEO-04"]["lineamiento"],
            status=status,
            score=score,
            max_score=10,
            details={
                "url_analyzed": url[:100],
                "query_param_count": param_count,
                "has_long_numeric_id": has_long_numeric_id,
                "is_friendly": status == "pass",
                "message": message
            },
            evidence={
                "url": url
            }
        )

    # ========================================================================
    # GRUPO FMT - Formato y Estructura Tecnica
    # ========================================================================

    def _evaluar_fmt01(self, structure: Dict) -> CriteriaEvaluation:
        """
        FMT-01: Encoding UTF-8 declarado
        Verificar <meta charset="UTF-8"> o equivalente
        Score: 10 si existe, 0 si no
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
            message = "No se declaro encoding de caracteres"

        return CriteriaEvaluation(
            criteria_id="FMT-01",
            criteria_name=self.criterios["FMT-01"]["name"],
            dimension=self.dimension,
            lineamiento=self.criterios["FMT-01"]["lineamiento"],
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

    def _evaluar_fmt02(self, metadata: Dict) -> CriteriaEvaluation:
        """
        FMT-02: Viewport para responsive design
        Verificar <meta name="viewport" content="width=device-width">
        Score: 10 si existe, 0 si no
        """
        viewport = metadata.get('viewport', '')
        has_viewport = metadata.get('has_viewport', bool(viewport))

        has_device_width = 'width=device-width' in viewport.lower().replace(' ', '') if viewport else False

        if has_viewport and has_device_width:
            status = "pass"
            score = 10.0
            message = "Viewport configurado correctamente para responsive"
        elif has_viewport:
            status = "partial"
            score = 5.0
            message = "Viewport presente pero puede no ser optimo"
        else:
            status = "fail"
            score = 0.0
            message = "No se encontro meta viewport (sitio no responsive)"

        return CriteriaEvaluation(
            criteria_id="FMT-02",
            criteria_name=self.criterios["FMT-02"]["name"],
            dimension=self.dimension,
            lineamiento=self.criterios["FMT-02"]["lineamiento"],
            status=status,
            score=score,
            max_score=10,
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


# Alias para compatibilidad con codigo existente
EvaluadorSemanticaTecnica = EvaluadorSemantica
