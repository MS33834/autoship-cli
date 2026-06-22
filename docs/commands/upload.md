# upload

上传产物到已配置的目标，支持 PyPI、Docker 和 GitHub Release。

## 语法

```bash
autoship upload [OPTIONS]
```

## 参数

`upload` 命令不接受位置参数。

## 选项

| 短选项 | 长选项 | 默认值 | 说明 |
|:-:|:-:|:-:|---|
| - | `--target TEXT` | - | 上传目标，例如 `pypi`、`docker`、`github`（必填） |
| - | `--image TEXT` | - | Docker 镜像名称 |
| `-t` | `--tag TEXT` | - | Docker 镜像标签或 GitHub release 标签 |
| - | `--artifact TEXT` | - | 要上传的产物，可多次指定 |
| - | `--repository TEXT` | `testpypi` | PyPI repository 名称 |
| - | `--repository-url TEXT` | - | PyPI repository 上传 URL |
| - | `--registry TEXT` | - | Docker registry 前缀（例如 `localhost:5000`） |

## 示例

上传到 PyPI：

```bash
autoship upload --target pypi
```

上传 Docker 镜像：

```bash
autoship upload --target docker --image myapp --tag 0.1.0
```

发布 GitHub Release 并上传产物：

```bash
autoship upload --target github --tag v0.1.0 --artifact dist/*.whl
```

预览将要执行的动作而不真正上传：

```bash
autoship --dry-run upload --target pypi
```

## 输出说明 / 常见错误

- `--dry-run` 会打印将要执行的操作，适合在 CI 中预审。
- Docker 上传需要本地 Docker daemon 可访问。
- PyPI 上传默认使用 `testpypi`，生产环境请显式指定 `--repository pypi`。

## 相关命令

- [commit](./commit.md) — 先提交再上传
- [verify](./verify.md) — 上传前运行验证
