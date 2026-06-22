# 演示脚本与录制指南

本页面提供 AutoShip-CLI 的 asciinema 演示录制脚本。将脚本内容保存后，可使用 [asciinema](https://asciinema.org/) 录制并导出为 `website/demo.cast`。

## 推荐录制环境

- 终端尺寸：80x24 或 120x30
- 字体：等宽字体，推荐使用 Fira Code 或 JetBrains Mono
- 主题：深色背景，高对比度
- 清屏命令：`clear`

## 演示脚本

```bash
# 1. 欢迎与安装
clear
echo "$ pipx install autoship"
pipx install autoship --quiet 2>/dev/null || echo "(已安装)"

# 2. 版本与帮助
clear
echo "$ autoship --version"
autoship --version
echo ""
echo "$ autoship --help"
autoship --help

# 3. 初始化项目
clear
echo "$ autoship init --yes"
autoship init --yes

# 4. 查看 doctor 诊断
clear
echo "$ autoship doctor"
autoship doctor

# 5. 清理代码
clear
echo "$ autoship clean"
autoship clean --yes

# 6. 验证
clear
echo "$ autoship verify python --version"
autoship verify python --version

# 7. 插件列表
clear
echo "$ autoship plugin list"
autoship plugin list

# 8. 生成提交信息（演示模式，不实际提交）
clear
echo "$ git diff --cached | autoship commit --dry-run"
git diff --cached 2>/dev/null | autoship commit --dry-run || echo "(演示：无 staged changes)"

# 9. 上传（演示模式）
clear
echo "$ autoship upload --target pypi --dry-run"
autoship upload --target pypi --dry-run

# 10. 结束
clear
echo "Thanks for trying AutoShip!"
echo ""
echo "  pipx install autoship"
echo "  https://autoship.dev"
```

## 录制命令

```bash
# 安装 asciinema
pipx install asciinema

# 录制
cd /workspace/autoship-cli
asciinema rec website/demo.cast --command "bash docs/demo-script.sh"

# 播放验证
asciinema play website/demo.cast
```

## 在官网嵌入

将 `website/demo.cast` 上传到 asciinema.org 后，可在 `website/index.html` 中嵌入播放器：

```html
<script src="https://asciinema.org/a/xxxxxx.js" id="asciicast-xxxxxx" async></script>
```

或在文档站使用 [mkdocs-asciinema](https://github.com/t6g/mkdocs-asciinema) 插件。
