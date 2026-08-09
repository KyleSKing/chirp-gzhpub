"""Platform registry: name → concrete BasePlatform class.

The CLI calls `get_platform(name, **kwargs)` and only talks to the returned
object through the BasePlatform interface. Adding a new platform means:

  1. Create `platforms/<name>.py` with a `<Name>Platform(BasePlatform)` class
  2. Add a branch in `get_platform()` below
  3. Add an entry to `AVAILABLE_PLATFORMS` (used by `--platform` help text)

Nothing else in the CLI or core code needs to change.
"""
from __future__ import annotations

from typing import Any

from .base import BasePlatform, PlatformError
from .wechat_mp import WeChatError, WeChatPlatform

AVAILABLE_PLATFORMS: dict[str, type[BasePlatform]] = {
    "wechat_mp": WeChatPlatform,
}


def get_platform(name: str, **kwargs: Any) -> BasePlatform:
    """Instantiate a platform by name. Pass platform-specific kwargs through.

    Raises:
        ValueError: unknown platform name.
    """
    cls = AVAILABLE_PLATFORMS.get(name)
    if cls is None:
        available = ", ".join(sorted(AVAILABLE_PLATFORMS))
        raise ValueError(f"Unknown platform: {name!r}. Available: {available}")
    return cls(**kwargs)


__all__ = [
    "AVAILABLE_PLATFORMS",
    "BasePlatform",
    "PlatformError",
    "WeChatError",
    "WeChatPlatform",
    "get_platform",
]
