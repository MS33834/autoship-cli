# Phase B — 插件生态压力测试设计

## 目标
构造 4 个具有不同复杂度与行为模式的插件，验证 AutoShip 插件系统在多插件共存、沙箱隔离、权限声明、错误恢复等方面的承载能力。

## 4 个复杂插件

| 插件 | 复杂度 | 验证重点 |
|------|--------|---------|
| `autoship-lifecycle-logger` | 注册全部 9 个 hook | hook 调用顺序、多插件串行执行、输出不冲突 |
| `autoship-policy-guard` | pre_commit / pre_verify / on_error 组合逻辑 | 插件对项目状态的深度检查与修复建议 |
| `autoship-network-probe` | 声明 network 能力并尝试外部请求 | 沙箱对 network 的隔离/放行策略 |
| `autoship-faulty-hook` | 在 hook 中抛出异常 | fail_fast / fail_fast=False 时的错误边界 |

## 执行方式
1. 在临时目录生成 4 个完整插件包（含 `pyproject.toml`、源码、测试）。
2. 通过 `autoship plugin install <abs-path> --yes --trust community` 本地安装。
3. 在一个目标项目中依次运行 `init`、`clean`、`verify`（触发失败）、`commit` 等命令，观察多个插件的 hook 协同行为。
4. 对每个插件单独使用 `PluginTestHarness` 进行隔离测试。
5. 最后卸载全部插件并清理注册表。

## 通过标准
- 4 个插件均可被 CLI 发现并安装。
- `lifecycle-logger` 在目标命令执行期间打印全部预期 hook 且不崩溃。
- `policy-guard` 在 verify 失败时返回 `FixSuggestion`。
- `network-probe` 在沙箱内网络请求被拦截（沙箱可用时），在非沙箱或声明 network 时可达。
- `faulty-hook` 的异常被捕获，且不会导致 CLI 整体不可恢复。
