---
title: 故障排查
---
# 故障排查

> 本页汇总 AutoShip 常见故障与排查思路。先尝试 `autoship doctor` 一键自检，再对照下文定位。命令代码块保持英文。

## 安装失败

### `autoship` 命令找不到（PATH 问题）

```bash
pipx list
pipx ensurepath
```

`pipx ensurepath` 会把 pipx 的 bin 目录写入 PATH。执行后**重开终端**或 `source` 你的 shell 配置（`~/.bashrc` / `~/.zshrc`）再试。

### pipx 与系统 pip 冲突

如果系统已用 `pip install autoship` 装过旧版，可能优先命中旧路径：

```bash
pip uninstall autoship
pipx install autoship
which -a autoship
```

### 权限不足 / EACCES

避免使用 `sudo pip install`。推荐：

```bash
pipx install autoship
# 或
uv tool install autoship
```

若必须用 pip，先确认 `python -m site --user-base` 指向的用户目录可写。

## `init` 卡住

### 交互式问卷卡住

`init` 默认会问若干问题。CI 或脚本环境请加 `--yes` 跳过：

```bash
autoship init --yes
```

### 卡在「检测模型后端」

`init` 会尝试探测本地 Ollama / LM Studio。后端未运行时会等待超时。可：

- 启动 Ollama 后重试；
- 或用 `--no-model` 跳过探测，事后再在 `.autoship.toml` 中配置。

## `clean` 误删恢复

`clean` 在删除无用 import / 重排代码前会把改动写入 Git 暂存区前的备份。若发现误删：

```bash
# 查看改动
git diff

# 丢弃 clean 的改动，恢复到 HEAD
git checkout -- .

# 若已 commit，回退一次
git reset --hard HEAD~1
```

> 建议在 `clean` 前先 `git status` 确认工作区干净，或加 `--dry-run` 预览。

## `commit` 空消息 / 超时

### 生成的 commit message 为空

- 确认有已暂存的改动：`git diff --cached`。
- 若使用 AI 后端，检查后端是否可用（见下条）。
- 临时回退到模板模式：

```bash
autoship commit --no-ai
```

### AI 生成超时

模型过大或后端响应慢会导致超时。在 `.autoship.toml` 调整：

```toml
[commit]
timeout_seconds = 60
```

或换用更小的本地模型。

## `verify --fix` 连不上后端

`verify --fix` 必须有可用 AI 后端，否则会报「no AI backend configured」。

```bash
# 1. 检查后端状态
autoship doctor

# 2. 确认 Ollama 在运行
ollama list

# 3. 用 verbose 看详细错误
autoship --verbose verify --fix pytest
```

详见 [已知问题](known-issues.md) 中「`verify --fix` 无 AI 后端不可用」。

## `upload` 凭证错误

### PyPI Token 无效 / 403

- 确认 token 是 **API Token**（非账号密码），且 scope 包含目标项目。
- 通过环境变量注入，避免写入配置：

```bash
export TWINE_PASSWORD=pypi-xxxxxxxx
autoship upload --target pypi
```

### Docker Registry 401

```bash
docker login ghcr.io
# 或
docker login registry.hub.docker.com
```

`upload --target docker` 依赖本机已 `docker login`。

## 三语切换不生效

### `--lang` 无效

```bash
autoship --lang en <command>
```

若输出仍是中文，检查：

1. `.autoship.toml` 中是否设置了 `locale`，配置优先级高于命令行参数以外的方式；
2. 当前安装版本是否支持该语言（运行 `autoship --version` 并对照发行说明）；
3. 文档站点的语言切换由 i18n 插件路由，与 CLI 输出语言相互独立。

详见 [常见问题](faq.md)「如何切换语言？」。

## 仍无法解决

- 运行 `autoship doctor` 并附上输出；
- 查看 [已知问题](known-issues.md)；
- 提交 issue：[GitHub Issues](https://github.com/MS33834/autoship-cli/issues)。
