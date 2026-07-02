# P4-2 公开文档站点 — 详细执行计划表

> **状态**：进行中（P4-2）
> **Owner**：文档/UX 组（主），发布/集成组（CI），安全/合规组（审查），性能/测试组（链接与构建验证）
> **前置**：5 个 Dependabot PR（#38–#42）影响 `website.yml` 及全部 workflow，必须先处理
> **验收标准**：三语可搜索文档站部署到 GitHub Pages，push `main` 自动部署，无断链，落地页含 demo/截图，命令参考与 README 互链
> **关联文件**：`mkdocs.yml`、`.github/workflows/website.yml`、`docs/`、`docs/en/`、`docs/ja/`、`website/`、`README*.md`
> **完成后**：勾选 `PLAN.md` 中 P4-2 全部任务，本文件保留作为 review 记录

---

## 0. 前置：远程仓库健康检查与 Dependabot PR 处理

> **为什么前置**：5 个 Dependabot PR 升级的 GitHub Actions 版本正好被 `website.yml` 使用，盲目合并会导致文档部署 CI 变红。必须先评估、逐个验证。

- [ ] **0.1** 核对 GitHub 仓库状态：open PR/Issue 数、CI 是否全绿、分支是否需清理（本次已查：5 PR / 0 Issue / CI 全绿，记录到 commit message）
- [ ] **0.2** 核对 GitCode 镜像 HEAD 与 GitHub 一致（`git ls-remote` 两边 main SHA 比对）
- [ ] **0.3** 评估 5 个 Dependabot PR 的破坏性：
  - #40 `astral-sh/setup-uv` v3→v7（跨 4 个大版本，最高风险，影响 6 个 workflow）
  - #38 `actions/upload-artifact` v4→v7（跨 3 个大版本，影响 5 处）
  - #42 `actions/download-artifact` v4→v8（跨 4 个大版本，影响 release.yml）
  - #39 `actions/setup-node` v4→v6（影响 website.yml 1 处）
  - #41 `actions/deploy-pages` v4→v5（影响 website.yml 1 处）
- [ ] **0.4** 决策：因跨大版本升级有破坏性，**不逐个合并 Dependabot PR**，而是在一个本地分支统一升级全部 6 个 action，本地 + CI 验证后一次性合并，再关闭 5 个 Dependabot PR（避免它们之间互相冲突 + 避免中间状态 CI 红）
- [ ] **0.5** 创建分支 `feat/p4-2-deps-and-docs`，在分支上统一把 `@v3/@v4` 升级到目标版本（setup-uv@v7、upload-artifact@v7、download-artifact@v8、setup-node@v6、deploy-pages@v5、upload-pages-artifact 已是 v5 保留）
- [ ] **0.6** 本地跑 `uv run ruff check`、`uv run pyright`、`uv run pytest -q` 确认源码无影响（workflow 改动不影响源码测试，但跑一遍防意外）
- [ ] **0.7** 推分支 → 等 CI（ci.yml / e2e.yml / website.yml）全绿 → 合并到 main → 关闭 5 个 Dependabot PR 并留言"Superseded by unified upgrade in commit <sha>"
- [ ] **0.8** 合并后再次确认 GitHub Actions 全绿（特别是 Deploy Website），GitCode 镜像同步

---

## 1. MkDocs 构建健康度

- [ ] **1.1** 确认 `mkdocs-material` 在 `pyproject.toml` dev 依赖中（`uv sync --all-extras --dev` 能装上）
- [ ] **1.2** 本地 `uv run mkdocs build --strict --site-dir /tmp/mkdocs-build` 跑 strict 模式，**0 warning 0 error**（strict 模式会把 warning 当 error，确保部署不因小问题失败）
- [ ] **1.3** 修复 strict 构建发现的所有问题（常见：nav 缺页、相对链接断、代码块语言标签缺失、snippet 引用文件不存在）
- [ ] **1.4** 验证 i18n 插件三语构建：`docs/`（zh 默认）、`docs/en/`、`docs/ja/` 都能生成，无 "missing translation" 警告
- [ ] **1.5** 把 `mkdocs build --strict` 加入 `ci.yml` 的 lint job，防止后续 PR 引入断链（**新增 CI 步骤**，不止 nightly）

