from bs4 import BeautifulSoup
from decimal import Decimal
from loguru import logger
from src.models import ProductBase
from src.scrapers.base import BaseScraper


class KabumScraper(BaseScraper):
    store_name = "Kabum"

    def _parse_price(self, price_str: str) -> Decimal:
        """
        Converte uma string de preço para decimal
        R$ 1.999,99 -> 1999.99
        """
        try:
            clean_str = (
                price_str.replace("R$", "")
                .replace(".", "")
                .replace(",", "")
                .strip()
            )
            return Decimal(clean_str)
        except Exception as e:
            logger.error(
                f"Erro ao converter string de preço '{price_str}': {e}")
            raise ValueError(f"Preço inválido: {price_str} ")

    def parse_product(self, html: str, url: str) -> ProductBase:
        """
        Analisa o HTML bruto da página do produto da Kabum utilizando BeautifulSoup e retorna um modelo ProductBase validado.
        """
        soup = BeautifulSoup(html, "html.parser")
        # 1. Extração do Título
        # (Nota: Os seletores da Kabum podem variar, usamos seletores padrão de título de produto)
        title_element = soup.find(
            "h1", {"class": "sc-52416c0c-0"}) or soup.find("h1")
        if not title_element:
            # Fallback para meta tags caso o h1 mude
            og_title = soup.find("meta", property="og:title")
            title = og_title["content"] if og_title else "Produto KaBuM Desconhecido"
        else:
            title = title_element.get_text()

        # 2. Extração do Preço Atual
        # Buscamos pelo elemento de preço à vista na Kabum
        price_element = soup.find(
            "h4", {"class": "sc-52416c0c-2"}) or soup.find(class_="finalPrice")
        if not price_element:
            raise ValueError(
                f"Não foi possível encontrar o preço atual na página da Kabum: {url}")

        current_price = self._parse_price(price_element.get_text())

        # 3. Verificação de Estoque
        # Se houver botão de indisponível ou mensagem correspondente
        out_of_stock_element = soup.find(
            string=lambda text: text and "esgotado" in text.lower())
        in_stock = False if out_of_stock_element else True

        logger.info(f"Kabum Scraper processado com sucesso para: {title}")

        return ProductBase(
            title=title,
            store=self.store_name,
            url=url,
            current_price=current_price,
            in_stock=in_stock,
            category="peripherals",
        )
