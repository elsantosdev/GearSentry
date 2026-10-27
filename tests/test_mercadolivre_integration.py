import pytest

from src.scrapers.exceptions import BlockedByStore
from src.scrapers.mercadolivre import MercadoLivreScraper

# URL teste
URL = "https://www.mercadolivre.com.br/ssd-samsung-pm9c1a-1tb-m2-2280-nvme-pcie-gen4-x4-gaming-preto/p/MLB66191177"


@pytest.mark.integration
@pytest.mark.anyio
async def test_mercadolivre_scraper_real_product():
    try:
        product = await MercadoLivreScraper().fetch_product(URL)
    except BlockedByStore as exc:
        pytest.skip(f"Mercado Livre bloqueou a requisição: {exc}")

    assert product.title
    assert product.current_price > 0
    assert product.store == "Mercado Livre"
    assert product.url == URL
