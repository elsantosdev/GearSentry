import json
from decimal import Decimal

import pytest

from gearsentry.scrapers.base import ParseError
from gearsentry.scrapers.stores import TerabyteScraper


def _page(payload) -> str:
    script = f'<script type="application/ld+json">{json.dumps(payload)}</script>'
    return f"<html><head>{script}</head></html>"


URL = "https://www.terabyteshop.com.br/produto/1/teclado"


def test_parse_simple_product():
    html = _page({
        "@type": "Product",
        "name": "  Teclado Mecânico X  ",
        "offers": {"@type": "Offer", "price": "299.90", "priceCurrency": "BRL"},
    })
    product = TerabyteScraper().parse(html, URL)
    assert product.title == "Teclado Mecânico X"
    assert product.price == Decimal("299.90")
    assert product.store == "terabyte"


def test_parse_product_inside_graph_with_offer_list():
    html = _page({
        "@graph": [
            {"@type": "BreadcrumbList"},
            {"@type": "Product", "name": "Mouse", "offers": [{"price": 129.5}]},
        ]
    })
    assert TerabyteScraper().parse(html, URL).price == Decimal("129.5")


def test_missing_jsonld_raises_parse_error():
    with pytest.raises(ParseError):
        TerabyteScraper().parse("<html></html>", URL)


def test_invalid_price_raises_parse_error():
    html = _page({"@type": "Product", "name": "X", "offers": {"price": "abc"}})
    with pytest.raises(ParseError):
        TerabyteScraper().parse(html, URL)
