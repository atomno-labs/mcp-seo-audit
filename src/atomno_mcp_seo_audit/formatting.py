"""Форматирование ответа /audit в компактный результат для MCP-агента.

Чистый presentation-слой: ничего не вычисляет, только перекладывает поля
бэкенда в удобную для LLM структуру + краткий markdown-сводный текст.
"""

from __future__ import annotations

from typing import Any

_STATUS_EMOJI = {"fail": "❌", "warn": "⚠️", "pass": "✅", "skip": "➖"}


def format_audit(resp: dict[str, Any]) -> dict[str, Any]:
    """Привести ответ /audit к компактной структуре + summary_text."""
    summary = resp.get("summary") or {}
    checks = resp.get("checks") or []
    problems = [c for c in checks if c.get("status") in ("warn", "fail")]

    result: dict[str, Any] = {
        "url": resp.get("url"),
        "plan": resp.get("plan", "free"),
        "lang": resp.get("lang", "ru"),
        "health": resp.get("health"),
        "grade": resp.get("grade"),
        "grade_label": resp.get("grade_label"),
        "problem_score": resp.get("score"),
        "depth_used": resp.get("depth_used", 1),
        "summary": {
            "checks_shown": summary.get("shown", len(checks)),
            "passed": summary.get("passed", 0),
            "warnings": summary.get("warnings", 0),
            "critical": summary.get("critical", 0),
            "skipped": summary.get("skipped", 0),
            "pro_checks_hidden": summary.get("pro_hidden", 0),
            "pro_problems_hidden": summary.get("pro_problems_hidden", 0),
        },
        "problems": problems,
        "checks": checks,
    }
    if resp.get("geo") is not None:
        result["geo"] = resp["geo"]
    if resp.get("upsell"):
        result["upsell"] = resp["upsell"]

    result["summary_text"] = _summary_text(result)
    return result


def _summary_text(r: dict[str, Any]) -> str:
    en = r.get("lang") == "en"
    lines: list[str] = []
    head = f"{r['url']} — health {r.get('health')}/100"
    if r.get("grade"):
        head += f" ({r['grade']})"
    lines.append(head)

    s = r["summary"]
    if en:
        lines.append(
            f"{s['passed']} passed · {s['warnings']} warnings · {s['critical']} critical "
            f"· {s['skipped']} n/a (plan: {r['plan']})"
        )
    else:
        lines.append(
            f"{s['passed']} ок · {s['warnings']} предупреждений · {s['critical']} критичных "
            f"· {s['skipped']} н/д (тариф: {r['plan']})"
        )

    problems = r.get("problems") or []
    if problems:
        lines.append("")
        lines.append("Problems:" if en else "Проблемы:")
        for c in problems[:15]:
            emoji = _STATUS_EMOJI.get(c.get("status", ""), "•")
            lines.append(f"  {emoji} [{c.get('category')}] {c.get('title')}")
        if len(problems) > 15:
            more = len(problems) - 15
            lines.append(f"  … +{more} more" if en else f"  … ещё {more}")

    if r.get("upsell"):
        lines.append("")
        lines.append(r["upsell"])
    return "\n".join(lines)


def format_checks(resp: dict[str, Any]) -> dict[str, Any]:
    """Реестр проверок /checks → компактная структура + summary_text."""
    en = resp.get("lang") == "en"
    categories = resp.get("categories") or []
    result: dict[str, Any] = {
        "lang": resp.get("lang", "ru"),
        "total": resp.get("total", 0),
        "free_count": resp.get("free_count", 0),
        "pro_count": resp.get("pro_count", 0),
        "categories": categories,
    }
    lines: list[str] = []
    if en:
        lines.append(
            f"{result['total']} checks: {result['free_count']} free · {result['pro_count']} PRO"
        )
    else:
        lines.append(
            f"{result['total']} проверок: {result['free_count']} free · {result['pro_count']} PRO"
        )
    for cat in categories:
        lines.append("")
        lines.append(
            f"{cat.get('label')} — {cat.get('free_count', 0)} free / {cat.get('pro_count', 0)} PRO"
        )
        for c in cat.get("checks", []):
            badge = "PRO" if c.get("tier") == "pro" else "free"
            lines.append(f"  [{badge}] {c.get('title')}")
    result["summary_text"] = "\n".join(lines)
    return result