---

## 2. 文档站导航与内容完整性

- [ ] **2.1** 审计 `mkdocs.yml` 的 `nav`：确认每个条目对应的 `.md` 文件三语都存在（zh 在 `docs/`、en 在 `docs/en/`、ja 在 `docs/ja/`）
- [ ] **2.2** 补齐缺失页：对照 `docs/` 下的文件清单，把 `docs/en/` 和 `docs/ja/` 里缺失的对应页面补齐（已知 `docs/commands/` 下有 12 个命令页，确认 en/ja 都有对应）
- [ ] **2.3** 新增三语 **Quickstart 快速开始** 页（`docs/quickstart.md` + en + ja），内容镜像 `docs/demo.md` 的端到端流程：`init → clean → commit → verify --fix → upload --dry-run`，每步含可复制命令 + 预期输出
- [ ] **2.4** 新增三语 **模型配置指南** 页（`docs/models.md` 已有 zh，确认 en/ja 对应页存在并覆盖全部 7 个 backend：Ollama / LM Studio / llama.cpp / vLLM / OpenAI / Azure OpenAI / OpenRouter + fallback 配置示例）
- [ ] **2.5** 新增三语 **插件开发教程** 页（`docs/plugin-development.md` 已有 zh，确认 en/ja；补充从 `autoship-sdk create_plugin` 到发布到 registry 的完整 walkthrough）
- [ ] **2.6** 在 `mkdocs.yml` nav 中加入 Quickstart（置顶，紧跟首页）+ 确认 models/plugin-development 已在 nav

---

## 3. 落地页与 demo

- [ ] **3.1** 录制 `docs/demo.cast`（asciinema）：执行 `autoship init && autoship clean && autoship commit && autoship verify --fix && autoship upload --dry-run`，时长 2-3 分钟，无敏感信息泄露（用 demo 项目，token 用占位符）
- [ ] **3.2** 在 `docs/index.md`（及 en/ja）落地页嵌入 asciinema：`[![asciicast](https://asciinema.org/a/XXX.svg)](https://asciinema.org/a/XXX)`
- [ ] **3.3** 为 `init` / `clean` / `commit` / `verify --fix` / `upload --dry-run` 各截 1 张 GIF 或截图，放到 `docs/assets/`（新建目录），嵌入 Quickstart 页
- [ ] **3.4** 三语 README 顶部 demo 区从"待录制"改为实际 asciinema 链接（目前 README 写的是 "Once the asciinema video is recorded..."）

---

## 4. README 与文档站互链

- [ ] **4.1** 三语 README 的 docs 徽章链接到 `https://ms33834.github.io/autoship-cli/docs`（确认徽章 URL 与 `mkdocs.yml` 的 `site_url` 一致）
- [ ] **4.2** 在 `docs/index.md` 落地页加入"README / FEATURES / PLAN"互链区，引导用户从文档站回到仓库
- [ ] **4.3** 每个命令参考页（`docs/commands/*.md` 三语共 36 页）底部加"编辑此页"链接（mkdocs i18n + `edit_uri` 已配，确认生效）
- [ ] **4.4** 确认 `FEATURES.md` 和 `PLAN.md` 不在 mkdocs nav 中（它们是仓库内开发者文档，不是用户文档站内容），但在 `docs/index.md` 提供"开发者文档"外链区指向仓库内这两个文件

---

## 5. 搜索与版本化

- [ ] **5.1** 确认 mkdocs Material 的 `search` 插件已启用（theme.features 含 `search.suggest` + `search.highlight`，已配），三语搜索都能工作
- [ ] **5.2** 确认 `extra.version.provider: mike` 已配（已配），但当前未实际发布版本化文档；P4-2 阶段**不启用 mike 多版本**（等 1.0 正式 tag 后再启用，避免未发布版本混淆），在 PLAN.md 注明
- [ ] **5.3** 验证 `site_url` 与 GitHub Pages 实际部署 URL 一致：`https://ms33834.github.io/autoship-cli/docs`（注意 `/docs` 子路径，因 website.yml 把 mkdocs 产物放到 `website/dist/docs`）

