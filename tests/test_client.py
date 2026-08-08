"""Tests for chirp_gzhpub.client — all HTTP calls are mocked."""
from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import pytest
import requests

from chirp_gzhpub.client import WeChatClient, WeChatError


def _mock_response(json_data: dict, status_code: int = 200) -> MagicMock:
    resp = MagicMock(spec=requests.Response)
    resp.status_code = status_code
    resp.json.return_value = json_data
    return resp


def test_get_token_caches_and_reuses() -> None:
    session = MagicMock()
    session.get.return_value = _mock_response(
        {"access_token": "tk_abc", "expires_in": 7200}
    )
    client = WeChatClient("id", "secret", session=session)
    t1 = client.get_token()
    t2 = client.get_token()
    assert t1 == t2 == "tk_abc"
    # second call should NOT hit the API again
    assert session.get.call_count == 1


def test_get_token_failure_raises_with_hint() -> None:
    session = MagicMock()
    session.get.return_value = _mock_response({"errcode": 40125, "errmsg": "invalid appsecret"})
    client = WeChatClient("id", "secret", session=session)
    with pytest.raises(WeChatError, match="IP whitelist"):
        client.get_token()


def test_get_token_refreshes_after_expiry() -> None:
    session = MagicMock()
    session.get.side_effect = [
        _mock_response({"access_token": "tk_first", "expires_in": 1}),
        _mock_response({"access_token": "tk_second", "expires_in": 7200}),
    ]
    client = WeChatClient("id", "secret", session=session, base_url="https://x")
    assert client.get_token() == "tk_first"
    # Force expiry by setting expires_at to past
    client._token_expires_at = 0  # noqa: SLF001
    assert client.get_token() == "tk_second"
    assert session.get.call_count == 2


def test_upload_image_returns_url(tmp_path: Path) -> None:
    img = tmp_path / "img.png"
    img.write_bytes(b"\x89PNG\r\n\x1a\n" + b"x" * 100)
    session = MagicMock()
    # First call: token
    session.get.return_value = _mock_response(
        {"access_token": "tk", "expires_in": 7200}
    )
    # Second call: upload
    session.post.return_value = _mock_response(
        {"media_id": "media_1", "url": "https://mmbiz.qpic.cn/x.png"}
    )
    client = WeChatClient("id", "secret", session=session)
    url = client.upload_image(img)
    assert url == "https://mmbiz.qpic.cn/x.png"
    assert session.post.call_args[0][0].endswith("/material/add_material")


def test_upload_image_rejects_missing_file(tmp_path: Path) -> None:
    client = WeChatClient("id", "secret", session=MagicMock())
    with pytest.raises(WeChatError, match="not found"):
        client.upload_image(tmp_path / "missing.png")


def test_upload_image_rejects_oversized(tmp_path: Path) -> None:
    big = tmp_path / "big.jpg"
    big.write_bytes(b"x" * (3 * 1024 * 1024))  # 3MB
    client = WeChatClient("id", "secret", session=MagicMock())
    with pytest.raises(WeChatError, match="too large"):
        client.upload_image(big)


def test_add_draft_happy_path() -> None:
    session = MagicMock()
    session.get.return_value = _mock_response(
        {"access_token": "tk", "expires_in": 7200}
    )
    session.request.return_value = _mock_response({"media_id": "draft_1"})
    client = WeChatClient("id", "secret", session=session)
    media_id = client.add_draft({"title": "t", "content": "<p>x</p>"})
    assert media_id == "draft_1"
    call = session.request.call_args
    assert call[0][0] == "POST"
    assert call[0][1].endswith("/draft/add")
    assert call[1]["json"] == {"articles": [{"title": "t", "content": "<p>x</p>"}]}


def test_add_draft_retries_after_token_invalid() -> None:
    session = MagicMock()
    session.get.return_value = _mock_response(
        {"access_token": "tk_new", "expires_in": 7200}
    )
    # First draft call: 40001, second: success
    session.request.side_effect = [
        _mock_response({"errcode": 40001, "errmsg": "invalid token"}),
        _mock_response({"media_id": "draft_ok"}),
    ]
    client = WeChatClient("id", "secret", session=session)
    media_id = client.add_draft({"title": "t"})
    assert media_id == "draft_ok"
    # token was invalidated after 40001 and re-fetched: 2 get_token() calls total.
    # Critically, the actual HTTP call to /token happened twice (first + refresh),
    # not three times — proving the retry path short-circuits.
    assert session.get.call_count == 2


def test_add_draft_raises_on_unrecoverable_error() -> None:
    session = MagicMock()
    session.get.return_value = _mock_response(
        {"access_token": "tk", "expires_in": 7200}
    )
    session.request.return_value = _mock_response(
        {"errcode": 40007, "errmsg": "invalid thumb"}
    )
    client = WeChatClient("id", "secret", session=session)
    with pytest.raises(WeChatError, match="40007"):
        client.add_draft({"title": "t"})


def test_client_requires_credentials() -> None:
    with pytest.raises(WeChatError, match="required"):
        WeChatClient("", "secret")
    with pytest.raises(WeChatError, match="required"):
        WeChatClient("id", "")
