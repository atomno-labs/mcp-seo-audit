"""atomno-mcp-seo-audit — тонкий MCP-клиент технического SEO-аудита detail.web.

Клиент НЕ содержит логики аудита: только httpx-вызовы на бэкенд
`audit.detailweb.ru` и форматирование ответа. Движок (56 проверок, скоринг,
GEO, SEO-vault) — приватный, на сервере. См. _knowledge/specs/spec.md.
"""

__version__ = "0.4.1"

__all__ = ["__version__"]
