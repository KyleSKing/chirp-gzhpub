"""Abstract base class for publishing platforms.

Each platform (WeChat MP, Toutiao, Juejin, ...) implements this interface.
The CLI uses the factory in platforms/__init__.py to obtain a concrete
instance by name, then calls only the methods defined here.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path


class PlatformError(Exception):
    """Raised by any platform when an operation fails."""


class BasePlatform(ABC):
    """Common interface every publishing platform must implement."""

    name: str  # subclasses set this, e.g. "wechat_mp"

    @abstractmethod
    def upload_thumb(self, file_path: Path) -> str:
        """Upload a thumbnail / cover image.

        Returns a platform-specific ID (e.g. WeChat `media_id`) used to set
        `thumb_media_id` on the draft.
        """

    @abstractmethod
    def upload_image(self, file_path: Path) -> str:
        """Upload an inline image for use in the article body.

        Returns the URL to embed as `<img src=...>`.
        """

    @abstractmethod
    def publish_draft(self, article: dict) -> str:
        """Create a draft article on the platform.

        `article` is a platform-shaped dict (title, content, thumb_media_id, ...).
        Returns the platform-specific draft id.
        """
