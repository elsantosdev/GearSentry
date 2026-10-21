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

STORE_NAME = "TerabyteShop"
TITLE_SELECTORS = ("h1.tit-prod", "h1", ".tit-prod")
PRICE_SELECTORS = ("#valVista", "#valVistaMob",
                   ".p-vista", "#valPix", ".val-prod")
PRICE_PATTERN = re.compile(r"\d[\d.,]*")


class TerabyteScraper:
    def __init__(self, timeout: float = 15.0):
        self.base_url = "https://www.terabyteshop.com.br"
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

    @staticmethod
    def _select_text(soup: BeautifulSoup, selectors: tuple[str, ...]) -> str | None:
        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                return element.get_text(strip=True)
        return None

    def _extract_title(self, soup: BeautifulSoup) -> str:
        title = self._select_text(soup, TITLE_SELECTORS)
        if not title:
            raise ParseError("Título não encontrado na Terabyte.")
        return title

    def _extract_price(self, soup: BeautifulSoup, title: str) -> Decimal:
        raw_price = self._select_text(soup, PRICE_SELECTORS)
        if not raw_price:
            raise ParseError(
                f"Preço não encontrado. Título extraído: '{title}'")

        price = self._parse_price(raw_price)
        if price <= 0:
            logger.warning(
                f"Produto indisponível ou sem preço válido: {title}")
            raise ProductUnavailable(title)
        return price

    @staticmethod
    def _parse_price(raw_price: str) -> Decimal:
        """Converte 'R$ 1.999,99' em Decimal('1999.99')."""
        match = PRICE_PATTERN.search(raw_price)
        if not match:
            raise ParseError(f"Formato de preço inválido: {raw_price!r}")

        normalized = match.group(0).replace(".", "").replace(",", ".")
        try:
            return Decimal(normalized)
        except InvalidOperation as exc:
            raise ParseError(
                f"Não foi possível converter o preço: {raw_price!r}"
            ) from exc
