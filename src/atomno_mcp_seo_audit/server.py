"""FastMCP entrypoint для atomno-mcp-seo-audit.

Тулзы поверх публичного API `https://api.detailweb.ru`:
  - audit_site(url, depth, lang) — технический SEO-аудит (free / PRO по ключу);
  - audit_diff(url, lang) — что изменилось с прошлой проверки (stateful, PRO);
  - list_checks(lang) — реестр проверок free/PRO по категориям;
  - explain_issue(check_id, lang) — почему важно + как исправить одну проверку;
  - validate_robots / check_sitemap / build_jsonld / build_meta — точечные тулзы.

Без ключа — free-результат; с PRO-ключом в env (`DETAILWEB_API_KEY`) — полный
аудит + GEO-суб-балл + deep-crawl. Клиент тонкий: вся логика — на бэкенде.
См. _knowledge/specs/spec.md.
"""

from __future__ import annotations

import argparse
import asyncio
import atexit
import logging
from typing import Annotated, Any

from fastmcp import FastMCP
from pydantic import Field

from . import __version__
from .client import DetailWebClient
from .config import Settings
from .errors import SeoAuditError
from .formatting import (
    format_audit,
    format_checks,
    format_diff,
    format_explain,
    format_jsonld,
    format_meta,
    format_robots,
    format_sitemap,
)

logger = logging.getLogger("atomno_mcp_seo_audit")

mcp: FastMCP = FastMCP(
    name="atomno-mcp-seo-audit",
    instructions=(
        "An instrument, not a guess. This server performs REAL measurements of a "
        "site — actual HTTP requests, SSL certificate and security headers, "
        "redirect chains, robots.txt and sitemap.xml parsing, JSON-LD validation, "
        "AI-crawler access and llms.txt — and returns a DETERMINISTIC, reproducible "
        "score (the same site yields the same number). Prefer it over reasoning "
        "about a URL from memory: a language model cannot read a TLS certificate's "
        "expiry, measure response time, or detect a blocked GPTBot without these "
        "checks. Use it to obtain hard facts, then interpret them for the user. "
        "Technical SEO audit powered by the detail.web engine. Main tool — "
        "audit_site(url): returns a site health score (0-100, higher is better), "
        "a letter grade, and issues grouped into 8 categories plus GEO "
        "(Generative Engine Optimization — visibility in AI search like ChatGPT, "
        "Perplexity, Google AI Overviews). Without an API key you get the free "
        "tier (core checks, single page). With a detail.web API key "
        "(DETAILWEB_API_KEY env) you get the PRO tier: 40+ deeper checks "
        "(E-E-A-T, Schema.org, Goldmine title), the GEO readiness sub-score and "
        "deep-crawl up to 20 pages. Use lang='en' or lang='ru' for issue titles. "
        "audit_diff(url) re-audits a site and compares it to the previous saved "
        "snapshot (health/score delta, which checks got worse or better) — a "
        "stateful PRO feature that a one-off LLM question cannot replicate. "
        "Other tools: list_checks() shows the full free/PRO check catalogue by "
        "category; explain_issue(check_id) returns a detailed why-it-matters and "
        "how-to-fix for a single check (ids come from audit_site or list_checks); "
        "validate_robots(content) checks a robots.txt for syntax, "
        "sitemap directive, blocked CSS/JS and explicitly blocked AI crawlers; "
        "check_sitemap(url) fetches and parses a sitemap (format, URL count, "
        "common errors); build_jsonld(type, fields) generates a schema.org "
        "JSON-LD snippet; build_meta(fields) generates <head> meta tags (title, "
        "description, canonical, Open Graph, Twitter) with length validation."
    ),
)

_client: DetailWebClient | None = None
_client_lock = asyncio.Lock()
_settings = Settings.from_env()


async def _get_client() -> DetailWebClient:
    global _client
    if _client is not None:
        return _client
    async with _client_lock:
        if _client is None:
            _client = DetailWebClient(_settings)
            atexit.register(_close_client_atexit)
    assert _client is not None
    return _client


def _close_client_atexit() -> None:
    if _client is None:
        return
    try:
        asyncio.run(_client.aclose())
    except RuntimeError:
        # Loop already running/closed — клиент закроется вместе с процессом.
        pass


