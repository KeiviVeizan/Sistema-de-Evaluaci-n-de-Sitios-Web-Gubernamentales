"""
Evaluador de Semántica Técnica (15% de la dimensión de 30%)
Evalúa 10 criterios: SEM-01 a SEM-04, SEO-01 a SEO-03, FMT-01, FMT-02, más 2 adicionales
"""
from typing import Dict, List
from .base_evaluator import BaseEvaluator, CriteriaEvaluation


class EvaluadorSemanticaTecnica(BaseEvaluator):
    """
    Evaluador de criterios de semántica técnica y SEO
    """

    def __init__(self):
        super().__init__(dimension="semantica")

        # Pesos según tabla_final.xlsx
        self.criterios = {
            "SEM-01": {"name": "Elementos semánticos HTML5", "points": 12, "lineamiento": "WCAG 1.3.1 / HTML5"},
            "SEM-02": {"name": "Estructura de documento", "points": 10, "lineamiento": "HTML5 / WCAG 1.3.1"},
            "SEM-03": {"name": "Estructura semántica HTML5", "points": 15, "lineamiento": "HTML5 / W3C"},
            "SEM-04": {"name": "Tablas con encabezados", "points": 10, "lineamiento": "WCAG 1.3.1"},
            "SEO-01": {"name": "Meta description", "points": 10, "lineamiento": "D.S. 3925 (BUSC-01)"},
            "SEO-02": {"name": "Meta keywords", "points": 8, "lineamiento": "D.S. 3925 (BUSC-02)"},
            "SEO-03": {"name": "URLs amigables", "points": 10, "lineamiento": "SEO best practices"},
            "FMT-01": {"name": "Responsive design", "points": 12, "lineamiento": "D.S. 3925 (FMT-01)"},
            "FMT-02": {"name": "Validación HTML", "points": 10, "lineamiento": "HTML5 standards"},
            "LANG-02": {"name": "Contenido en español", "points": 10, "lineamiento": "D.S. 3925 (LANG-02)"}
        }

    def evaluate(self, extracted_content: Dict) -> List[CriteriaEvaluation]:
        """Evalúa todos los criterios de semántica técnica"""
        self.clear_results()

        # Extraer datos relevantes
        metadata = extracted_content.get('metadata', {})
        structure = extracted_content.get('structure', {})
        semantic_elements = extracted_content.get('semantic_elements', {})
        links = extracted_content.get('links', {})
        text_corpus = extracted_content.get('text_corpus', {})

        # Evaluar cada criterio
        self.add_result(self._evaluar_sem01(semantic_elements))
        self.add_result(self._evaluar_sem02(semantic_elements, structure))
        self.add_result(self._evaluar_sem03(semantic_elements, structure))
        self.add_result(self._evaluar_sem04(structure))
        self.add_result(self._evaluar_seo01(metadata))
        self.add_result(self._evaluar_seo02(metadata))
        self.add_result(self._evaluar_seo03(links))
        self.add_result(self._evaluar_fmt01(metadata))
        self.add_result(self._evaluar_fmt02(structure))
        self.add_result(self._evaluar_lang02(text_corpus, metadata))

        return self.results

    def _evaluar_sem01(self, semantic_elements: Dict) -> CriteriaEvaluation:
        """
        SEM-01: Elementos semánticos HTML5
        Uso de header, nav, main, article, section, aside, footer
        """
        required_elements = ['header', 'nav', 'main', 'footer']
        optional_elements = ['article', 'section', 'aside']

        required_count = 0
        optional_count = 0

        for elem in required_elements:
            if self.extract_count(semantic_elements.get(elem, 0)) > 0:
                required_count += 1

        for elem in optional_elements:
            if self.extract_count(semantic_elements.get(elem, 0)) > 0:
                optional_count += 1

        # Score: 3 puntos por cada elemento requerido, 1.5 por opcionales (hasta 3)
        score = (required_count * 3) + min(optional_count, 2)

        if required_count == 4 and optional_count >= 2:
            status = "pass"
        elif required_count >= 3:
            status = "partial"
        else:
            status = "fail"

        return CriteriaEvaluation(
            criteria_id="SEM-01",
            criteria_name=self.criterios["SEM-01"]["name"],
            dimension=self.dimension,
            lineamiento=self.criterios["SEM-01"]["lineamiento"],
            status=status,
            score=round(score, 2),
            max_score=12,
            details={
                "required_elements": {elem: semantic_elements.get(elem, 0) for elem in required_elements},
                "optional_elements": {elem: semantic_elements.get(elem, 0) for elem in optional_elements},
                "required_count": required_count,
                "optional_count": optional_count,
                "message": f"{required_count}/4 elementos requeridos, {optional_count}/3 opcionales"
            },
            evidence=semantic_elements
        )

    def _evaluar_sem02(self, semantic_elements: Dict, structure: Dict) -> CriteriaEvaluation:
        """
        SEM-02: Estructura de documento
        Debe tener estructura lógica con header, main, footer
        """
        has_header = self.extract_count(semantic_elements.get('header', 0)) > 0
        has_main = self.extract_count(semantic_elements.get('main', 0)) > 0
        has_footer = self.extract_count(semantic_elements.get('footer', 0)) > 0

        components = sum([has_header, has_main, has_footer])

        # 10 puntos totales: header=4, main=4, footer=2
        score = 0
        if has_header:
            score += 4
        if has_main:
            score += 4
        if has_footer:
            score += 2

        if components == 3:
            status = "pass"
        elif components == 2:
            status = "partial"
        else:
            status = "fail"

        return CriteriaEvaluation(
            criteria_id="SEM-02",
            criteria_name=self.criterios["SEM-02"]["name"],
            dimension=self.dimension,
            lineamiento=self.criterios["SEM-02"]["lineamiento"],
            status=status,
            score=score,
            max_score=10,
            details={
                "has_header": has_header,
                "has_main": has_main,
                "has_footer": has_footer,
                "components": components,
                "message": f"Estructura con {components}/3 componentes principales"
            },
            evidence={
                "header_count": self._get_count(semantic_elements.get('header', 0)),
                "main_count": self._get_count(semantic_elements.get('main', 0)),
                "footer_count": self._get_count(semantic_elements.get('footer', 0))
            }
        )

    def _evaluar_sem03(self, semantic_elements: Dict, structure: Dict) -> CriteriaEvaluation:
        """
        SEM-03: Elementos semánticos HTML5
        NO solo verifica presencia, sino CORRECTA ESTRUCTURA

        Evalúa:
        1. Presencia de elementos básicos (30%)
        2. Estructura jerárquica correcta (40%)
        3. Sin anti-patrones (30%)
        """
        score = 0
        max_score = 15
        issues = []
        recommendations = []

        # Obtener análisis de estructura
        hierarchy = structure.get('document_hierarchy', {})
        analysis = hierarchy.get('structure_analysis', {})

        # ═══════════════════════════════════════════════════════════
        # PARTE 1: PRESENCIA DE ELEMENTOS BÁSICOS (30% = 4.5 puntos)
        # ═══════════════════════════════════════════════════════════

        required_elements = {
            'header': semantic_elements.get('header', {}).get('present', False),
            'nav': semantic_elements.get('nav', {}).get('present', False),
            'main': semantic_elements.get('main', {}).get('present', False),
            'footer': semantic_elements.get('footer', {}).get('present', False)
        }

        present_count = sum(required_elements.values())
        score += (present_count / 4) * 4.5

        for element, present in required_elements.items():
            if not present:
                issues.append(f"Falta elemento <{element}>")
                recommendations.append(f"Agregar <{element}> para estructura semántica completa")

        # ═══════════════════════════════════════════════════════════
        # PARTE 2: ESTRUCTURA JERÁRQUICA CORRECTA (40% = 6 puntos)
        # ═══════════════════════════════════════════════════════════

        structure_score = 6.0

        # 2.1: Solo debe haber 1 <main>
        main_count = analysis.get('main_count', 0)
        if main_count == 1:
            # Perfecto
            pass
        elif main_count == 0:
            structure_score -= 2
            issues.append("No hay elemento <main>")
            recommendations.append("Agregar <main> único para el contenido principal")
        else:
            structure_score -= 1.5
            issues.append(f"Hay {main_count} elementos <main> (debe ser único)")
            recommendations.append("Usar solo un <main> por página")

        # 2.2: <main> NO debe estar dentro de <section>
        if analysis.get('main_inside_section', False):
            structure_score -= 2
            issues.append("<main> está incorrectamente dentro de <section>")
            recommendations.append("Mover <main> fuera de <section>. Estructura correcta: <main> contiene <section>, no al revés")

        # 2.3: <nav> debería estar en <header> o <footer>
        nav_count = analysis.get('nav_count', 0)
        navs_floating = analysis.get('navs_floating', 0)

        if nav_count > 0:
            if navs_floating == nav_count:
                # Todos los nav están flotantes
                structure_score -= 1.5
                issues.append("Todos los <nav> están fuera de <header>/<footer>")
                recommendations.append("Colocar <nav> dentro de <header> para mejor semántica")
            elif navs_floating > 0:
                structure_score -= 0.5
                issues.append(f"{navs_floating} de {nav_count} <nav> están mal ubicados")

        # 2.4: Solo debería haber 1 <header> principal
        header_count = analysis.get('header_count', 0)
        if header_count > 1:
            structure_score -= 0.5
            issues.append(f"Hay {header_count} elementos <header> (generalmente debe ser 1 principal)")
            recommendations.append("Considerar si todos los <header> son necesarios o usar <div> para sub-headers")

        score += max(0, structure_score)

        # ═══════════════════════════════════════════════════════════
        # PARTE 3: AUSENCIA DE ANTI-PATRONES (30% = 4.5 puntos)
        # ═══════════════════════════════════════════════════════════

        antipattern_score = 4.5

        # 3.1: Detectar "div-itis" (exceso de divs)
        has_divitis = analysis.get('has_divitis', False)
        div_ratio = analysis.get('div_ratio', 0)

        if has_divitis:
            antipattern_score -= 3
            issues.append(f"Exceso de <div> genéricos ({int(div_ratio * 100)}% del contenido)")
            recommendations.append("Reemplazar <div> por elementos semánticos donde sea apropiado (<section>, <article>, <aside>)")
        elif div_ratio > 0.5:
            antipattern_score -= 1.5
            issues.append(f"Alto uso de <div> ({int(div_ratio * 100)}%)")
            recommendations.append("Considerar usar más elementos semánticos HTML5")

        # 3.2: Verificar uso de <section> y <article>
        has_section = semantic_elements.get('section', {}).get('present', False)
        has_article = semantic_elements.get('article', {}).get('present', False)

        if not has_section and not has_article:
            antipattern_score -= 1.5
            issues.append("No usa <section> ni <article> para organizar contenido")
            recommendations.append("Usar <section> para agrupar contenido temático y <article> para contenido independiente")

        score += max(0, antipattern_score)

        # ═══════════════════════════════════════════════════════════
        # DETERMINAR STATUS
        # ═══════════════════════════════════════════════════════════

        percentage = (score / max_score) * 100

        if percentage >= 90:
            status = "pass"
        elif percentage >= 70:
            status = "partial"
        else:
            status = "fail"

        return CriteriaEvaluation(
            criteria_id="SEM-03",
            criteria_name=self.criterios["SEM-03"]["name"],
            dimension=self.dimension,
            lineamiento=self.criterios["SEM-03"]["lineamiento"],
            status=status,
            score=round(score, 2),
            max_score=max_score,
            details={
                "percentage": round(percentage, 2),
                "elements_present": present_count,
                "structure_correct": structure_score > 4,
                "no_antipatterns": antipattern_score > 3,
                "issues": issues,
                "recommendations": recommendations,
                "structure_analysis": analysis
            },
            evidence={
                "hierarchy": hierarchy.get('hierarchy', [])[:5]  # Primeras 5 capas
            }
        )

    def _evaluar_sem04(self, structure: Dict) -> CriteriaEvaluation:
        """
        SEM-04: Tablas con encabezados
        Las tablas deben tener <th> o scope
        """
        table_count = structure.get('table_count', 0)

        if table_count == 0:
            # No hay tablas, criterio N/A
            return CriteriaEvaluation(
                criteria_id="SEM-04",
                criteria_name=self.criterios["SEM-04"]["name"],
                dimension=self.dimension,
                lineamiento=self.criterios["SEM-04"]["lineamiento"],
                status="na",
                score=10,
                max_score=10,
                details={"message": "No se encontraron tablas"},
                evidence={}
            )

        # Por ahora asumimos que si hay tablas, cumplen (placeholder)
        # En implementación real, verificaríamos la estructura
        status = "pass"
        score = 10
        message = f"{table_count} tabla(s) encontrada(s)"

        return CriteriaEvaluation(
            criteria_id="SEM-04",
            criteria_name=self.criterios["SEM-04"]["name"],
            dimension=self.dimension,
            lineamiento=self.criterios["SEM-04"]["lineamiento"],
            status=status,
            score=score,
            max_score=10,
            details={
                "table_count": table_count,
                "message": message,
                "note": "Verificación detallada de <th> pendiente"
            },
            evidence={}
        )

    def _evaluar_seo01(self, metadata: Dict) -> CriteriaEvaluation:
        """
        SEO-01: Meta description
        Debe tener meta description de al menos 50 caracteres
        """
        description = metadata.get('description') or ''
        desc_length = len(description)

        if desc_length >= 50:
            status = "pass"
            score = 10
            message = f"Meta description presente ({desc_length} caracteres)"
        elif desc_length > 0:
            status = "partial"
            score = 5
            message = f"Meta description muy corta ({desc_length} caracteres)"
        else:
            status = "fail"
            score = 0
            message = "No hay meta description"

        return CriteriaEvaluation(
            criteria_id="SEO-01",
            criteria_name=self.criterios["SEO-01"]["name"],
            dimension=self.dimension,
            lineamiento=self.criterios["SEO-01"]["lineamiento"],
            status=status,
            score=score,
            max_score=10,
            details={
                "description": description,
                "length": desc_length,
                "min_required": 50,
                "message": message
            },
            evidence={"meta_description": description}
        )

    def _evaluar_seo02(self, metadata: Dict) -> CriteriaEvaluation:
        """
        SEO-02: Meta keywords
        Debe tener meta keywords
        """
        keywords = metadata.get('keywords') or ''
        has_keywords = len(keywords) > 0

        if has_keywords and len(keywords) >= 20:
            status = "pass"
            score = 8
            message = "Meta keywords presente"
        elif has_keywords:
            status = "partial"
            score = 4
            message = "Meta keywords muy breve"
        else:
            status = "fail"
            score = 0
            message = "No hay meta keywords"

        return CriteriaEvaluation(
            criteria_id="SEO-02",
            criteria_name=self.criterios["SEO-02"]["name"],
            dimension=self.dimension,
            lineamiento=self.criterios["SEO-02"]["lineamiento"],
            status=status,
            score=score,
            max_score=8,
            details={
                "keywords": keywords,
                "has_keywords": has_keywords,
                "length": len(keywords),
                "message": message
            },
            evidence={"meta_keywords": keywords}
        )

    def _evaluar_seo03(self, links: Dict) -> CriteriaEvaluation:
        """
        SEO-03: URLs amigables
        URLs no deben tener muchos parámetros o IDs numéricos
        """
        links_list = links.get('links', [])

        if len(links_list) == 0:
            return CriteriaEvaluation(
                criteria_id="SEO-03",
                criteria_name=self.criterios["SEO-03"]["name"],
                dimension=self.dimension,
                lineamiento=self.criterios["SEO-03"]["lineamiento"],
                status="na",
                score=10,
                max_score=10,
                details={"message": "No hay enlaces para evaluar"},
                evidence={}
            )

        friendly_urls = 0
        unfriendly_urls = 0

        for link in links_list[:50]:  # Revisar primeros 50 enlaces
            href = link.get('href', '').lower()

            # URLs relativas o con rutas semánticas son amigables
            if not href or href.startswith('#'):
                continue

            # Indicadores de URL no amigable
            if '?' in href and href.count('=') > 2:
                unfriendly_urls += 1
            elif href.count('id=') > 0:
                unfriendly_urls += 1
            else:
                friendly_urls += 1

        total_analyzed = friendly_urls + unfriendly_urls

        if total_analyzed == 0:
            compliance = 100
        else:
            compliance = (friendly_urls / total_analyzed) * 100

        score = (compliance / 100) * 10

        if compliance >= 80:
            status = "pass"
        elif compliance >= 60:
            status = "partial"
        else:
            status = "fail"

        return CriteriaEvaluation(
            criteria_id="SEO-03",
            criteria_name=self.criterios["SEO-03"]["name"],
            dimension=self.dimension,
            lineamiento=self.criterios["SEO-03"]["lineamiento"],
            status=status,
            score=round(score, 2),
            max_score=10,
            details={
                "friendly_urls": friendly_urls,
                "unfriendly_urls": unfriendly_urls,
                "total_analyzed": total_analyzed,
                "compliance_percentage": round(compliance, 2),
                "message": f"{friendly_urls}/{total_analyzed} URLs amigables"
            },
            evidence={}
        )

    def _evaluar_fmt01(self, metadata: Dict) -> CriteriaEvaluation:
        """
        FMT-01: Responsive design
        Debe tener viewport meta tag
        """
        viewport = metadata.get('viewport') or ''
        has_viewport = len(viewport) > 0

        if has_viewport and 'width=device-width' in viewport:
            status = "pass"
            score = 12
            message = "Viewport configurado para responsive design"
        elif has_viewport:
            status = "partial"
            score = 6
            message = "Viewport presente pero no optimizado"
        else:
            status = "fail"
            score = 0
            message = "No hay meta viewport"

        return CriteriaEvaluation(
            criteria_id="FMT-01",
            criteria_name=self.criterios["FMT-01"]["name"],
            dimension=self.dimension,
            lineamiento=self.criterios["FMT-01"]["lineamiento"],
            status=status,
            score=score,
            max_score=12,
            details={
                "viewport": viewport,
                "has_viewport": has_viewport,
                "is_responsive": 'width=device-width' in viewport if has_viewport else False,
                "message": message
            },
            evidence={"meta_viewport": viewport}
        )

    def _evaluar_fmt02(self, structure: Dict) -> CriteriaEvaluation:
        """
        FMT-02: Validación HTML
        Estructura básica debe estar presente
        """
        # FIX: El crawler guarda 'has_html5_doctype', no 'has_doctype'
        has_doctype = structure.get('has_html5_doctype', False)
        has_html = structure.get('has_html', False)
        has_head = structure.get('has_head', False)
        has_body = structure.get('has_body', False)

        components = sum([has_doctype, has_html, has_head, has_body])

        # 2.5 puntos por cada componente
        score = components * 2.5

        if components == 4:
            status = "pass"
        elif components >= 3:
            status = "partial"
        else:
            status = "fail"

        return CriteriaEvaluation(
            criteria_id="FMT-02",
            criteria_name=self.criterios["FMT-02"]["name"],
            dimension=self.dimension,
            lineamiento=self.criterios["FMT-02"]["lineamiento"],
            status=status,
            score=score,
            max_score=10,
            details={
                "has_doctype": has_doctype,
                "has_html": has_html,
                "has_head": has_head,
                "has_body": has_body,
                "components": components,
                "message": f"Estructura HTML con {components}/4 componentes básicos"
            },
            evidence={}
        )

    def _evaluar_lang02(self, text_corpus: Dict, metadata: Dict) -> CriteriaEvaluation:
        """
        LANG-02: Contenido en español
        El contenido principal debe estar en español
        """
        total_words = text_corpus.get('total_words', 0)
        lang = metadata.get('lang', '')

        # Si el idioma está declarado como español y hay contenido, asumimos que cumple
        if lang and lang.lower().startswith('es') and total_words > 100:
            status = "pass"
            score = 10
            message = f"Contenido en español ({total_words} palabras)"
        elif total_words > 100:
            status = "partial"
            score = 5
            message = "Hay contenido pero el idioma no está claramente definido"
        else:
            status = "fail"
            score = 0
            message = "No se detectó contenido suficiente en español"

        return CriteriaEvaluation(
            criteria_id="LANG-02",
            criteria_name=self.criterios["LANG-02"]["name"],
            dimension=self.dimension,
            lineamiento=self.criterios["LANG-02"]["lineamiento"],
            status=status,
            score=score,
            max_score=10,
            details={
                "total_words": total_words,
                "declared_lang": lang,
                "is_spanish": lang and lang.lower().startswith('es') if lang else False,
                "message": message
            },
            evidence={
                "lang": lang,
                "word_count": total_words
            }
        )