---

## 6. CI 自动部署验证

- [ ] **6.1** 确认 `website.yml` 触发路径含 `docs/**`、`mkdocs.yml`、`website/**`（已配），本次 docs 改动会自动触发部署
- [ ] **6.2** 合并 P4-2 改动到 main 后，观察 GitHub Actions "Deploy Website" run 成功（conclusion=success）
- [ ] **6.3** 部署后用浏览器/curl 访问 `https://ms33834.github.io/autoship-cli/docs/`、`/en/`、`/ja/` 三个入口都返回 200 且内容正确
- [ ] **6.4** 用 `mkdocs build --strict` 在 CI 中作为部署前置门禁（任务 1.5 已加到 ci.yml），确认 PR 级别也能拦截断链

---

## 7. 多角色评审（交付前必过）

> 每个角色从自己视角审查，问题记录到本文件"评审记录"区，修复后才能合并

- [ ] **7.1 架构师**：mkdocs i18n folder 结构是否合理、mike 版本化预留是否影响未来、website.yml 与 docs 构建的耦合度是否过高
- [ ] **7.2 产品经理**：Quickstart 是否能让新用户 5 分钟跑通、落地页是否清晰传达"本地优先"价值主张、三语体验是否一致
- [ ] **7.3 开发组长**：命令参考页与实际 CLI `--help` 是否一致、代码示例是否可复制即跑、是否有遗漏的命令页
- [ ] **7.4 安全/合规**：demo.cast 和截图里有无泄露真实 token/路径/密钥、文档是否教用户安全配置（ToolVerifier、脱敏、权限）、隐私政策页是否与代码实现一致
- [ ] **7.5 性能/测试**：mkdocs strict 构建有无 warning、三语构建产物大小是否合理、CI 构建时长是否可接受、断链测试是否自动化
- [ ] **7.6 发布/集成**：website.yml 升级后 CI 全绿、GitHub Pages 部署成功、GitCode 镜像同步、Dependabot PR 已关闭

---

## 8. 连贯跑通与门禁

- [ ] **8.1** 本地完整跑一遍门禁：
  ```bash
  uv run ruff check src tests dogfood benchmarks
  uv run ruff format --check src tests dogfood benchmarks
  uv run pyright
  uv run pytest -q
  uv run bandit -r src -ll
  uv run pip-audit --desc
  uv run mkdocs build --strict --site-dir /tmp/mkdocs-build
  ```
- [ ] **8.2** 手动跑一遍 dogfood：`uv run python dogfood/dogfood.py`（确认文档改动没破坏 CLI 运行）
- [ ] **8.3** 确认本次改动没有引入源码逻辑变更（纯文档 + workflow 升级），pytest 数量与覆盖率不下降（基准：670 passed / 87.88%）
- [ ] **8.4** review 全部 git diff，确认无意外改动、无密钥泄露、无调试残留

---

## 9. 交付与同步

- [ ] **9.1** 更新 `PLAN.md`：勾选 P4-2 全部 `- [x]`，并在 P4-2 段落顶部加"✅ 已完成"标记
- [ ] **9.2** 更新 `CHANGELOG.md` `## [Unreleased]` Added 节：记录 P4-2 成果（三语 Quickstart、模型配置指南、插件开发教程、asciinema demo、mkdocs strict CI 门禁、统一升级 GitHub Actions）
- [ ] **9.3** 三语 `docs/changelog.md` 同步对应条目
- [ ] **9.4** `git commit`（conventional commits：`docs: P4-2 public docs site — quickstart/models/plugin tutorial, asciinema demo, strict mkdocs CI`）
- [ ] **9.5** `git push origin main && git push gitcode main` 双仓库同步
- [ ] **9.6** 验证两个远程 HEAD 一致 + GitHub "Deploy Website" CI 全绿
- [ ] **9.7** 本文件标记完成，保留作为 review 记录

