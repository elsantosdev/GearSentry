from bs4 import BeautifulSoup

from src.scrapers.base import BaseScraper
from src.scrapers.utils import RawPrice, first_text


class TerabyteScraper(BaseScraper):
    store_name = "TerabyteShop"
    base_url = "https://www.terabyteshop.com.br"
    title_selectors = ("h1.tit-prod", "h1", ".tit-prod")
    price_selectors = (
        "#valVista",
        "#valVistaMob",
        ".p-vista",
        "#valPix",
        ".val-prod",
    )

    def _find_raw_price(self, soup: BeautifulSoup) -> RawPrice | None:
        return first_text(soup, self.price_selectors)
