# 插件发布指南（Plugin Publishing Guide）

本文档说明如何将插件提交到 AutoShip 官方插件商店。

## 1. 发布流程概览

1. 使用 [examples/custom-plugin](../examples/custom-plugin) 作为模板开发插件。
2. 在本地完成测试，确保至少通过 `ruff check`、`pytest` 以及 AutoShip 的 `plugin verify`。
3. 为插件包生成 sha256 校验和，并可选地生成 PGP 签名。
4. 将包发布到 PyPI（或 GitHub Release 等可 pip 安装的位置）。
5. 向本仓库提交 PR，在 `registry/plugins.json` 中新增插件条目。
6. 维护者审核通过后合并，插件自动出现在 [registry-web](../registry-web)。

## 2. 元数据格式

每个插件条目必须是一个 JSON 对象，字段如下：

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `name` | string | 是 | 插件唯一标识，仅允许小写字母、数字、连字符。 |
| `package` | string | 是 | pip 安装包名，例如 `autoship-commit-sign`。 |
| `module` | string | 是 | Python 导入路径，例如 `autoship_commit_sign.plugin`。 |
| `version` | string | 是 | 语义化版本号，例如 `1.2.3`。 |
| `description` | string | 是 | 一句话描述。 |
| `trust_level` | string | 是 | `builtin` / `verified` / `community` / `untrusted`。 |
| `entry_point` | string | 是 | 插件入口，例如 `autoship_commit_sign.plugin:CommitSignPlugin`。 |
| `hooks` | string[] | 是 | 支持的钩子，例如 `["pre_commit", "post_commit"]`。 |
| `publisher` | object | 是 | `{ id, verified, url }`，`verified` 需管理员确认。 |
| `maintainer` | string | 是 | 维护者姓名与联系邮箱。 |
| `license` | string | 是 | SPDX 许可证标识。 |
| `sha256` | string | 推荐 | 发布包（wheel）的 sha256 校验和。`verified` 插件必填。 |
| `signature` | string | 推荐 | 使用 AutoShip 官方私钥对 sha256 进行 base64 编码的签名。`verified` 插件必填。 |
| `permissions` | object | 是 | `{ filesystem, network, shell, git, env }`，声明插件所需权限。 |
| `categories` | string[] | 是 | 分类标签，例如 `["security", "git"]`。 |
| `tags` | string[] | 否 | 搜索关键词。 |
| `homepage` | string | 推荐 | 插件主页 URL。 |
| `source_url` | string | 推荐 | 源码仓库 URL。 |
| `downloads` | integer | 否 | 下载次数，由注册表维护。 |
| `rating` | object | 否 | `{ score, count }`，由注册表维护。 |
| `audit_status` | string | 是 | `pending` / `approved` / `rejected`，新提交为 `pending`，管理员审核后更新。 |

完整示例：

```json
{
  "name": "commit-sign",
  "package": "autoship-commit-sign",
  "module": "autoship_commit_sign.plugin",
  "version": "1.0.0",
  "description": "自动为生成的 commit 添加签名。",
  "trust_level": "verified",
  "entry_point": "autoship_commit_sign.plugin:CommitSignPlugin",
  "hooks": ["pre_commit"],
  "publisher": {
    "id": "alice-chen",
    "verified": true,
    "url": "https://github.com/alice-chen"
  },
  "maintainer": "Alice Chen <alice@example.com>",
  "license": "MIT",
  "sha256": "a3f5c8e2b4d6f7a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5",
  "signature": "base64-encoded-pgp-signature",
  "permissions": {
    "filesystem": "read-only",
    "network": false,
    "shell": false,
    "git": true,
    "env": []
  },
  "categories": ["security", "git"],
  "tags": ["gpg", "sign", "commit"],
  "downloads": 0,
  "rating": { "score": 0.0, "count": 0 },
  "homepage": "https://github.com/example/autoship-commit-sign",
  "source_url": "https://github.com/example/autoship-commit-sign",
  "audit_status": "approved"
}
```

## 3. 校验和与签名要求

### 3.1 计算 sha256

```bash
python -m build --wheel
sha256sum dist/autoship_commit_sign-1.0.0-py3-none-any.whl
```

将输出的 64 位十六进制字符串写入 `registry/plugins.json` 的 `sha256` 字段。

### 3.2 生成签名（verified 插件）

只有 `trust_level: verified` 的插件才需要签名。管理员使用 AutoShip 官方 PGP 私钥对 sha256 字符串签名：

```bash
echo -n "<sha256-hex>" | gpg --armor --detach-sign --output signature.asc
# 将 base64 编码后的签名内容写入 registry/plugins.json
base64 -w 0 signature.asc
```

如果插件未申请 `verified` 等级，则保持 `trust_level: community` 且不填写 `sha256`/`signature`。

## 4. PR 模板

提交插件到 `registry/plugins.json` 时，请在 PR 描述中填写以下内容：

```markdown
## Plugin Submission

- **Plugin name**:
- **PyPI package name**:
- **Source URL**:
- **Requested trust level**: community / verified
- **sha256 of wheel**:
- **Signature** (if verified):

## Checklist

- [ ] 插件源码仓库包含 `README.md`、开源许可证与使用示例。
- [ ] 插件至少通过 `pytest` 与 `ruff check`。
- [ ] 已使用 `autoship plugin verify <package>` 验证安装。
- [ ] 已填写 `permissions`，且权限范围不超过插件实际所需。
- [ ] 已提供 wheel 的 sha256 校验和（verified 插件还需提供签名）。
- [ ] 我已阅读并同意 [隐私政策](./privacy.md)。
```

## 5. 审核与上架

1. 自动检查：CI 会校验 JSON schema、sha256 格式与必填字段。
2. 安全审核：维护者审查 `permissions`、`network`、`shell` 等高敏感声明。
3. 体验审核：确认文档、错误提示与使用示例完整。
4. 合并后：registry-web 自动部署，用户可通过 `autoship plugin search <name>` 找到插件。

## 6. 更新与下架

- **版本更新**：提交新的 PR，更新 `version`、`sha256`、`signature`。
- **下架插件**：将 `audit_status` 改为 `rejected` 并说明原因；严重安全问题的插件会被移出注册表。

## 7. 相关资源

- [插件开发示例](../examples/custom-plugin)
- [插件注册表 schema](../registry/schema.json)
- [插件注册表 Web UI](../registry-web)
