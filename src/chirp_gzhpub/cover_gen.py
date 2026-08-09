"""Generate cover images for posts.

Style: light minimal (white bg + red accent + black title).
Suitable for tech/security/AI content on WeChat.

CJK font requirement: Pillow's default font doesn't render Chinese.
We auto-detect a CJK font on the system; if none is found, raise
FileNotFoundError with install instructions. The cover image is rendered
to a PNG (lossless, supports the bar/gradient/text cleanly).
"""
from __future__ import annotations

from datetime import date
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

# --- design constants -----------------------------------------------------

# Color palette (light minimal: 浅色简约)
BG_COLOR: tuple[int, int, int] = (250, 250, 250)  # near-white
ACCENT_COLOR: tuple[int, int, int] = (220, 38, 38)  # red-600
TITLE_COLOR: tuple[int, int, int] = (24, 24, 27)  # near-black
FOOTER_COLOR: tuple[int, int, int] = (113, 113, 122)  # zinc-500

# Default dimensions. 16:9-ish; WeChat displays 2.35:1 in cards so the
# side margins crop naturally on small thumbs.
DEFAULT_WIDTH: int = 900
DEFAULT_HEIGHT: int = 500

TITLE_FONT_SIZE: int = 64
FOOTER_FONT_SIZE: int = 24
ACCENT_BAR_WIDTH: int = 8

# Approx CJK chars per line at TITLE_FONT_SIZE in DEFAULT_WIDTH. Pillow
# measures per-glyph; this is a conservative ceiling so a 10-char title
# fits without measuring. Longer titles wrap.
MAX_CHARS_PER_LINE: int = 10

# CJK font candidates, in priority order. First existing file wins.
DEFAULT_CANDIDATES: list[Path] = [
    # Windows
    Path("C:/Windows/Fonts/msyhbd.ttc"),
    Path("C:/Windows/Fonts/msyh.ttc"),
    Path("C:/Windows/Fonts/simhei.ttf"),
    # macOS
    Path("/System/Library/Fonts/PingFang.ttc"),
    Path("/System/Library/Fonts/STHeiti Medium.ttc"),
    # Linux
    Path("/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"),
    Path("/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"),
    Path("/usr/share/fonts/truetype/wqy/wqy-microhei.ttc"),
]


# --- public API ------------------------------------------------------------


def find_cjk_font(
    *,
    candidates: list[Path] | None = None,
) -> Path:
    """Return the first existing CJK font from `candidates` (or DEFAULT_CANDIDATES).

    Raises:
        FileNotFoundError: no candidate font exists. Message lists install commands.
    """
    paths = candidates if candidates is not None else DEFAULT_CANDIDATES
    for p in paths:
        if p.is_file():
            return p
    raise FileNotFoundError(
        "No CJK font found on this system. Install one of:\n"
        "  Windows: 微软雅黑 (msyh.ttc, comes pre-installed)\n"
        "  macOS:   PingFang (pre-installed)\n"
        "  Linux:   sudo apt install fonts-noto-cjk   # or wqy-microhei"
    )


def _wrap_lines(text: str, max_chars: int) -> list[str]:
    """Naive char-count wrap. CJK has no spaces; break at max_chars."""
    if not text:
        return [""]
    return [text[i : i + max_chars] for i in range(0, len(text), max_chars)]


def generate_cover(
    title: str,
    *,
    brand: str = "AI 安全情报",
    output_path: Path,
    width: int = DEFAULT_WIDTH,
    height: int = DEFAULT_HEIGHT,
    font_path: Path | None = None,
) -> Path:
    """Render a light-minimal cover image to `output_path`.

    Args:
        title: Post title (Chinese OK; wraps at MAX_CHARS_PER_LINE).
        brand: Brand name shown in the footer.
        output_path: Where to write the PNG.
        width/height: Image dimensions in pixels.
        font_path: Override CJK font (testing); auto-detected if None.

    Returns:
        The same `output_path`, for chaining.
    """
    fpath = font_path or find_cjk_font()
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    img = Image.new("RGB", (width, height), BG_COLOR)
    draw = ImageDraw.Draw(img)

    # Left red accent bar
    draw.rectangle([(0, 0), (ACCENT_BAR_WIDTH, height)], fill=ACCENT_COLOR)

    # Title (centered, wraps if too long)
    title_font = ImageFont.truetype(str(fpath), TITLE_FONT_SIZE)
    lines = _wrap_lines(title, MAX_CHARS_PER_LINE)
    line_height = TITLE_FONT_SIZE + 8
    block_h = line_height * len(lines)
    y = (height - block_h) // 2 - 30  # bias up to leave room for footer
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=title_font)
        x = (width - (bbox[2] - bbox[0])) // 2
        draw.text((x, y), line, fill=TITLE_COLOR, font=title_font)
        y += line_height

    # Footer: brand · date
    footer_font = ImageFont.truetype(str(fpath), FOOTER_FONT_SIZE)
    footer = f"{brand} · {date.today().isoformat()}"
    fbbox = draw.textbbox((0, 0), footer, font=footer_font)
    fw = fbbox[2] - fbbox[0]
    draw.text(
        ((width - fw) // 2, height - FOOTER_FONT_SIZE - 30),
        footer,
        fill=FOOTER_COLOR,
        font=footer_font,
    )

    img.save(output_path, format="PNG", optimize=True)
    return output_path
