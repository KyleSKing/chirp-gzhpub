"""Parse a Jekyll post (.md with YAML frontmatter) into (metadata, chinese_markdown).

Frontmatter is loaded with python-frontmatter. The Chinese body is extracted from
the <div class="lang-cn" markdown="1">...</div> block.
"""
from __future__ import annotations

import re
from pathlib import Path

import frontmatter

_LANG_CN_RE = re.compile(
    r'<div\s+class="lang-cn"[^>]*>(.*?)</div>',
    re.DOTALL | re.IGNORECASE,
)


def parse_post(path: Path) -> tuple[dict, str]:
    """Read a Jekyll post and return (frontmatter dict, Chinese body Markdown).

    Raises ValueError if the lang-cn block is missing.
    """
    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(f"Post not found: {path}")
    post = frontmatter.loads(path.read_text(encoding="utf-8"))
    body = post.content

    m = _LANG_CN_RE.search(body)
    if not m:
        raise ValueError(
            f"未找到 <div class=\"lang-cn\"> 块 in {path}. "
            "Make sure the post has a Chinese body wrapped in a lang-cn div."
        )
    cn_md = m.group(1).strip()
    if not cn_md:
        raise ValueError(f"<div class=\"lang-cn\"> 块为空 in {path}")

    return dict(post.metadata), cn_md


def resolve_asset_path(cover_value: str, post_dir: Path) -> Path:
    """Resolve a cover value (relative path) against the post's directory."""
    cover_path = Path(cover_value)
    if not cover_path.is_absolute():
        cover_path = post_dir / cover_path
    return cover_path
