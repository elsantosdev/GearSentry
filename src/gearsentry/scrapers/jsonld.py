import json
from collections.abc import Iterator
from decimal import Decimal, InvalidOperation
from typing import Any

from bs4 import BeautifulSoup

from gearsentry.schemas.product import ScrapedProduct
from gearsentry.scrapers.base import BaseScraper, ParseError


def _walk(node: Any) -> Iterator[dict]:
    if isinstance(node, list):
        for item in node:
            yield from _walk(item)
    elif isinstance(node, dict):
        yield node
        yield from _walk(node.get("@graph", []))


def _is_product(node: dict) -> bool:
    kind = node.get("@type")
    return kind == "Product" or (isinstance(kind, list) and "Product" in kind)


def extract_product_node(html: str) -> dict | None:
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup.find_all("script", type="application/ld+json"):
        try:
            data = json.loads(tag.string or "")
        except json.JSONDecodeError:
            continue
        for node in _walk(data):
            if _is_product(node):
                return node
    return None


def _extract_price(node: dict) -> tuple[Decimal, str]:
    offers = node.get("offers")
    if isinstance(offers, list):
        offers = offers[0] if offers else None
    if not isinstance(offers, dict):
        raise ParseError("JSON-LD sem 'offers'")
    raw = offers.get("price", offers.get("lowPrice"))
    try:
        return Decimal(str(raw)), offers.get("priceCurrency", "BRL")
    except (InvalidOperation, TypeError) as exc:
        raise ParseError(f"Preço inválido no JSON-LD: {raw!r}") from exc


class JsonLdScraper(BaseScraper):
    """Base para lojas que publicam schema.org/Product em JSON-LD (a maioria).

    Lojas que não publicam (ou publicam incompleto) sobrescrevem `parse`
    com seletores CSS próprios.
    """

    def parse(self, html: str, url: str) -> ScrapedProduct:
        node = extract_product_node(html)
        if node is None:
            raise ParseError(f"[{self.store}] JSON-LD de produto não encontrado")
        price, currency = _extract_price(node)
        return ScrapedProduct(
            url=url,
            store=self.store,
            title=node.get("name", ""),
            price=price,
            currency=currency,
        )
