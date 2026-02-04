"""
Evaluador de Accesibilidad (30%)
Evalúa 10 criterios WCAG 2.0: ACC-01 a ACC-10
"""
from typing import Dict, List
from .base_evaluator import BaseEvaluator, CriteriaEvaluation


class EvaluadorAccesibilidad(BaseEvaluator):
    """
    Evaluador de criterios de accesibilidad WCAG 2.0
    """

    def __init__(self):
        super().__init__(dimension="accesibilidad")

        # Pesos según tabla_final.xlsx
        self.criterios = {
            "ACC-01": {"name": "Texto alternativo en imágenes", "points": 14, "lineamiento": "D.S. 3925 (FMT-02) / WCAG 1.1.1"},
            "ACC-02": {"name": "Idioma de la página", "points": 10, "lineamiento": "D.S. 3925 (LANG-01) / WCAG 3.1.1"},
            "ACC-03": {"name": "Título descriptivo de página", "points": 10, "lineamiento": "D.S. 3925 (BUSC-03) / WCAG 2.4.2"},
            "ACC-04": {"name": "Estructura de encabezados", "points": 12, "lineamiento": "WCAG 1.3.1, 2.4.6"},
            "ACC-05": {"name": "Sin auto reproducción multimedia", "points": 10, "lineamiento": "D.S. 3925 (PROH-04) / WCAG 1.4.2"},
            "ACC-06": {"name": "Contraste texto-fondo", "points": 12, "lineamiento": "WCAG 1.4.3"},
            "ACC-07": {"name": "Etiquetas en formularios", "points": 12, "lineamiento": "WCAG 3.3.2"},
            "ACC-08": {"name": "Enlaces descriptivos", "points": 8, "lineamiento": "WCAG 2.4.4"},
            "ACC-09": {"name": "Encabezados y etiquetas descriptivas", "points": 6, "lineamiento": "WCAG 2.4.6"},
            "ACC-10": {"name": "Idioma de partes", "points": 6, "lineamiento": "WCAG 3.1.2"}
        }

    def evaluate(self, extracted_content: Dict) -> List[CriteriaEvaluation]:
        """Evalúa todos los criterios de accesibilidad"""
        self.clear_results()

        # Extraer datos relevantes
        metadata = extracted_content.get('metadata', {})
        images = extracted_content.get('images', {})
        headings = extracted_content.get('headings', {})
        forms = extracted_content.get('forms', {})
        media = extracted_content.get('media', {})
        links = extracted_content.get('links', {})
        language_parts = extracted_content.get('language_parts', {})

        # Evaluar cada criterio
        self.add_result(self._evaluar_acc01(images))
        self.add_result(self._evaluar_acc02(metadata))
        self.add_result(self._evaluar_acc03(metadata))
        self.add_result(self._evaluar_acc04(headings))
        self.add_result(self._evaluar_acc05(media))
        # ACC-06 requiere análisis de CSS (pendiente implementación completa)
        self.add_result(self._evaluar_acc06_placeholder())
        self.add_result(self._evaluar_acc07(forms))
        self.add_result(self._evaluar_acc08(links))
        self.add_result(self._evaluar_acc09(headings, forms))
        # ACC-10 usa datos de language_parts del crawler
        self.add_result(self._evaluar_acc10(language_parts))

        return self.results

    def _evaluar_acc01(self, images: Dict) -> CriteriaEvaluation:
        """
        ACC-01: Texto alternativo en imágenes
        100% de imágenes deben tener alt no vacío
        """
        total = images.get('total_count', 0)
        with_alt = images.get('with_alt', 0)  # FIX: crawler usa 'with_alt', no 'with_alt_count'

        if total == 0:
            # No hay imágenes, criterio N/A
            return CriteriaEvaluation(
                criteria_id="ACC-01",
                criteria_name=self.criterios["ACC-01"]["name"],
                dimension=self.dimension,
                lineamiento=self.criterios["ACC-01"]["lineamiento"],
                status="na",
                score=14,  # Full points si no aplica
                max_score=14,
                details={"message": "No se encontraron imágenes en el sitio"},
                evidence={"total_images": 0}
            )

        compliance = (with_alt / total) * 100

        # Scoring: 100% = 14pts proporcional
        score = (compliance / 100) * 14

        if compliance == 100:
            status = "pass"
        elif compliance >= 80:
            status = "partial"
        else:
            status = "fail"

        return CriteriaEvaluation(
            criteria_id="ACC-01",
            criteria_name=self.criterios["ACC-01"]["name"],
            dimension=self.dimension,
            lineamiento=self.criterios["ACC-01"]["lineamiento"],
            status=status,
            score=round(score, 2),
            max_score=14,
            details={
                "total_images": total,
                "with_alt": with_alt,
                "without_alt": total - with_alt,
                "compliance_percentage": round(compliance, 2),
                "message": f"{with_alt} de {total} imágenes tienen texto alternativo"
            },
            evidence={
                "images_without_alt": [
                    img for img in images.get('images', [])
                    if not img.get('has_alt') or img.get('alt') == ''
                ][:5]  # Primeros 5 ejemplos
            }
        )

    def _evaluar_acc02(self, metadata: Dict) -> CriteriaEvaluation:
        """
        ACC-02: Idioma de la página
        <html lang="..."> debe estar presente
        """
        lang = metadata.get('lang')

        if lang and lang.lower().startswith('es'):
            status = "pass"
            score = 10
            message = f"Idioma declarado correctamente: {lang}"
        elif lang:
            status = "partial"
            score = 5
            message = f"Idioma declarado pero no es español: {lang}"
        else:
            status = "fail"
            score = 0
            message = "No se declaró el idioma de la página"

        return CriteriaEvaluation(
            criteria_id="ACC-02",
            criteria_name=self.criterios["ACC-02"]["name"],
            dimension=self.dimension,
            lineamiento=self.criterios["ACC-02"]["lineamiento"],
            status=status,
            score=score,
            max_score=10,
            details={
                "lang_attribute": lang,
                "is_spanish": lang and lang.lower().startswith('es') if lang else False,
                "message": message
            },
            evidence={"html_lang": lang}
        )

    def _evaluar_acc03(self, metadata: Dict) -> CriteriaEvaluation:
        """
        ACC-03: Título descriptivo de página
        <title> debe tener al menos 10 caracteres
        """
        title = metadata.get('title', '')
        title_length = metadata.get('title_length', 0)

        if title_length >= 10:
            status = "pass"
            score = 10
            message = "Título presente y descriptivo"
        elif title_length > 0:
            status = "partial"
            score = 5
            message = "Título presente pero muy corto"
        else:
            status = "fail"
            score = 0
            message = "No hay título en la página"

        return CriteriaEvaluation(
            criteria_id="ACC-03",
            criteria_name=self.criterios["ACC-03"]["name"],
            dimension=self.dimension,
            lineamiento=self.criterios["ACC-03"]["lineamiento"],
            status=status,
            score=score,
            max_score=10,
            details={
                "title": title,
                "length": title_length,
                "min_required": 10,
                "message": message
            },
            evidence={"title_tag": title}
        )

    def _evaluar_acc04(self, headings: Dict) -> CriteriaEvaluation:
        """
        ACC-04: Estructura de encabezados
        - Debe haber al menos un h1
        - No debe haber saltos en la jerarquía
        """
        h1_count = headings.get('h1_count', 0)
        hierarchy_valid = headings.get('hierarchy_valid', False)
        total = headings.get('total_count', 0)

        score = 0
        issues = []

        # Verificar h1
        if h1_count == 0:
            issues.append("No hay encabezado h1")
        elif h1_count == 1:
            score += 6  # 50% del puntaje
        else:
            issues.append(f"Hay {h1_count} encabezados h1 (debería haber solo 1)")
            score += 3

        # Verificar jerarquía
        if hierarchy_valid:
            score += 6  # 50% del puntaje
        else:
            issues.append("La jerarquía tiene saltos de nivel")

        if score >= 10:
            status = "pass"
        elif score >= 6:
            status = "partial"
        else:
            status = "fail"

        return CriteriaEvaluation(
            criteria_id="ACC-04",
            criteria_name=self.criterios["ACC-04"]["name"],
            dimension=self.dimension,
            lineamiento=self.criterios["ACC-04"]["lineamiento"],
            status=status,
            score=score,
            max_score=12,
            details={
                "h1_count": h1_count,
                "hierarchy_valid": hierarchy_valid,
                "total_headings": total,
                "issues": issues,
                "message": " | ".join(issues) if issues else "Estructura de encabezados correcta"
            },
            evidence={
                "headings_list": headings.get('headings', [])[:10]  # Primeros 10
            }
        )

    def _evaluar_acc05(self, media: Dict) -> CriteriaEvaluation:
        """
        ACC-05: Sin auto reproducción multimedia
        No debe haber audio/video con autoplay
        """
        has_autoplay = media.get('has_autoplay', False)

        if has_autoplay:
            status = "fail"
            score = 0
            message = "Se detectó contenido multimedia con reproducción automática"
        else:
            status = "pass"
            score = 10
            message = "No hay reproducción automática de multimedia"

        return CriteriaEvaluation(
            criteria_id="ACC-05",
            criteria_name=self.criterios["ACC-05"]["name"],
            dimension=self.dimension,
            lineamiento=self.criterios["ACC-05"]["lineamiento"],
            status=status,
            score=score,
            max_score=10,
            details={
                "has_autoplay": has_autoplay,
                "audio_count": media.get('audio_count', 0),
                "video_count": media.get('video_count', 0),
                "message": message
            },
            evidence=media.get('media', {})
        )

    def _evaluar_acc06_placeholder(self) -> CriteriaEvaluation:
        """
        ACC-06: Contraste texto-fondo
        Placeholder - requiere análisis de CSS más complejo
        """
        return CriteriaEvaluation(
            criteria_id="ACC-06",
            criteria_name=self.criterios["ACC-06"]["name"],
            dimension=self.dimension,
            lineamiento=self.criterios["ACC-06"]["lineamiento"],
            status="na",
            score=12,  # Por ahora full points
            max_score=12,
            details={
                "message": "Análisis de contraste pendiente de implementación completa",
                "note": "Requiere análisis de estilos CSS"
            },
            evidence={}
        )

    def _evaluar_acc07(self, forms: Dict) -> CriteriaEvaluation:
        """
        ACC-07: Etiquetas en formularios
        100% de inputs deben tener label asociado
        """
        total_inputs = forms.get('total_inputs', 0)
        inputs_with_label = forms.get('inputs_with_label', 0)

        if total_inputs == 0:
            return CriteriaEvaluation(
                criteria_id="ACC-07",
                criteria_name=self.criterios["ACC-07"]["name"],
                dimension=self.dimension,
                lineamiento=self.criterios["ACC-07"]["lineamiento"],
                status="na",
                score=12,
                max_score=12,
                details={"message": "No se encontraron formularios"},
                evidence={}
            )

        compliance = (inputs_with_label / total_inputs) * 100
        score = (compliance / 100) * 12

        if compliance == 100:
            status = "pass"
        elif compliance >= 80:
            status = "partial"
        else:
            status = "fail"

        return CriteriaEvaluation(
            criteria_id="ACC-07",
            criteria_name=self.criterios["ACC-07"]["name"],
            dimension=self.dimension,
            lineamiento=self.criterios["ACC-07"]["lineamiento"],
            status=status,
            score=round(score, 2),
            max_score=12,
            details={
                "total_inputs": total_inputs,
                "with_label": inputs_with_label,
                "without_label": total_inputs - inputs_with_label,
                "compliance_percentage": round(compliance, 2),
                "message": f"{inputs_with_label} de {total_inputs} inputs tienen etiqueta asociada"
            },
            evidence={
                "forms": forms.get('forms', [])
            }
        )

    def _evaluar_acc08(self, links: Dict) -> CriteriaEvaluation:
        """
        ACC-08: Enlaces descriptivos
        Los enlaces no deben tener texto genérico como "clic aquí"
        """
        total = links.get('total_count', 0)
        generic_data = links.get('generic_text', {})
        empty_data = links.get('empty_links', {})

        generic = generic_data.get('count', 0) if isinstance(generic_data, dict) else generic_data
        empty = empty_data.get('count', 0) if isinstance(empty_data, dict) else empty_data

        if total == 0:
            return CriteriaEvaluation(
                criteria_id="ACC-08",
                criteria_name=self.criterios["ACC-08"]["name"],
                dimension=self.dimension,
                lineamiento=self.criterios["ACC-08"]["lineamiento"],
                status="na",
                score=8,
                max_score=8,
                details={"message": "No se encontraron enlaces"},
                evidence={}
            )

        problematic = generic + empty
        compliance = ((total - problematic) / total) * 100
        score = (compliance / 100) * 8

        if compliance >= 95:
            status = "pass"
        elif compliance >= 80:
            status = "partial"
        else:
            status = "fail"

        return CriteriaEvaluation(
            criteria_id="ACC-08",
            criteria_name=self.criterios["ACC-08"]["name"],
            dimension=self.dimension,
            lineamiento=self.criterios["ACC-08"]["lineamiento"],
            status=status,
            score=round(score, 2),
            max_score=8,
            details={
                "total_links": total,
                "generic_text": generic,
                "empty_links": empty,
                "problematic_links": problematic,
                "compliance_percentage": round(compliance, 2),
                "message": f"{problematic} enlaces problemáticos de {total} totales"
            },
            evidence={
                "generic_examples": []  # Se llenarían con los enlaces problemáticos
            }
        )

    def _evaluar_acc09(self, headings: Dict, forms: Dict) -> CriteriaEvaluation:
        """
        ACC-09: Encabezados y etiquetas descriptivas
        Los headings y labels deben tener contenido descriptivo
        """
        # Verificar headings vacíos
        headings_list = headings.get('headings', [])
        empty_headings = [h for h in headings_list if not h.get('text') or len(h.get('text', '').strip()) < 3]

        # Verificar labels vacíos
        forms_list = forms.get('forms', [])
        empty_labels = 0
        for form in forms_list:
            for input_item in form.get('inputs', []):
                label_text = input_item.get('label_text', '')
                if input_item.get('has_label') and (not label_text or len(label_text.strip()) < 2):
                    empty_labels += 1

        total_elements = len(headings_list) + forms.get('total_inputs', 0)
        problematic = len(empty_headings) + empty_labels

        if total_elements == 0:
            return CriteriaEvaluation(
                criteria_id="ACC-09",
                criteria_name=self.criterios["ACC-09"]["name"],
                dimension=self.dimension,
                lineamiento=self.criterios["ACC-09"]["lineamiento"],
                status="na",
                score=6,
                max_score=6,
                details={"message": "No hay headings ni formularios para evaluar"},
                evidence={}
            )

        compliance = ((total_elements - problematic) / total_elements) * 100
        score = (compliance / 100) * 6

        if compliance >= 95:
            status = "pass"
        elif compliance >= 80:
            status = "partial"
        else:
            status = "fail"

        return CriteriaEvaluation(
            criteria_id="ACC-09",
            criteria_name=self.criterios["ACC-09"]["name"],
            dimension=self.dimension,
            lineamiento=self.criterios["ACC-09"]["lineamiento"],
            status=status,
            score=round(score, 2),
            max_score=6,
            details={
                "total_elements": total_elements,
                "empty_headings": len(empty_headings),
                "empty_labels": empty_labels,
                "compliance_percentage": round(compliance, 2),
                "message": f"{problematic} elementos sin contenido descriptivo"
            },
            evidence={
                "empty_headings_examples": empty_headings[:5]
            }
        )

    def _evaluar_acc10(self, language_parts: Dict) -> CriteriaEvaluation:
        """
        ACC-10: Idioma de partes
        Verifica que elementos con idioma diferente tengan lang declarado
        """
        main_lang = language_parts.get('main_language', '')
        has_main_lang = language_parts.get('has_main_language', False)
        elements_diff_lang = language_parts.get('elements_with_different_lang', [])
        count_diff_lang = language_parts.get('count_different_lang', 0)
        acc_10_compliant = language_parts.get('acc_10_compliant', False)

        # Si no hay idioma principal declarado, falla
        if not has_main_lang:
            return CriteriaEvaluation(
                criteria_id="ACC-10",
                criteria_name=self.criterios["ACC-10"]["name"],
                dimension=self.dimension,
                lineamiento=self.criterios["ACC-10"]["lineamiento"],
                status="fail",
                score=0,
                max_score=6,
                details={
                    "main_language": main_lang,
                    "has_main_language": False,
                    "message": "No se declaró el idioma principal del documento"
                },
                evidence={"html_lang": main_lang}
            )

        # Si el sitio tiene idioma principal y maneja bien los elementos con idioma diferente
        if acc_10_compliant:
            status = "pass"
            score = 6
            message = f"Idioma principal '{main_lang}' declarado correctamente"
            if count_diff_lang > 0:
                message += f". {count_diff_lang} elementos con idioma diferente correctamente marcados"
        else:
            status = "partial"
            score = 3
            message = f"Idioma principal declarado pero posibles elementos sin marcar"

        return CriteriaEvaluation(
            criteria_id="ACC-10",
            criteria_name=self.criterios["ACC-10"]["name"],
            dimension=self.dimension,
            lineamiento=self.criterios["ACC-10"]["lineamiento"],
            status=status,
            score=score,
            max_score=6,
            details={
                "main_language": main_lang,
                "has_main_language": has_main_lang,
                "elements_with_different_lang": count_diff_lang,
                "languages_found": language_parts.get('languages_found', []),
                "message": message
            },
            evidence={
                "different_lang_elements": elements_diff_lang[:5]
            }
        )
