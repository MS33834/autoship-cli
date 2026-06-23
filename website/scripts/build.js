const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

const srcDir = path.join(__dirname, '..');
const distDir = path.join(srcDir, 'dist');
const registryWebDir = path.join(srcDir, '..', 'registry-web');

const files = [
  'index.html',
  'index.zh.html',
  'index.ja.html',
  'plugins.html',
  'plugins.zh.html',
  'plugins.ja.html',
  'styles.css',
];

fs.mkdirSync(distDir, { recursive: true });

for (const file of files) {
  const src = path.join(srcDir, file);
  const dest = path.join(distDir, file);
  fs.copyFileSync(src, dest);
  console.log(`Copied ${file}`);
}

if (fs.existsSync(registryWebDir)) {
  console.log('Building registry web UI...');
  execSync('npm run build', { cwd: registryWebDir, stdio: 'inherit' });
  const registrySrc = path.join(registryWebDir, 'dist');
  const registryDest = path.join(distDir, 'registry');
  fs.mkdirSync(registryDest, { recursive: true });
  for (const file of fs.readdirSync(registrySrc)) {
    const src = path.join(registrySrc, file);
    const dest = path.join(registryDest, file);
    fs.cpSync(src, dest, { recursive: true });
  }
  console.log('Copied registry web UI to /registry');
}

console.log('Build complete.');
