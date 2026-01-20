"""
Tests unitarios para el evaluador de semántica técnica.

Verifica especialmente SEM-03 que tiene la lógica más compleja.
"""

import pytest
from app.evaluator.semantica_evaluator import EvaluadorSemanticaTecnica


class TestSEM03:
    """Tests para el criterio SEM-03: Estructura semántica HTML5"""

    def test_sem03_estructura_perfecta(self):
        """Verifica que SEM-03 otorga puntaje completo a estructura perfecta"""
        extracted_content = {
            'semantic_elements': {
                'header': {'count': 1, 'present': True},
                'nav': {'count': 1, 'present': True},
                'main': {'count': 1, 'present': True},
                'footer': {'count': 1, 'present': True},
                'section': {'count': 3, 'present': True},
                'article': {'count': 2, 'present': True},
            },
            'structure': {
                'document_hierarchy': {
                    'structure_analysis': {
                        'main_count': 1,
                        'main_inside_section': False,
                        'nav_count': 1,
                        'navs_floating': 0,
                        'navs_in_header': 1,
                        'header_count': 1,
                        'div_ratio': 0.30,
                        'has_divitis': False
                    }
                }
            }
        }

        evaluador = EvaluadorSemanticaTecnica()
        results = evaluador.evaluate(extracted_content)
        sem03 = next(r for r in results if r.criteria_id == "SEM-03")

        assert sem03.status == "pass"
        assert sem03.score == 15.0
        assert len(sem03.details['issues']) == 0

    def test_sem03_detecta_main_inside_section(self):
        """Verifica que SEM-03 detecta main incorrectamente dentro de section"""
        extracted_content = {
            'semantic_elements': {
                'header': {'count': 1, 'present': True},
                'nav': {'count': 1, 'present': True},
                'main': {'count': 1, 'present': True},
                'footer': {'count': 1, 'present': True},
            },
            'structure': {
                'document_hierarchy': {
                    'structure_analysis': {
                        'main_count': 1,
                        'main_inside_section': True,  # ❌ Problema
                        'nav_count': 1,
                        'navs_floating': 0,
                        'header_count': 1,
                        'div_ratio': 0.3,
                        'has_divitis': False
                    }
                }
            }
        }

        evaluador = EvaluadorSemanticaTecnica()
        results = evaluador.evaluate(extracted_content)
        sem03 = next(r for r in results if r.criteria_id == "SEM-03")

        assert sem03.status in ["partial", "fail"]
        assert "<main> está incorrectamente dentro de <section>" in sem03.details['issues']
        assert sem03.score < 15.0

    def test_sem03_detecta_divitis(self):
        """Verifica que SEM-03 detecta exceso de divs (div-itis)"""
        extracted_content = {
            'semantic_elements': {
                'header': {'count': 1, 'present': True},
                'main': {'count': 1, 'present': True},
                'footer': {'count': 1, 'present': True},
                'nav': {'count': 1, 'present': True},
            },
            'structure': {
                'document_hierarchy': {
                    'structure_analysis': {
                        'main_count': 1,
                        'main_inside_section': False,
                        'nav_count': 1,
                        'navs_floating': 0,
                        'header_count': 1,
                        'div_ratio': 0.85,  # ❌ 85% divs
                        'has_divitis': True
                    }
                }
            }
        }

        evaluador = EvaluadorSemanticaTecnica()
        results = evaluador.evaluate(extracted_content)
        sem03 = next(r for r in results if r.criteria_id == "SEM-03")

        assert sem03.status in ["partial", "fail"]
        assert any("Exceso de <div>" in issue or "Alto uso de <div>" in issue
                   for issue in sem03.details['issues'])
        assert sem03.score < 15.0

    def test_sem03_detecta_navs_flotantes(self):
        """Verifica que SEM-03 detecta nav fuera de header/footer"""
        extracted_content = {
            'semantic_elements': {
                'header': {'count': 1, 'present': True},
                'main': {'count': 1, 'present': True},
                'footer': {'count': 1, 'present': True},
                'nav': {'count': 2, 'present': True},
            },
            'structure': {
                'document_hierarchy': {
                    'structure_analysis': {
                        'main_count': 1,
                        'main_inside_section': False,
                        'nav_count': 2,
                        'navs_floating': 2,  # ❌ Todos flotantes
                        'navs_in_header': 0,
                        'header_count': 1,
                        'div_ratio': 0.3,
                        'has_divitis': False
                    }
                }
            }
        }

        evaluador = EvaluadorSemanticaTecnica()
        results = evaluador.evaluate(extracted_content)
        sem03 = next(r for r in results if r.criteria_id == "SEM-03")

        assert sem03.status in ["partial", "fail"]
        assert any("<nav>" in issue for issue in sem03.details['issues'])

    def test_sem03_detecta_multiples_main(self):
        """Verifica que SEM-03 detecta múltiples elementos main"""
        extracted_content = {
            'semantic_elements': {
                'header': {'count': 1, 'present': True},
                'main': {'count': 3, 'present': True},  # ❌ Múltiples main
                'footer': {'count': 1, 'present': True},
                'nav': {'count': 1, 'present': True},
            },
            'structure': {
                'document_hierarchy': {
                    'structure_analysis': {
                        'main_count': 3,  # ❌ Debe ser 1
                        'main_inside_section': False,
                        'nav_count': 1,
                        'navs_floating': 0,
                        'header_count': 1,
                        'div_ratio': 0.3,
                        'has_divitis': False
                    }
                }
            }
        }

        evaluador = EvaluadorSemanticaTecnica()
        results = evaluador.evaluate(extracted_content)
        sem03 = next(r for r in results if r.criteria_id == "SEM-03")

        assert sem03.status in ["partial", "fail"]
        assert any("main" in issue.lower() for issue in sem03.details['issues'])

    def test_sem03_falta_elementos_basicos(self):
        """Verifica que SEM-03 penaliza falta de elementos básicos"""
        extracted_content = {
            'semantic_elements': {
                'header': {'count': 0, 'present': False},  # ❌ Falta
                'main': {'count': 0, 'present': False},     # ❌ Falta
                'footer': {'count': 1, 'present': True},
                'nav': {'count': 1, 'present': True},
            },
            'structure': {
                'document_hierarchy': {
                    'structure_analysis': {
                        'main_count': 0,
                        'main_inside_section': False,
                        'nav_count': 1,
                        'navs_floating': 0,
                        'header_count': 0,
                        'div_ratio': 0.3,
                        'has_divitis': False
                    }
                }
            }
        }

        evaluador = EvaluadorSemanticaTecnica()
        results = evaluador.evaluate(extracted_content)
        sem03 = next(r for r in results if r.criteria_id == "SEM-03")

        assert sem03.status == "fail"
        assert sem03.details['elements_present'] == 2  # Solo footer y nav
        assert len(sem03.details['issues']) > 0


