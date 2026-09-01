"""HTTP-клиент к бэкенду detail.web.

Тонкая обёртка над httpx: один общий AsyncClient, опц. Bearer-ключ,
маппинг ошибок в SeoAuditError. Никакой логики аудита — только транспорт.
"""

from __future__ import annotations

from typing import Any

import httpx

from . import __version__
from .config import Settings
from .errors import BackendError, BackendUnavailable

_USER_AGENT = f"atomno-mcp-seo-audit/{__version__}"


class DetailWebClient:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        headers = {"User-Agent": _USER_AGENT, "Accept": "application/json"}
        if settings.api_key:
            headers["Authorization"] = f"Bearer {settings.api_key}"
        self._client = httpx.AsyncClient(
            base_url=settings.api_base,
            timeout=settings.timeout,
            headers=headers,
        )

    async def aclose(self) -> None:
        await self._client.aclose()

    async def _post(self, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        try:
            resp = await self._client.post(path, json=payload)
        except httpx.TimeoutException as exc:  # noqa: PERF203
            raise BackendUnavailable(f"timeout calling {path}") from exc
        except httpx.HTTPError as exc:
            raise BackendUnavailable(f"network error calling {path}: {exc}") from exc
        return self._parse(resp, path)

    async def _get(self, path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        try:
            resp = await self._client.get(path, params=params)
        except httpx.TimeoutException as exc:  # noqa: PERF203
            raise BackendUnavailable(f"timeout calling {path}") from exc
        except httpx.HTTPError as exc:
            raise BackendUnavailable(f"network error calling {path}: {exc}") from exc
        return self._parse(resp, path)

    @staticmethod
    def _parse(resp: httpx.Response, path: str) -> dict[str, Any]:
        if resp.status_code >= 400:
            detail = _extract_detail(resp)
            raise BackendError(resp.status_code, detail)
        try:
            return resp.json()
        except ValueError as exc:
            raise BackendError(resp.status_code, "invalid JSON in response") from exc

    async def audit(self, url: str, *, depth: int = 1, lang: str | None = None) -> dict[str, Any]:
        """POST /audit. Без ключа или Free/PRO — free; ключ PRO+ и выше — pro (GEO + deep-crawl)."""
        payload: dict[str, Any] = {
            "url": url,
            "depth": depth,
            "lang": lang or self._settings.lang,
        }
        return await self._post("/audit", payload)

    async def audit_diff(self, url: str, *, lang: str | None = None) -> dict[str, Any]:
        """POST /audit/diff — что изменилось с прошлой проверки (stateful, PRO+)."""
        payload = {"url": url, "lang": lang or self._settings.lang}
        return await self._post("/audit/diff", payload)

    async def list_checks(self, *, lang: str | None = None) -> dict[str, Any]:
        """GET /checks — реестр проверок движка (free/pro, по категориям)."""
        return await self._get("/checks", params={"lang": lang or self._settings.lang})

    async def explain_issue(self, check_id: str, *, lang: str | None = None) -> dict[str, Any]:
        """GET /checks/{check_id} — подробное объяснение проверки (why/fix)."""
        return await self._get(
            f"/checks/{check_id}", params={"lang": lang or self._settings.lang}
        )

    async def validate_robots(self, content: str, *, lang: str | None = None) -> dict[str, Any]:
        """POST /tools/robots — валидация содержимого robots.txt."""
        payload = {"content": content, "lang": lang or self._settings.lang}
        return await self._post("/tools/robots", payload)

    async def check_sitemap(self, url: str, *, lang: str | None = None) -> dict[str, Any]:
        """POST /tools/sitemap — фетч и разбор sitemap по URL."""
        payload = {"url": url, "lang": lang or self._settings.lang}
        return await self._post("/tools/sitemap", payload)

    async def build_jsonld(
        self, schema_type: str, fields: dict[str, Any], *, lang: str | None = None
    ) -> dict[str, Any]:
        """POST /tools/jsonld — генерация JSON-LD schema.org."""
        payload = {"type": schema_type, "fields": fields, "lang": lang or self._settings.lang}
        return await self._post("/tools/jsonld", payload)

    async def build_meta(self, fields: dict[str, Any], *, lang: str | None = None) -> dict[str, Any]:
        """POST /tools/meta — генерация meta-тегов."""
        payload = {"fields": fields, "lang": lang or self._settings.lang}
        return await self._post("/tools/meta", payload)


def _extract_detail(resp: httpx.Response) -> str:
    try:
        body = resp.json()
    except ValueError:
        return resp.text[:300] or resp.reason_phrase
    if isinstance(body, dict):
        for key in ("detail", "message", "error"):
            if body.get(key):
                return str(body[key])
    return str(body)[:300]
