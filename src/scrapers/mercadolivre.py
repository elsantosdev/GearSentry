from __future__ import annotations

import json

from bs4 import BeautifulSoup

from src.schemas.product import ProductCreate
from src.scrapers.base import BaseScraper
from src.scrapers.exceptions import BlockedByStore, ParseError
from src.scrapers.utils import (
    RawPrice,
    find_json_value,
    first_text,
    load_json_lenient,
)

# Páginas reais de produtos no ML têm dezenas/centenas de KB. HTML muito pequeno
# somado a uma falha de parse indica bloqueio anti-bot (soft block).
BLOCKED_HTML_MAX_SIZE = 50_000


class MercadoLivreScraper(BaseScraper):
    """Scraper do Mercado Livre com extração de preço em camadas.

    Ordem: seletores visuais/meta tags -> JSON-LD (schema.org) -> JSON em scripts.
    """

    store_name = "Mercado Livre"
    base_url = "https://www.mercadolivre.com.br"
    title_selectors = (
        "h1.ui-pdp-title",
        "h1.item-title__primary",
        "h1[class*='title']",
        "h1",
    )
    price_selectors = (
        ".andes-money-amount__fraction",
        "span[class*='andes-money-amount__fraction']",
        ".ui-pdp-price__second-line .andes-money-amount__fraction",
        ".item-price .price-tag-fraction",
        "meta[property='product:price:amount']",
        "meta[property='og:price:amount']",
    )
    # Só chaves específicas de preço: "value", "amount" e "rate" casam com frete e parcelas.
    script_price_keys = ("price", "sellingPrice", "currentPrice", "bestPrice")

    async def fetch_product(self, url: str) -> ProductCreate:
        html = await self._download(url)
        try:
            return self.parse(html, url)
        except ParseError as exc:
            if len(html) < BLOCKED_HTML_MAX_SIZE:
                raise BlockedByStore(
                    f"Mercado Livre devolveu uma página incompleta "
                    f"({len(html)} bytes), provável bloqueio anti-bot: {url}"
                ) from exc
            raise

    def _find_raw_price(self, soup: BeautifulSoup) -> RawPrice | None:
        strategies = (
            self._price_from_selectors,
            self._price_from_json_ld,
            self._price_from_scripts,
        )
        for strategy in strategies:
            raw_price = strategy(soup)
            if raw_price is not None:
                return raw_price
        return None

    def _price_from_selectors(self, soup: BeautifulSoup) -> RawPrice | None:
        return first_text(soup, self.price_selectors, require_digit=True)

    @staticmethod
    def _price_from_json_ld(soup: BeautifulSoup) -> RawPrice | None:
        for script in soup.find_all("script", type="application/ld+json"):
            if not script.string:
                continue
            try:
                data = json.loads(script.string)
            except ValueError:
                continue

            items = data if isinstance(data, list) else [data]
            for item in items:
                if not isinstance(item, dict) or item.get("@type") != "Product":
                    continue
                offers = item.get("offers") or []
                for offer in offers if isinstance(offers, list) else [offers]:
                    if not isinstance(offer, dict):
                        continue
                    price = offer.get("price")
                    if price is None:
                        price = offer.get("lowPrice")
                    if price is not None:
                        return price  # type: ignore[no-any-return]
        return None

    def _price_from_scripts(self, soup: BeautifulSoup) -> RawPrice | None:
        for script in soup.find_all("script"):
            if not script.string:
                continue
            raw_price = find_json_value(load_json_lenient(script.string), self.script_price_keys)
            if raw_price is not None:
                return raw_price
        return None
