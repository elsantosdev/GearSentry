import httpx
from abc import ABC, abstractmethod
from typing import Optional
from loguru import logger
from src.models import ProductBase


class BaseScraper(ABC):
    """
    Classe Abstrata Base (Interface) para todos os scrapers de e-commerce do GearSentry.
    Assegura que qualquer scraper específico implemente os métodos essenciais de extração.
    """

    def __init__(self, timeout: float = 10.0):
        self.timeout = timeout
        self.headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
            "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
        }

    async def fetch_html(self, url: str) -> Optional[str]:
        """
        Faz uma chamada HTTP assíncrona para capturar o conteúdo HTML puro da página do item.
        Lida com falhas de rede frequentes de maneira robusta.
        """
        logger.info(f"Carregar HTML do URL: {url}")
        try:
            async with httpx.AsyncClient(headers=self.headers, follow_redirects=True, timeout=self.timeout) as client:
                response = await client.get(url)

                # Se o site retornar erro (por exemplo: 404 Not Found, 503 Service Unavailable)
                if response.status_code != 200:
                    logger.error(
                        f"Erro HTTP {response.status_code} ao aceder a {url}")
                    return None

                return response.text
        except httpx.RequestError as e:
            logger.error(f"Erro de conexão ao acessar {url}: {e}")
            return None

    @abstractmethod
    def parse_product(self, html: str, url: str) -> ProductBase:
        """
        Método abstrato obrigatório. Cada scraper de loja específica deve implementar a lógica de 
        BeautifulSoup para extrair os dados e retornar um ProductBase validado.
        """
        pass

    async def scrape(self, url: str) -> Optional[ProductBase]:
        # (Template Method): Orquestra o fluxo completo de busca e parsing.
        html = await self.fetch_html(url)
        if not html:
            return None

        try:
            product = self.parse_product(html, url)
            logger.success(
                f"Produto localizado com sucesso: {product.title} [{product.current_price}]")
            return product
        except Exception as e:
            logger.exception(
                f"Erro ao processar o parsing do HTML para a URL {url}: {e}")
            return None