---

## 评审记录

> 多角色评审（任务 7）的问题与修复记录写在这里，格式：`[角色] 问题 → 修复`

### 计划评审（执行前，2026-07-02）

三组子代理（架构师 / 产品经理 / 开发组长+安全+测试）对计划表本身做了执行前评审。汇总的 P0/P1 阻塞项已回写为下方"补充任务"，P2 建议项择优纳入。

**P0 必修（已纳入补充任务）**：
- [架构师] `website/index*.html`、`plugins*.html` 共 6 处跨语言链接错链到 zh（en/ja 页应链 `docs/en/`、`docs/ja/`）→ 补充任务 3.5
- [架构师] en/ja 的 .md 缺 `title:` front matter，导致导航栏显示中文标签 → 补充任务 2.7
- [PM] Quickstart 缺前置条件，`verify --fix` 依赖 AI 后端未说明，5 分钟承诺破产 → 补充任务 2.3 拆分
- [PM] 四处文档命令不一致（index.md / README / demo.md / 计划 2.3）→ 补充任务 2.3 统一口径
- [PM] 落地页无价值主张 hero + 无 CTA → 补充任务 3.6
- [开发组长] 7.3 命令参考与 --help 一致性无方法，已发现 upload.md 示例矛盾、36 页缺全局选项 → 补充任务 7.3a 写脚本
- [开发组长] 1.5/6.4 strict 门禁未落地到 website.yml 部署构建 → 修正任务 1.5/6.4
- [安全] 7.4 缺发布前敏感信息扫描（SECURITY.md 经 snippet 公开、SIEM 概念、邮箱确认）→ 补充任务 7.4a
- [测试] 7.5 缺外部链接检查（mkdocs --strict 只测内部）→ 补充任务 7.5a 引入 lychee

**P1 重要（已纳入补充任务）**：
- [PM] 缺 "Why AutoShip" 对比页 → 补充任务 2.8
- [PM] FAQ 未更新 + Troubleshooting 独立页 + Known Issues 缺失 → 补充任务 2.9/2.10/2.11
- [PM] 三语同步机制缺失 → 补充任务 2.12 写 check_i18n_sync.py
- [PM] demo 没展示脱敏卖点 + 录制环境未规定 → 补充任务 3.1a/3.1b
- [开发组长] 1.5 应独立 docs job + paths 过滤，不在 5 倍矩阵跑 → 修正任务 1.5

**P2 建议（择优纳入）**：
- [架构师] robots.txt/sitemap 入口、CNAME 预留、CDN 缓存提示 → 补充任务 9.8
- [架构师] mike 与 upload-pages-artifact 不兼容的迁移路径 → 补充任务 5.4（预留，1.0 后再做）
- [测试] CJK 搜索分词验证、部署后内容 smoke test → 纳入任务 5.1/6.5
- [PM] 7.x 评审应执行前先评审方案（本次已完成）+ 加新用户实测 → 补充任务 7.7

---

## 补充任务（来自执行前评审）

> 以下任务编号接在原任务之后，按评审意见补充。

### 2.7 en/ja 文档 front matter title 补齐
- [ ] 为所有 `docs/en/*.md`、`docs/en/commands/*.md`、`docs/ja/*.md`、`docs/ja/commands/*.md` 补 `title:` front matter（英文/日文标题），让导航栏不显示中文标签
- [ ] 验证：`mkdocs build` 后 en/ja 站点导航栏标签为对应语言

### 2.3（修订）Quickstart 拆分 + 前置条件 + 统一口径
- [ ] **统一口径**：以 Quickstart 为准，反向修订 `docs/index.md`（三语）、`README.md`（三语）、`docs/demo.md` 的命令序列，确保四处一致
- [ ] Quickstart 拆两段：
  - 5 分钟无 AI 版：`init → clean → commit → verify pytest → upload --dry-run`（不需 AI 后端）
  - +5 分钟带 AI 版：先配 Ollama + 小模型，再 `verify --fix`
