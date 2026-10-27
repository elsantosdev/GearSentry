import json
import re
from decimal import Decimal, InvalidOperation

from bs4 import BeautifulSoup
from curl_cffi.requests import AsyncSession
from curl_cffi.requests.exceptions import RequestException
from loguru import logger

from src.schemas.product import ProductCreate
from src.scrapers.exceptions import (
    BlockedByStore,
    ParseError,
    ProductNotFound,
    ProductUnavailable,
    StoreRequestError,
)

STORE_NAME = "Pichau"
TITLE_SELECTORS = ("h1[class*='title']", "h1.font-bold", "h1")
PRICE_SELECTORS = (
    "div[class*='price'] span",
    ".text-price",
    "div[class*='current-price']",
    "span[class*='price']",
    "div[class*='product-price']",
)
PRICE_PATTERN = re.compile(r"\d[\d.,]*")


class PichauScraper:
    def __init__(self, timeout: float = 15.0):
        self.base_url = "https://www.pichau.com.br"
        self.timeout = timeout

    # ---------- API pública ----------

    async def fetch_product(self, url: str) -> ProductCreate:
        html = await self._download(url)
        return self.parse(html, url)

    def parse(self, html: str, url: str) -> ProductCreate:
        """Extrai os dados do HTML sem dependência de rede."""
        soup = BeautifulSoup(html, "html.parser")
        title = self._extract_title(soup)
        price = self._extract_price(soup, title)
        return ProductCreate(
            title=title,
            current_price=price,
            url=url,
            store=STORE_NAME,
        )

    # ---------- Rede ----------

    async def _download(self, url: str) -> str:
        try:
            async with AsyncSession(impersonate="chrome") as session:
                response = await session.get(url, timeout=self.timeout)
        except RequestException as exc:
            raise StoreRequestError(f"Falha ao acessar {url}: {exc}") from exc

        status = response.status_code
        if status == 404:
            raise ProductNotFound(url)
        if status in (403, 429):
            raise BlockedByStore(f"HTTP {status} em {url}")
        if status != 200:
            raise StoreRequestError(f"HTTP {status} em {url}")

        return response.text

    # ---------- Parsing ----------

    def _extract_title(self, soup: BeautifulSoup) -> str:
        for selector in TITLE_SELECTORS:
            element = soup.select_one(selector)
            if element:
                text = element.get_text(strip=True)
                if text:
                    return text

        meta_title = soup.find("meta", property="og:title")
        if meta_title and meta_title.get("content"):
            return meta_title["content"].strip()

        raise ParseError("Título não encontrado na Pichau.")

    def _extract_price(self, soup: BeautifulSoup, title: str) -> Decimal:
        raw_price = None
        for selector in PRICE_SELECTORS:
            element = soup.select_one(selector)
            if element:
                text = element.get_text(strip=True)
                if text and any(char.isdigit() for char in text):
                    raw_price = text
                    break

        if not raw_price:
            raw_price = self._extract_price_from_next_data(soup)

        if not raw_price:
            raise ParseError(
                f"Preço não encontrado. Título extraído: '{title}'")

        price = self._parse_price(raw_price)
        if price <= 0:
            logger.warning(
                f"Produto indisponível ou sem preço válido: {title}")
            raise ProductUnavailable(title)
        return price

    def _extract_price_from_next_data(self, soup: BeautifulSoup) -> str | None:
        script = soup.find("script", id="__NEXT_DATA__")
        if not script or not script.string:
            return None
        try:
            data = json.loads(script.string)
            target_keys = (
                "price", "sellingPrice", "specialPrice", "finalPrice",
                "por", "preco", "bestPrice", "priceWithDiscount", "valor"
            )
            price_val = self._find_key_in_dict(data, target_keys)
            if price_val is not None:
                return str(price_val)
        except Exception:
            pass
        return None

    def _find_key_in_dict(self, obj, target_keys):
        if isinstance(obj, dict):
            for k, v in obj.items():
                if k.lower() in [tk.lower() for tk in target_keys] and v is not None:
                    if isinstance(v, (int, float, str)) and str(v).strip() != "":
                        return v
                res = self._find_key_in_dict(v, target_keys)
                if res is not None:
                    return res
        elif isinstance(obj, list):
            for item in obj:
                res = self._find_key_in_dict(item, target_keys)
                if res is not None:
                    return res
        return None

    @staticmethod
    def _parse_price(raw_price: str | int | float) -> Decimal:
        if isinstance(raw_price, (int, float)):
            return Decimal(str(raw_price))

        match = PRICE_PATTERN.search(str(raw_price))
        if not match:
            raise ParseError(f"Formato de preço inválido: {raw_price!r}")

        normalized = match.group(0).replace(".", "").replace(",", ".")
        try:
            return Decimal(normalized)
        except InvalidOperation as exc:
            raise ParseError(
                f"Não foi possível converter o preço: {raw_price!r}"
            ) from exc
