from decimal import Decimal
import pytest

from src.scrapers.exceptions import ParseError, ProductUnavailable
from src.scrapers.terabyte import TerabyteScraper

URL = "https://www.terabyteshop.com.br/produto/20782/processador-amd-ryzen-5-5500-36ghz-42ghz-turbo-6-cores-12-threads-cooler-wraith-stealth-am4-100-100000457box"


def make_html(title: str | None = "Placa de Vídeo RTX 4060", price: str | None = "R$ 1.999,99") -> str:
    h1 = f'<h1 class="tit-prod">{title}</h1>' if title else ""
    val = f'<div id="valVista">{price}</div>' if price else ""
    return f"<html><body>{h1}{val}</body></html>"


@pytest.fixture
def scraper() -> TerabyteScraper:
    return TerabyteScraper()


def test_parse_produto_valido(scraper):
    product = scraper.parse(make_html(), URL)

    assert product.title == "Placa de Vídeo RTX 4060"
    assert product.current_price == Decimal("1999.99")
    assert product.store == "TerabyteShop"
    assert product.url == URL


def test_parse_usa_seletor_alternativo_de_preco(scraper):
    html = '<h1>Produto</h1><span class="p-vista">R$ 50,00</span>'
    assert scraper.parse(html, URL).current_price == Decimal("50.00")


def test_parse_sem_titulo(scraper):
    with pytest.raises(ParseError):
        scraper.parse(make_html(title=None), URL)


def test_parse_sem_preco(scraper):
    with pytest.raises(ParseError):
        scraper.parse(make_html(price=None), URL)


def test_parse_preco_sem_numero(scraper):
    with pytest.raises(ParseError):
        scraper.parse(make_html(price="Indisponível"), URL)


def test_parse_preco_zerado(scraper):
    with pytest.raises(ProductUnavailable):
        scraper.parse(make_html(price="R$ 0,00"), URL)


@pytest.mark.parametrize(
    "raw, esperado",
    [
        ("R$ 1.999,99", Decimal("1999.99")),
        ("R$ 999,90", Decimal("999.90")),
        ("À vista R$ 12.345,00 no pix", Decimal("12345.00")),
        ("R$ 0,00", Decimal("0.00")),
    ],
)
def test_parse_price(raw, esperado):
    assert TerabyteScraper._parse_price(raw) == esperado
