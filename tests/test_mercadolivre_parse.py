from decimal import Decimal
import pytest

from src.scrapers.exceptions import ParseError, ProductUnavailable
from src.scrapers.mercadolivre import MercadoLivreScraper

URL = "https://www.mercadolivre.com.br/produto/exemplo"


def make_html(title: str | None = "Smartphone Xiaomi Redmi Note 13", price: str | None = "1299") -> str:
    h1 = f'<h1 class="ui-pdp-title">{title}</h1>' if title else ""
    val = f'<span class="andes-money-amount__fraction">{price}</span>' if price else ""
    return f"<html><body>{h1}{val}</body></html>"


@pytest.fixture
def scraper() -> MercadoLivreScraper:
    return MercadoLivreScraper()


def test_parse_produto_valido(scraper):
    product = scraper.parse(make_html(), URL)

    assert product.title == "Smartphone Xiaomi Redmi Note 13"
    assert product.current_price == Decimal("1299")
    assert product.store == "Mercado Livre"
    assert product.url == URL


def test_parse_sem_titulo(scraper):
    with pytest.raises(ParseError):
        scraper.parse(make_html(title=None), URL)


def test_parse_sem_preco(scraper):
    with pytest.raises(ParseError):
        scraper.parse(make_html(price=None), URL)


def test_parse_preco_zerado(scraper):
    with pytest.raises(ProductUnavailable):
        scraper.parse(make_html(price="0"), URL)
