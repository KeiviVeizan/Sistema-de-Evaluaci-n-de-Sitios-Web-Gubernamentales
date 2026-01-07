"""
Motor de evaluación que orquesta todos los evaluadores
"""
from typing import Dict, List
from datetime import datetime
from sqlalchemy.orm import Session
from app.models.database_models import Evaluation, ExtractedContent, CriteriaResult
from .accesibilidad_evaluator import EvaluadorAccesibilidad
from .usabilidad_evaluator import EvaluadorUsabilidad
from .semantica_evaluator import EvaluadorSemanticaTecnica
from .soberania_evaluator import EvaluadorSoberania


class EvaluationEngine:
    """
    Motor principal de evaluación
    Ejecuta todos los evaluadores y calcula scores finales
    """

    def __init__(self, db: Session):
        self.db = db
        self.evaluadores = {
            "accesibilidad": EvaluadorAccesibilidad(),
            "usabilidad": EvaluadorUsabilidad(),
            "semantica": EvaluadorSemanticaTecnica(),
            "soberania": EvaluadorSoberania()
        }

    def evaluar_sitio(self, website_id: int) -> Dict:
        """
        Evalúa un sitio completo
        1. Obtiene el contenido extraído
        2. Ejecuta todos los evaluadores
        3. Guarda resultados en BD
        4. Calcula scores finales
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

            # 3. Ejecutar cada evaluador
            for dimension_name, evaluador in self.evaluadores.items():
                results = evaluador.evaluate(extracted_data)

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

            # 4. Calcular scores por dimensión
            scores_por_dimension = {}
            for dimension_name, evaluador in self.evaluadores.items():
                scores_por_dimension[dimension_name] = evaluador.get_dimension_score()

            # 5. Calcular score final ponderado (30-30-30-10)
            pesos = {
                "accesibilidad": 0.30,
                "usabilidad": 0.30,
                "semantica": 0.30,  # Solo parte técnica (15% real del total)
                "soberania": 0.10
            }

            score_final = 0
            for dimension, peso in pesos.items():
                dim_score = scores_por_dimension[dimension]['percentage']
                score_final += dim_score * peso

            # 6. Actualizar evaluación
            evaluation.score_digital_sovereignty = scores_por_dimension['soberania']['percentage']
            evaluation.score_accessibility = scores_por_dimension['accesibilidad']['percentage']
            evaluation.score_usability = scores_por_dimension['usabilidad']['percentage']
            evaluation.score_semantic_web = scores_por_dimension['semantica']['percentage']  # Por ahora solo técnica
            evaluation.score_total = score_final
            evaluation.status = 'completed'
            evaluation.completed_at = datetime.utcnow()

            self.db.commit()

            return {
                "evaluation_id": evaluation.id,
                "website_id": website_id,
                "status": "completed",
                "scores": {
                    "accesibilidad": scores_por_dimension['accesibilidad'],
                    "usabilidad": scores_por_dimension['usabilidad'],
                    "semantica_tecnica": scores_por_dimension['semantica'],
                    "soberania": scores_por_dimension['soberania'],
                    "total": score_final
                },
                "total_criteria": len(all_results),
                "passed": len([r for r in all_results if r.status == "pass"]),
                "failed": len([r for r in all_results if r.status == "fail"]),
                "partial": len([r for r in all_results if r.status == "partial"]),
                "not_applicable": len([r for r in all_results if r.status == "na"])
            }

        except Exception as e:
            evaluation.status = 'failed'
            evaluation.error_message = str(e)
            self.db.commit()
            raise
