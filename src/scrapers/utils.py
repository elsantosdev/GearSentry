"""Funções puras compartilhadas pelos scrapers (sem rede e sem estado)."""

from __future__ import annotations

import json
import re
from collections.abc import Iterable
from decimal import Decimal, InvalidOperation
from typing import Any

from bs4 import BeautifulSoup, Tag

from src.scrapers.exceptions import ParseError

RawPrice = str | int | float

_NUMBER_PATTERN = re.compile(r"\d[\d.,]*")
_THOUSANDS_ONLY = re.compile(r"\d{1,3}(\.\d{3})+")


# ---------- Preço ----------


def parse_price(raw: RawPrice) -> Decimal:
    """Converte um preço bruto em ``Decimal``.

    Aceita números vindos de JSON (``199.9``) e textos como ``"R$ 1.999,99"``,
    ``"199.9"`` ou ``"1,299.00"``. Em texto com um único separador, a vírgula é
    tratada como decimal (padrão brasileiro) e um ponto seguido de exatamente
    três dígitos como separador de milhar (``"1.999"`` -> 1999).
    """
    if isinstance(raw, bool):
        raise ParseError(f"Formato de preço inválido: {raw!r}")

    if isinstance(raw, (int, float)):
        value = Decimal(str(raw))
    else:
        match = _NUMBER_PATTERN.search(raw)
        if match is None:
            raise ParseError(f"Formato de preço inválido: {raw!r}")
        number = match.group(0).rstrip(".,")
        try:
            value = Decimal(_normalize(number))
        except InvalidOperation as exc:
            raise ParseError(f"Não foi possível converter o preço: {raw!r}") from exc

    if not value.is_finite():
        raise ParseError(f"Preço não finito: {raw!r}")
    return value


def _normalize(number: str) -> str:
    has_comma = "," in number
    has_dot = "." in number

    if has_comma and has_dot:
        # O último separador é o decimal: "1.999,99" (BR) ou "1,999.99" (US).
        if number.rfind(",") > number.rfind("."):
            return number.replace(".", "").replace(",", ".")
        return number.replace(",", "")
    if has_comma:
        return number.replace(",", ".")
    if _THOUSANDS_ONLY.fullmatch(number):
        return number.replace(".", "")
    return number


# ---------- HTML ----------


def attr_text(tag: Tag, name: str) -> str | None:
    """Lê um atributo como texto limpo (atributos como ``class`` vêm em lista)."""
    value = tag.get(name)
    if value is None:
        return None
    if not isinstance(value, str):
        value = " ".join(value)
    return value.strip() or None


def first_text(
    soup: BeautifulSoup,
    selectors: Iterable[str],
    *,
    require_digit: bool = False,
) -> str | None:
    """Texto do primeiro seletor que casar com um conteúdo não vazio.

    Tags ``<meta>`` são lidas pelo atributo ``content``. Com ``require_digit``,
    textos sem nenhum dígito são ignorados (útil para preços, nunca para títulos).
    """
    for selector in selectors:
        element = soup.select_one(selector)
        if element is None:
            continue
        if element.name == "meta":
            text = attr_text(element, "content")
        else:
            text = element.get_text(strip=True)
        if not text:
            continue
        if require_digit and not any(char.isdigit() for char in text):
            continue
        return text
    return None


# ---------- JSON embutido na página ----------


def load_json_lenient(content: str) -> Any | None:
    """Carrega JSON puro ou, se falhar, o trecho entre a primeira ``{`` e a última ``}``."""
    content = content.strip()
    start, end = content.find("{"), content.rfind("}")
    candidates = [content]
    if start != -1 and end > start:
        candidates.append(content[start : end + 1])

    for candidate in candidates:
        try:
            return json.loads(candidate)
        except ValueError:
            continue
    return None


def find_json_value(data: Any, keys: Iterable[str]) -> RawPrice | None:
    """Busca em profundidade o primeiro valor de preço cujas chaves estejam em ``keys``.

    Chaves do mesmo nível têm prioridade sobre as aninhadas. Booleanos e valores
    sem dígito são ignorados. Use apenas chaves específicas de preço: chaves
    genéricas como ``value`` ou ``amount`` casam com frete, parcelas e afins.
    """
    wanted = {key.lower() for key in keys}
    return _walk(data, wanted)


def _walk(node: Any, wanted: set[str]) -> RawPrice | None:
    if isinstance(node, dict):
        for key, value in node.items():
            if str(key).lower() in wanted and _is_price_like(value):
                return value  # type: ignore[no-any-return]
        children: Iterable[Any] = node.values()
    elif isinstance(node, list):
        children = node
    else:
        return None

    for child in children:
        found = _walk(child, wanted)
        if found is not None:
            return found
    return None


def _is_price_like(value: Any) -> bool:
    if isinstance(value, bool):
        return False
    if isinstance(value, (int, float)):
        return True
    return isinstance(value, str) and any(char.isdigit() for char in value)


def find_next_data_price(soup: BeautifulSoup, keys: Iterable[str]) -> RawPrice | None:
    """Preço dentro do ``<script id="__NEXT_DATA__">`` de páginas Next.js."""
    script = soup.find("script", id="__NEXT_DATA__")
    if script is None or not script.string:
        return None
    return find_json_value(load_json_lenient(script.string), keys)
