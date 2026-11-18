import asyncio
from abc import ABC, abstractmethod
from typing import ClassVar

from curl_cffi.requests import AsyncSession
from curl_cffi.requests.exceptions import RequestException
from loguru import logger

from gearsentry.schemas.product import ScrapedProduct


class ScraperError(Exception):
    """Erro base de raspagem."""


class FetchError(ScraperError):
    """Falha de rede/HTTP após esgotar as tentativas."""


class ParseError(ScraperError):
    """O HTML foi obtido, mas não foi possível extrair o produto."""


class BaseScraper(ABC):
    """Contrato comum: cada loja só implementa `parse`.

    O download usa curl_cffi com impersonate de navegador para contornar
    bloqueios anti-bot básicos, com retry e backoff exponencial.
    """

    store: ClassVar[str]
    domains: ClassVar[tuple[str, ...]]

    def __init__(self, timeout: float = 20.0, retries: int = 3) -> None:
        self.timeout = timeout
        self.retries = retries

    async def fetch(self, url: str) -> str:
        last_error: Exception | None = None
        for attempt in range(1, self.retries + 1):
            try:
                async with AsyncSession(impersonate="chrome") as session:
                    response = await session.get(url, timeout=self.timeout)
                    response.raise_for_status()
                    return response.text
            except RequestException as exc:
                last_error = exc
                logger.warning(f"[{self.store}] tentativa {attempt}/{self.retries} falhou: {exc}")
                if attempt < self.retries:
                    await asyncio.sleep(2**attempt)
        raise FetchError(f"Não foi possível obter {url}") from last_error

    @abstractmethod
    def parse(self, html: str, url: str) -> ScrapedProduct:
        """Converte HTML em ScrapedProduct. Deve levantar ParseError se falhar."""

    async def scrape(self, url: str) -> ScrapedProduct:
        return self.parse(await self.fetch(url), url)
