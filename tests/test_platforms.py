"""Tests for chirp_gzhpub.platforms — the registry and base class."""
from __future__ import annotations

import pytest

from chirp_gzhpub.platforms import (
    AVAILABLE_PLATFORMS,
    PlatformError,
    WeChatPlatform,
    get_platform,
)


def test_registry_includes_wechat_mp() -> None:
    assert "wechat_mp" in AVAILABLE_PLATFORMS


def test_toutiao_not_registered() -> None:
    """Toutiao is intentionally absent (abandoned, see README)."""
    assert "toutiao" not in AVAILABLE_PLATFORMS


def test_get_platform_returns_wechat_mp_instance() -> None:
    p = get_platform("wechat_mp", app_id="x", app_secret="y")
    assert isinstance(p, WeChatPlatform)
    assert p.name == "wechat_mp"


def test_get_platform_unknown_name_raises_value_error() -> None:
    with pytest.raises(ValueError, match="Unknown platform"):
        get_platform("weibo")


def test_all_registered_platforms_subclass_base() -> None:
    """The factory only accepts BasePlatform subclasses."""
    for name, cls in AVAILABLE_PLATFORMS.items():
        assert hasattr(cls, "name")
        assert hasattr(cls, "upload_thumb")
        assert hasattr(cls, "upload_image")
        assert hasattr(cls, "publish_draft")
        assert name == cls.name, f"name mismatch for {cls}"


def test_platform_error_is_exception() -> None:
    assert issubclass(PlatformError, Exception)
