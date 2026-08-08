"""Tests for chirp_gzhpub.platforms.wechat_mp — all HTTP calls are mocked."""
from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import pytest
import requests

from chirp_gzhpub.platforms.base import PlatformError
from chirp_gzhpub.platforms.wechat_mp import WeChatError, WeChatPlatform


def _mock_response(json_data: dict, status_code: int = 200) -> MagicMock:
    resp = MagicMock(spec=requests.Response)
    resp.status_code = status_code
    resp.json.return_value = json_data
    return resp


def test_platform_name() -> None:
    assert WeChatPlatform.name == "wechat_mp"


def test_constructor_requires_credentials() -> None:
    with pytest.raises(WeChatError, match="required"):
        WeChatPlatform("", "secret")
    with pytest.raises(WeChatError, match="required"):
        WeChatPlatform("id", "")


def test_get_token_caches_and_reuses() -> None:
    session = MagicMock()
    session.get.return_value = _mock_response(
        {"access_token": "tk_abc", "expires_in": 7200}
    )
    platform = WeChatPlatform("id", "secret", session=session)
    t1 = platform._get_token()  # noqa: SLF001
    t2 = platform._get_token()  # noqa: SLF001
    assert t1 == t2 == "tk_abc"
    assert session.get.call_count == 1


def test_get_token_failure_raises_with_hint() -> None:
    session = MagicMock()
    session.get.return_value = _mock_response(
        {"errcode": 40125, "errmsg": "invalid appsecret"}
    )
    platform = WeChatPlatform("id", "secret", session=session)
    with pytest.raises(WeChatError, match="IP whitelist"):
        platform._get_token()  # noqa: SLF001


def test_get_token_refreshes_after_expiry() -> None:
    session = MagicMock()
    session.get.side_effect = [
        _mock_response({"access_token": "tk_first", "expires_in": 1}),
        _mock_response({"access_token": "tk_second", "expires_in": 7200}),
    ]
    platform = WeChatPlatform("id", "secret", session=session, base_url="https://x")
    assert platform._get_token() == "tk_first"  # noqa: SLF001
    platform._token_expires_at = 0  # noqa: SLF001
    assert platform._get_token() == "tk_second"  # noqa: SLF001
    assert session.get.call_count == 2


def test_upload_thumb_returns_media_id(tmp_path: Path) -> None:
    img = tmp_path / "cover.png"
    img.write_bytes(b"\x89PNG\r\n\x1a\n" + b"x" * 100)
    session = MagicMock()
    session.get.return_value = _mock_response(
        {"access_token": "tk", "expires_in": 7200}
    )
    session.post.return_value = _mock_response({"media_id": "thumb_1"})
    platform = WeChatPlatform("id", "secret", session=session)
    media_id = platform.upload_thumb(img)
    assert media_id == "thumb_1"
    assert session.post.call_args[0][0].endswith("/material/add_material")


def test_upload_thumb_rejects_missing_file(tmp_path: Path) -> None:
    platform = WeChatPlatform("id", "secret", session=MagicMock())
    with pytest.raises(WeChatError, match="not found"):
        platform.upload_thumb(tmp_path / "missing.png")


def test_upload_thumb_rejects_oversized(tmp_path: Path) -> None:
    big = tmp_path / "big.jpg"
    big.write_bytes(b"x" * (3 * 1024 * 1024))
    platform = WeChatPlatform("id", "secret", session=MagicMock())
    with pytest.raises(WeChatError, match="too large"):
        platform.upload_thumb(big)


def test_upload_image_returns_url(tmp_path: Path) -> None:
    img = tmp_path / "img.png"
    img.write_bytes(b"\x89PNG\r\n\x1a\n" + b"x" * 100)
    session = MagicMock()
    session.get.return_value = _mock_response(
        {"access_token": "tk", "expires_in": 7200}
    )
    session.post.return_value = _mock_response(
        {"media_id": "media_1", "url": "https://mmbiz.qpic.cn/x.png"}
    )
    platform = WeChatPlatform("id", "secret", session=session)
    url = platform.upload_image(img)
    assert url == "https://mmbiz.qpic.cn/x.png"
    assert session.post.call_args[0][0].endswith("/material/add_material")


def test_upload_image_rejects_missing_file(tmp_path: Path) -> None:
    platform = WeChatPlatform("id", "secret", session=MagicMock())
    with pytest.raises(WeChatError, match="not found"):
        platform.upload_image(tmp_path / "missing.png")


def test_publish_draft_happy_path() -> None:
    session = MagicMock()
    session.get.return_value = _mock_response(
        {"access_token": "tk", "expires_in": 7200}
    )
    session.request.return_value = _mock_response({"media_id": "draft_1"})
    platform = WeChatPlatform("id", "secret", session=session)
    media_id = platform.publish_draft({"title": "t", "content": "<p>x</p>"})
    assert media_id == "draft_1"
    call = session.request.call_args
    assert call[0][0] == "POST"
    assert call[0][1].endswith("/draft/add")
    assert call[1]["json"] == {"articles": [{"title": "t", "content": "<p>x</p>"}]}


def test_publish_draft_retries_after_token_invalid() -> None:
    session = MagicMock()
    session.get.return_value = _mock_response(
        {"access_token": "tk_new", "expires_in": 7200}
    )
    session.request.side_effect = [
        _mock_response({"errcode": 40001, "errmsg": "invalid token"}),
        _mock_response({"media_id": "draft_ok"}),
    ]
    platform = WeChatPlatform("id", "secret", session=session)
    media_id = platform.publish_draft({"title": "t"})
    assert media_id == "draft_ok"
    # token was invalidated after 40001 and re-fetched: 2 get_token() calls total.
    assert session.get.call_count == 2


def test_publish_draft_raises_on_unrecoverable_error() -> None:
    session = MagicMock()
    session.get.return_value = _mock_response(
        {"access_token": "tk", "expires_in": 7200}
    )
    session.request.return_value = _mock_response(
        {"errcode": 40007, "errmsg": "invalid thumb"}
    )
    platform = WeChatPlatform("id", "secret", session=session)
    with pytest.raises(WeChatError, match="40007"):
        platform.publish_draft({"title": "t"})


def test_wechat_error_is_platform_error() -> None:
    """WeChatError must inherit PlatformError so the CLI can catch both."""
    assert issubclass(WeChatError, PlatformError)
