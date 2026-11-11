from __future__ import annotations

from abc import ABC, abstractmethod
from decimal import Decimal
from typing import ClassVar

from bs4 import BeautifulSoup, Tag
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
from src.scrapers.utils import RawPrice, attr_text, first_text, parse_price


class BaseScraper(ABC):
    """Base de todos os scrapers de loja.

    Concentra o que é comum (download com impersonação de navegador, tradução de
    status HTTP em exceções, título e validação do preço). Cada loja informa seus
    seletores e implementa apenas ``_find_raw_price``.
    """

    store_name: ClassVar[str]
    base_url: ClassVar[str]
    title_selectors: ClassVar[tuple[str, ...]] = ("h1",)
    impersonate: ClassVar[str] = "chrome"

    def __init__(self, timeout: float = 15.0) -> None:
        self.timeout = timeout

    # ---------- API pública ----------

    async def fetch_product(self, url: str) -> ProductCreate:
        html = await self._download(url)
        return self.parse(html, url)

    def parse(self, html: str, url: str) -> ProductCreate:
        """Extrai os dados do HTML, sem dependência de rede."""
        soup = BeautifulSoup(html, "html.parser")
        title = self._extract_title(soup)
        price = self._extract_price(soup, title)
        return ProductCreate(
            title=title,
            current_price=price,
            url=url,
            store=self.store_name,
        )

    # ---------- Rede ----------

    async def _download(self, url: str) -> str:
        try:
            async with AsyncSession(impersonate=self.impersonate) as session:  # type: ignore[arg-type]
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

    @abstractmethod
    def _find_raw_price(self, soup: BeautifulSoup) -> RawPrice | None:
        """Devolve o preço bruto da página (texto ou número), ou ``None`` se não achar."""

    def _extract_title(self, soup: BeautifulSoup) -> str:
        title = first_text(soup, self.title_selectors)
        if title:
            return title

        meta_title = soup.find("meta", property="og:title")
        if isinstance(meta_title, Tag):
            title = attr_text(meta_title, "content")
            if title:
                return title

        raise ParseError(f"Título não encontrado em {self.store_name}.")

    def _extract_price(self, soup: BeautifulSoup, title: str) -> Decimal:
        raw_price = self._find_raw_price(soup)
        if raw_price is None:
            raise ParseError(f"Preço não encontrado. Título extraído: '{title}'")

        price = parse_price(raw_price)
        if price <= 0:
            logger.warning(f"Produto indisponível ou sem preço válido: {title}")
            raise ProductUnavailable(title)
        return price
