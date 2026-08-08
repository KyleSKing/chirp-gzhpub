"""Inline CSS injected into rendered HTML for WeChat Official Account compatibility.

WeChat strips <style> blocks and external CSS. Every visible element must have its
styles declared inline. Edit values here to tune the article look.
"""

INLINE_STYLES: dict[str, str] = {
    "body": (
        "font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'PingFang SC', "
        "'Hiragino Sans GB', 'Microsoft YaHei', sans-serif; "
        "line-height: 1.75; color: #333; max-width: 100%; margin: 0; padding: 0;"
    ),
    "p": "margin: 1em 0; line-height: 1.75; font-size: 16px; color: #333;",
    "h1": "font-size: 22px; font-weight: bold; margin: 1.6em 0 0.8em; color: #1a1a1a;",
    "h2": (
        "font-size: 20px; font-weight: bold; margin: 1.6em 0 0.8em; color: #1a1a1a; "
        "border-left: 4px solid #1e88e5; padding-left: 12px;"
    ),
    "h3": "font-size: 18px; font-weight: bold; margin: 1.2em 0 0.6em; color: #1a1a1a;",
    "h4": "font-size: 16px; font-weight: bold; margin: 1em 0 0.5em; color: #1a1a1a;",
    "ul": "margin: 0.8em 0; padding-left: 1.5em;",
    "ol": "margin: 0.8em 0; padding-left: 1.5em;",
    "li": "margin: 0.4em 0; line-height: 1.7;",
    "code": (
        "background: #f5f5f5; padding: 2px 6px; border-radius: 3px; "
        "font-family: Consolas, 'Courier New', monospace; font-size: 14px; color: #c7254e;"
    ),
    "pre": (
        "background: #f5f5f5; padding: 12px; border-radius: 4px; overflow-x: auto; "
        "line-height: 1.5; font-size: 14px;"
    ),
    "blockquote": (
        "border-left: 4px solid #ddd; padding-left: 12px; color: #666; margin: 1em 0;"
    ),
    "img": "max-width: 100%; height: auto; display: block; margin: 1em auto;",
    "a": "color: #1e88e5; text-decoration: none;",
    "strong": "font-weight: bold; color: #1a1a1a;",
    "em": "font-style: italic;",
    "table": "width: 100%; border-collapse: collapse; margin: 1em 0; font-size: 14px;",
    "th": "border: 1px solid #ddd; padding: 8px; background: #f5f5f5;",
    "td": "border: 1px solid #ddd; padding: 8px;",
    "hr": "border: none; border-top: 1px solid #eee; margin: 2em 0;",
}
