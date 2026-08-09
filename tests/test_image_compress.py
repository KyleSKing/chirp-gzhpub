"""Tests for chirp_gzhpub.image_compress."""
from __future__ import annotations

import random
from pathlib import Path

import pytest
from PIL import Image

from chirp_gzhpub.image_compress import (
    COMPRESSIBLE_SUFFIXES,
    THRESHOLD_BYTES,
    ImageCompressionError,
    compress_for_upload,
)


def _make_png(path: Path, width: int = 10, height: int = 10) -> Path:
    Image.new("RGB", (width, height), "red").save(path, format="PNG")
    return path


def _make_large_jpeg(path: Path, width: int = 2500, height: int = 2500) -> Path:
    """Build a JPEG guaranteed to exceed the threshold (random pixels don't compress)."""
    rng = random.Random(42)
    img = Image.new("RGB", (width, height))
    pixels = img.load()
    for x in range(0, width, 4):
        for y in range(0, height, 4):
            pixels[x, y] = (rng.randint(0, 255), rng.randint(0, 255), rng.randint(0, 255))
    img.save(path, format="JPEG", quality=98)
    return path


def test_small_image_returns_unchanged(tmp_path: Path) -> None:
    """File already under threshold → no compression, no copy."""
    small = _make_png(tmp_path / "tiny.png")
    result = compress_for_upload(small)
    assert result == small


def test_missing_file_raises(tmp_path: Path) -> None:
    with pytest.raises(ImageCompressionError, match="not found"):
        compress_for_upload(tmp_path / "missing.png")


def test_unsupported_format_raises_for_oversized(tmp_path: Path) -> None:
    """GIF (animation) and other non-compressible formats fail fast, not silently."""
    big = tmp_path / "big.gif"
    big.write_bytes(b"x" * (3 * 1024 * 1024))
    with pytest.raises(ImageCompressionError, match="not auto-compressed"):
        compress_for_upload(big)


def test_large_jpeg_compresses_under_threshold(tmp_path: Path) -> None:
    """A >threshold JPEG is compressed to a new file that fits."""
    big = _make_large_jpeg(tmp_path / "big.jpg")
    assert big.stat().st_size > THRESHOLD_BYTES, (
        f"fixture should exceed threshold: {big.stat().st_size}"
    )

    result = compress_for_upload(big)
    try:
        assert result != big, "compression should produce a new file"
        assert result.stat().st_size <= THRESHOLD_BYTES
        assert result.suffix.lower() in COMPRESSIBLE_SUFFIXES
    finally:
        if result != big and result.exists():
            result.unlink()
