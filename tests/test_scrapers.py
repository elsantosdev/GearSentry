import pytest
from decimal import Decimal
from src.models import ProductBase
from src.scrapers.base import BaseScraper


class DummyScraper(BaseScraper):
    # Scraper falso
    def parse_product(self, html: str, url: str) -> ProductBase:
        return ProductBase(
            title="Teclado teste",
            store="Loja teste",
            url=url,
            current_price=Decimal("100.00")
        )


@pytest.mark.anyio
async def test_base_scraper_success(mocker):
    # Mock da resposta HTTP do httpx
    mock_response = mocker.Mock()
    mock_response.status_code = 200
    mock_response.text = "<html>Mock HTML Content</html>"

    # Mock do cliente assíncrono para retornar o nosso response simulado
    mocker.patch("httpx.AsyncClient.get", return_value=mock_response)

    scraper = DummyScraper()
    product = await scraper.scrape("https://www.exemplo.com.br/produto")

    assert product is not None
    assert product.title == "Teclado teste"
    assert product.current_price == Decimal("100.00")
    assert product.store == "Loja teste"
