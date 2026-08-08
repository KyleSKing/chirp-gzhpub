"""CLI entry point: parse → render → upload assets → create draft.

Usage:
    chirp --post _posts/2026-08-08-xxx.md           # push to WeChat draft
    chirp --post _posts/2026-08-08-xxx.md --dry-run  # render only, no API calls
    chirp --post _posts/2026-08-08-xxx.md --state-file state/x.jsonl
"""
from __future__ import annotations

import argparse
import os
import re
import sys
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

from .client import WeChatClient, WeChatError
from .parser import parse_post, resolve_asset_path
from .renderer import render
from .state import record

# Ensure UTF-8 output on Windows (GBK default breaks emoji in console).
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
    except (AttributeError, ValueError):
        pass  # Python < 3.7 or already reconfigured; not a hard failure

TITLE_MAX = 64
DIGEST_MAX = 120

_IMG_SRC_RE = re.compile(r"""<img\s[^>]*?src\s*=\s*['"]([^'"]+)['"][^>]*?>""", re.IGNORECASE)


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="chirp",
        description="Push a Jekyll Markdown post to WeChat Official Account as a draft.",
    )
    p.add_argument(
        "--post",
        type=Path,
        required=True,
        help="Path to a Jekyll post .md file.",
    )
    p.add_argument(
        "--dry-run",
        action="store_true",
        help="Render the post and print a preview. Do not call WeChat API.",
    )
    p.add_argument(
        "--state-file",
        type=Path,
        default=Path("state/wechat_publishes.jsonl"),
        help="Path to the JSONL state log (default: state/wechat_publishes.jsonl).",
    )
    p.add_argument(
        "--site-url",
        type=str,
        default=os.environ.get("SITE_URL", ""),
        help="Base URL of the source site (for content_source_url). "
        "Defaults to $SITE_URL env var.",
    )
    return p


def main(argv: list[str] | None = None) -> int:
    load_dotenv()  # local dev only; production uses real env vars
    args = _build_parser().parse_args(argv)

    try:
        meta, cn_md = parse_post(args.post)
    except (FileNotFoundError, ValueError) as exc:
        print(f"❌ {exc}", file=sys.stderr)
        return 2

    if not meta.get("wechat"):
        print(f"❌ frontmatter 缺少 wechat: true in {args.post}", file=sys.stderr)
        return 2
    if "cover" not in meta:
        print(f"❌ frontmatter 必须有 cover 字段 in {args.post}", file=sys.stderr)
        return 2
    if "title_cn" not in meta:
        print(f"❌ frontmatter 必须有 title_cn 字段 in {args.post}", file=sys.stderr)
        return 2
    if "summary_cn" not in meta:
        print(f"❌ frontmatter 必须有 summary_cn 字段 in {args.post}", file=sys.stderr)
        return 2

    html = render(cn_md)

    if args.dry_run:
        print(f"📄 Frontmatter keys: {sorted(meta.keys())}")
        print(f"📝 title_cn: {meta['title_cn'][:TITLE_MAX]}")
        print(f"📝 cover: {meta['cover']}")
        print("🔍 HTML preview (first 800 chars):")
        print("-" * 60)
        print(html[:800])
        print("-" * 60)
        print(f"✅ dry-run complete. {len(html)} chars total.")
        return 0

    app_id = os.environ.get("WECHAT_APP_ID", "")
    app_secret = os.environ.get("WECHAT_APP_SECRET", "")
    if not app_id or not app_secret:
        print("❌ WECHAT_APP_ID / WECHAT_APP_SECRET 未设置。", file=sys.stderr)
        return 2

    try:
        client = WeChatClient(app_id, app_secret)
        token = client.get_token()
        print(f"✅ Token 取得 (len={len(token)})")

        cover_path = resolve_asset_path(meta["cover"], args.post.parent)
        thumb_id = client.upload_thumb(cover_path)
        print(f"✅ 封面图上传 thumb_media_id={thumb_id}")

        html, image_count = _upload_inline_images(client, html, args.post.parent)
        print(f"✅ 正文图片上传 {image_count} 张")

        article = _build_article(meta, html, thumb_id, args.site_url, args.post)
        media_id = client.add_draft(article)
        print(f"✅ 草稿创建 media_id={media_id}")

        record(
            post=str(args.post),
            media_id=media_id,
            title=meta["title_cn"],
            status="drafted",
            state_file=args.state_file,
        )
        print(f"📝 状态: {args.state_file}")
        return 0
    except WeChatError as exc:
        record(
            post=str(args.post),
            media_id=None,
            title=meta.get("title_cn", ""),
            status="failed",
            state_file=args.state_file,
            error=str(exc),
        )
        print(f"❌ WeChat API 错误: {exc}", file=sys.stderr)
        return 1
    except (FileNotFoundError, ValueError) as exc:
        print(f"❌ {exc}", file=sys.stderr)
        return 2


def _build_article(
    meta: dict[str, Any],
    html: str,
    thumb_media_id: str,
    site_url: str,
    post_path: Path,
) -> dict[str, Any]:
    """Build the article dict for the WeChat draft/add API."""
    author = (
        meta.get("wechat_author")
        or os.environ.get("WECHAT_AUTHOR")
        or "AI安全情报"
    )
    digest = (meta.get("summary_cn") or "")[:DIGEST_MAX]
    title = (meta.get("title_cn") or "")[:TITLE_MAX]

    source_url = ""
    if site_url and meta.get("slug"):
        source_url = f"{site_url.rstrip('/')}/{meta['slug']}/"

    return {
        "title": title,
        "author": author,
        "digest": digest,
        "content": html,
        "content_source_url": source_url,
        "thumb_media_id": thumb_media_id,
        "need_open_comment": 0,
        "only_fans_can_comment": 0,
    }


def _upload_inline_images(
    client: WeChatClient,
    html: str,
    post_dir: Path,
) -> tuple[str, int]:
    """Find local <img src=...> in HTML, upload each, replace src with WeChat URL.

    External URLs (http://, https://, //) are left as-is and will be replaced by
    WeChat's anti-leech proxy (mmbiz.qpic.cn) on display — not ideal but acceptable
    for v1. Local relative paths are uploaded and replaced.
    """
    count = 0
    seen: dict[str, str] = {}  # local path → WeChat URL (dedupe)

    def repl(m: re.Match[str]) -> str:
        nonlocal count
        src = m.group(1)
        if src.startswith(("http://", "https://", "//", "data:")):
            return m.group(0)
        local_path = (post_dir / src).resolve()
        if not local_path.is_file():
            print(f"⚠️  image not found, skipping: {local_path}", file=sys.stderr)
            return m.group(0)
        if str(local_path) in seen:
            return m.group(0).replace(src, seen[str(local_path)])
        url = client.upload_image(local_path)
        seen[str(local_path)] = url
        count += 1
        return m.group(0).replace(src, url)

    new_html = _IMG_SRC_RE.sub(repl, html)
    return new_html, count


if __name__ == "__main__":
    raise SystemExit(main())
