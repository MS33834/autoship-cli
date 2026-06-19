const fs = require('fs');
const path = require('path');

const srcDir = path.join(__dirname, '..');
const distDir = path.join(srcDir, 'dist');

const files = ['index.html', 'styles.css'];

fs.mkdirSync(distDir, { recursive: true });

for (const file of files) {
  const src = path.join(srcDir, file);
  const dest = path.join(distDir, file);
  fs.copyFileSync(src, dest);
  console.log(`Copied ${file}`);
}

console.log('Build complete.');
