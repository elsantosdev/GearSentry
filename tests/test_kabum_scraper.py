import pytest
from decimal import Decimal
from src.scrapers.kabum import KabumScraper


@pytest.mark.anyio
async def test_kabum_scraper_parses_correctly(mocker):
    """Garante que o KabumScraper consegue extrair corretamente título e preço de um HTML simulado."""

    # HTML falso simulando a página de um produto na Kabum
    mock_html = """
    <html>
        <head><meta property="og:title" content="Teclado Mecânico Gamer Redragon Kumara" /></head>
        <body>
            <h1 class="sc-52416c0c-0">Teclado Mecânico Gamer Redragon Kumara</h1>
            <h4 class="sc-52416c0c-2">R$ 199,90</h4>
        </body>
    </html>
    """

    mock_response = mocker.Mock()
    mock_response.status_code = 200
    mock_response.text = mock_html

    mocker.patch("httpx.AsyncClient.get", return_value=mock_response)

    scraper = KabumScraper()
    product = await scraper.scrape("https://www.kabum.com.br/produto/12345/teclado-teste")

    assert product is not None
    assert product.title == "Teclado Mecânico Gamer Redragon Kumara"
    assert product.store == "Kabum"
    assert product.current_price == Decimal("199.90")
    assert product.in_stock is True