def format_explain(resp: dict[str, Any], *, lang: str = "ru") -> dict[str, Any]:
    """Ответ /checks/{id} → структура + summary_text (why/fix)."""
    en = lang == "en"
    result = dict(resp)
    lines: list[str] = []
    if not resp.get("found"):
        cid = resp.get("id")
        lines.append(
            f"Unknown check: {cid}" if en else f"Неизвестная проверка: {cid}"
        )
        lines.append(
            "Use list_checks to see valid ids." if en else "Список id — в list_checks."
        )
        result["summary_text"] = "\n".join(lines)
        return result
    badge = "PRO" if resp.get("tier") == "pro" else "free"
    lines.append(f"[{badge}] [{resp.get('label')}] {resp.get('title')}")
    why = resp.get("why")
    fix = resp.get("fix")
    if why:
        lines.append("")
        lines.append(("Why it matters:" if en else "Почему важно:"))
        lines.append(f"  {why}")
    if fix:
        lines.append("")
        lines.append(("How to fix:" if en else "Как исправить:"))
        lines.append(f"  {fix}")
    # advice_lang честно сообщает язык развёрнутых текстов (пока всегда ru).
    if en and resp.get("advice_lang") == "ru" and (why or fix):
        lines.append("")
        lines.append("(detailed advice currently in Russian)")
    result["summary_text"] = "\n".join(lines)
    return result


def format_sitemap(resp: dict[str, Any], *, lang: str = "ru") -> dict[str, Any]:
    """Ответ /tools/sitemap → структура + summary_text."""
    en = lang == "en"
    result = dict(resp)
    lines: list[str] = []
    fmt = resp.get("format")
    if not resp.get("found"):
        lines.append("sitemap: " + ("not found / unreadable ❌" if en else "не найден / не читается ❌"))
    elif fmt == "sitemapindex":
        n = resp.get("sitemap_count", 0)
        lines.append(
            f"sitemap index ✅ — {n} child sitemap(s)" if en else f"sitemap-индекс ✅ — {n} под-карт"
        )
    elif fmt == "urlset":
        n = resp.get("url_count", 0)
        lines.append(f"sitemap ✅ — {n} URL(s)" if en else f"sitemap ✅ — {n} URL")
    issues = resp.get("issues") or []
    if issues:
        lines.append("")
        lines.append("Issues:" if en else "Замечания:")
        for it in issues:
            mark = {"fail": "❌", "warn": "⚠️"}.get(it.get("severity"), "•")
            lines.append(f"  {mark} {it.get('message')}")
    result["summary_text"] = "\n".join(lines)
    return result


def format_jsonld(resp: dict[str, Any], *, lang: str = "ru") -> dict[str, Any]:
    """Ответ /tools/jsonld → структура + summary_text (готовый <script>)."""
    en = lang == "en"
    result = dict(resp)
    lines: list[str] = []
    issues = resp.get("issues") or []
    fails = [it for it in issues if it.get("severity") == "fail"]
    if resp.get("jsonld") is None:
        lines.append("JSON-LD: " + ("invalid type ❌" if en else "неизвестный тип ❌"))
    elif fails:
        lines.append("JSON-LD: " + ("generated, but incomplete ⚠️" if en else "сгенерирован, но неполный ⚠️"))
    else:
        lines.append("JSON-LD ✅")
    if issues:
        for it in issues:
            mark = {"fail": "❌", "warn": "⚠️"}.get(it.get("severity"), "•")
            lines.append(f"  {mark} {it.get('message')}")
    if resp.get("script"):
        lines.append("")
        lines.append(resp["script"])
    result["summary_text"] = "\n".join(lines)
    return result


def format_meta(resp: dict[str, Any], *, lang: str = "ru") -> dict[str, Any]:
    """Ответ /tools/meta → структура + summary_text (готовый <head>-блок)."""
    en = lang == "en"
    result = dict(resp)
    lines: list[str] = []
    checks = resp.get("checks") or []
    if checks:
        lines.append("Validation:" if en else "Проверка:")
        for c in checks:
            mark = {"fail": "❌", "warn": "⚠️", "pass": "✅"}.get(c.get("status"), "•")
            lines.append(f"  {mark} {c.get('message')}")
    if resp.get("html_head"):
        lines.append("")
        lines.append(resp["html_head"])
    result["summary_text"] = "\n".join(lines)
    return result


def format_robots(resp: dict[str, Any], *, lang: str = "ru") -> dict[str, Any]:
    """Ответ /tools/robots → структура + читабельный summary_text."""
    en = lang == "en"
    result = dict(resp)
    issues = resp.get("issues") or []
    lines: list[str] = []
    verdict_ok = resp.get("valid")
    if en:
        lines.append("robots.txt: " + ("valid ✅" if verdict_ok else "has critical errors ❌"))
    else:
        lines.append("robots.txt: " + ("валиден ✅" if verdict_ok else "есть критичные ошибки ❌"))

    sitemaps = resp.get("sitemaps") or []
    uas = resp.get("user_agents") or []
    if en:
        lines.append(f"{len(uas)} user-agent(s) · {resp.get('rules_count', 0)} rules · {len(sitemaps)} sitemap(s)")
    else:
        lines.append(f"{len(uas)} user-agent · {resp.get('rules_count', 0)} правил · {len(sitemaps)} sitemap")

    if issues:
        lines.append("")
        lines.append("Issues:" if en else "Замечания:")
        for it in issues:
            mark = {"fail": "❌", "warn": "⚠️"}.get(it.get("severity"), "•")
            lines.append(f"  {mark} {it.get('message')}")
    result["summary_text"] = "\n".join(lines)
    return result
