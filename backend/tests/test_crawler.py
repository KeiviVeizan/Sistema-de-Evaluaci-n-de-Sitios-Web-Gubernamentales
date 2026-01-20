"""
Tests unitarios para el crawler.
"""

import pytest
from app.crawler.html_crawler import GobBoCrawler


class TestCrawlerValidation:
    """Tests para validación de input del crawler"""

    def test_url_none_raises_valueerror(self):
        """Verifica que URL None lanza ValueError"""
        crawler = GobBoCrawler()
        with pytest.raises(ValueError, match="URL debe ser un string no vacío"):
            crawler.crawl(None)

    def test_url_empty_raises_valueerror(self):
        """Verifica que URL vacía lanza ValueError"""
        crawler = GobBoCrawler()
        with pytest.raises(ValueError, match="URL debe ser un string no vacío"):
            crawler.crawl("")

    def test_url_sin_protocolo_raises_valueerror(self):
        """Verifica que URL sin http/https lanza ValueError"""
        crawler = GobBoCrawler()
        with pytest.raises(ValueError, match="debe comenzar con http"):
            crawler.crawl("www.migracion.gob.bo")

    def test_url_no_gobbo_raises_valueerror(self):
        """Verifica que URL no .gob.bo lanza ValueError"""
        crawler = GobBoCrawler()
        with pytest.raises(ValueError, match="no es un dominio .gob.bo válido"):
            crawler.crawl("https://www.google.com")

    def test_url_javascript_raises_valueerror(self):
        """Verifica que URL con javascript: lanza ValueError"""
        crawler = GobBoCrawler()
        with pytest.raises(ValueError, match="debe comenzar con http"):
            crawler.crawl("javascript:alert(1)")

    def test_is_gob_bo_domain_valid(self):
        """Verifica detección correcta de dominios .gob.bo válidos"""
        crawler = GobBoCrawler()
        assert crawler._is_gob_bo_domain("https://www.migracion.gob.bo")
        assert crawler._is_gob_bo_domain("https://adsib.gob.bo")
        assert crawler._is_gob_bo_domain("http://www.comunicacion.gob.bo")

    def test_is_gob_bo_domain_invalid(self):
        """Verifica detección correcta de dominios NO .gob.bo"""
        crawler = GobBoCrawler()
        assert not crawler._is_gob_bo_domain("https://www.google.com")
        assert not crawler._is_gob_bo_domain("https://www.gob.bo.fake.com")
        assert not crawler._is_gob_bo_domain("https://example.com")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
