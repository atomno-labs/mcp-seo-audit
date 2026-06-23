"""Тесты HTTP-клиента (respx-моки бэкенда)."""

from __future__ import annotations

import httpx
import pytest
import respx

from atomno_mcp_seo_audit.client import DetailWebClient
from atomno_mcp_seo_audit.config import Settings
from atomno_mcp_seo_audit.errors import BackendError, BackendUnavailable

BASE = "https://api.test"


def _settings(api_key: str | None = None) -> Settings:
    return Settings(api_base=BASE, api_key=api_key, timeout=5.0, lang="ru")


@respx.mock
async def test_audit_free_posts_expected_payload(free_response):
    route = respx.post(f"{BASE}/audit").mock(return_value=httpx.Response(200, json=free_response))
    client = DetailWebClient(_settings())
    try:
        data = await client.audit("https://example.com", depth=1)
    finally:
        await client.aclose()

    assert data["plan"] == "free"
    sent = route.calls.last.request
    assert b'"url"' in sent.content
    assert b'"lang": "ru"' in sent.content or b'"lang":"ru"' in sent.content
    # без ключа — нет Authorization
    assert "authorization" not in {k.lower() for k in sent.headers}


@respx.mock
async def test_audit_pro_sends_bearer(pro_response):
    route = respx.post(f"{BASE}/audit").mock(return_value=httpx.Response(200, json=pro_response))
    client = DetailWebClient(_settings(api_key="dwa_secret"))
    try:
        data = await client.audit("https://example.com", depth=2)
    finally:
        await client.aclose()

    assert data["plan"] == "pro"
    assert route.calls.last.request.headers["authorization"] == "Bearer dwa_secret"


@respx.mock
async def test_backend_error_maps(free_response):
    respx.post(f"{BASE}/audit").mock(return_value=httpx.Response(422, json={"detail": "bad url"}))
    client = DetailWebClient(_settings())
    try:
        with pytest.raises(BackendError) as ei:
            await client.audit("not-a-url")
    finally:
        await client.aclose()
    assert ei.value.status_code == 422
    assert "bad url" in ei.value.detail


@respx.mock
async def test_network_error_maps():
    respx.post(f"{BASE}/audit").mock(side_effect=httpx.ConnectError("boom"))
    client = DetailWebClient(_settings())
    try:
        with pytest.raises(BackendUnavailable):
            await client.audit("https://example.com")
    finally:
        await client.aclose()


@respx.mock
async def test_list_checks_get_with_lang():
    payload = {"lang": "en", "total": 2, "free_count": 1, "pro_count": 1, "categories": []}
    route = respx.get(f"{BASE}/checks").mock(return_value=httpx.Response(200, json=payload))
    client = DetailWebClient(_settings())
    try:
        data = await client.list_checks(lang="en")
    finally:
        await client.aclose()
    assert data["total"] == 2
    assert route.calls.last.request.url.params["lang"] == "en"


@respx.mock
async def test_explain_issue_get_with_id_and_lang():
    payload = {"id": "hsts", "found": True, "lang": "en", "tier": "free", "title": "HSTS", "why": "w", "fix": "f", "advice_lang": "ru"}
    route = respx.get(f"{BASE}/checks/hsts").mock(return_value=httpx.Response(200, json=payload))
    client = DetailWebClient(_settings())
    try:
        data = await client.explain_issue("hsts", lang="en")
    finally:
        await client.aclose()
    assert data["found"] is True
    assert data["id"] == "hsts"
    assert route.calls.last.request.url.params["lang"] == "en"


@respx.mock
async def test_validate_robots_posts_content():
    payload = {"valid": True, "issues": [], "sitemaps": [], "user_agents": ["*"]}
    route = respx.post(f"{BASE}/tools/robots").mock(return_value=httpx.Response(200, json=payload))
    client = DetailWebClient(_settings())
    try:
        data = await client.validate_robots("User-agent: *\nDisallow:", lang="ru")
    finally:
        await client.aclose()
    assert data["valid"] is True
    assert b'"content"' in route.calls.last.request.content


@respx.mock
async def test_check_sitemap_posts_url():
    payload = {"found": True, "format": "urlset", "url_count": 5, "issues": []}
    route = respx.post(f"{BASE}/tools/sitemap").mock(return_value=httpx.Response(200, json=payload))
    client = DetailWebClient(_settings())
    try:
        data = await client.check_sitemap("https://x.ru/sitemap.xml", lang="en")
    finally:
        await client.aclose()
    assert data["url_count"] == 5
    assert b'"url"' in route.calls.last.request.content


@respx.mock
async def test_build_jsonld_posts_type_and_fields():
    payload = {"jsonld": {"@type": "Organization"}, "script": "<script>", "issues": []}
    route = respx.post(f"{BASE}/tools/jsonld").mock(return_value=httpx.Response(200, json=payload))
    client = DetailWebClient(_settings())
    try:
        data = await client.build_jsonld("Organization", {"name": "Acme"}, lang="ru")
    finally:
        await client.aclose()
    assert data["jsonld"]["@type"] == "Organization"
    body = route.calls.last.request.content
    assert b'"type"' in body and b'"fields"' in body


@respx.mock
async def test_build_meta_posts_fields():
    payload = {"tags": ["<title>X</title>"], "html_head": "<title>X</title>", "checks": []}
    route = respx.post(f"{BASE}/tools/meta").mock(return_value=httpx.Response(200, json=payload))
    client = DetailWebClient(_settings())
    try:
        data = await client.build_meta({"title": "X"}, lang="ru")
    finally:
        await client.aclose()
    assert data["html_head"] == "<title>X</title>"
    assert b'"fields"' in route.calls.last.request.content
