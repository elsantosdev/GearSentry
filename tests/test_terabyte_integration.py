import pytest
from src.scrapers.terabyte import TerabyteScraper

# Cole a URL real de um produto que esteja em estoque no momento
URL = "https://www.terabyteshop.com.br/produto/20782/processador-amd-ryzen-5-5500-36ghz-42ghz-turbo-6-cores-12-threads-cooler-wraith-stealth-am4-100-100000457box"


@pytest.mark.integration
@pytest.mark.anyio
async def test_terabyte_scraper_real_product():
    product = await TerabyteScraper().fetch_product(URL)

    assert product.title
    assert product.current_price > 0
    assert product.store == "TerabyteShop"
    assert product.url == URL
