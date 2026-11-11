"""Executa um scraper contra uma URL real, para teste manual.

Uso:
    python scripts/try_scraper.py kabum <url-do-produto>
"""

import asyncio
import sys

from src.scrapers.exceptions import ScraperError
from src.scrapers.kabum import KabumScraper
from src.scrapers.mercadolivre import MercadoLivreScraper
from src.scrapers.pichau import PichauScraper
from src.scrapers.terabyte import TerabyteScraper

SCRAPERS = {
    "kabum": KabumScraper,
    "pichau": PichauScraper,
    "terabyte": TerabyteScraper,
    "mercadolivre": MercadoLivreScraper,
}


async def main(store: str, url: str) -> int:
    scraper = SCRAPERS[store]()
    try:
        product = await scraper.fetch_product(url)
    except ScraperError as exc:
        print(f"Falha ({type(exc).__name__}): {exc}")
        return 1

    print(f"Título : {product.title}")
    print(f"Loja   : {product.store}")
    print(f"Preço  : R$ {product.current_price}")
    return 0


if __name__ == "__main__":
    if len(sys.argv) != 3 or sys.argv[1] not in SCRAPERS:
        print(f"Uso: python scripts/try_scraper.py <{'|'.join(SCRAPERS)}> <url>")
        sys.exit(2)
    sys.exit(asyncio.run(main(sys.argv[1], sys.argv[2])))
