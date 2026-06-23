# atomno-mcp-seo-audit

[![PyPI](https://img.shields.io/pypi/v/atomno-mcp-seo-audit)](https://pypi.org/project/atomno-mcp-seo-audit/)
[![Python](https://img.shields.io/pypi/pyversions/atomno-mcp-seo-audit)](https://pypi.org/project/atomno-mcp-seo-audit/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![MCP](https://img.shields.io/badge/MCP-server-blue)](https://modelcontextprotocol.io)

MCP (Model Context Protocol) server for **technical SEO audits**, powered by the
[detail.web](https://detailweb.ru) engine. Run a site audit straight from your
AI agent in Cursor, Claude Desktop or any MCP client — get a health score,
issues across 8 categories, and a **GEO** (Generative Engine Optimization —
visibility in AI search) sub-score.

## What you get

- **`audit_site(url, depth=1, lang="ru")`** — one call returns:
  - health score `0–100` (higher is better) and a letter grade `A–F`;
  - issues grouped by category (security, SEO & indexing, performance, GEO, …),
    each with status `pass / warn / fail`;
  - a short human-readable summary.
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

Get a PRO key in the detail.web dashboard → Account → API keys.

## Example

> "Audit https://example.com"

The agent calls `audit_site("https://example.com")` and gets back the health
score, grade and the list of issues to fix.

## License

MIT © atomno-labs. The open-source client talks to a proprietary hosted backend.
