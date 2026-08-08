"""WeChat Official Account platform adapter.

Implements the BasePlatform interface against three WeChat endpoints:
  - /cgi-bin/token                          → access_token
  - /cgi-bin/material/add_material          → image upload (media_id + url)
  - /cgi-bin/draft/add                      → create draft (media_id)

Token cache: in-memory, 2h, refresh 60s early.
Error handling: 40001/42001/40014 → re-fetch token and retry once.
                45009/45002       → exponential backoff (rate limit).
                anything else      → raise WeChatError.
"""
from __future__ import annotations

import time
from pathlib import Path
from typing import Any

import requests

from .base import BasePlatform, PlatformError

API_BASE = "https://api.weixin.qq.com/cgi-bin"
TOKEN_TTL_BUFFER_SEC = 60
DEFAULT_MAX_RETRIES = 3


class WeChatError(PlatformError):
    """Raised when a WeChat API call fails unrecoverably."""


class WeChatPlatform(BasePlatform):
    name = "wechat_mp"

    def __init__(
        self,
        app_id: str,
        app_secret: str,
        *,
        max_retries: int = DEFAULT_MAX_RETRIES,
        session: requests.Session | None = None,
        base_url: str = API_BASE,
    ) -> None:
        if not app_id or not app_secret:
            raise WeChatError("app_id and app_secret are required")
        self.app_id = app_id
        self.app_secret = app_secret
        self.max_retries = max_retries
        self.session = session or requests.Session()
        self.base_url = base_url.rstrip("/")
        self._token: str | None = None
        self._token_expires_at: float = 0.0

    # --- BasePlatform ---------------------------------------------------------

    def upload_thumb(self, file_path: Path) -> str:
        file_path = Path(file_path)
        if not file_path.is_file():
            raise WeChatError(f"Thumbnail not found: {file_path}")
        if file_path.stat().st_size > 2 * 1024 * 1024:
            raise WeChatError(f"Thumbnail too large (>2MB): {file_path}")

        mime = _guess_mime(file_path)
        with file_path.open("rb") as f:
            resp = self.session.post(
                f"{self.base_url}/material/add_material",
                params={"access_token": self._get_token(), "type": "image"},
                files={"media": (file_path.name, f, mime)},
                timeout=60,
            )
        data = resp.json()
        if "media_id" not in data:
            raise WeChatError(
                f"Thumbnail upload failed (errcode={data.get('errcode')}): {data.get('errmsg')}"
            )
        return data["media_id"]

    def upload_image(self, file_path: Path) -> str:
        file_path = Path(file_path)
        if not file_path.is_file():
            raise WeChatError(f"Image not found: {file_path}")
        if file_path.stat().st_size > 2 * 1024 * 1024:
            raise WeChatError(f"Image too large (>2MB): {file_path}")

        mime = _guess_mime(file_path)
        with file_path.open("rb") as f:
            resp = self.session.post(
                f"{self.base_url}/material/add_material",
                params={"access_token": self._get_token(), "type": "image"},
                files={"media": (file_path.name, f, mime)},
                timeout=60,
            )
        data = resp.json()
        if "url" not in data:
            raise WeChatError(
                f"Image upload failed (errcode={data.get('errcode')}): {data.get('errmsg')}"
            )
        return data["url"]

    def publish_draft(self, article: dict[str, Any]) -> str:
        data = self._request_json("POST", "/draft/add", json_body={"articles": [article]})
        if "media_id" not in data:
            raise WeChatError(f"draft/add returned no media_id: {data}")
        return data["media_id"]

    # --- token ----------------------------------------------------------------

    def _get_token(self) -> str:
        now = time.time()
        if self._token and now < self._token_expires_at - TOKEN_TTL_BUFFER_SEC:
            return self._token
        url = f"{self.base_url}/token"
        resp = self.session.get(
            url,
            params={
                "grant_type": "client_credential",
                "appid": self.app_id,
                "secret": self.app_secret,
            },
            timeout=10,
        )
        data = resp.json()
        if "access_token" not in data:
            raise WeChatError(
                f"Failed to get access_token (errcode={data.get('errcode')}): "
                f"{data.get('errmsg')}. Check IP whitelist, AppID, and AppSecret."
            )
        self._token = data["access_token"]
        self._token_expires_at = now + int(data.get("expires_in", 7200))
        return self._token

    def _invalidate_token(self) -> None:
        self._token = None
        self._token_expires_at = 0.0

    # --- internal -------------------------------------------------------------

    def _request_json(
        self,
        method: str,
        path: str,
        *,
        json_body: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        last_err: Exception | None = None
        retried_after_token_refresh = False
        for attempt in range(self.max_retries):
            try:
                resp = self.session.request(
                    method,
                    f"{self.base_url}{path}",
                    params={"access_token": self._get_token()},
                    json=json_body,
                    timeout=30,
                )
                data = resp.json()
            except requests.RequestException as exc:
                last_err = WeChatError(f"Network error: {exc}")
                time.sleep(2**attempt)
                continue

            errcode = data.get("errcode", 0)
            if errcode in (0, None):
                return data

            if errcode in (40001, 42001, 40014) and not retried_after_token_refresh:
                self._invalidate_token()
                retried_after_token_refresh = True
                continue

            if errcode in (45009, 45002):
                time.sleep(2**attempt)
                continue

            raise WeChatError(
                f"WeChat API error {errcode} at {path}: {data.get('errmsg')}"
            )

        raise last_err or WeChatError(f"WeChat API failed after {self.max_retries} retries")


def _guess_mime(file_path: Path) -> str:
    suffix = file_path.suffix.lower()
    if suffix in (".jpg", ".jpeg"):
        return "image/jpeg"
    if suffix == ".png":
        return "image/png"
    if suffix == ".gif":
        return "image/gif"
    if suffix == ".webp":
        return "image/webp"
    return "application/octet-stream"