- [ ] 顶部加"前置条件"小节：Python ≥3.10、pipx/uv、git 仓库、（带 AI 版需）Ollama
- [ ] upload 步骤标注"演示用 --dry-run，真实上传需配凭证"并折叠链接到 upload.md
- [ ] 开头加 admonition 安全承诺："AutoShip 默认本地优先，clean/verify/commit 全程不离开本机"

### 2.8 Why AutoShip 对比页（三语）
- [ ] 新增 `docs/why-autoship.md` + en + ja，与 husky/pre-commit/GitHub Actions/commitizen 对比
- [ ] 维度：本地优先、AI 生成 commit、内置安全扫描、插件化、多语言、配置复杂度
- [ ] 诚实标注 AutoShip 不占优的维度，避免自夸广告
- [ ] 加入 mkdocs.yml nav，置于 Quickstart 之后

### 2.9 FAQ 更新（三语）
- [ ] 新增条目："Quickstart 的 verify --fix 为什么报错说没有 AI 后端？"
- [ ] 新增条目："Quickstart 跑完想体验完整 AI 功能怎么配？"
- [ ] 新增条目："如何选模型"（链 models.md）
- [ ] 新增条目："插件安装失败排查"
- [ ] 新增条目："三语文档同步策略说明"
- [ ] 确认 `docs/en/faq.md`、`docs/ja/faq.md` 存在并与 zh 同步

### 2.10 Troubleshooting 故障排查页（三语）
- [ ] 新增 `docs/troubleshooting.md` + en + ja，覆盖：安装失败、init 卡住、clean 误删恢复、commit 空消息/超时、verify --fix 连不上后端、upload 凭证错误、三语切换不生效
- [ ] 加入 mkdocs.yml nav

### 2.11 Known Issues 已知问题页（三语）
- [ ] 新增 `docs/known-issues.md` + en + ja，诚实列出：verify --fix 无 AI 后端不可用、Windows 路径 edge case、大仓库 clean 性能、三语翻译可能滞后
- [ ] 加入 mkdocs.yml nav

### 2.12 i18n 同步检查脚本
- [ ] 新增 `scripts/check_i18n_sync.py`：对比三语同名 .md 的 H2/H3 标题层级、代码块数量、front-matter 字段
- [ ] 接入 ci.yml docs job，zh 改了 en/ja 没跟则 CI 红
- [ ] 在 CONTRIBUTING.md 声明"改 zh 需同步 en/ja 或在 PR 标注待翻译"

### 3.1a demo.cast 录制环境与分镜
- [ ] demo.md 顶部加"录制环境"：Python 版本、Ollama 版本、模型名+tag、OS
- [ ] 分镜：0:00 安装→0:15 init→0:30 clean→0:50 commit→1:20 verify --fix→1:50 upload --dry-run→2:10 CTA
- [ ] demo.md 现有脚本（`verify python --version`、`commit --dry-run`）与 Quickstart 对齐

### 3.1b demo 展示脱敏卖点
- [ ] 在 verify/commit 步骤后插 `--verbose` 输出，展示 `sk-xxxx` → `sk-***` 脱敏效果
- [ ] 录制后对 `docs/demo.cast` 跑 `gitleaks detect --source docs/demo.cast`

### 3.5 修复跨语言断链（website/ 6 处）
- [ ] `website/index.html`（en）：`docs/plugin-development/` → `docs/en/plugin-development/`
- [ ] `website/index.zh.html`：保留 `docs/plugin-development/`（zh 正确）
- [ ] `website/index.ja.html`：`docs/plugin-development/` → `docs/ja/plugin-development/`
- [ ] `website/plugins.html`、`plugins.zh.html`、`plugins.ja.html`：同上按 locale 修正
- [ ] 验证：三语 landing 页点击"AutoShip SDK"跳到对应语言文档

