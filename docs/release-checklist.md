# 发布前检查清单（Release Checklist）

本清单用于指导 AutoShip-CLI 维护者完成一次正式或预发布版本。发布前必须由至少两名维护者交叉复核并勾选全部项。

---

## 1. 版本与变更日志

- [ ] 确认版本号遵循 [SemVer](https://semver.org/lang/zh-CN/)。
  - 正式版：`MAJOR.MINOR.PATCH`，例如 `1.0.0`。
  - 预发布版：附加 `-alpha.N`、`-beta.N` 或 `-rc.N`，例如 `1.1.0-rc.1`。
- [ ] 更新根目录 [`CHANGELOG.md`](https://github.com/autoship-cli/autoship-cli/blob/main/CHANGELOG.md) 与文档 [`changelog.md`](./changelog.md)。
  - 新增版本节，包含 `Added` / `Changed` / `Deprecated` / `Removed` / `Fixed` / `Security` 子节。
  - 标注发布日期（UTC+8）。
- [ ] 确认 `pyproject.toml` 中 `project.version` 与目标版本一致。
- [ ] 确认 `autoship-sdk/pyproject.toml` 中版本号与依赖约束同步更新。

## 2. 代码质量门禁

在本地运行并通过：

```bash
uv run ruff check src tests dogfood benchmarks
uv run ruff format --check src tests dogfood benchmarks
uv run pyright
uv run pytest -q
uv run pytest autoship-sdk/tests -q
uv run bandit -r src -ll
uv run pip-audit --desc
```

- [ ] ruff lint 通过
- [ ] ruff format 检查通过
- [ ] pyright 类型检查通过
- [ ] autoship 单元测试通过（覆盖率 ≥ 85%）
- [ ] autoship-sdk 测试通过
- [ ] bandit 安全扫描无中高危问题
- [ ] pip-audit 依赖漏洞扫描无未修复问题

## 3. 集成与性能测试

```bash
uv run python dogfood/dogfood.py
uv run python benchmarks/benchmark.py
```

- [ ] dogfood 冒烟测试通过
- [ ] benchmark 回归测试通过，未出现性能退化

## 4. 文档与网站

- [ ] 命令参考文档与实际 CLI 行为一致。
- [ ] `docs/index.md` 与 `README.md` 中的安装/快速开始步骤可复现。
- [ ] `docs/privacy.md` 与 `docs/telemetry.md` 中的数据收集范围准确。
- [ ] 本地预览 MkDocs 站点：`uv run mkdocs serve`，确认导航与链接正常。
- [ ] 官网 `website/` 构建通过：`cd website && npm install && npm run build`。

## 5. 签名密钥与凭证

- [ ] 用于签名 `verified` 插件的 PGP 私钥有效且未过期。
- [ ] PyPI/TestPyPI 发布令牌或 Trusted Publishing 配置有效。
- [ ] GitHub Actions 环境 `pypi` / `testpypi` 的审批规则已配置。

## 6. 发布执行

### 6.1 创建 Git Tag

```bash
git switch main
git pull origin main
git tag -a v<X.Y.Z> -m "Release v<X.Y.Z>"
git push origin v<X.Y.Z>
```

- [ ] tag 名称与版本号一致（例如 `v1.0.0`）。
- [ ] tag 指向 `main` 分支最新 commit。

### 6.2 触发 Release 工作流

tag push 会自动触发 [`.github/workflows/release.yml`](https://github.com/autoship-cli/autoship-cli/blob/main/.github/workflows/release.yml)：

- [ ] `pypi` / `testpypi` 自动路由正确（预发布 tag 进入 TestPyPI）。
- [ ] `autoship` 与 `autoship-sdk` wheel 上传成功。
- [ ] 多平台二进制与 SHA256 checksum 生成成功。
- [ ] GitHub Release Notes 自动生成并包含二进制 artifact。

## 7. 发布后验证

- [ ] PyPI/TestPyPI 页面显示新版本。
- [ ] `pip install autoship==<X.Y.Z>` 可正常安装。
- [ ] 下载 GitHub Release 中的二进制，执行 `autoship --help` 与 `autoship doctor` 正常。
- [ ] 官方文档站 `https://docs.autoship.dev` 已刷新。
- [ ] 官网 `https://autoship.dev` 已刷新（如涉及 website 改动）。

## 8. 安全公告与沟通

如本次发布包含安全修复：

- [ ] 在 `SECURITY.md` 中更新支持版本与修复说明。
- [ ] 通过 GitHub Security Advisory 发布安全公告。
- [ ] 在社区渠道（Discussions、Twitter/X、知乎等）同步发布信息。

---

## 历史发布记录

| 版本 | 发布日期 | 发布人 | 备注 |
|------|----------|--------|------|
| 1.0.0 | 2026-06-19 | AutoShip Team | 首个稳定版 |
| 1.0.0-rc.1 | 2026-06-19 | AutoShip Team | 首个 RC |
| 0.2.0-beta.1 | 2026-06-18 | AutoShip Team | Beta 预览 |
| 0.1.0 | 2026-06-18 | AutoShip Team | 初始版本 |
