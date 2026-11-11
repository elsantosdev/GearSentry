import json
from decimal import Decimal

import pytest

from src.scrapers.exceptions import BlockedByStore, ParseError, ProductUnavailable
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


# ---------- Fallbacks e regressões ----------

def _html_sem_css(script: str, title: str = "Smartphone Xiaomi Redmi Note 13") -> str:
    return f"<html><body><h1>{title}</h1>{script}</body></html>"


def test_preco_via_json_ld(scraper):
    ld = {"@type": "Product", "offers": {"price": "1299.9"}}
    html = _html_sem_css(f'<script type="application/ld+json">{json.dumps(ld)}</script>')
    assert scraper.parse(html, URL).current_price == Decimal("1299.9")


def test_preco_via_json_ld_com_lista_de_ofertas(scraper):
    ld = [{"@type": "Product", "offers": [{"lowPrice": 899}]}]
    html = _html_sem_css(f'<script type="application/ld+json">{json.dumps(ld)}</script>')
    assert scraper.parse(html, URL).current_price == Decimal("899")


def test_preco_via_meta_tag(scraper):
    html = _html_sem_css('<meta property="product:price:amount" content="249.90">')
    assert scraper.parse(html, URL).current_price == Decimal("249.90")


def test_preco_via_script_ignora_chaves_genericas(scraper):
    # Regressão: "value" (frete) vinha antes do preço e era devolvido como preço.
    data = {"shipping": {"value": 12}, "price": 199.9}
    html = _html_sem_css(f"<script>window.__PRELOADED__ = {json.dumps(data)};</script>")
    assert scraper.parse(html, URL).current_price == Decimal("199.9")


def test_script_so_com_chave_generica_nao_gera_preco(scraper):
    html = _html_sem_css('<script>{"shipping": {"value": 12}, "rate": 4.5}</script>')
    with pytest.raises(ParseError):
        scraper.parse(html, URL)


@pytest.mark.anyio
async def test_html_pequeno_sem_preco_vira_bloqueio(scraper, monkeypatch):
    monkeypatch.setattr(scraper, "_download", _async_return("<html><h1>Produto</h1></html>"))
    with pytest.raises(BlockedByStore):
        await scraper.fetch_product(URL)


@pytest.mark.anyio
async def test_html_grande_sem_preco_continua_parse_error(scraper, monkeypatch):
    html = "<html><h1>Produto</h1>" + "<!-- x -->" * 10_000 + "</html>"
    monkeypatch.setattr(scraper, "_download", _async_return(html))
    with pytest.raises(ParseError):
        await scraper.fetch_product(URL)


def _async_return(value):
    async def _inner(*_args, **_kwargs):
        return value

    return _inner
