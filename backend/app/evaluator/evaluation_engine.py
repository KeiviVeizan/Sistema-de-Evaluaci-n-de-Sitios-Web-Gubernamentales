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
from datetime import datetime

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
            # Adaptar datos al formato NLP
            nlp_data = self.nlp_adapter.adapt(extracted_data)

            # Ejecutar análisis
            result = self.nlp_analyzer.analyze_website(nlp_data)

            logger.info(f"Análisis NLP completado: {result['global_score']:.1f}/100")
            return result

        except Exception as e:
            logger.error(f"Error en análisis NLP: {e}")
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
                analyzed_at=datetime.utcnow()
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
            "timestamp": datetime.utcnow().isoformat(),
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
            "criteria_results": [
                r.to_dict() if hasattr(r, 'to_dict') else r
                for r in all_results
            ],
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
