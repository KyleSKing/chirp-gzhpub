"""Tests for chirp_gzhpub.cover_gen — CJK font detection + cover image generation."""
from __future__ import annotations

from pathlib import Path

import pytest
from PIL import Image

from chirp_gzhpub import cover_gen
from chirp_gzhpub.cover_gen import find_cjk_font, generate_cover


def test_find_cjk_font_succeeds_on_this_system() -> None:
    """If the test machine has a CJK font (Windows msyh, Mac PingFang, Linux Noto), we get a path."""
    # Don't skip on this system — the project author runs on Windows with msyh.ttc.
    # If a future CI machine lacks fonts, this test will be the canary.
    font_path = find_cjk_font()
    assert font_path.is_file()
    assert font_path.suffix.lower() in {".ttf", ".ttc", ".otf"}


def test_find_cjk_font_raises_when_no_candidates(tmp_path: Path, monkeypatch) -> None:
    """If no candidate font exists anywhere, raise FileNotFoundError with a helpful hint."""
    monkeypatch.setattr(cover_gen, "DEFAULT_CANDIDATES", [tmp_path / "nope.ttf"])
    with pytest.raises(FileNotFoundError, match="CJK font"):
        find_cjk_font()


def test_find_cjk_font_respects_explicit_candidates(tmp_path: Path) -> None:
    """Custom candidate list is consulted first."""
    fake_font = tmp_path / "custom.ttf"
    fake_font.write_bytes(b"\x00" * 100)  # not a real TTF, but exists
    result = find_cjk_font(candidates=[fake_font])
    assert result == fake_font


def test_generate_cover_creates_png(tmp_path: Path) -> None:
    """generate_cover writes a valid PNG with the requested dimensions."""
    out = tmp_path / "cover.png"
    result = generate_cover(
        title="测试中文标题",
        brand="AI 安全情报",
        output_path=out,
    )
    assert result == out
    assert out.is_file()
    with Image.open(out) as img:
        assert img.size == (900, 500)
        assert img.format == "PNG"


def test_generate_cover_has_visible_content(tmp_path: Path) -> None:
    """Generated cover is not blank — has enough non-background pixels to indicate rendered design."""
    out = tmp_path / "cover.png"
    generate_cover(title="测试标题", brand="Brand", output_path=out)
    with Image.open(out) as img:
        rgb = img.convert("RGB")
        # Sample the corner (should be background) and the middle (should have text/accent).
        w, h = rgb.size
        corner = rgb.getpixel((5, 5))
        center = rgb.getpixel((w // 2, h // 2))
    # The corner should be near-white; the center should differ from corner
    # (text or accent color). We don't pin exact RGBs because the design may evolve.
    assert corner[0] > 200, f"corner should be light bg, got {corner}"
    assert center != corner, "center should differ from background — looks blank"


def test_generate_cover_uses_custom_dimensions(tmp_path: Path) -> None:
    out = tmp_path / "cover.png"
    generate_cover(title="x", brand="y", output_path=out, width=1200, height=630)
    with Image.open(out) as img:
        assert img.size == (1200, 630)
