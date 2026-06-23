# Changelog

本文档遵循 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.0.0/) 格式，并遵守 [Semantic Versioning](https://semver.org/lang/zh-CN/)。

## [1.0.0] - 2026-06-19

### Added

- 首个稳定版本发布。
- 新增社区健康文件与 issue 模板，便于收集生产环境反馈。

### Changed

- `autoship` 版本号升级至 `1.0.0`。
- `autoship-sdk` 版本号升级至 `1.0.0`，并依赖 `autoship>=1.0.0`。

### Fixed

- 所有 GitHub Actions 工作流更新为基于仓库根目录的路径假设，移除此前 `autoship-cli/` 子目录前缀。
- `release.yml` 现在同时构建并发布 `autoship-sdk` 到 PyPI。

## [1.0.0-rc.1] - 2026-06-19

### Added

- CLI 国际化（i18n），支持英文与中文。
  - 使用 `--lang zh|en` 或在 `.autoship.toml` 中设置 `locale = "zh"`。
  - 自动检测系统语言，默认回退到英文。
- `autoship doctor` 诊断命令：检查 Python、Git、模型后端、清理工具链、插件依赖以及审计/遥测目录权限。
- `autoship audit export` 与 `autoship audit cleanup` 命令，支持审计日志结构化导出与保留期管理。
- 官方插件注册表索引 `src/autoship/registry/plugins.json`，支持 `autoship plugin search` 与 `autoship plugin install`。
- `autoship-sdk` 插件开发套件（位于 `autoship-sdk/`）：
  - `Plugin` 基类与 `hook` 装饰器。
  - `PluginTestHarness` 用于隔离 Hook 测试。
  - `create_plugin` 脚手架用于创建新插件项目。
- `website/` 静态官方网站与 GitHub Pages 部署工作流。
- 通过 `.autoship.team.toml` 支持团队级配置。
- 使用 `AUTOSHIP_*` 前缀的环境变量覆盖所有配置项。

### Changed

- `autoship` 版本号升级至 `1.0.0-rc.1`。
- `autoship-sdk` 版本号升级至 `1.0.0-rc.1`，并依赖 `autoship>=1.0.0rc1`。

### Fixed

- 修复 `ollama.py`、`registry_index.py`、`config_center.py`、`hardware_profiler.py` 与 `hook_dispatcher.py` 中的 mypy/pyright 兼容性问题。

## [0.2.0-beta.1] - 2026-06-18

### Added

- 边界测试与错误注入覆盖模型层、Git 层、工具链层、插件层与文件/资源层。
- 性能基准测试框架 `benchmarks/benchmark.py`，支持启动时间、clean 执行时间、空闲内存等指标。
- CI/CD 多平台打包：Linux/macOS/Windows 单文件可执行程序、SHA256 checksum、SBOM。
- `benchmark.yml` 工作流支持手动与 PR 触发性能回归。
- MkDocs Material 文档站点与 GitHub Pages 自动部署。
- 可选遥测与错误上报，默认关闭，仅收集命令/时长/退出码/异常类型（不含代码内容）。

### Fixed

- `OllamaGateway.chat` 现在正确将 HTTP 错误、JSON 解析错误与超时转换为 `ModelGatewayError`。
- `clean` 命令的 `--check` 参数在直接调用时使用真实布尔默认值。

### Changed

- 开发依赖增加 `pyinstaller>=6.0.0` 与 `mkdocs-material>=9.0.0`。

## [0.1.0] - 2026-06-18

### Added

- 初始化 AutoShip-CLI 核心命令：`init`、`clean`、`commit`、`verify`、`upload`、`plugin`。
- 基于 [pluggy](https://pluggy.readthedocs.io/) 的插件系统，支持 `pre_*`、`post_*` 与 `on_error` 生命周期钩子。
- 本地优先的 AI 模型路由，支持 Ollama、LM Studio、llama.cpp 与 vLLM 后端。
- 硬件感知能力：根据 CPU/GPU/内存自动推荐模型层级。
- 官方内置插件：
  - `security-scan`：提交前运行 bandit/gitleaks/osv-scanner 安全扫描。
  - `docker-ship`：`upload --target docker` 时自动构建/推送镜像。
  - `web-search`：`verify --fix` 失败时联网搜索错误上下文。
- 审计日志系统，记录关键 CLI 操作。
- 插件信任等级与本地注册表管理（`builtin`/`verified`/`community`/`untrusted`）。
- 上传适配器支持 PyPI、Docker 与 GitHub。
- 端到端（E2E）测试与边界场景覆盖。
- 性能基准测试与结果记录（`benchmarks/`）。
- 完整的中文 MkDocs Material 文档站点。
- GitHub Actions 文档自动部署工作流。

### Changed

- 统一 Typer CLI 入口与全局选项（`--verbose`、`--dry-run`、`--yes`、`--config`）。
- 使用 Pydantic 定义 `.autoship.toml` 配置模型。

### Security

- 安全扫描集成 bandit 与 pip-audit。
- 凭证信息默认不写入日志。
- 插件通过 Hook 机制运行，遵循最小权限原则。

[1.0.0]: https://github.com/MS33834/autoship-cli/releases/tag/v1.0.0
[1.0.0-rc.1]: https://github.com/MS33834/autoship-cli/releases/tag/v1.0.0-rc.1
[0.2.0-beta.1]: https://github.com/MS33834/autoship-cli/releases/tag/v0.2.0-beta.1
[0.1.0]: https://github.com/MS33834/autoship-cli/releases/tag/v0.1.0
