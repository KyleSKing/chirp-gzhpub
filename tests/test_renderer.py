"""Tests for chirp_gzhpub.renderer."""
import re

from chirp_gzhpub.renderer import inject_inline_styles, render


def test_render_basic_paragraph_has_style() -> None:
    html = render("hello world")
    assert '<p style="' in html
    assert "hello world" in html


def test_render_heading_h2_has_blue_left_border() -> None:
    html = render("## 标题")
    assert '<h2 style="' in html
    assert "border-left: 4px solid #1e88e5" in html


def test_render_image_has_responsive_style() -> None:
    html = render("![alt](https://example.com/x.png)")
    assert '<img style="' in html
    assert "max-width: 100%" in html


def test_render_blockquote_has_gray_border() -> None:
    html = render("> quoted text")
    assert '<blockquote style="' in html


def test_render_inline_code_has_background() -> None:
    html = render("use `pip install` to install")
    assert '<code style="' in html
    assert "background: #f5f5f5" in html


def test_render_code_block_has_background() -> None:
    md = "```python\nprint('hi')\n```"
    html = render(md)
    assert '<pre style="' in html
    assert "<code" in html


def test_render_list_items_have_style() -> None:
    html = render("- one\n- two\n")
    assert '<ul style="' in html
    assert '<li style="' in html


def test_render_link_has_blue_color() -> None:
    html = render("[click](https://example.com)")
    assert '<a style="' in html
    assert "color: #1e88e5" in html


def test_render_table_cells_have_style() -> None:
    md = "| a | b |\n|---|---|\n| 1 | 2 |\n"
    html = render(md)
    assert '<table style="' in html
    assert '<th style="' in html
    assert '<td style="' in html


def test_inject_inline_styles_preserves_existing_attrs() -> None:
    html = '<p class="foo">x</p>'
    out = inject_inline_styles(html)
    # Order of attributes is implementation-defined; check both are present
    assert 'class="foo"' in out
    assert 'style="' in out
    # And the style is on the <p> tag (not injected somewhere unrelated)
    assert re.search(r'<p[^>]*style="', out) is not None


def test_inject_inline_styles_merges_existing_style() -> None:
    html = '<p style="color: red">x</p>'
    out = inject_inline_styles(html)
    # original color:red preserved, plus injected css appended
    assert "color: red" in out
    assert "margin:" in out


def test_inject_inline_styles_only_touches_target_tag() -> None:
    html = '<p>x</p><div>y</div>'
    out = inject_inline_styles(html, styles={"p": "color: red"})
    assert '<p style="color: red"' in out
    assert '<div>y</div>' in out  # div untouched
