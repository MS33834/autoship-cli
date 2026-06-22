# AutoShip Website

AutoShip 产品官网的静态页面，包含首页与插件介绍页。

## 页面

- `index.html`：产品首页，展示核心功能、工作流与插件生态入口。
- `plugins.html`：插件生态介绍页，链接到插件市场。
- `styles.css`：共享样式。

## 本地预览

```bash
cd website
python -m http.server 8080
# 浏览器打开 http://localhost:8080
```

## 部署

本目录为纯静态站点，可直接部署到 GitHub Pages、Cloudflare Pages、Vercel、Netlify 等静态托管服务。

如果与 `registry-web/` 一起部署，确保 `/registry-web/` 路径可访问，以便用户从首页跳转到插件市场。
