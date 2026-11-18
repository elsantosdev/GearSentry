from urllib.parse import urlparse

from gearsentry.scrapers.base import BaseScraper, ScraperError
from gearsentry.scrapers.stores import MercadoLivreScraper, TerabyteScraper

SCRAPERS: tuple[type[BaseScraper], ...] = (TerabyteScraper, MercadoLivreScraper)


def get_scraper(url: str) -> BaseScraper:
    host = (urlparse(url).hostname or "").lower()
    for cls in SCRAPERS:
        if any(host == d or host.endswith(f".{d}") for d in cls.domains):
            return cls()
    raise ScraperError(f"Nenhum scraper registrado para o domínio '{host}'")