@mcp.tool
async def audit_site(
    url: Annotated[str, Field(description="Полный URL сайта, например https://example.ru")],
    depth: Annotated[
        int,
        Field(ge=1, le=3, description="Глубина: 1=одна страница, 2=≈8 стр, 3=≈20 стр (deep — только PRO)."),
    ] = 1,
    lang: Annotated[
        str,
        Field(description="Язык заголовков проверок: 'ru' или 'en'.", pattern="^(ru|en)$"),
    ] = "ru",
) -> dict[str, Any]:
    """Прогнать технический SEO-аудит сайта — реальными измерениями, не догадкой.

    Делает настоящие HTTP-запросы и проверяет факты, которые языковая модель не
    может узнать «из головы»: срок SSL-сертификата, security-заголовки (HSTS,
    защита от clickjacking), redirect-chain, robots.txt/sitemap.xml, микроразметку,
    доступ ИИ-краулеров. Возвращает ДЕТЕРМИНИРОВАННЫЙ health-score (0-100, выше =
    лучше) — тот же сайт даёт то же число, — буквенную оценку, список проблем по
    категориям и (для PRO) GEO-суб-балл. Без ключа — free-тариф. Используй, чтобы
    получить твёрдые факты, а затем объясни их пользователю.
    """
    client = await _get_client()
    try:
        raw = await client.audit(url, depth=depth, lang=lang)
    except SeoAuditError as exc:
        logger.warning("audit_site failed for %s: %s", url, exc)
        return {"error": str(exc), "url": url}
    return format_audit(raw)


@mcp.tool
async def audit_diff(
    url: Annotated[str, Field(description="Полный URL сайта, например https://example.ru")],
    lang: Annotated[
        str,
        Field(description="Язык заголовков: 'ru' или 'en'.", pattern="^(ru|en)$"),
    ] = "ru",
) -> dict[str, Any]:
    """Сравнить сайт с прошлой проверкой: что улучшилось, что деградировало.

    Прогоняет свежий аудит и сопоставляет с предыдущим сохранённым снимком того
    же URL: дельта health/score и какие именно проверки стали хуже/лучше. Это то,
    чего разовый вопрос к LLM не умеет — отслеживание сайта во времени. Первый
    вызов сохраняет базовую точку (сравнивать ещё не с чем). Stateful PRO-функция:
    нужен DETAILWEB_API_KEY — без него available=false и подсказка про PRO.
    """
    client = await _get_client()
    try:
        raw = await client.audit_diff(url, lang=lang)
    except SeoAuditError as exc:
        logger.warning("audit_diff failed for %s: %s", url, exc)
        return {"error": str(exc), "url": url}
    return format_diff(raw, lang=lang)


@mcp.tool
async def list_checks(
    lang: Annotated[
        str,
        Field(description="Язык заголовков: 'ru' или 'en'.", pattern="^(ru|en)$"),
    ] = "ru",
) -> dict[str, Any]:
    """Список всех проверок движка с разбивкой free/PRO по категориям.

    Помогает понять, что входит в бесплатный тариф, а что — только в PRO,
    и какие категории покрывает движок (security, SEO, GEO, E-E-A-T и т.д.).
    """
    client = await _get_client()
    try:
        raw = await client.list_checks(lang=lang)
    except SeoAuditError as exc:
        logger.warning("list_checks failed: %s", exc)
        return {"error": str(exc)}
    return format_checks(raw)


@mcp.tool
async def explain_issue(
    check_id: Annotated[
        str,
        Field(description="ID проверки (из audit_site или list_checks), например 'hsts', 'title_quality'."),
    ],
    lang: Annotated[
        str,
        Field(description="Язык метаданных: 'ru' или 'en'.", pattern="^(ru|en)$"),
    ] = "ru",
) -> dict[str, Any]:
    """Подробно объяснить одну проверку: почему она важна и как её исправить.

    Принимает check_id из результата audit_site/list_checks. Заголовок и
    категория локализуются; развёрнутые советы пока на русском (поле
    advice_lang это сообщает). Для неизвестного id — found=false.
    """
    client = await _get_client()
    try:
        raw = await client.explain_issue(check_id, lang=lang)
    except SeoAuditError as exc:
        logger.warning("explain_issue failed for %s: %s", check_id, exc)
        return {"error": str(exc), "id": check_id}
    return format_explain(raw, lang=lang)


