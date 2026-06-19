const fs = require("fs");
const path = require("path");

const rootDir = path.resolve(__dirname, "..");
const distDir = path.join(rootDir, "dist");
const registryPath = path.join(rootDir, "..", "src", "autoship", "registry", "plugins.json");
const indexPath = path.join(rootDir, "index.html");
const distIndexPath = path.join(distDir, "index.html");

function copyFile(src, dest) {
  fs.mkdirSync(path.dirname(dest), { recursive: true });
  fs.copyFileSync(src, dest);
}

function main() {
  if (!fs.existsSync(registryPath)) {
    console.error(`Registry index not found: ${registryPath}`);
    process.exit(1);
  }

  const registry = JSON.parse(fs.readFileSync(registryPath, "utf-8"));

  let html = fs.readFileSync(indexPath, "utf-8");
  html = html.replace(
    "<!-- PLUGIN_DATA_PLACEHOLDER -->",
    `<script>window.PLUGIN_REGISTRY = ${JSON.stringify(registry)};</script>`
  );

  fs.mkdirSync(distDir, { recursive: true });
  fs.writeFileSync(distIndexPath, html, "utf-8");
  copyFile(path.join(rootDir, "styles.css"), path.join(distDir, "styles.css"));
  copyFile(path.join(rootDir, "app.js"), path.join(distDir, "app.js"));

  console.log(`Built registry web UI with ${registry.plugins.length} plugins.`);
}

main();