### 3.6 落地页价值主张 hero + CTA
- [ ] `docs/index.md`（三语）加 hero 主标题：zh「你的代码，从不上云」/ en「Your code, never in the cloud」/ ja「コードをクラウドに送らない」
- [ ] 3 个核心卖点卡片：本地优先 / 插件化 / 安全可靠
- [ ] 醒目安装命令块（`pipx install autoship` 一键复制）
- [ ] 主 CTA「5 分钟 Quickstart」+ 次 CTA「Why AutoShip」按钮

### 5.1（修订）CJK 搜索验证
- [ ] 配置 mkdocs search lang + lunr-languages（en/ja）
- [ ] 中文需 jieba 或 zh tokenizer
- [ ] 验收：三语分别用 `清理`/`clean`/`クリーンアップ` 搜索，前 3 条结果含 quickstart

### 5.4（预留）mike 版本化迁移路径
- [ ] 文档化：未来启用 mike 需重构 website.yml 为"mike 管 docs 版本 + landing/registry 同步 gh-pages 根"双轨模式
- [ ] 当前不执行，仅在 PLAN.md 标注 1.0 tag 后再启用

### 6.4（修正）strict 门禁双轨落地
- [ ] ci.yml 新建独立 docs job（单 Python + paths 过滤 `docs/**,mkdocs.yml,website/**`），跑 `mkdocs build --strict`
- [ ] website.yml:47 部署构建改为 `mkdocs build --strict --site-dir website/dist/docs`
- [ ] PR 级（ci.yml docs job）+ 部署级（website.yml）双重 strict 门禁

### 6.5 部署后内容 smoke test
- [ ] 部署后抓三入口首页，校验含 demo.cast 嵌入、含 Quickstart 链接、含 CTA、`search_index.json` 存在非空
- [ ] 抽 2-3 个深链 + sitemap.xml + robots.txt 各 200

### 7.3a 命令参考与 --help 一致性脚本
- [ ] 新增 `scripts/sync_command_docs.py`：对 12 命令跑 `autoship <cmd> --help`，解析选项/参数，与 `docs/commands/*.md` 选项表 diff
- [ ] 接入 ci.yml docs job
- [ ] 已知缺口先修：upload.md 示例改为 `autoship upload --target pypi --dry-run`（命令级）；36 页补全局选项 `--verbose/-v --dry-run/-n --yes/-y`；init.md 输出示例不硬编码（标注 i18n 渲染）

### 7.4a 发布前敏感信息扫描
- [ ] 对 `mkdocs build` 产物跑 `gitleaks detect --source site/`
- [ ] grep 内部 hostname/邮箱/AWS 账号模式（确认 `team@autoship.dev`/`security@autoship.dev` 是公开别名）
- [ ] 确认 SECURITY.md（含内部审计/红队内容）经 snippet 公开是否有意；若无意则脱敏或改 include
- [ ] 确认 docs/ 配置示例/截图无真实 SIEM URL/API key

### 7.5a 外部链接检查
- [ ] 引入 lychee（有官方 GitHub Action），nightly 全量 + docs PR 增量
- [ ] 覆盖 docs/ 全部外链（GitHub/PyPI/asciinema.org/telemetry 等）

### 7.7 新用户实测
- [ ] 找 1-2 位未用过 AutoShip 的开发者按 Quickstart（无 AI 版）实操
- [ ] 记录耗时与卡点，超 8 分钟或卡点 >2 处则回炉

### 9.8 SEO 与域名预留
- [ ] `website/dist/` 根放 `robots.txt` 指向 `/docs/sitemap.xml`
- [ ] 预留 CNAME 文件（自定义域名迁移时启用）
- [ ] 部署验证提示"CDN 缓存约 10 分钟，部署后几分钟内可能新旧混现"
- [ ] 确认 GitCode 侧无独立 Pages 部署（仅镜像）

---

## 执行日志

> 每完成一个子任务，在此追加一行，便于回溯

（执行时按时间顺序追加）
