# 安全审计与渗透测试

本文档记录 AutoShip-CLI 的安全审计流程、工具配置与历史结果，供安全团队、审计人员和高级用户参考。

## 持续安全扫描

每次提交和 Nightly Build 都会运行以下安全扫描：

| 工具 | 作用 | 触发时机 |
|---|---|---|
| [bandit](https://bandit.readthedocs.io/) | Python SAST | CI、nightly |
| [pip-audit](https://pypi.org/project/pip-audit/) | 依赖漏洞扫描 | CI、nightly |
| [gitleaks](https://gitleaks.io/) | 密钥泄露检测 | CI、nightly |
| [ruff](https://docs.astral.sh/ruff/) | lint + 部分安全规则 | CI、pre-commit |
| Dependabot | 依赖自动更新 | 每周 |

## 发布前安全审计流程

在每次大版本发布前，安全团队应执行以下审计：

### 1. 代码审计

- 审查所有涉及外部输入的代码路径（CLI 参数、配置文件、插件、模型响应）。
- 确认路径操作使用 `Path.resolve()` 并限制在允许范围内。
- 确认子进程调用不使用 `shell=True`，除非经用户显式授权。
- 检查敏感数据是否通过 `autoship.core.redaction` 或等价逻辑脱敏。

### 2. 配置与凭证审计

- 确认默认配置关闭遥测与外部模型后端。
- 确认 API key、token 等字段支持 `${ENV_VAR}` 注入。
- 验证配置文件默认权限为 `0o600`。

### 3. 插件安全审计

- 使用 `autoship plugin verify <package>` 检查第三方插件的声明权限与实际行为。
- 对申请 `verified` 等级的插件进行源码审查。
- 确认 `sandbox` 对插件的文件系统访问进行限制。

### 4. 依赖与供应链审计

- 运行 `uv run pip-audit --desc` 并修复所有 `HIGH` 级别漏洞。
- 检查 `pyproject.toml` 中依赖是否有未固定版本或已知问题。
- 确认 release.yml 使用 Trusted Publishing 或最小权限 PyPI token。

### 5. 渗透测试检查清单

| 测试项 | 方法 | 预期结果 |
|---|---|---|
| 路径穿越 | 构造 `../../../etc/passwd` 类参数 | 被拒绝或解析后仍在允许目录 |
| 命令注入 | 在 commit message / diff 中嵌入反引号与分号 | 不会被 shell 解析执行 |
| SSRF | 配置指向内网地址的模型后端 | 遵循用户配置，但默认不信任 |
| 敏感信息泄露 | 触发异常并检查日志 | 无 API key、密码、token 明文 |
| 插件越权 | 安装声明低权限但尝试高权限操作的插件 | 被权限检查拦截 |
| 拒绝服务 | 1000+ 文件项目 + 超长 diff | 在超时内完成，不崩溃 |

## 历史审计结果

### 2026-06-19 v1.0.0 内部安全审查

- **执行方**：AutoShip 安全团队
- **范围**：CLI、核心库、内置插件、registry、CI/CD
- **结果**：
  - bandit：0 个 High/Medium
  - pip-audit：0 个未修复漏洞
  - 路径穿越与命令注入测试：通过
  - 敏感信息泄露测试：通过
  - 插件权限测试：通过
- **遗留风险**：
  - 本地模型后端默认使用 HTTP，需依赖用户环境安全。
  - 第三方 community 插件未经过完整源码审计，用户需自行判断。

### 计划中的外部审计

- **目标版本**：v1.1.0
- **执行方**：第三方安全公司 / 社区红队
- **范围**：完整 CLI 攻击面、插件系统、供应链
- **交付物**：渗透测试报告、修复建议、公开摘要

## 如何报告安全问题

请遵循 [SECURITY.md](https://github.com/MS33834/autoship-cli/blob/main/SECURITY.md) 中的流程，通过邮件私下报告。
