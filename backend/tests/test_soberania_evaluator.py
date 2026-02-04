"""
Tests para el Evaluador de Soberania Digital
"""
import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.evaluator.soberania_evaluator import EvaluadorSoberania, evaluar_soberania
from app.evaluator.base_evaluator import CriteriaEvaluation


class TestEvaluadorSoberaniaUnitario:
    """Tests unitarios con datos mock"""

    def setup_method(self):
        self.evaluador = EvaluadorSoberania()

    # ================================================================
    # PROH-01: Sin iframes externos (25 pts)
    # ================================================================

    def test_proh01_sin_iframes(self):
        """PROH-01: Sitio sin iframes externos debe pasar (25 pts)"""
        content = {
            'external_resources': {
                'iframes': {'external': [], 'count': 0}
            }
        }
        results = self.evaluador.evaluate(content)
        proh01 = next(r for r in results if r.criteria_id == 'PROH-01')

        assert proh01.status == 'pass'
        assert proh01.score == 25.0
        assert proh01.max_score == 25.0
        assert proh01.details['compliant'] is True

    def test_proh01_pocos_iframes(self):
        """PROH-01: 1-2 iframes externos = partial (12.5 pts)"""
        content = {
            'external_resources': {
                'iframes': {
                    'external': [
                        {'absolute_src': 'https://www.youtube.com/embed/VIDEO1', 'domain': 'youtube.com'}
                    ],
                    'count': 1
                }
            }
        }
        results = self.evaluador.evaluate(content)
        proh01 = next(r for r in results if r.criteria_id == 'PROH-01')

        assert proh01.status == 'partial'
        assert proh01.score == 12.5

    def test_proh01_muchos_iframes(self):
        """PROH-01: >2 iframes externos = fail (0 pts)"""
        content = {
            'external_resources': {
                'iframes': {
                    'external': [
                        {'absolute_src': 'https://www.youtube.com/embed/V1', 'domain': 'youtube.com'},
                        {'absolute_src': 'https://www.google.com/maps/embed', 'domain': 'google.com'},
                        {'absolute_src': 'https://www.facebook.com/plugins/page', 'domain': 'facebook.com'}
                    ],
                    'count': 3
                }
            }
        }
        results = self.evaluador.evaluate(content)
        proh01 = next(r for r in results if r.criteria_id == 'PROH-01')

        assert proh01.status == 'fail'
        assert proh01.score == 0.0

    # ================================================================
    # PROH-02: Sin CDNs externos no autorizados (25 pts)
    # ================================================================

    def test_proh02_sin_cdns_externos(self):
        """PROH-02: Sitio sin CDNs externos debe pasar (25 pts)"""
        content = {
            'external_resources': {
                'cdn': {'external': [], 'count': 0}
            }
        }
        results = self.evaluador.evaluate(content)
        proh02 = next(r for r in results if r.criteria_id == 'PROH-02')

        assert proh02.status == 'pass'
        assert proh02.score == 25.0
        assert proh02.max_score == 25.0

    def test_proh02_fonts_excluidos(self):
        """PROH-02: CDNs de fuentes deben excluirse (evaluados en PROH-03)"""
        content = {
            'external_resources': {
                'cdn': {
                    'external': [
                        {'domain': 'fonts.googleapis.com', 'type': 'link'},
                        {'domain': 'fonts.gstatic.com', 'type': 'link'}
                    ],
                    'count': 2
                }
            }
        }
        results = self.evaluador.evaluate(content)
        proh02 = next(r for r in results if r.criteria_id == 'PROH-02')

        # Fuentes se excluyen de PROH-02, asi que 0 CDNs no autorizados
        assert proh02.status == 'pass'
        assert proh02.score == 25.0
        assert 'fonts.googleapis.com' in proh02.details['font_cdns_excluded']

    def test_proh02_con_cdns_no_autorizados(self):
        """PROH-02: CDNs externos no autorizados penalizan"""
        content = {
            'external_resources': {
                'cdn': {
                    'external': [
                        {'domain': 'code.jquery.com', 'type': 'script'},
                        {'domain': 'cdn.jsdelivr.net', 'type': 'script'},
                        {'domain': 'cdnjs.cloudflare.com', 'type': 'script'}
                    ],
                    'count': 3
                }
            }
        }
        results = self.evaluador.evaluate(content)
        proh02 = next(r for r in results if r.criteria_id == 'PROH-02')

        assert proh02.status == 'partial'
        assert proh02.score == 10.0  # 3-5 CDNs = 40% = 10

    def test_proh02_muchos_cdns(self):
        """PROH-02: >5 CDNs externos = fail (0 pts)"""
        content = {
            'external_resources': {
                'cdn': {
                    'external': [
                        {'domain': f'cdn{i}.example.com', 'type': 'script'}
                        for i in range(6)
                    ],
                    'count': 6
                }
            }
        }
        results = self.evaluador.evaluate(content)
        proh02 = next(r for r in results if r.criteria_id == 'PROH-02')

        assert proh02.status == 'fail'
        assert proh02.score == 0.0

    # ================================================================
    # PROH-03: Sin fuentes externas (20 pts)
    # ================================================================

    def test_proh03_sin_fuentes_externas(self):
        """PROH-03: Sitio sin fuentes externas debe pasar (20 pts)"""
        content = {
            'external_resources': {
                'cdn': {'external': [], 'count': 0}
            }
        }
        results = self.evaluador.evaluate(content)
        proh03 = next(r for r in results if r.criteria_id == 'PROH-03')

        assert proh03.status == 'pass'
        assert proh03.score == 20.0
        assert proh03.max_score == 20.0
        assert proh03.details['compliant'] is True

    def test_proh03_con_google_fonts(self):
        """PROH-03: Google Fonts debe penalizar (fuentes externas)"""
        content = {
            'external_resources': {
                'cdn': {
                    'external': [
                        {'domain': 'fonts.googleapis.com', 'type': 'link',
                         'absolute_src': 'https://fonts.googleapis.com/css2?family=Roboto'},
                        {'domain': 'fonts.gstatic.com', 'type': 'link',
                         'absolute_src': 'https://fonts.gstatic.com/s/roboto/v30/font.woff2'}
                    ],
                    'count': 2
                }
            }
        }
        results = self.evaluador.evaluate(content)
        proh03 = next(r for r in results if r.criteria_id == 'PROH-03')

        assert proh03.status == 'partial'
        assert proh03.score == 10.0  # 1-2 fuentes = 50%
        assert proh03.details['font_count'] == 2

    def test_proh03_muchas_fuentes(self):
        """PROH-03: >2 fuentes externas = fail (0 pts)"""
        content = {
            'external_resources': {
                'cdn': {
                    'external': [
                        {'domain': 'fonts.googleapis.com', 'type': 'link',
                         'absolute_src': 'https://fonts.googleapis.com/css2?family=Roboto'},
                        {'domain': 'fonts.gstatic.com', 'type': 'link',
                         'absolute_src': 'https://fonts.gstatic.com/s/roboto/v30/font.woff2'},
                        {'domain': 'use.typekit.net', 'type': 'link',
                         'absolute_src': 'https://use.typekit.net/abc123.css'}
                    ],
                    'count': 3
                }
            }
        }
        results = self.evaluador.evaluate(content)
        proh03 = next(r for r in results if r.criteria_id == 'PROH-03')

        assert proh03.status == 'fail'
        assert proh03.score == 0.0

    def test_proh03_cdns_no_font_no_afectan(self):
        """PROH-03: CDNs que no son fuentes no deben afectar"""
        content = {
            'external_resources': {
                'cdn': {
                    'external': [
                        {'domain': 'code.jquery.com', 'type': 'script'},
                        {'domain': 'cdn.jsdelivr.net', 'type': 'script'}
                    ],
                    'count': 2
                }
            }
        }
        results = self.evaluador.evaluate(content)
        proh03 = next(r for r in results if r.criteria_id == 'PROH-03')

        # CDNs que no son fuentes no afectan PROH-03
        assert proh03.status == 'pass'
        assert proh03.score == 20.0

    # ================================================================
    # PROH-04: Sin trackers externos (30 pts - CRITICO)
    # ================================================================

    def test_proh04_sin_trackers(self):
        """PROH-04: Sitio sin trackers debe pasar (30 pts)"""
        content = {
            'external_resources': {
                'trackers': {'found': [], 'count': 0}
            }
        }
        results = self.evaluador.evaluate(content)
        proh04 = next(r for r in results if r.criteria_id == 'PROH-04')

        assert proh04.status == 'pass'
        assert proh04.score == 30.0
        assert proh04.max_score == 30.0
        assert proh04.details['compliant'] is True

    def test_proh04_con_google_analytics(self):
        """PROH-04: Google Analytics = fail critico (0 pts)"""
        content = {
            'external_resources': {
                'trackers': {
                    'found': [
                        {'tracker': 'google-analytics.com', 'type': 'script_src'},
                        {'tracker': 'googletagmanager.com', 'type': 'script_src'}
                    ],
                    'count': 2
                }
            }
        }
        results = self.evaluador.evaluate(content)
        proh04 = next(r for r in results if r.criteria_id == 'PROH-04')

        assert proh04.status == 'fail'
        assert proh04.score == 0.0
        assert len(proh04.details['critical_trackers']) == 2

    def test_proh04_trackers_menores(self):
        """PROH-04: Trackers menores = fail con score parcial (5 pts)"""
        content = {
            'external_resources': {
                'trackers': {
                    'found': [
                        {'tracker': 'clarity.ms', 'type': 'script_src'}
                    ],
                    'count': 1
                }
            }
        }
        results = self.evaluador.evaluate(content)
        proh04 = next(r for r in results if r.criteria_id == 'PROH-04')

        assert proh04.status == 'fail'
        assert proh04.score == 5.0

    # ================================================================
    # Test integral: max_score = 100
    # ================================================================

    def test_max_score_total_100(self):
        """Verificar que el total de puntos sea 100"""
        content = {
            'external_resources': {
                'trackers': {'found': [], 'count': 0},
                'cdn': {'external': [], 'count': 0},
                'iframes': {'external': [], 'count': 0}
            }
        }
        results = self.evaluador.evaluate(content)

        assert len(results) == 4
        max_score = sum(r.max_score for r in results)
        assert max_score == 100.0, f"max_score total debe ser 100, es {max_score}"

        total_score = sum(r.score for r in results)
        assert total_score == 100.0, f"score perfecto debe ser 100, es {total_score}"

    def test_evaluar_soberania_funcion(self):
        """Test de la funcion de conveniencia"""
        content = {
            'external_resources': {
                'trackers': {'found': [], 'count': 0},
                'cdn': {'external': [], 'count': 0},
                'iframes': {'external': [], 'count': 0}
            }
        }
        result = evaluar_soberania(content)

        assert result['dimension'] == 'sovereignty'
        assert result['score'] == 100.0
        assert result['max_score'] == 100.0
        assert result['summary']['passed'] == 4
        assert len(result['criteria_results']) == 4

    def test_criterios_correctos(self):
        """Verificar que los criterios tengan los nombres y puntajes correctos"""
        criterios = self.evaluador.criterios

        assert criterios['PROH-01']['name'] == 'Sin iframes externos'
        assert criterios['PROH-01']['max_score'] == 25.0

        assert criterios['PROH-02']['name'] == 'Sin CDNs externos no autorizados'
        assert criterios['PROH-02']['max_score'] == 25.0

        assert criterios['PROH-03']['name'] == 'Sin fuentes externas'
        assert criterios['PROH-03']['max_score'] == 20.0

        assert criterios['PROH-04']['name'] == 'Sin trackers externos'
        assert criterios['PROH-04']['max_score'] == 30.0


