"""Конфигурация клиента из переменных окружения.

Все настройки — через env, чтобы клиент оставался stateless и тонким:
    DETAILWEB_API_BASE   — базовый URL бэкенда (default: публичный прод).
    DETAILWEB_API_KEY    — опц. ключ PRO+ и выше (формат dwa_...). Без него или на Free/PRO — free-режим.
    DETAILWEB_TIMEOUT     — таймаут HTTP в секундах (default 60).
    DETAILWEB_LANG        — язык заголовков по умолчанию: ru | en (default ru).
"""

from __future__ import annotations

import os
from dataclasses import dataclass

DEFAULT_API_BASE = "https://api.detailweb.ru"
DEFAULT_TIMEOUT = 60.0
DEFAULT_LANG = "ru"


@dataclass(frozen=True)
class Settings:
    api_base: str
    api_key: str | None
    timeout: float
    lang: str

    @classmethod
    def from_env(cls) -> "Settings":
        base = (os.environ.get("DETAILWEB_API_BASE") or DEFAULT_API_BASE).rstrip("/")
        key = os.environ.get("DETAILWEB_API_KEY") or None
        try:
            timeout = float(os.environ.get("DETAILWEB_TIMEOUT") or DEFAULT_TIMEOUT)
        except ValueError:
            timeout = DEFAULT_TIMEOUT
        lang = (os.environ.get("DETAILWEB_LANG") or DEFAULT_LANG).strip().lower()
        if lang not in ("ru", "en"):
            lang = DEFAULT_LANG
        return cls(api_base=base, api_key=key, timeout=timeout, lang=lang)

    @property
    def has_key(self) -> bool:
        return bool(self.api_key)
