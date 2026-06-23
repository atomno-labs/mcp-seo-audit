"""Тесты presentation-слоя (без сети)."""

from __future__ import annotations

from atomno_mcp_seo_audit.formatting import (
    format_audit,
    format_checks,
    format_diff,
    format_explain,
    format_jsonld,
    format_meta,
    format_robots,
    format_sitemap,
)


def test_format_free_extracts_problems_and_summary(free_response):
    out = format_audit(free_response)
    assert out["plan"] == "free"
    assert out["health"] == 82
    assert out["grade"] == "B"
    # problems = только warn/fail.
    assert {p["id"] for p in out["problems"]} == {"hsts", "description"}
    assert out["summary"]["pro_problems_hidden"] == 7
    assert "geo" not in out  # free → geo=None не пробрасывается
    assert out["upsell"]
    assert "health 82/100" in out["summary_text"]
    assert "HSTS" in out["summary_text"]


def test_format_pro_includes_geo_no_upsell(pro_response):
    out = format_audit(pro_response)
    assert out["plan"] == "pro"
    assert out["geo"]["score"] == 64
    assert "upsell" not in out
    assert out["summary"]["pro_checks_hidden"] == 0


def test_summary_text_en(free_response):
    free_response["lang"] = "en"
    out = format_audit(free_response)
    assert "passed" in out["summary_text"]
    assert "Problems:" in out["summary_text"]


def test_format_checks_summary_text():
    resp = {
        "lang": "ru",
        "total": 3,
        "free_count": 1,
        "pro_count": 2,
        "categories": [
            {
                "category": "security",
                "label": "Безопасность",
                "free_count": 1,
                "pro_count": 1,
                "checks": [
                    {"id": "https", "tier": "free", "title": "HTTPS"},
                    {"id": "hsts", "tier": "pro", "title": "HSTS"},
                ],
            },
            {
                "category": "geo",
                "label": "GEO",
                "free_count": 0,
                "pro_count": 1,
                "checks": [{"id": "geo_llms", "tier": "pro", "title": "llms.txt"}],
            },
        ],
    }
    out = format_checks(resp)
    assert out["total"] == 3
    assert "1 free" in out["summary_text"]
    assert "[PRO] HSTS" in out["summary_text"]
    assert "Безопасность" in out["summary_text"]


def test_format_explain_found():
    resp = {
        "id": "hsts",
        "found": True,
        "lang": "ru",
        "category": "security",
        "label": "Безопасность",
        "tier": "free",
        "title": "HSTS",
        "why": "Защищает от downgrade.",
        "fix": "Добавьте Strict-Transport-Security.",
        "advice_lang": "ru",
    }
    out = format_explain(resp, lang="ru")
    assert "[free] [Безопасность] HSTS" in out["summary_text"]
    assert "Почему важно:" in out["summary_text"]
    assert "Как исправить:" in out["summary_text"]


def test_format_explain_en_notes_ru_advice():
    resp = {
        "id": "hsts",
        "found": True,
        "lang": "en",
        "category": "security",
        "label": "Security",
        "tier": "free",
        "title": "HSTS",
        "why": "Protects from downgrade.",
        "fix": "Add header.",
        "advice_lang": "ru",
    }
    out = format_explain(resp, lang="en")
    assert "Why it matters:" in out["summary_text"]
    assert "How to fix:" in out["summary_text"]
    assert "Russian" in out["summary_text"]


def test_format_explain_not_found():
    out = format_explain({"id": "zzz", "found": False, "lang": "ru"}, lang="ru")
    assert "Неизвестная проверка: zzz" in out["summary_text"]


def test_format_diff_unavailable_shows_upsell():
    resp = {"url": "https://x.ru", "lang": "ru", "available": False, "upsell": "Нужен PRO-ключ"}
    out = format_diff(resp)
    assert "Нужен PRO-ключ" in out["summary_text"]


