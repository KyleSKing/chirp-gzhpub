"""Render Markdown to WeChat-compatible HTML with inline CSS.

WeChat's draft API strips <style> blocks and external CSS. We use markdown-it-py
for the MD → HTML conversion, then post-process the output to inject inline
`style="..."` attributes on every visible tag listed in styles.INLINE_STYLES.
"""
from __future__ import annotations

import re

from markdown_it import MarkdownIt
from mdit_py_plugins.gfm import gfm_plugin
from mdit_py_plugins.tasklists import tasklists_plugin

from .styles import INLINE_STYLES

_md = MarkdownIt("commonmark", {"html": True, "breaks": False, "linkify": True})
_md.use(gfm_plugin)
_md.use(tasklists_plugin)


def render(md_text: str) -> str:
    """Render Markdown to HTML with inline CSS, ready for WeChat draft."""
    html = _md.render(md_text)
    return inject_inline_styles(html)


def inject_inline_styles(html: str, styles: dict[str, str] | None = None) -> str:
    """For each tag in `styles`, ensure opening tags have a `style` attribute.

    Existing style attributes are preserved; the injected CSS is appended.
    Handles `<tag>` and `<tag attr="...">` forms. Closing tags are not touched.
    """
    if styles is None:
        styles = INLINE_STYLES
    for tag, css in styles.items():
        pattern = re.compile(
            rf"<{re.escape(tag)}(\s[^>]*?)?>",
            re.IGNORECASE,
        )
        html = pattern.sub(_make_replacer(tag, css), html)
    return html


def _make_replacer(tag: str, css: str):
    """Return a re.sub replacer that injects/merges `style` for the given tag."""

    def repl(m: re.Match[str]) -> str:
        attrs = m.group(1) or ""
        existing = re.search(r"""style\s*=\s*(['"])(.*?)\1""", attrs, re.IGNORECASE)
        if existing:
            current = existing.group(2).strip()
            new_css = f"{current}; {css}" if current else css
            attrs = attrs[: existing.start()] + f'style="{new_css}"' + attrs[existing.end() :]
        else:
            attrs = f' style="{css}"' + attrs
        return f"<{tag}{attrs}>"

    return repl
