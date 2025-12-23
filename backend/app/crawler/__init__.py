"""
Módulo de web crawling.

Proporciona funcionalidad para crawlear sitios web gubernamentales
usando Scrapy y Playwright.
"""

from app.crawler.spider import GobBoSpider
from app.crawler.parser import HTMLParser

__all__ = ["GobBoSpider", "HTMLParser"]
