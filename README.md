# GearSentry

Monitor de preços de periféricos (teclados, mouses, headsets, monitores) em Python.
Raspa lojas, valida os dados, guarda o histórico e (em breve) avisa quedas de preço no Discord.

## Status

- [x] Interface comum de scrapers (`BaseScraper`) com retry e backoff
- [x] Extração via JSON-LD (schema.org/Product) para Terabyte e Mercado Livre
- [x] Validação com Pydantic
- [x] Histórico de preços em SQLite via SQLAlchemy (só grava quando o preço muda)
- [x] CLI: `track`, `scrape`, `list`, `history`
- [ ] Alertas por webhook do Discord
- [ ] Agendamento e Docker

## Uso

```bash
pip install -e ".[dev]"
gearsentry track "https://www.terabyteshop.com.br/produto/..."
gearsentry scrape      # atualiza todos os produtos
gearsentry list
gearsentry history 1
pytest                 # testes unitários (sem rede)
```

O banco fica em `gearsentry.db`; use `GEARSENTRY_DB` para mudar a URL.

## Decisões técnicas

- **curl_cffi em vez de httpx:** as lojas bloqueiam clientes HTTP comuns; o `impersonate`
  imita o fingerprint TLS de um navegador.
- **Preço em centavos (inteiro):** evita erros de ponto flutuante e o suporte parcial a
  `Decimal` do SQLite.
- **Uma classe por loja, mesmo contrato:** adicionar uma loja é herdar de `JsonLdScraper`
  (ou implementar `parse`) e registrá-la em `scrapers/registry.py`.
