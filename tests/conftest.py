"""Общие фикстуры тестов."""

from __future__ import annotations

from typing import Any

import pytest


@pytest.fixture()
def free_response() -> dict[str, Any]:
    """Типовой free-ответ /audit (tier-gated, только free-проверки)."""
    return {
        "url": "https://example.com",
        "score": 18,
        "health": 82,
        "grade": "B",
        "grade_label": "Хорошо",
        "issues": ["Нет meta-description", "Нет HSTS"],
        "signals": {},
        "audited_at": "2026-06-23T00:00:00Z",
        "render_seconds": 1.2,
        "request_id": "req-1",
        "plan": "free",
        "lang": "ru",
        "depth_used": 1,
        "checks": [
            {"id": "https", "category": "security", "tier": "free", "status": "pass", "title": "HTTPS / SSL"},
            {"id": "hsts", "category": "security", "tier": "free", "status": "fail", "title": "HSTS"},
            {"id": "description", "category": "seo", "tier": "free", "status": "warn", "title": "Meta description"},
        ],
        "summary": {
            "shown": 3,
            "passed": 1,
            "warnings": 1,
            "critical": 1,
            "skipped": 0,
            "pro_hidden": 40,
            "pro_problems_hidden": 7,
        },
        "geo": None,
        "upsell": "Free-результат (single-page, базовые проверки). Ещё 7 проблем(ы) — в PRO-проверках.",
    }


@pytest.fixture()
def pro_response(free_response: dict[str, Any]) -> dict[str, Any]:
    r = dict(free_response)
    r["plan"] = "pro"
    r["depth_used"] = 2
    r["upsell"] = None
    r["geo"] = {"score": 64, "ai_crawlers_blocked": ["GPTBot"], "has_llmstxt": False}
    r["summary"] = {**free_response["summary"], "pro_hidden": 0, "pro_problems_hidden": 0}
    return r
