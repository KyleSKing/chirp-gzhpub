"""Tests for chirp_gzhpub.parser."""
import os
from pathlib import Path

import pytest

from chirp_gzhpub.parser import parse_post, resolve_asset_path

SAMPLE_POST = """\
---
title_cn: 测试标题
title_en: Test Title
summary_cn: 一段中文摘要。
wechat: true
cover: ./cover.jpg
date: 2026-08-08 10:00:00 +0800
---

<!-- Chinese Version -->
<div class="lang-cn" markdown="1">

## 中文标题

这是中文正文。**加粗**、`code`、![图片](./img.png)。

</div>

---

<!-- English Version -->
<div class="lang-en" markdown="1">

## English Title

English body.

</div>
"""


def test_parse_post_returns_metadata_and_chinese_body(tmp_path: Path) -> None:
    p = tmp_path / "post.md"
    p.write_text(SAMPLE_POST, encoding="utf-8")
    meta, cn_md = parse_post(p)
    assert meta["title_cn"] == "测试标题"
    assert meta["wechat"] is True
    assert "## 中文标题" in cn_md
    assert "English Title" not in cn_md
    assert "这是中文正文" in cn_md


def test_parse_post_missing_lang_cn_block(tmp_path: Path) -> None:
    p = tmp_path / "post.md"
    p.write_text(
        "---\ntitle_cn: x\n---\n\nno div here\n",
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="lang-cn"):
        parse_post(p)


def test_parse_post_empty_lang_cn_block(tmp_path: Path) -> None:
    p = tmp_path / "post.md"
    p.write_text(
        '---\ntitle_cn: x\n---\n\n<div class="lang-cn" markdown="1"></div>\n',
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="为空"):
        parse_post(p)


def test_parse_post_file_not_found(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        parse_post(tmp_path / "missing.md")


def test_resolve_asset_path_relative(tmp_path: Path) -> None:
    p = resolve_asset_path("./cover.jpg", tmp_path)
    assert p == tmp_path / "cover.jpg"


def test_resolve_asset_path_absolute(tmp_path: Path) -> None:
    # On Windows, POSIX-style absolute paths get drive-prefixed; use OS-native form.
    if os.name == "nt":
        p = resolve_asset_path("C:/abs/cover.jpg", tmp_path)
        assert p == Path("C:/abs/cover.jpg")
    else:
        p = resolve_asset_path("/abs/cover.jpg", tmp_path)
        assert p == Path("/abs/cover.jpg")
