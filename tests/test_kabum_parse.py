from decimal import Decimal
import pytest

from src.scrapers.exceptions import ParseError, ProductUnavailable
from src.scrapers.kabum import KabumScraper

URL = "https://www.kabum.com.br/produto/1/exemplo"


def make_html(title: str | None = "Processador AMD Ryzen 5 5600", price: str | None = "R$ 899,99") -> str:
    h1 = f'<h1 class="boxTitle">{title}</h1>' if title else ""
    val = f'<h4 class="sc-5c3b3135-2">{price}</h4>' if price else ""
    return f"<html><body>{h1}{val}</body></html>"


@pytest.fixture
def scraper() -> KabumScraper:
    return KabumScraper()


def test_parse_produto_valido(scraper):
    product = scraper.parse(make_html(), URL)

    assert product.title == "Processador AMD Ryzen 5 5600"
    assert product.current_price == Decimal("899.99")
    assert product.store == "Kabum"
    assert product.url == URL


def test_parse_sem_titulo(scraper):
    with pytest.raises(ParseError):
        scraper.parse(make_html(title=None), URL)


def test_parse_sem_preco(scraper):
    with pytest.raises(ParseError):
        scraper.parse(make_html(price=None), URL)


def test_parse_preco_zerado(scraper):
    with pytest.raises(ProductUnavailable):
        scraper.parse(make_html(price="R$ 0,00"), URL)
