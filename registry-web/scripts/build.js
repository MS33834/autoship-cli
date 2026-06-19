const fs = require("fs");
const path = require("path");

const rootDir = path.resolve(__dirname, "..");
const distDir = path.join(rootDir, "dist");
const registryPath = path.join(rootDir, "..", "registry", "plugins.json");

function copyFile(src, dest) {
  fs.mkdirSync(path.dirname(dest), { recursive: true });
  fs.copyFileSync(src, dest);
}

function buildHtml(inputPath, outputPath, registry) {
  let html = fs.readFileSync(inputPath, "utf-8");

  // Determine which app script to load from the source HTML loader.
  const loaderMatch = html.match(/<script id="plugin-data-loader"[^>]*data-app-script="([^"]*)"[^>]*>/);
  const appScript = loaderMatch ? loaderMatch[1] : "app.js";

  // Replace the runtime loader with the injected registry data and the app script.
  html = html.replace(
    /<script id="plugin-data-loader"[\s\S]*?<\/script>/,
    `<script>window.PLUGIN_REGISTRY = ${JSON.stringify(registry)};</script>\n  <script src="${appScript}"></script>`
  );

  fs.mkdirSync(path.dirname(outputPath), { recursive: true });
  fs.writeFileSync(outputPath, html, "utf-8");
}

function main() {
  if (!fs.existsSync(registryPath)) {
    console.error(`Registry index not found: ${registryPath}`);
    process.exit(1);
  }

  const registry = JSON.parse(fs.readFileSync(registryPath, "utf-8"));

  buildHtml(path.join(rootDir, "index.html"), path.join(distDir, "index.html"), registry);
  buildHtml(path.join(rootDir, "dashboard.html"), path.join(distDir, "dashboard.html"), registry);

  copyFile(path.join(rootDir, "styles.css"), path.join(distDir, "styles.css"));
  copyFile(path.join(rootDir, "app.js"), path.join(distDir, "app.js"));
  copyFile(path.join(rootDir, "dashboard.js"), path.join(distDir, "dashboard.js"));

  console.log(`Built registry web UI with ${registry.plugins.length} plugins.`);
}

main();
