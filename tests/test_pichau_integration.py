import pytest
from src.scrapers.pichau import PichauScraper

# URL teste
URL = "https://www.pichau.com.br/energetico-pichau-protein-black-cherry-zero-350ml-pch-eng-probc-zero-un"


@pytest.mark.integration
@pytest.mark.anyio
async def test_pichau_scraper_real_product():
    product = await PichauScraper().fetch_product(URL)

    assert product.title
    assert product.current_price > 0
    assert product.store == "Pichau"
    assert product.url == URL
