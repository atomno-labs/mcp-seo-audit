# atomno-mcp-seo-audit

[![PyPI](https://img.shields.io/pypi/v/atomno-mcp-seo-audit)](https://pypi.org/project/atomno-mcp-seo-audit/)
[![Python](https://img.shields.io/pypi/pyversions/atomno-mcp-seo-audit)](https://pypi.org/project/atomno-mcp-seo-audit/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![MCP](https://img.shields.io/badge/MCP-server-blue)](https://modelcontextprotocol.io)

MCP (Model Context Protocol) server for **technical SEO audits**, powered by the
[detail.web](https://audit.detailweb.ru) engine. Run a site audit straight from
your AI agent in Cursor, Claude Desktop or any MCP client — get a health score,
issues across 8 categories, and a **GEO** (Generative Engine Optimization —
visibility in AI search) sub-score.

## Why pair it with an LLM?

A language model on its own infers a site from training data and, at best, one
rendered page — it can't directly read your TLS certificate's expiry, measure
response time, parse `sitemap.xml`, or check whether `GPTBot` is blocked in
`robots.txt`. This server runs those checks for real: actual HTTP requests,
security headers, redirect chains, structured-data validation — and returns a
**deterministic** score (same site → same number), reproducible enough to put in
a client report. Think of it as the instrument and the LLM as the analyst that
interprets the readout — the two work best together.

## What you get

- **`audit_site(url, depth=1, lang="ru")`** — one call returns:
  - health score `0–100` (higher is better) and a letter grade `A–F`;
  - issues grouped by category (security, SEO & indexing, performance, GEO, …),
    each with status `pass / warn / fail`;
  - a short human-readable summary.
- **`audit_diff(url, lang="ru")`** — re-audits a site and compares it to the
  previous run: health/score delta and which checks got worse or better. The
  first call stores a baseline. This is something a one-off LLM question can't
  do — track a site over time. Stateful **PRO** feature (needs an API key).
- **`list_checks(lang="ru")`** — the full catalogue of engine checks grouped by
  category, with a `free` / `PRO` badge on each — so you (and the agent) can see
  exactly what the free tier covers and what PRO unlocks.
- **`explain_issue(check_id, lang="ru")`** — a deep-dive on a single check:
  why it matters and how to fix it. Pass a `check_id` from `audit_site` or
  `list_checks`. Title and category are localized; detailed advice is currently
  in Russian (the `advice_lang` field reports this).
- **`validate_robots(content, lang="ru")`** — paste a `robots.txt` and get back
  syntax issues, whether a `Sitemap:` directive is present, whether CSS/JS is
  blocked from render bots, and which AI crawlers (GPTBot, ClaudeBot, …) are
  explicitly blocked. No fetch — validates the text you provide.
- **`check_sitemap(url, lang="ru")`** — fetches a sitemap by URL and reports its
  format (`urlset` / `sitemapindex`), URL count and common problems (404,
  non-XML content type, `http://` links, missing `<lastmod>`, the 50k-per-file
  limit). The fetch is SSRF-guarded on the server.
- **`build_jsonld(type, fields, lang="ru")`** — generates a ready-to-paste
  schema.org JSON-LD `<script>` (Organization, LocalBusiness, Article, Product,
  FAQPage, BreadcrumbList, WebSite) and tells you which required/recommended
  fields are missing. It never invents data — only what you pass in.
- **`build_meta(fields, lang="ru")`** — generates `<head>` meta tags (title,
  description, canonical, Open Graph, Twitter Card) and validates the title
  (50–60 chars) and description (120–160 chars) lengths.

### Free vs PRO

| | Free (no key) | PRO (with API key) |
|---|---|---|
| Checks | core technical basics | 40+ deeper checks (E-E-A-T, Schema.org, Goldmine title) |
| GEO | 4 GEO signals | GEO readiness sub-score + deep GEO checks |
| Crawl | single page | deep-crawl up to 20 pages (`depth=2/3`) |

The audit engine itself stays on the server — this package is a thin client
(HTTP calls + formatting only).

## Install

```bash
uvx atomno-mcp-seo-audit
```

Or add to your MCP client config (`mcp.json`):

```json
{
  "mcpServers": {
    "seo-audit": {
      "command": "uvx",
      "args": ["atomno-mcp-seo-audit"]
    }
  }
}
```

## Configuration

All via environment variables:

| Variable | Default | Purpose |
|---|---|---|
| `DETAILWEB_API_BASE` | `https://api.detailweb.ru` | Backend base URL |
| `DETAILWEB_API_KEY` | — | PRO key (`dwa_...`). Without it → free tier |
| `DETAILWEB_TIMEOUT` | `60` | HTTP timeout (seconds) |
| `DETAILWEB_LANG` | `ru` | Default issue-title language (`ru` / `en`) |

**Getting a PRO key:** sign in at [audit.detailweb.ru](https://audit.detailweb.ru)
→ **Dashboard → Account → API keys** → create a key (`dwa_…`, shown once) and put
it in `DETAILWEB_API_KEY`. The free tier works without any key.

## Example

> "Audit https://example.com"

The agent calls `audit_site("https://example.com")` and gets back the health
score, grade and the list of issues to fix.

## License

MIT © atomno-labs. The open-source client talks to a proprietary hosted backend.

---

## 🇷🇺 На русском

MCP-сервер технического SEO-аудита на движке
[detail.web](https://audit.detailweb.ru). Запускайте аудит прямо из ИИ-агента
(Cursor, Claude Desktop и любой MCP-клиент): **health-score**, проблемы по 8
категориям и **GEO**-суб-балл (видимость в ИИ-поиске — ChatGPT, Perplexity,
AI Overviews).

**Зачем в связке с нейросетью.** Языковая модель сама по себе судит о сайте по
обучающим данным и в лучшем случае по одной отрисованной странице — она не
прочитает напрямую срок SSL-сертификата, не измерит время ответа, не распарсит
`sitemap.xml` и не проверит, заблокирован ли `GPTBot` в `robots.txt`. Этот сервер
выполняет такие проверки по-настоящему: HTTP-запросы, заголовки, редиректы,
микроразметка — и даёт **детерминированный** score (тот же сайт → то же число),
пригодный для отчёта клиенту. Это прибор, а нейросеть — аналитик, который читает
показания. Лучше всего работает связка.

**Инструменты:** `audit_site` (аудит + score + GEO), `audit_diff` (что
изменилось с прошлой проверки — stateful PRO), `list_checks` (каталог
проверок free/PRO), `explain_issue` (почему важно + как исправить),
`validate_robots`, `check_sitemap`, `build_jsonld`, `build_meta`.

**Установка:**

```bash
uvx atomno-mcp-seo-audit
```

В конфиге MCP-клиента (`mcp.json`):

```json
{
  "mcpServers": {
    "seo-audit": {
      "command": "uvx",
      "args": ["atomno-mcp-seo-audit"],
      "env": { "DETAILWEB_LANG": "ru" }
    }
  }
}
```

PRO-режим (40+ глубоких проверок, GEO-суб-балл, deep-crawl до 20 страниц):
добавьте `DETAILWEB_API_KEY` (`dwa_…`) в `env`. Ключ создаётся в кабинете
[audit.detailweb.ru](https://audit.detailweb.ru) → **Аккаунт → API-ключи**
(полный ключ показывается один раз). Без ключа работает бесплатный тариф
(базовые проверки, одна страница). Полное описание инструментов и настроек —
в английской версии выше.