def test_format_diff_first_run():
    resp = {
        "url": "https://x.ru", "lang": "ru", "available": True, "first_run": True,
        "current": {"health": 90, "grade": "A", "score": 10},
        "message": "Сохранил базовую точку — сравнивать пока не с чем.",
    }
    out = format_diff(resp)
    assert "health 90/100" in out["summary_text"]
    assert "базовую точку" in out["summary_text"]


def test_format_diff_with_changes():
    resp = {
        "url": "https://x.ru", "lang": "ru", "available": True, "first_run": False,
        "current": {"health": 80, "score": 20}, "previous": {"health": 90, "score": 10},
        "score_delta": 10, "health_delta": -10,
        "worsened": [{"id": "hsts", "category": "security", "title": "HSTS", "from": "pass", "to": "fail"}],
        "improved": [{"id": "title", "category": "seo", "title": "Title", "from": "warn", "to": "pass"}],
        "unchanged": 20, "message": "С прошлого прогона: 1 проверок хуже, 1 лучше.",
    }
    out = format_diff(resp)
    txt = out["summary_text"]
    assert "90 → 80" in txt
    assert "Стало хуже:" in txt and "HSTS" in txt
    assert "Стало лучше:" in txt and "Title" in txt


def test_format_diff_en_no_changes():
    resp = {
        "url": "https://x.ru", "lang": "en", "available": True, "first_run": False,
        "current": {"health": 90}, "previous": {"health": 90},
        "score_delta": 0, "health_delta": 0, "worsened": [], "improved": [], "unchanged": 30,
        "message": "No changes since the previous run.",
    }
    out = format_diff(resp, lang="en")
    assert "No changes" in out["summary_text"]


def test_format_robots_valid_and_issues():
    resp = {
        "valid": False,
        "issues": [
            {"severity": "fail", "message": "no User-agent"},
            {"severity": "warn", "message": "no Sitemap"},
        ],
        "sitemaps": [],
        "user_agents": [],
        "rules_count": 0,
        "ai_crawlers_blocked": ["GPTBot"],
        "blocks_assets": False,
        "blocks_assets_examples": [],
        "disallow_all_star": False,
    }
    out = format_robots(resp, lang="ru")
    assert out["valid"] is False
    assert "критичные ошибки" in out["summary_text"]
    assert "❌ no User-agent" in out["summary_text"]
    assert "⚠️ no Sitemap" in out["summary_text"]


def test_format_robots_en():
    resp = {"valid": True, "issues": [], "sitemaps": ["https://x/s.xml"], "user_agents": ["*"], "rules_count": 1}
    out = format_robots(resp, lang="en")
    assert "valid ✅" in out["summary_text"]
    assert "1 sitemap(s)" in out["summary_text"]


def test_format_sitemap_urlset():
    resp = {"found": True, "format": "urlset", "url_count": 12, "sitemap_count": 0, "issues": []}
    out = format_sitemap(resp, lang="en")
    assert "12 URL(s)" in out["summary_text"]


def test_format_sitemap_not_found_with_issue():
    resp = {"found": False, "format": None, "issues": [{"severity": "fail", "message": "HTTP 404"}]}
    out = format_sitemap(resp, lang="ru")
    assert "не найден" in out["summary_text"]
    assert "❌ HTTP 404" in out["summary_text"]


def test_format_jsonld_includes_script():
    resp = {"jsonld": {"@type": "Organization"}, "script": "<script>{}</script>", "issues": []}
    out = format_jsonld(resp, lang="en")
    assert "JSON-LD ✅" in out["summary_text"]
    assert "<script>" in out["summary_text"]


def test_format_jsonld_unknown_type():
    resp = {"jsonld": None, "script": "", "issues": [{"severity": "fail", "message": "Unknown type"}]}
    out = format_jsonld(resp, lang="en")
    assert "invalid type" in out["summary_text"]


def test_format_meta_validation_and_head():
    resp = {
        "tags": ["<title>X</title>"],
        "html_head": "<title>X</title>",
        "checks": [{"field": "title", "status": "pass", "message": "ok"}],
    }
    out = format_meta(resp, lang="en")
    assert "✅ ok" in out["summary_text"]
    assert "<title>X</title>" in out["summary_text"]
