"""Тесты конфигурации из env."""

from __future__ import annotations

from atomno_mcp_seo_audit.config import DEFAULT_API_BASE, Settings


def test_defaults(monkeypatch):
    for k in ("DETAILWEB_API_BASE", "DETAILWEB_API_KEY", "DETAILWEB_TIMEOUT", "DETAILWEB_LANG"):
        monkeypatch.delenv(k, raising=False)
    s = Settings.from_env()
    assert s.api_base == DEFAULT_API_BASE
    assert s.api_key is None
    assert s.has_key is False
    assert s.lang == "ru"


def test_env_overrides(monkeypatch):
    monkeypatch.setenv("DETAILWEB_API_BASE", "http://localhost:8000/")
    monkeypatch.setenv("DETAILWEB_API_KEY", "dwa_x")
    monkeypatch.setenv("DETAILWEB_LANG", "EN")
    monkeypatch.setenv("DETAILWEB_TIMEOUT", "12.5")
    s = Settings.from_env()
    assert s.api_base == "http://localhost:8000"  # trailing slash stripped
    assert s.has_key is True
    assert s.lang == "en"
    assert s.timeout == 12.5


def test_bad_lang_falls_back(monkeypatch):
    monkeypatch.setenv("DETAILWEB_LANG", "fr")
    assert Settings.from_env().lang == "ru"
