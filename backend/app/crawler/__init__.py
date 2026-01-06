"""
Módulo de web crawling.

Proporciona funcionalidad para crawlear sitios web gubernamentales
usando diferentes estrategias: Scrapy, Playwright y requests + BeautifulSoup.
"""

# Importación lazy para evitar errores si faltan dependencias opcionales
__all__ = ["GobBoSpider", "HTMLParser", "GobBoCrawler"]


def __getattr__(name):
    """Lazy import para evitar errores de dependencias."""
    if name == "GobBoSpider":
        from app.crawler.spider import GobBoSpider
        return GobBoSpider
    elif name == "HTMLParser":
        from app.crawler.parser import HTMLParser
        return HTMLParser
    elif name == "GobBoCrawler":
        from app.crawler.html_crawler import GobBoCrawler
        return GobBoCrawler
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
