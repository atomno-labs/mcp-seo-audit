<!-- mcp-name: io.github.atomno-mcp/mcp-seo-audit -->

# atomno-mcp-seo-audit

[![PyPI](https://img.shields.io/pypi/v/atomno-mcp-seo-audit)](https://pypi.org/project/atomno-mcp-seo-audit/)
[![Python](https://img.shields.io/pypi/pyversions/atomno-mcp-seo-audit)](https://pypi.org/project/atomno-mcp-seo-audit/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![MCP](https://img.shields.io/badge/MCP-server-blue)](https://modelcontextprotocol.io)

MCP (Model Context Protocol) server for **technical SEO & GEO audits**, powered by
the [detail.web](https://audit.detailweb.ru) engine — **real measurements, not LLM
guesses**. Run it from Cursor, Claude Desktop or any MCP client. **8 tools:**
`audit_site` (deterministic `0–100` health score + letter grade, 78 checks across
8 categories, plus a **GEO** sub-score — visibility in ChatGPT / Perplexity /
Google AI Overviews), `audit_diff` (compare vs the previous snapshot),
`robots.txt` & `sitemap.xml` validators, JSON-LD & meta/OpenGraph builders, and
per-check fix explainers. Probes TLS, redirects, TTFB, AI-crawler access (GPTBot)
and `llms.txt`. Free tier + **PRO+** (deep-crawl, GEO, 40+ deeper checks) — API
keys unlock the deeper engine on the **PRO+** plan and up (see [Free vs PRO+](#free-vs-pro)).

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
  do — track a site over time. Stateful feature — needs a key on the **PRO+**
  plan or higher.
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

### Free vs PRO+

| | Free (no key) | PRO+ and up (API key) |
|---|---|---|
| Checks | core technical basics | 40+ deeper checks (E-E-A-T, Schema.org, Goldmine title) |
| GEO | 4 GEO signals | GEO readiness sub-score + deep GEO checks |
| Crawl | single page | deep-crawl up to 20 pages (`depth=2/3`) |

> **Which plan unlocks the API/MCP?** Programmatic access (this server, `audit_diff`,
> deep-crawl, GEO sub-score) is enabled on **PRO+** (`pro_plus`), **Business** and
> **Enterprise**. The entry-level **PRO** plan and the Free tier are web-dashboard
> only — an API key issued on them authenticates but still returns the **free**
> result. If you need programmatic access, pick **PRO+** or higher.

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
| `DETAILWEB_API_KEY` | — | API key (`dwa_...`) from a **PRO+** plan or higher. Without it (or on Free/PRO) → free tier |
| `DETAILWEB_TIMEOUT` | `60` | HTTP timeout (seconds) |
| `DETAILWEB_LANG` | `ru` | Default issue-title language (`ru` / `en`) |

**The free tier needs no key and no signup** — just run the command above.
Programmatic access (40+ deeper checks, GEO sub-score, deep-crawl, `audit_diff`)
requires a key from the **PRO+** plan or higher — the entry-level **PRO** plan is
web-dashboard only and its key returns the free result. It is currently
provisioned on request: email **kir@detailweb.ru** or reach out via
[audit.detailweb.ru](https://audit.detailweb.ru). Once your account is active you
create keys yourself in **Dashboard → Account → API keys** (`dwa_…`, shown once)
and put the key in `DETAILWEB_API_KEY`.

## Example

> "Audit https://example.com"

The agent calls `audit_site("https://example.com")` and gets back the health
score, grade and the list of issues to fix.

## License

MIT © atomno-mcp. The open-source client talks to a proprietary hosted backend.

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
изменилось с прошлой проверки — stateful, тариф PRO+ и выше), `list_checks` (каталог
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

Бесплатный тариф (базовые проверки, одна страница) работает **сразу, без ключа
и регистрации**. Программный доступ (40+ глубоких проверок, GEO-суб-балл,
deep-crawl до 20 страниц, `audit_diff`) работает с ключом тарифа **PRO+**
(`pro_plus`) и выше — **Business**, **Enterprise**. Начальный тариф **PRO**
(1290 ₽) и Free — только веб-кабинет: ключ на них проходит авторизацию, но
результат остаётся бесплатным. Тариф пока выдаём по запросу: напишите на
**kir@detailweb.ru** или через [audit.detailweb.ru](https://audit.detailweb.ru).
После активации аккаунта ключ (`dwa_…`) создаётся в кабинете → **Аккаунт →
API-ключи** (показывается один раз) и подставляется в `DETAILWEB_API_KEY` в
`env`. Полное описание инструментов и настроек — в английской версии выше.
