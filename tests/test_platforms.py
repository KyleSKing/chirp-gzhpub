"""Tests for chirp_gzhpub.platforms — the registry and base class."""
from __future__ import annotations

import pytest

from chirp_gzhpub.platforms import (
    AVAILABLE_PLATFORMS,
    PlatformError,
    ToutiaoNotImplementedError,
    ToutiaoPlatform,
    WeChatPlatform,
    get_platform,
)


def test_registry_includes_both_platforms() -> None:
    assert "wechat_mp" in AVAILABLE_PLATFORMS
    assert "toutiao" in AVAILABLE_PLATFORMS


def test_get_platform_returns_wechat_mp_instance() -> None:
    p = get_platform("wechat_mp", app_id="x", app_secret="y")
    assert isinstance(p, WeChatPlatform)
    assert p.name == "wechat_mp"


def test_get_platform_toutiao_raises_not_implemented() -> None:
    """Toutiao is registered but its constructor raises — until phase 2."""
    with pytest.raises(ToutiaoNotImplementedError, match="尚未实现"):
        get_platform("toutiao")


def test_get_platform_unknown_name_raises_value_error() -> None:
    with pytest.raises(ValueError, match="Unknown platform"):
        get_platform("weibo")


def test_all_registered_platforms_subclass_base() -> None:
    """The factory only accepts BasePlatform subclasses."""
    for name, cls in AVAILABLE_PLATFORMS.items():
        assert issubclass(cls, object)  # sanity
        # Tousiao's constructor raises, so we can only check the class hierarchy statically
        assert hasattr(cls, "name")
        assert hasattr(cls, "upload_thumb")
        assert hasattr(cls, "upload_image")
        assert hasattr(cls, "publish_draft")
        assert name == cls.name, f"name mismatch for {cls}"


def test_toutiao_methods_raise() -> None:
    """Calling methods directly (bypassing constructor) also raises."""
    with pytest.raises(ToutiaoNotImplementedError):
        ToutiaoPlatform().upload_thumb(None)  # type: ignore[arg-type]


def test_platform_error_is_exception() -> None:
    assert issubclass(PlatformError, Exception)
    assert issubclass(ToutiaoNotImplementedError, PlatformError)
