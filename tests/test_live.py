import asyncio
from src.scrapers.kabum import KabumScraper


async def main():
    # URL real de um produto na KaBuM (pode alterar para qualquer outro periférico se preferir)
    url = "https://www.kabum.com.br/produto/102322/mouse-gamer-redragon-cobra-chroma-rgb-10000dpi-7-botoes-preto-m711"

    print(f"🔍 A contactar a KaBuM para a URL:\n{url}\n")

    scraper = KabumScraper()
    product = await scraper.scrape(url)

    if product:
        print("\n✅ SUCESSO! O Scraper extraiu os dados reais:")
        print(f"  • Título       : {product.title}")
        print(f"  • Loja         : {product.store}")
        print(f"  • Preço Atual  : R$ {product.current_price}")
        print(f"  • Em Estoque   : {product.in_stock}")
    else:
        print("\n❌ FALHA! Não foi possível extrair. Verifique se a KaBuM bloqueou a requisição ou se o HTML mudou.")

if __name__ == "__main__":
    asyncio.run(main())
