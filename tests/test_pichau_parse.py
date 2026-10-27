from decimal import Decimal
import pytest

from src.scrapers.exceptions import ParseError, ProductUnavailable
from src.scrapers.pichau import PichauScraper

URL = "https://www.pichau.com.br/produto/exemplo"


def make_html(title: str | None = "Placa de Vídeo RTX 4060", price: str | None = "R$ 1.899,99") -> str:
    h1 = f'<h1 class="font-bold">{title}</h1>' if title else ""
    val = f'<span class="text-price">{price}</span>' if price else ""
    return f"<html><body>{h1}{val}</body></html>"


@pytest.fixture
def scraper() -> PichauScraper:
    return PichauScraper()


def test_parse_produto_valido(scraper):
    product = scraper.parse(make_html(), URL)

    assert product.title == "Placa de Vídeo RTX 4060"
    assert product.current_price == Decimal("1899.99")
    assert product.store == "Pichau"
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
