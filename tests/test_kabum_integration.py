import pytest
from src.scrapers.kabum import KabumScraper

# URL de um produto estável na Kabum para teste de integração
URL = "https://www.kabum.com.br/produto/102803/patinete-eletrico-xiaomi-m365-ate-25km-h-rodas-8-5-suporta-100kg-branco-px251bra"


@pytest.mark.integration
@pytest.mark.anyio
async def test_kabum_scraper_real_product():
    product = await KabumScraper().fetch_product(URL)

    assert product.title
    assert product.current_price > 0
    assert product.store == "Kabum"
    assert product.url == URL
