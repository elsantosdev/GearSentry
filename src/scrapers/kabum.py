from bs4 import BeautifulSoup

from src.scrapers.base import BaseScraper
from src.scrapers.utils import RawPrice, find_next_data_price, first_text


class KabumScraper(BaseScraper):
    store_name = "Kabum"
    base_url = "https://www.kabum.com.br"
    title_selectors = ("h1.boxTitle", "h1[class*='Title']", "h1")
    price_selectors = (
        "h4[class*='sc-']",
        ".finalPrice",
        ".priceCard",
        "h4[class*='price']",
        "span[class*='price']",
    )
    next_data_price_keys = ("price", "sellingPrice", "valVista", "priceWithDiscount")

    def _find_raw_price(self, soup: BeautifulSoup) -> RawPrice | None:
        text = first_text(soup, self.price_selectors, require_digit=True)
        if text is not None:
            return text
        # Fallback: o CSS das lojas Next.js muda com frequência; o JSON é mais estável.
        return find_next_data_price(soup, self.next_data_price_keys)
