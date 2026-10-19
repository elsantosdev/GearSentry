# 🛡️ GearSentry

Um sistema de rastreamento e monitoramento inteligente de preços para periféricos de computador (teclados, mouses, headsets, monitores), projetado com arquitetura modular e boas práticas de engenharia de software em Python.

## 🚀 Funcionalidades Planejadas
- **Raspagem Resiliente:** Coleta automática de preços em e-commerces de tecnologia.
- **Validação Estrita:** Garantia de integridade de dados usando Pydantic.
- **Análise de Histórico:** Armazenamento em banco de dados relacional para detecção de reais promoções.
- **Alertas Automatizados:** Notificações instantâneas via Webhooks do Discord.

## 🛠️ Tech Stack
- **Linguagem:** Python 3.10+
- **HTTP & Parsing:** `httpx`, `BeautifulSoup4`
- **Validação & DB:** `Pydantic`, `SQLAlchemy`
- **CLI & Logs:** `Typer`, `Loguru`
- **Testes:** `pytest`