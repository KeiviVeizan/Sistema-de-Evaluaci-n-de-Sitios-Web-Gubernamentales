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

    def test_proh01_sin_trackers(self):
        """PROH-01: Sitio sin trackers debe pasar"""
        content = {
            'url': 'https://www.ejemplo.gob.bo',
            'external_resources': {
                'trackers': {'found': [], 'count': 0}
            }
        }
        results = self.evaluador.evaluate(content)
        proh01 = next(r for r in results if r.criteria_id == 'PROH-01')

        assert proh01.status == 'pass'
        assert proh01.score == 10.0
        assert proh01.details['compliant'] is True

    def test_proh01_con_google_analytics(self):
        """PROH-01: Sitio con Google Analytics debe fallar"""
        content = {
            'url': 'https://www.ejemplo.gob.bo',
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
        proh01 = next(r for r in results if r.criteria_id == 'PROH-01')

        assert proh01.status == 'fail'
        assert proh01.score == 0.0
        assert len(proh01.details['critical_trackers']) == 2

    def test_proh02_sin_cdns_externos(self):
        """PROH-02: Sitio sin CDNs externos debe pasar"""
        content = {
            'url': 'https://www.ejemplo.gob.bo',
            'external_resources': {
                'cdn': {'external': [], 'count': 0}
            }
        }
        results = self.evaluador.evaluate(content)
        proh02 = next(r for r in results if r.criteria_id == 'PROH-02')

        assert proh02.status == 'pass'
        assert proh02.score == 10.0

    def test_proh02_con_cdns_permitidos(self):
        """PROH-02: Fuentes de Google deben ser permitidas"""
        content = {
            'url': 'https://www.ejemplo.gob.bo',
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

        assert proh02.status == 'pass'
        assert proh02.score == 10.0
        assert 'fonts.googleapis.com' in proh02.details['allowed_cdns_used']

    def test_proh02_con_cdns_no_autorizados(self):
        """PROH-02: CDNs externos no autorizados deben penalizar"""
        content = {
            'url': 'https://www.ejemplo.gob.bo',
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
        assert proh02.score == 4.0  # 3-5 CDNs = 4.0

    def test_proh03_dominio_gob_bo(self):
        """PROH-03: Dominio .gob.bo debe pasar"""
        content = {
            'url': 'https://www.aduana.gob.bo',
            'metadata': {'domain': 'www.aduana.gob.bo'}
        }
        results = self.evaluador.evaluate(content)
        proh03 = next(r for r in results if r.criteria_id == 'PROH-03')

        assert proh03.status == 'pass'
        assert proh03.score == 10.0
        assert proh03.details['tipo_dominio'] == 'gubernamental_boliviano'

    def test_proh03_dominio_bo_no_gob(self):
        """PROH-03: Dominio .bo sin .gob debe ser parcial"""
        content = {
            'url': 'https://www.empresa.bo',
            'metadata': {'domain': 'www.empresa.bo'}
        }
        results = self.evaluador.evaluate(content)
        proh03 = next(r for r in results if r.criteria_id == 'PROH-03')

        assert proh03.status == 'partial'
        assert proh03.score == 5.0
        assert proh03.details['tipo_dominio'] == 'boliviano_no_gubernamental'

    def test_proh03_dominio_extranjero(self):
        """PROH-03: Dominio extranjero debe fallar"""
        content = {
            'url': 'https://www.example.com',
            'metadata': {'domain': 'www.example.com'}
        }
        results = self.evaluador.evaluate(content)
        proh03 = next(r for r in results if r.criteria_id == 'PROH-03')

        assert proh03.status == 'fail'
        assert proh03.score == 0.0
        assert proh03.details['tipo_dominio'] == 'extranjero'

    def test_proh04_sin_widgets_sociales(self):
        """PROH-04: Sin widgets de redes sociales debe pasar"""
        content = {
            'url': 'https://www.ejemplo.gob.bo',
            'external_resources': {
                'iframes': {'external': [], 'count': 0},
                'cdn': {'external': [], 'count': 0}
            }
        }
        results = self.evaluador.evaluate(content)
        proh04 = next(r for r in results if r.criteria_id == 'PROH-04')

        assert proh04.status == 'pass'
        assert proh04.score == 10.0

    def test_proh04_con_youtube_embed(self):
        """PROH-04: YouTube embed debe penalizar"""
        content = {
            'url': 'https://www.ejemplo.gob.bo',
            'external_resources': {
                'iframes': {
                    'external': [
                        {
                            'src': 'https://www.youtube.com/embed/VIDEO_ID',
                            'absolute_src': 'https://www.youtube.com/embed/VIDEO_ID',
                            'domain': 'youtube.com'
                        }
                    ],
                    'count': 1
                },
                'cdn': {'external': [], 'count': 0}
            }
        }
        results = self.evaluador.evaluate(content)
        proh04 = next(r for r in results if r.criteria_id == 'PROH-04')

        assert proh04.status == 'partial'
        assert proh04.score == 5.0
        assert len(proh04.details['widgets_found']) == 1

    def test_proh04_con_multiples_widgets(self):
        """PROH-04: Multiples widgets deben fallar"""
        content = {
            'url': 'https://www.ejemplo.gob.bo',
            'external_resources': {
                'iframes': {
                    'external': [
                        {'absolute_src': 'https://www.youtube.com/embed/VIDEO1', 'domain': 'youtube.com'},
                        {'absolute_src': 'https://www.facebook.com/plugins/page', 'domain': 'facebook.com'},
                        {'absolute_src': 'https://platform.twitter.com/widgets', 'domain': 'twitter.com'}
                    ],
                    'count': 3
                },
                'cdn': {'external': [], 'count': 0}
            }
        }
        results = self.evaluador.evaluate(content)
        proh04 = next(r for r in results if r.criteria_id == 'PROH-04')

        assert proh04.status == 'fail'
        assert proh04.score == 0.0

    def test_evaluar_soberania_funcion(self):
        """Test de la funcion de conveniencia"""
        content = {
            'url': 'https://www.ejemplo.gob.bo',
            'metadata': {'domain': 'www.ejemplo.gob.bo'},
            'external_resources': {
                'trackers': {'found': [], 'count': 0},
                'cdn': {'external': [], 'count': 0},
                'iframes': {'external': [], 'count': 0}
            }
        }
        result = evaluar_soberania(content)

        assert result['dimension'] == 'sovereignty'
        assert result['score'] == 100.0
        assert result['summary']['passed'] == 4
        assert len(result['criteria_results']) == 4


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

        # PROH-03 debe pasar (es .gob.bo)
        proh03 = next(r for r in results if r.criteria_id == 'PROH-03')
        assert proh03.status == 'pass', "aduana.gob.bo debe cumplir PROH-03"


if __name__ == '__main__':
    pytest.main([__file__, '-v', '-s'])
