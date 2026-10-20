import json
import re
from decimal import Decimal
from bs4 import BeautifulSoup
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
            if isinstance(price_str, (int, float, Decimal)):
                return Decimal(str(price_str))

            clean_str = re.sub(r"[^\d.,]", "", str(price_str)).strip()
            if "." in clean_str and "," in clean_str:
                clean_str = clean_str.replace(".", "").replace(",", ".")
            elif "," in clean_str:
                clean_str = clean_str.replace(",", ".")
            return Decimal(clean_str)
        except Exception as e:
            logger.error(f"Erro ao converter preço '{price_str}': {e}")
            raise ValueError(f"Preço inválido: {price_str}")

    def parse_product(self, html: str, url: str) -> ProductBase:
        """
        Analisa o HTML bruto da página do produto da Kabum utilizando BeautifulSoup e retorna um modelo ProductBase validado.
        """
        soup = BeautifulSoup(html, "html.parser")

        title = "Produto KaBuM Desconhecido"
        current_price = None
        in_stock = True

        # Tentativa 1: Extrair via script Next.js (__NEXT_DATA__)
        next_data_script = soup.find("script", id="__NEXT_DATA__")
        if next_data_script:
            try:
                data = json.loads(next_data_script.string)
                # Navega de forma segura pela árvore JSON típica do Next.js da KaBuM
                # (A estrutura exata pode variar, mas geralmente fica em props.pageProps...)
                logger.info(
                    "A extrair dados via JSON estruturado (__NEXT_DATA__)")

                # Exemplo genérico de busca recursiva por chaves de preço/título no JSON ou caminho direto
                # Vamos implementar um fallback inteligente caso o caminho mude
                product_data = self._find_product_in_json(data)
                if product_data:
                    title = product_data.get("title", title)
                    raw_price = product_data.get(
                        "price") or product_data.get("current_price")
                    if raw_price:
                        current_price = self._parse_price(raw_price)
                    in_stock = product_data.get("in_stock", True)
            except Exception as e:
                logger.warning(f"Falha ao interpretar __NEXT_DATA__: {e}")

        # Tentativa 2: Fallback para seletores tradicionais e Meta Tags se o JSON falhar
        if not current_price:
            og_title = soup.find("meta", property="og:title")
            if og_title and og_title.get("content"):
                title = og_title["content"]

            og_price = soup.find("meta", property="product:price:amount") or soup.find(
                "meta", property="og:price:amount")
            if og_price and og_price.get("content"):
                current_price = self._parse_price(og_price["content"])

        if not current_price:
            raise ValueError(
                f"Não foi possível encontrar o preço atual na página da Kabum: {url}")

        logger.success(
            f"Kabum Scraper processado com sucesso: {title} [R$ {current_price}]")

        return ProductBase(
            title=title,
            store=self.store_name,
            url=url,
            current_price=current_price,
            in_stock=in_stock,
            category="peripherals",
        )

    def _find_product_in_json(self, data: dict) -> dict:
        """Função auxiliar para procurar chaves de produto em dicionários aninhados complexos."""
        # Procura por chaves comuns de produto em payloads do Next.js
        if isinstance(data, dict):
            if "product" in data and isinstance(data["product"], dict):
                return data["product"]
            for k, v in data.items():
                if isinstance(v, (dict, list)):
                    res = self._find_product_in_json(v)
                    if res:
                        return res
        elif isinstance(data, list):
            for item in data:
                if isinstance(item, (dict, list)):
                    res = self._find_product_in_json(item)
                    if res:
                        return res
        return {}