class TestBaseEvaluatorHelpers:
    """Tests para los helpers de BaseEvaluator"""

    def test_extract_count_from_int(self):
        """Verifica extracción de count desde int"""
        from app.evaluator.base_evaluator import BaseEvaluator
        assert BaseEvaluator.extract_count(5) == 5

    def test_extract_count_from_dict(self):
        """Verifica extracción de count desde dict"""
        from app.evaluator.base_evaluator import BaseEvaluator
        assert BaseEvaluator.extract_count({'count': 10, 'present': True}) == 10

    def test_extract_count_from_none(self):
        """Verifica que None retorna default"""
        from app.evaluator.base_evaluator import BaseEvaluator
        assert BaseEvaluator.extract_count(None) == 0
        assert BaseEvaluator.extract_count(None, default=5) == 5

    def test_extract_present_from_bool(self):
        """Verifica extracción de present desde bool"""
        from app.evaluator.base_evaluator import BaseEvaluator
        assert BaseEvaluator.extract_present(True) is True
        assert BaseEvaluator.extract_present(False) is False

    def test_extract_present_from_dict(self):
        """Verifica extracción de present desde dict"""
        from app.evaluator.base_evaluator import BaseEvaluator
        assert BaseEvaluator.extract_present({'count': 10, 'present': True}) is True

    def test_calculate_status(self):
        """Verifica cálculo de status por porcentaje"""
        from app.evaluator.base_evaluator import BaseEvaluator
        assert BaseEvaluator.calculate_status(95) == "pass"
        assert BaseEvaluator.calculate_status(75) == "partial"
        assert BaseEvaluator.calculate_status(50) == "fail"

    def test_safe_divide(self):
        """Verifica división segura sin división por cero"""
        from app.evaluator.base_evaluator import BaseEvaluator
        assert BaseEvaluator.safe_divide(10, 2) == 5.0
        assert BaseEvaluator.safe_divide(10, 0) == 0.0
        assert BaseEvaluator.safe_divide(10, 0, default=999) == 999


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
