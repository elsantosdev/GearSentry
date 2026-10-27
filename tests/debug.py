import asyncio
from curl_cffi.requests import AsyncSession

URL = "https://www.mercadolivre.com.br/ssd-samsung-pm9c1a-1tb-m2-2280-nvme-pcie-gen4-x4-gaming-preto/p/MLB66191177"
PERFIS = ["chrome", "chrome124", "chrome131",
          "safari17_0", "firefox133", "edge101"]


async def testar(perfil):
    try:
        async with AsyncSession(impersonate=perfil) as s:
            # visita a home antes, para pegar cookies
            await s.get("https://www.mercadolivre.com.br/", timeout=15)
            r = await s.get(
                URL,
                timeout=15,
                headers={"Accept-Language": "pt-BR,pt;q=0.9"},
            )
        html = r.text
        print(f"{perfil:12} status={r.status_code} tamanho={len(html):>8} "
              f"preco={'andes-money-amount' in html} ldjson={'application/ld+json' in html}")
    except Exception as exc:
        print(f"{perfil:12} erro: {exc}")


async def main():
    for p in PERFIS:
        await testar(p)

asyncio.run(main())
