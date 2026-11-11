from decimal import Decimal

import pytest

from src.scrapers.exceptions import ParseError, ProductUnavailable
from src.scrapers.kabum import KabumScraper

URL = "https://www.kabum.com.br/produto/1/exemplo"


def make_html(
    title: str | None = "Processador AMD Ryzen 5 5600",
    price: str | None = "R$ 899,99",
) -> str:
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


# ---------- Regressões ----------


def test_titulo_sem_digito_e_aceito(scraper):
    # O filtro "precisa ter dígito" vale para preço, não para título.
    product = scraper.parse(make_html(title="Mouse Gamer Redragon"), URL)
    assert product.title == "Mouse Gamer Redragon"


def test_preco_decimal_do_next_data_nao_vira_10x(scraper):
    html = (
        '<h1 class="boxTitle">Mouse Gamer 7000 DPI</h1>'
        '<script id="__NEXT_DATA__" type="application/json">'
        '{"props": {"product": {"price": 199.9}}}</script>'
    )
    assert scraper.parse(html, URL).current_price == Decimal("199.9")


def test_next_data_usado_apenas_se_css_falhar(scraper):
    html = (
        f"{make_html(price='R$ 100,00')}"
        '<script id="__NEXT_DATA__">{"price": 999}</script>'
    )
    assert scraper.parse(html, URL).current_price == Decimal("100.00")
