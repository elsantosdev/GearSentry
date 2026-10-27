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

STORE_NAME = "Mercado Livre"

TITLE_SELECTORS = (
    "h1.ui-pdp-title",
    "h1.item-title__primary",
    "h1[class*='title']",
    "h1",
)

PRICE_INTEGER_SELECTORS = (
    ".andes-money-amount__fraction",
    "span[class*='andes-money-amount__fraction']",
    ".ui-pdp-price__second-line .andes-money-amount__fraction",
    ".item-price .price-tag-fraction",
    "meta[property='product:price:amount']",
    "meta[property='og:price:amount']",
)

PRICE_PATTERN = re.compile(r"\d[\d.,]*")

# Páginas reais de produtos no ML contêm dezenas/centenas de KB.
# Tamanhos muito baixos com falha de parse indicam bloqueio anti-bot (soft block).
BLOCKED_HTML_MAX_SIZE = 50_000


class MercadoLivreScraper:
    """Scraper resiliente para o Mercado Livre com suporte a impersonação TLS,

    extração em camadas (Visual, JSON-LD, Scripts) e tratamento de bloqueios.
    """

    def __init__(self, timeout: float = 15.0):
        self.base_url = "https://www.mercadolivre.com.br"
        self.timeout = timeout

    # ---------- API Pública ----------

    async def fetch_product(self, url: str) -> ProductCreate:
        """Faz o download da página com impersonação de navegador e executa o parse."""
        html = await self._download(url)
        try:
            return self.parse(html, url)
        except ParseError as exc:
            if len(html) < BLOCKED_HTML_MAX_SIZE:
                raise BlockedByStore(
                    f"Mercado Livre devolveu uma página incompleta "
                    f"({len(html)} bytes), provável bloqueio anti-bot: {url}"
                ) from exc
            raise

    def parse(self, html: str, url: str) -> ProductCreate:
        """Extrai os dados do HTML de forma isolada (puro parsing, sem rede)."""
        soup = BeautifulSoup(html, "html.parser")
        title = self._extract_title(soup)
        price = self._extract_price(soup, title)

        return ProductCreate(
            title=title,
            current_price=price,
            url=url,
            store=STORE_NAME,
        )

    # ---------- Camada de Rede ----------

    async def _download(self, url: str) -> str:
        """Baixa o HTML utilizando curl_cffi para mascarar a assinatura TLS (ja4/ja3)."""
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

    # ---------- Camada de Parsing ----------

    def _extract_title(self, soup: BeautifulSoup) -> str:
        """Busca o título do produto por seletores visuais ou OpenGraph."""
        for selector in TITLE_SELECTORS:
            element = soup.select_one(selector)
            if element:
                text = element.get_text(strip=True)
                if text:
                    return text

        meta_title = soup.find("meta", property="og:title")
        if meta_title and meta_title.get("content"):
            return meta_title["content"].strip()

        raise ParseError("Título não encontrado no Mercado Livre.")

    def _extract_price(self, soup: BeautifulSoup, title: str) -> Decimal:
        """Extrai o preço utilizando múltiplas estratégias em cascata (Resiliência Máxima)."""
        raw_price = None

        # 1. Estratégia Visual e Meta Tags
        for selector in PRICE_INTEGER_SELECTORS:
            element = soup.select_one(selector)
            if element:
                text = element.get(
                    "content") if element.name == "meta" else element.get_text(strip=True)
                if text and any(char.isdigit() for char in text):
                    raw_price = text
                    break

        # 2. Estratégia JSON-LD (Schema.org)
        if not raw_price:
            raw_price = self._extract_price_from_json_ld(soup)

        # 3. Estratégia de Varredura Profunda em Scripts Globais
        if not raw_price:
            raw_price = self._extract_price_from_scripts(soup)

        if not raw_price:
            raise ParseError(
                f"Preço não encontrado. Título extraído: '{title}'")

        price = self._parse_price(raw_price)
        if price <= 0:
            logger.warning(
                f"Produto indisponível ou sem preço válido: {title}")
            raise ProductUnavailable(title)

        return price

    def _extract_price_from_json_ld(self, soup: BeautifulSoup) -> str | None:
        """Extrai o preço das tags de dados estruturados JSON-LD."""
        scripts = soup.find_all("script", type="application/ld+json")
        for script in scripts:
            if not script.string:
                continue
            try:
                data = json.loads(script.string)
                items = data if isinstance(data, list) else [data]
                for item in items:
                    if item.get("@type") == "Product":
                        offers = item.get("offers")
                        if offers:
                            offer_list = offers if isinstance(
                                offers, list) else [offers]
                            for offer in offer_list:
                                price = offer.get(
                                    "price") or offer.get("lowPrice")
                                if price is not None:
                                    return str(price)
            except Exception:
                continue
        return None

    def _extract_price_from_scripts(self, soup: BeautifulSoup) -> str | None:
        """Vasculha recursivamente objetos JSON dentro de blocos de script da página."""
        target_keys = ("price", "sellingPrice", "currentPrice",
                       "amount", "value", "bestPrice", "rate")
        for script in soup.find_all("script"):
            if not script.string:
                continue
            content = script.string.strip()

            try:
                data = json.loads(content)
                val = self._find_key_in_dict(data, target_keys)
                if val is not None and str(val).strip():
                    return str(val)
            except Exception:
                pass

            try:
                start = content.find('{')
                end = content.rfind('}')
                if start != -1 and end != -1 and end > start:
                    json_str = content[start:end+1]
                    data = json.loads(json_str)
                    val = self._find_key_in_dict(data, target_keys)
                    if val is not None and str(val).strip():
                        return str(val)
            except Exception:
                continue

        return None

    def _find_key_in_dict(self, obj, target_keys):
        """Função auxiliar recursiva para buscar chaves de preço em dicionários aninhados."""
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
        """Normaliza e converte strings de preço brasileiras/internacionais em Decimal exato."""
        if isinstance(raw_price, (int, float)):
            return Decimal(str(raw_price))

        match = PRICE_PATTERN.search(str(raw_price))
        if not match:
            raise ParseError(f"Formato de preço inválido: {raw_price!r}")

        cleaned = match.group(0)
        if "." in cleaned and "," in cleaned:
            normalized = cleaned.replace(".", "").replace(",", ".")
        elif "," in cleaned and "." not in cleaned:
            normalized = cleaned.replace(",", ".")
        else:
            normalized = cleaned

        try:
            return Decimal(normalized)
        except InvalidOperation as exc:
            raise ParseError(
                f"Não foi possível converter o preço: {raw_price!r}"
            ) from exc