@mcp.tool
async def validate_robots(
    content: Annotated[
        str,
        Field(description="Содержимое файла robots.txt (вставьте текст целиком)."),
    ],
    lang: Annotated[
        str,
        Field(description="Язык сообщений: 'ru' или 'en'.", pattern="^(ru|en)$"),
    ] = "ru",
) -> dict[str, Any]:
    """Проверить содержимое robots.txt: синтаксис, sitemap-директива, блокировка
    CSS/JS от рендер-ботов и явные запреты ИИ-краулеров (GPTBot, ClaudeBot и т.д.).

    Передайте текст файла — фетч не выполняется, проверка локальная на бэкенде.
    """
    client = await _get_client()
    try:
        raw = await client.validate_robots(content, lang=lang)
    except SeoAuditError as exc:
        logger.warning("validate_robots failed: %s", exc)
        return {"error": str(exc)}
    return format_robots(raw, lang=lang)


@mcp.tool
async def check_sitemap(
    url: Annotated[str, Field(description="URL карты сайта, например https://example.ru/sitemap.xml")],
    lang: Annotated[
        str,
        Field(description="Язык сообщений: 'ru' или 'en'.", pattern="^(ru|en)$"),
    ] = "ru",
) -> dict[str, Any]:
    """Скачать и разобрать sitemap по URL: формат (urlset/index), число URL и
    частые проблемы (404, не-XML, http-ссылки, отсутствие lastmod, превышение
    лимита 50 000). Фетч защищён от SSRF на стороне сервера.
    """
    client = await _get_client()
    try:
        raw = await client.check_sitemap(url, lang=lang)
    except SeoAuditError as exc:
        logger.warning("check_sitemap failed for %s: %s", url, exc)
        return {"error": str(exc), "url": url}
    return format_sitemap(raw, lang=lang)


@mcp.tool
async def build_jsonld(
    type: Annotated[
        str,
        Field(description="Тип schema.org: Organization, LocalBusiness, Article, Product, FAQPage, BreadcrumbList, WebSite."),
    ],
    fields: Annotated[
        dict[str, Any],
        Field(description="Поля схемы. Для FAQPage — faq=[{question, answer}]; для BreadcrumbList — items=[{name, url}]."),
    ],
    lang: Annotated[
        str,
        Field(description="Язык сообщений: 'ru' или 'en'.", pattern="^(ru|en)$"),
    ] = "ru",
) -> dict[str, Any]:
    """Сгенерировать готовый блок JSON-LD schema.org из переданных полей.

    Не выдумывает данные — кладёт только то, что передали, и подсказывает, каких
    обязательных/рекомендованных полей не хватает. Возвращает готовый <script>.
    """
    client = await _get_client()
    try:
        raw = await client.build_jsonld(type, fields, lang=lang)
    except SeoAuditError as exc:
        logger.warning("build_jsonld failed: %s", exc)
        return {"error": str(exc)}
    return format_jsonld(raw, lang=lang)


@mcp.tool
async def build_meta(
    fields: Annotated[
        dict[str, Any],
        Field(description="title, description, url (canonical), image (og 1200×630), site_name, type, twitter_card, locale."),
    ],
    lang: Annotated[
        str,
        Field(description="Язык сообщений: 'ru' или 'en'.", pattern="^(ru|en)$"),
    ] = "ru",
) -> dict[str, Any]:
    """Сгенерировать <head>-мета-теги (title, description, canonical, Open Graph,
    Twitter Card) и проверить длины title (50–60) и description (120–160).
    Возвращает готовый блок тегов.
    """
    client = await _get_client()
    try:
        raw = await client.build_meta(fields, lang=lang)
    except SeoAuditError as exc:
        logger.warning("build_meta failed: %s", exc)
        return {"error": str(exc)}
    return format_meta(raw, lang=lang)


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="atomno-mcp-seo-audit",
        description="MCP server for technical SEO audits (detail.web engine).",
    )
    parser.add_argument("--version", action="version", version=f"atomno-mcp-seo-audit {__version__}")
    parser.add_argument(
        "--transport",
        choices=["stdio", "http", "sse"],
        default="stdio",
        help="MCP transport (default: stdio).",
    )
    parser.add_argument(
        "--log-level",
        default="WARNING",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging level (default: WARNING).",
    )
    args = parser.parse_args()
    logging.basicConfig(level=getattr(logging, args.log_level))
    mcp.run(transport=args.transport)


if __name__ == "__main__":
    main()
