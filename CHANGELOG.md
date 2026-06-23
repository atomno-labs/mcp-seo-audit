# Changelog

All notable changes to this project are documented here.

## [Unreleased]

### Changed
- Positioning «instrument, not a guess»: server `instructions` and the
  `audit_site` description now make explicit that the engine performs real
  measurements (SSL, headers, robots/sitemap, structured data) and returns a
  deterministic score — vs an LLM guessing about a URL.
- README: added "Why not just ask an LLM?" section + a condensed Russian
  (`🇷🇺 На русском`) section for RU users.

### Planned
- Stateful monitoring (`watch_site` + alerts, idea I-4) — see
  `_knowledge/specs/monitoring.md`.

## [0.3.0] - 2026-06-23

### Added
- `explain_issue(check_id, lang)` tool — detailed why-it-matters and how-to-fix
  for a single check, over `GET /checks/{check_id}`. Title/category localized
  (ru|en); detailed advice currently in Russian (`advice_lang` field reports it).
  ids come from `audit_site` or `list_checks`.

### Infra
- Public API ingress live: `https://api.detailweb.ru` (Caddy vhost → loopback
  8090, allowlisted public paths). Client default base now reachable in prod.
- Publication artifacts prepared: `Dockerfile` (multi-stage, for the Glama
  analyzer), `.dockerignore`, root `glama.json`, README shield badges. Validated
  via `pip install .` + console-script `--version`/`--help` smoke.

## [0.2.0] - unreleased

### Added
- `list_checks(lang)` tool — full free/PRO check catalogue grouped by category,
  over `GET /checks`.
- `validate_robots(content, lang)` tool — robots.txt validator (syntax, sitemap
  directive, blocked CSS/JS, explicitly blocked AI crawlers like GPTBot /
  ClaudeBot), over `POST /tools/robots`. No fetch — works on pasted content.
- `check_sitemap(url, lang)` tool — fetches and parses a sitemap (urlset vs
  index, URL count, common errors: 404, non-XML, http links, missing lastmod,
  50k limit), over `POST /tools/sitemap`. SSRF-guarded fetch on the backend.
- `build_jsonld(type, fields, lang)` tool — generates a schema.org JSON-LD
  snippet (Organization, LocalBusiness, Article, Product, FAQPage,
  BreadcrumbList, WebSite) with required/recommended field hints, over
  `POST /tools/jsonld`.
- `build_meta(fields, lang)` tool — generates `<head>` meta tags (title,
  description, canonical, Open Graph, Twitter Card) with title/description
  length validation, over `POST /tools/meta`.

## [0.1.0] - unreleased

### Added
- Initial thin MCP client (Phase 0).
- `audit_site(url, depth, lang)` tool over `POST /audit` of the detail.web backend.
- Free tier without an API key; PRO tier (GEO sub-score + deep-crawl) via
  `DETAILWEB_API_KEY`.
- `ru` / `en` issue titles via `lang`.
- CLI entrypoint `atomno-mcp-seo-audit` with `--version` / `--transport` / `--log-level`.
