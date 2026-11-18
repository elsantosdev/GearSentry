import pytest

from gearsentry.scrapers.base import ScraperError
from gearsentry.scrapers.registry import get_scraper
from gearsentry.scrapers.stores import MercadoLivreScraper, TerabyteScraper


def test_resolves_by_domain_and_subdomain():
    assert isinstance(get_scraper("https://www.terabyteshop.com.br/x"), TerabyteScraper)
    assert isinstance(get_scraper("https://produto.mercadolivre.com.br/MLB-1"), MercadoLivreScraper)


def test_unknown_domain():
    with pytest.raises(ScraperError):
        get_scraper("https://exemplo.com/x")


def test_does_not_match_lookalike_domain():
    with pytest.raises(ScraperError):
        get_scraper("https://faketerabyteshop.com.br/x")
