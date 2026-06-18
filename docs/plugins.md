# 插件

AutoShip-CLI 采用 [pluggy](https://pluggy.readthedocs.io/) 实现插件化架构。插件通过声明生命周期钩子（Hooks）来扩展命令行为，例如在执行 `verify` 前做额外检查，或在命令失败时给出 AI 修复建议。

## 官方内置插件

### security-scan

在 `pre_commit` 阶段运行 `bandit`/`gitleaks`/`osv-scanner` 等安全检查，发现达到阈值的问题时阻止提交。

```toml
[security]
enabled = true
tools = ["bandit"]
threshold = "medium"
fail_fast = true
```

```bash
autoship commit
# 若 security-scan 发现中危及以上问题，将中止提交
```

### docker-ship

在 `autoship upload --target docker` 前后自动构建/推送 Docker 镜像。

```toml
[docker_ship]
enabled = true
default_image = "myapp"
default_tag = "latest"
push = true
```

```bash
autoship upload --target docker --image myapp --tag 0.1.0
```

### web-search

当 `verify --fix` 失败且配置中 `web_search.enabled = true` 时，联网搜索错误上下文并辅助生成修复建议。默认关闭。

```toml
[web_search]
enabled = true
provider = "duckduckgo"
max_results = 3
```

```bash
autoship verify pytest --fix
```

!!! warning "隐私提醒"
    启用 `web-search` 后，错误摘要会被发送到公共搜索服务。启用前请确认你愿意共享这些信息。

## 插件管理 CLI

AutoShip 内置插件管理命令，方便查看、安装和配置第三方插件：

```bash
# 列出已注册插件
autoship plugin list

# 安装插件（支持 PyPI 包名、本地路径或 git URL）
autoship plugin install my-plugin

# 调整插件信任等级
autoship plugin trust my-plugin verified

# 卸载插件
autoship plugin uninstall my-plugin
```

信任等级分为：`builtin`、`verified`、`community`、`untrusted`。默认安装的第三方插件为 `community`，建议仅在审阅源码后再提升为 `verified`。

## 可用钩子

所有钩子定义在 `autoship.hookspec.AutoShipHookSpec` 中：

| 钩子名 | 触发时机 | 返回值 |
|---|---|---|
| `pre_init` | `autoship init` 写入配置文件之前 | `None` |
| `post_init` | `autoship init` 写入配置文件之后 | `None` |
| `pre_clean` | `autoship clean` 运行清理工具之前 | `None` |
| `post_clean` | `autoship clean` 运行清理工具之后 | `None` |
| `pre_commit` | `autoship commit` 生成提交信息之前 | `None` |
| `post_commit` | `autoship commit` 完成之后 | `None` |
| `pre_verify` | `autoship verify` 运行验证命令之前 | `None` |
| `post_verify` | `autoship verify` 完成之后 | `None` |
| `pre_upload` | `autoship upload` 发布产物之前 | `None` |
| `post_upload` | `autoship upload` 完成之后 | `None` |
| `on_error` | 命令执行抛出异常时 | `FixSuggestion \| None` |

`on_error` 是唯一允许返回值的钩子。当命令带 `--fix` 标志失败时，AutoShip 会收集所有 `FixSuggestion`，展示给用户并可选地应用补丁。

## 开发自定义插件

请参考 [插件开发指南](plugin-development.md) 了解如何创建、打包、注册和测试自己的插件。
