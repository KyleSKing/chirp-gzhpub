# chirp-gzhpub

> 把 Markdown 文章推到微信公众号草稿箱的 CLI 工具
> CLI tool to push Markdown articles to WeChat Official Account as drafts.

**chirp-gzhpub** 读取 Jekyll 风格的双语 Markdown 文章（body 里有 `<div class="lang-cn">` / `<div class="lang-en">` 两个块），把中文块作为草稿送进微信公众号后台，作者再到 mp.weixin.qq.com 人工一键群发。

**chirp-gzhpub** reads a Jekyll-style bilingual Markdown post (with `<div class="lang-cn">` / `<div class="lang-en">` body blocks), creates a draft in the WeChat Official Account (公众号) backend with the Chinese block, and the author then reviews and publishes manually from mp.weixin.qq.com.

> 名字 = **chirp** (鸟鸣) + **gzhpub** (公众号 + publish)

---

## 为什么是"草稿"而不是"直发" / Why "draft" not "direct publish"?

微信官方只对**已认证服务号**开放公开发布接口；草稿 `draft/add` 对所有号开放，是 2026 年生态里唯一稳定的形态。

WeChat only exposes the public-publish API to **verified service accounts**. The `draft/add` API is open to all account types and is the only stable form in the 2026 ecosystem.

---

## 安装 / Installation

```bash
pip install -e ".[dev]"
```

需要 Python 3.11+。

Requires Python 3.11+.

---

## 前置条件 / Prerequisites

1. **公众号已开通并有 AppID / AppSecret**
   - 获取：mp.weixin.qq.com → 开发 → 基本配置
2. **公众号后台把本机 IP 加入 IP 白名单**（开发 → 基本配置 → IP 白名单）
   - 本机 IP 会变，需每次更新；或用固定 IP 的运行环境
3. **post 文件 frontmatter 含以下字段**（其他字段忽略）：
   ```yaml
   ---
   title_cn: "中文标题"            # 必填，会作为微信标题（截断 64 字）
   summary_cn: "中文摘要"          # 必填，作为 digest（截断 120 字）
   cover: ./cover.jpg             # 必填，相对 post 文件路径
   wechat: true                   # 必填，缺省不推
   wechat_author: "AI安全情报"     # 可选，缺省用 $WECHAT_AUTHOR
   slug: 2026-08-08-test          # 可选，用于 content_source_url
   ---
   ```
4. **post body 包含 `<div class="lang-cn" markdown="1">...</div>` 块**（中文正文）

1. **WeChat Official Account with AppID and AppSecret**
   - Get them from mp.weixin.qq.com → 开发 → 基本配置
2. **Add your local IP to the WeChat IP whitelist** (开发 → 基本配置 → IP 白名单)
   - Local IPs change; update each time, or use an environment with a fixed IP
3. **Post frontmatter must include** (other keys are ignored):
   ```yaml
   ---
   title_cn: "中文标题"            # required, used as WeChat title (truncated to 64 chars)
   summary_cn: "中文摘要"          # required, used as digest (truncated to 120 chars)
   cover: ./cover.jpg             # required, path relative to the post file
   wechat: true                   # required, posts without this are skipped
   wechat_author: "AI安全情报"     # optional, falls back to $WECHAT_AUTHOR
   slug: 2026-08-08-test          # optional, used in content_source_url
   ---
   ```
4. **Post body must include `<div class="lang-cn" markdown="1">...</div>`** (the Chinese body)

> ⚠️ YAML frontmatter 里的字符串如果含半角冒号 `:`，必须用引号包起来：
> ⚠️ String values in YAML frontmatter containing half-width colons `:` must be quoted:
> ```yaml
> title_cn: "标题：副标题"     # OK / OK
> title_cn: 标题：副标题       # YAML 解析报错 / YAML parse error
> ```

---

## 配置 / Configuration

复制 `.env.example` 为 `.env`：

Copy `.env.example` to `.env`:

```bash
cp .env.example .env
```

填入：

Fill in:

```env
WECHAT_APP_ID=wx...
WECHAT_APP_SECRET=...
WECHAT_AUTHOR=AI安全情报          # 缺省作者 / default author
SITE_URL=https://...             # 可选：源文章 URL 前缀 / optional source URL prefix
```

---

## 用法 / Usage

### Dry-run（不调真 API，只渲染）/ Dry-run (no API calls, render only)

```bash
chirp --post _posts/2026-08-08-xxx.md --dry-run
```

打印 frontmatter 摘要、HTML 前 800 字符、是否注入了行内 CSS。**任何时间本地任意跑。**

Prints frontmatter summary, first 800 chars of HTML, confirms inline CSS is injected. **Safe to run anytime locally.**

