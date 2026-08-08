"""Toutiao (头条号) platform adapter — placeholder.

Not yet implemented. 头条号 has no public publish API; full automation requires
Playwright + 头条号 backend browser automation, which is fragile and out of
scope for phase 1. When implemented, this module will:

  - Drive a headless Chromium to log into mp.toutiao.com
  - Use the 头条号 article editor (likely via background page)
  - Upload cover + inline images via the editor's UI
  - Click 发布 to push the article

For now, importing this module raises NotImplementedError so the CLI factory
can detect "platform exists but not ready" and surface a friendly error.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

from .base import BasePlatform, PlatformError


class ToutiaoNotImplementedError(PlatformError):
    """Raised when the user attempts to publish to Toutiao before it's wired up."""


class ToutiaoPlatform(BasePlatform):
    name = "toutiao"

    def __init__(self, *args: Any, **kwargs: Any) -> None:  # noqa: D401 - simple stub
        raise ToutiaoNotImplementedError(
            "头条号 (Toutiao) 适配器尚未实现。"
            "Phase 2: Playwright + 头条号后台浏览器自动化。"
            "追踪：https://github.com/KyleSKing/chirp-gzhpub/issues"
        )

    def upload_thumb(self, file_path: Path) -> str:  # pragma: no cover - constructor raises
        raise ToutiaoNotImplementedError("Toutiao adapter not implemented")

    def upload_image(self, file_path: Path) -> str:  # pragma: no cover - constructor raises
        raise ToutiaoNotImplementedError("Toutiao adapter not implemented")

    def publish_draft(self, article: dict) -> str:  # pragma: no cover - constructor raises
        raise ToutiaoNotImplementedError("Toutiao adapter not implemented")
