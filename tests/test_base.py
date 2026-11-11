from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock

import pytest
from bs4 import BeautifulSoup
from curl_cffi.requests.exceptions import RequestException

from src.scrapers import base
from src.scrapers.base import BaseScraper
from src.scrapers.exceptions import (
    BlockedByStore,
    ParseError,
    ProductNotFound,
    ProductUnavailable,
    StoreRequestError,
)
from src.scrapers.utils import RawPrice, first_text

URL = "https://loja.exemplo.com/produto/1"


class DummyScraper(BaseScraper):
    store_name = "Loja Teste"
    base_url = "https://loja.exemplo.com"

    def _find_raw_price(self, soup: BeautifulSoup) -> RawPrice | None:
        return first_text(soup, (".preco",))


def fake_session(status: int = 200, text: str = "<html></html>", error: Exception | None = None):
    """Substitui AsyncSession por um double que responde com o status informado."""
    response = MagicMock(status_code=status, text=text)
    session = MagicMock()
    session.get = AsyncMock(side_effect=error) if error else AsyncMock(return_value=response)
    session.__aenter__ = AsyncMock(return_value=session)
    session.__aexit__ = AsyncMock(return_value=False)
    return MagicMock(return_value=session)


def test_base_scraper_e_abstrata():
    with pytest.raises(TypeError):
        BaseScraper()  # type: ignore[abstract]


def test_parse_monta_produto():
    html = '<h1>Teclado Mecânico</h1><span class="preco">R$ 249,90</span>'
    product = DummyScraper().parse(html, URL)

    assert product.title == "Teclado Mecânico"
    assert product.current_price == Decimal("249.90")
    assert product.store == "Loja Teste"
    assert product.url == URL


def test_titulo_cai_para_og_title():
    html = '<meta property="og:title" content=" Mouse Gamer "><span class="preco">R$ 99,00</span>'
    assert DummyScraper().parse(html, URL).title == "Mouse Gamer"


def test_sem_titulo():
    with pytest.raises(ParseError):
        DummyScraper().parse('<span class="preco">R$ 99,00</span>', URL)


def test_sem_preco():
    with pytest.raises(ParseError):
        DummyScraper().parse("<h1>Teclado</h1>", URL)


def test_preco_zerado_indisponivel():
    with pytest.raises(ProductUnavailable):
        DummyScraper().parse('<h1>Teclado</h1><span class="preco">R$ 0,00</span>', URL)


@pytest.mark.anyio
async def test_download_sucesso(monkeypatch):
    monkeypatch.setattr(base, "AsyncSession", fake_session(200, "<html>ok</html>"))
    assert await DummyScraper()._download(URL) == "<html>ok</html>"


@pytest.mark.anyio
@pytest.mark.parametrize(
    "status, excecao",
    [
        (404, ProductNotFound),
        (403, BlockedByStore),
        (429, BlockedByStore),
        (500, StoreRequestError),
        (301, StoreRequestError),
    ],
)
async def test_download_traduz_status_em_excecao(monkeypatch, status, excecao):
    monkeypatch.setattr(base, "AsyncSession", fake_session(status))
    with pytest.raises(excecao):
        await DummyScraper()._download(URL)


@pytest.mark.anyio
async def test_download_falha_de_rede(monkeypatch):
    monkeypatch.setattr(base, "AsyncSession", fake_session(error=RequestException("timeout")))
    with pytest.raises(StoreRequestError):
        await DummyScraper()._download(URL)


@pytest.mark.anyio
async def test_fetch_product_integra_download_e_parse(monkeypatch):
    html = '<h1>Headset</h1><span class="preco">R$ 300,00</span>'
    monkeypatch.setattr(base, "AsyncSession", fake_session(200, html))

    product = await DummyScraper().fetch_product(URL)

    assert product.title == "Headset"
    assert product.current_price == Decimal("300.00")