### 真实发布 / Real publish

```bash
chirp --post _posts/2026-08-08-xxx.md
```

执行流程 / Pipeline:

1. 读 post → 抽出 frontmatter + 中文 body / Read post → extract frontmatter + Chinese body
2. Markdown → HTML（带行内 CSS，WeChat 可识别）/ Markdown → HTML with inline CSS
3. 上传封面图 → 拿 `thumb_media_id` / Upload cover → get `thumb_media_id`
4. 上传正文图片（本地相对路径）→ 替换为 WeChat CDN URL / Upload inline images → replace with WeChat CDN URLs
5. 创建草稿 → 拿 `media_id` / Create draft → get `media_id`
6. 追加一行到 `state/wechat_publishes.jsonl` / Append a line to the state log

成功后在 mp.weixin.qq.com → 草稿箱 看到该文，手机端预览样式。

After success, find the article in mp.weixin.qq.com → 草稿箱. **Preview on a real phone** — the desktop editor preview often differs from the mobile rendering.

### 完整参数 / Full parameters

```bash
chirp --post PATH \
      [--dry-run] \
      [--state-file state/wechat_publishes.jsonl] \
      [--site-url https://example.com]
```

---

## 测试 / Testing

```bash
pytest -v
ruff check src tests
mypy src
```

所有 HTTP 调用都通过 `unittest.mock` mock，不会连真 API。

All HTTP calls are mocked via `unittest.mock` — no live API calls.

---

## 失败模式 / Failure modes

| 现象 / Symptom | 原因 / Cause |
|---|---|
| `Failed to get access_token (errcode=40125)` | AppID/Secret 错，或本机 IP 没在白名单 / Wrong AppID/Secret, or local IP not whitelisted |
| `frontmatter 缺少 wechat: true` | post 没加 `wechat: true` / Post missing `wechat: true` |
| `frontmatter 必须有 cover 字段` | 缺封面图 / Missing cover image |
| `未找到 <div class="lang-cn"> 块` | post body 没有中文 div / Body has no Chinese div |
| `image too large (>2MB)` | 图片 > 2MB，需压缩 / Image > 2MB, needs compression |
| `WeChat API error 40007` | thumb_media_id 失效（罕见，重跑）/ thumb_media_id invalid (rare, rerun) |

---

## 已知限制 / Known limitations

- **不做直发**：只进草稿箱，由人审核后群发 / **No direct publish**: drafts only, human reviews and sends
- **不做自动生成封面图**：作者必须显式提供 / **No auto-generated cover**: author must provide one
- **不做图片压缩**：原图上传，超过 2MB 报错 / **No image compression**: uploads as-is, fails if > 2MB
- **外链图片不过 WeChat 防盗链**：本地图片才上传替换；外链保留，由 WeChat 显示时换为 `mmbiz.qpic.cn` 代理 / **External image URLs are not WeChat-CDN'd**: only local images get uploaded; external URLs stay and WeChat will proxy them through `mmbiz.qpic.cn` on display
- **CI 自动发布不在 v1 范围**：GitHub Actions IP 段会变，会破坏 IP 白名单 / **No CI auto-publish in v1**: GitHub Actions IPs rotate, which breaks the IP whitelist. A self-hosted runner can be added later.

---

## 项目结构 / Project structure

```
chirp-gzhpub/
├── pyproject.toml
├── README.md
├── .env.example
├── .gitignore
├── src/chirp_gzhpub/
│   ├── __init__.py
│   ├── __main__.py
│   ├── cli.py          # argparse + 编排 / orchestration
│   ├── parser.py       # Jekyll post → (frontmatter, cn_md)
│   ├── renderer.py     # MD → HTML + inline CSS
│   ├── client.py       # WeChat HTTP client (token 缓存 + 重试 / cache + retry)
│   ├── state.py        # JSONL 状态日志 / state log
│   └── styles.py       # INLINE_STYLES 常量 / constants
├── tests/
│   ├── test_parser.py
│   ├── test_renderer.py
│   ├── test_client.py
│   └── fixtures/sample_post.md
├── .github/workflows/ci.yml
└── state/              # 运行时生成，gitignore / runtime, gitignored
```

---

## 阶段 1 不做的事（留给后续）/ Out of scope for phase 1

- 头条号、百家号、掘金、知乎适配器 / Toutiao / Baijia / Juejin / Zhihu adapters
- 自动重试失败的草稿 / Auto-retry failed drafts
- 集成进 `ai-infosec-landing` 的 GitHub Actions / Wire into ai-infosec-landing CI
- 批量发布 / 定时发布 / Batch / scheduled publishing
- Web UI

---

## License

MIT