class TestEvaluadorSoberaniaIntegracion:
    """Tests de integracion con crawler real"""

    @pytest.fixture
    def crawler(self):
        from app.crawler.html_crawler import GobBoCrawler
        return GobBoCrawler(timeout=45)

    def test_evaluar_aduana_gob_bo(self, crawler):
        """Test con sitio real: aduana.gob.bo"""
        extracted = crawler.crawl('https://www.aduana.gob.bo')

        if 'error' in extracted:
            pytest.skip(f"No se pudo conectar: {extracted['error']}")

        evaluador = EvaluadorSoberania()
        results = evaluador.evaluate(extracted)

        print("\n" + "=" * 80)
        print("EVALUACION DE SOBERANIA DIGITAL: aduana.gob.bo")
        print("=" * 80)

        for r in results:
            rec = r.evidence.get('recomendacion', {})
            estado = rec.get('estado', 'N/A') if isinstance(rec, dict) else 'N/A'
            print(f"\n{r.criteria_id}: {r.criteria_name}")
            print(f"  Score: {r.score}/{r.max_score} - Status: {r.status}")
            print(f"  Estado: {estado}")
            print(f"  Mensaje: {r.details.get('message', 'N/A')}")

        dimension_score = evaluador.get_dimension_score()
        print("\n" + "=" * 80)
        print(f"SCORE TOTAL: {dimension_score['total_score']}/{dimension_score['max_score']} "
              f"({dimension_score['percentage']:.1f}%)")
        print(f"Passed: {dimension_score['passed']}, Partial: {dimension_score['partial']}, "
              f"Failed: {dimension_score['failed']}")
        print("=" * 80)

        # Verificaciones basicas
        assert len(results) == 4
        max_total = sum(r.max_score for r in results)
        assert max_total == 100.0


if __name__ == '__main__':
    pytest.main([__file__, '-v', '-s'])
