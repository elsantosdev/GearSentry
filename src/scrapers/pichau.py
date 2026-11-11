from bs4 import BeautifulSoup

from src.scrapers.base import BaseScraper
from src.scrapers.utils import RawPrice, find_next_data_price, first_text


class PichauScraper(BaseScraper):
    store_name = "Pichau"
    base_url = "https://www.pichau.com.br"
    title_selectors = ("h1[class*='title']", "h1.font-bold", "h1")
    price_selectors = (
        "div[class*='price'] span",
        ".text-price",
        "div[class*='current-price']",
        "span[class*='price']",
        "div[class*='product-price']",
    )
    next_data_price_keys = (
        "price",
        "sellingPrice",
        "specialPrice",
        "finalPrice",
        "por",
        "preco",
        "bestPrice",
        "priceWithDiscount",
        "valor",
    )

    def _find_raw_price(self, soup: BeautifulSoup) -> RawPrice | None:
        text = first_text(soup, self.price_selectors, require_digit=True)
        if text is not None:
            return text
        return find_next_data_price(soup, self.next_data_price_keys)
