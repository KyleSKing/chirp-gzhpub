# NEXT.md — 后续计划 / Follow-up plan

记录在 `chirp-gzhpub` 当前 commit（图像压缩 + 幂等性 + 自动封面 + 摘除 Toutiao）之后的下一步工作。

## 背景 / Context

截至本次 commit：
- ✅ 42 → **57** pytest 通过
- ✅ ruff clean
- ✅ mypy 11 个**预存**错误，0 新增
- ✅ 三件主要功能完成：图片自动压缩、state 幂等性、浅色简约自动封面
- ✅ Toutiao 从 `AVAILABLE_PLATFORMS` 摘除（用户决定「不推头条了」）

**未完成**（按 ROI 排序）：

## 1. 端到端打通：测试文章 + 真公众号上传

**Why**：当前所有测试都是 mock HTTP。没有真在 `mp.weixin.qq.com` 草稿箱里看到过一篇用 chirp 推的文章，**WeChat 的真实渲染、压缩、行为都没验证过**。这是 chirp 接入任何工作流（手动 CLI、CI、其他项目）之前的必要前提。

**任务**：

1. **建测试 post 集**：`tests/integration_posts/`
   - `01-short-title.md` — 短标题、纯文本段落
   - `02-long-title.md` — >10 字标题（验证换行）
   - `03-with-images.md` — 2-3 张本地图片（验证上传 + 压缩）
   - `04-code-block.md` — 代码块（验证 monospace + 行内 CSS）
   - `05-tables-lists.md` — 表格、嵌套列表、引用块
2. **配 WECHAT_APP_ID / WECHAT_APP_SECRET**：
   - 选项 A：作者现有公众号（草稿箱会有 5 篇测试文要手动删）
   - 选项 B：新申请个人订阅号（chirp 专用，0 污染正式账号）
3. **逐篇跑** `chirp --post tests/integration_posts/0N-*.md --auto-cover` —— 看草稿箱里实际效果
4. **写「回归 checklist」** `docs/integration-coverage.md`：列出每篇 post 验证什么（HTML 渲染、封面、压缩、上传、草稿 ID 入 state.jsonl）
5. **修发现的格式 bug** —— WeChat 经常吞掉某些 CSS / 标签，要修 `styles.py`

**预期工作量**：半天到 1 天（取决于 WeChat 渲染坑多少）

**完成标志**：
- [ ] `tests/integration_posts/` 5 篇 post
- [ ] `docs/integration-coverage.md` checklist
- [ ] 5 篇草稿在 mp.weixin.qq.com 草稿箱里可看
- [ ] 5 条 `status: drafted` 在 `state/wechat_publishes.jsonl`

## 2. 集成进 ai-infosec-landing（**用户决定暂不做**）

**Why 用户推迟**：想先用测试文章打通端到端，验证管道稳定后再谈 CI。

**真正的难点**：GitHub Actions IP 段会变，会破坏微信公众号 IP 白名单。**必须用自托管 runner**（固定 IP 的机器或 VM），不能用 GitHub 托管的 ubuntu-latest。

**重启条件**：
- [ ] 任务 1 完成（5 篇真草稿验证通过）
- [ ] 用户有固定 IP 的 VM / 旧笔记本可作 runner
- [ ] 决定用哪种触发：每天定时 / 每次 `_posts/wechat-true.md` push / 手动 dispatch

**预期工作量**：1-2 天（含 runner 设置 + workflow 编写 + 灰度）

## 3. Google Doc 适配器（**用户决定暂不做**）

**Why 用户推迟**：chirp 还没验证过 MD → 草稿的真流程，加新源格式会叠加调试复杂度。

**正确路径**（将来要做时）：
1. 先把任务 1 完成（MD 管道稳定）
2. 加 `google_doc.py` parser：Google Docs API → HTML → MD
3. CLI 加 `--source {md, google_doc}` flag
4. 复用现有 parse → render → upload 管道

**不推荐走的方向**：直接让 Google Doc 走「手动 export .md → 跑 chirp」两步——临时方案，不是产品方案。

**预期工作量**：1-2 周（含 OAuth、API client、HTML→MD 转换、image 处理）

## 4. 已知 TODO（低优先级）

- [ ] mypy 11 个预存错误清理（base.py / toutiao.py / parser.py / renderer.py / cli.py）—— 不阻塞新功能
- [ ] `platforms/toutiao.py` 文件物理删除（vs 仅从 `AVAILABLE_PLATFORMS` 摘除）—— 等用户决定何时动
- [ ] cover_gen 加 2 套视觉变体（红橙渐变 / 暗夜绿）—— 用 hash(slug) 选模板
- [ ] cover_gen 中英混排标题按像素宽度换行（v1 是 char-count 切，可能切得不准）
- [ ] image_compress 的 PNG 压缩：当前 `optimize=True` 不一定够强，可加调色板量化

## 相关 / Related

- [README.md](README.md) — 当前主文档
- `D:\AI\Obsidian Vault Memory-KB\memory\chirp-gzhpub-project.md` — 项目主记忆
- `D:\AI\Obsidian Vault Memory-KB\memory\chirp-image-compression-design.md`
- `D:\AI\Obsidian Vault Memory-KB\memory\chirp-idempotency-design.md`
- `D:\AI\Obsidian Vault Memory-KB\memory\chirp-cover-gen-design.md`
