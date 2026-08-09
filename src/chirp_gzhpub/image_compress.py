"""Compress images to fit WeChat's 2MB upload limit.

WeChat's material/add_material rejects images > 2MB. Without compression,
authors must pre-shrink every cover/inline image by hand. This module
provides `compress_for_upload(path)` that returns a path guaranteed to
be under the threshold (with a 200KB buffer for safety).

Behavior:
  - If `src` is already under the threshold, returns it unchanged (no copy).
  - Otherwise compresses to a NEW temp file; the caller MUST delete the
    returned file (e.g. via try/finally) since we don't own the temp dir.
  - Skips GIFs (loses animation) and any other format Pillow can't write
    with quality control — those fail fast with ImageCompressionError.
  - Uses progressive quality reduction (85 → 30) until the file fits.

Note: this module deliberately does NOT import from `platforms.base` to
avoid a circular dependency. Callers (e.g. WeChatPlatform) wrap
ImageCompressionError into their own PlatformError subclass.
"""
from __future__ import annotations

import os
import tempfile
from pathlib import Path

from PIL import Image, UnidentifiedImageError

# Leave 200KB buffer under WeChat's 2MB hard limit.
THRESHOLD_BYTES = 1800 * 1024

# Quality reduction sequence; stops at first one that fits.
QUALITY_STEPS: tuple[int, ...] = (85, 70, 55, 40, 30)

# Suffixes Pillow can write with quality control. GIF is excluded:
# compressing a GIF to a still image would lose its animation.
COMPRESSIBLE_SUFFIXES: frozenset[str] = frozenset({".jpg", ".jpeg", ".png", ".webp"})


class ImageCompressionError(Exception):
    """Raised when an image cannot be compressed under the upload limit."""


def compress_for_upload(src: Path) -> Path:
    """Return a path suitable for upload (guaranteed < THRESHOLD_BYTES).

    If `src` is already small enough, returns it unchanged. Otherwise
    writes a compressed copy to a temp file and returns that path —
    the caller is responsible for deleting the returned file.

    Raises:
        ImageCompressionError: file missing, format unsupported, source
            can't be decoded, or can't be reduced under threshold at
            minimum quality.
    """
    src = Path(src)
    if not src.is_file():
        raise ImageCompressionError(f"Image not found: {src}")
    if src.stat().st_size <= THRESHOLD_BYTES:
        return src
    if src.suffix.lower() not in COMPRESSIBLE_SUFFIXES:
        raise ImageCompressionError(
            f"Image too large and format not auto-compressed: {src.suffix}"
        )

    try:
        with Image.open(src) as raw:
            raw.load()
            img = raw.convert("RGB") if raw.mode in ("RGBA", "P", "LA") else raw
            for quality in QUALITY_STEPS:
                tmp = _write_temp(img, src.suffix, quality)
                if tmp.stat().st_size <= THRESHOLD_BYTES:
                    return tmp
                tmp.unlink(missing_ok=True)
    except UnidentifiedImageError as exc:
        raise ImageCompressionError(f"Cannot decode image: {src} ({exc})") from exc

    raise ImageCompressionError(
        f"Cannot compress {src} under {THRESHOLD_BYTES // 1024}KB"
    )


def _write_temp(img: Image.Image, suffix: str, quality: int) -> Path:
    """Write a compressed copy to a temp file and return its path."""
    fd, name = tempfile.mkstemp(suffix=suffix, prefix="chirp_compressed_")
    os.close(fd)
    if suffix.lower() in (".jpg", ".jpeg"):
        img.save(name, format="JPEG", quality=quality, optimize=True)
    elif suffix.lower() == ".webp":
        img.save(name, format="WEBP", quality=quality, method=4)
    else:  # PNG: quality param ignored by Pillow, optimize=True is the lever
        img.save(name, format="PNG", optimize=True)
    return Path(name)
