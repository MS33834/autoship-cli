# AutoShip Plugin Registry Web

AutoShip 插件市场的静态前端页面，可直接部署到任何静态托管服务（GitHub Pages、Cloudflare Pages、Vercel、Netlify 等）。

## 功能

- 插件卡片展示（名称、版本、信任等级、描述、发布者、分类、标签、下载量、评分）。
- 搜索：按名称、描述、标签过滤。
- 筛选：按信任等级、分类筛选。
- 排序：默认、下载量、评分、名称。
- 一键复制安装命令：`autoship plugin install <name>`。
- 详情弹窗展示完整插件元数据与来源链接。
- Dashboard：生态指标、分布统计、热门插件榜单。

## 本地预览

```bash
cd registry-web
python -m http.server 8080
# 浏览器打开 http://localhost:8080
```

## 数据源

页面通过 `fetch("../registry/plugins.json")` 加载插件数据。请确保部署时 `registry/plugins.json` 可通过相对路径访问。

如果需要在 `file://` 协议下预览，可以使用 `build.py` 将插件数据内联到 HTML 中。

## 部署

将整个 `registry-web` 目录与 `registry/plugins.json` 一起上传到静态托管服务即可。

例如 GitHub Pages：

```bash
# 在项目设置中启用 Pages，选择 / (root) 或 /docs 目录
# 将 registry-web 内容复制到 gh-pages 分支或 docs 目录
```
