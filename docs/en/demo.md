# Demo Script & Recording Guide

This page provides the asciinema demo recording script for AutoShip-CLI. Save the script content and use [asciinema](https://asciinema.org/) to record and export it as `website/demo.cast`.

## Recommended Recording Environment

- Terminal size: 80x24 or 120x30
- Font: monospace font; Fira Code or JetBrains Mono recommended
- Theme: dark background, high contrast
- Clear command: `clear`

## Demo Script

```bash
# 1. Welcome & installation
clear
echo "$ pipx install autoship"
pipx install autoship --quiet 2>/dev/null || echo "(already installed)"

# 2. Version & help
clear
echo "$ autoship --version"
autoship --version
echo ""
echo "$ autoship --help"
autoship --help

# 3. Initialize project
clear
echo "$ autoship init --yes"
autoship init --yes

# 4. View doctor diagnostics
clear
echo "$ autoship doctor"
autoship doctor

# 5. Clean code
clear
echo "$ autoship clean"
autoship clean --yes

# 6. Verify
clear
echo "$ autoship verify python --version"
autoship verify python --version

# 7. Plugin list
clear
echo "$ autoship plugin list"
autoship plugin list

# 8. Generate commit message (demo mode, no actual commit)
clear
echo "$ git diff --cached | autoship commit --dry-run"
git diff --cached 2>/dev/null | autoship commit --dry-run || echo "(demo: no staged changes)"

# 9. Upload (demo mode)
clear
echo "$ autoship upload --target pypi --dry-run"
autoship upload --target pypi --dry-run

# 10. End
clear
echo "Thanks for trying AutoShip!"
echo ""
echo "  pipx install autoship"
echo "  https://autoship.dev"
```

## Recording Command

```bash
# Install asciinema
pipx install asciinema

# Record
cd /workspace/autoship-cli
asciinema rec website/demo.cast --command "bash docs/demo-script.sh"

# Play back to verify
asciinema play website/demo.cast
```

## Embedding on the Official Website

After uploading `website/demo.cast` to asciinema.org, you can embed the player in `website/index.html`:

```html
<script src="https://asciinema.org/a/xxxxxx.js" id="asciicast-xxxxxx" async></script>
```

Or use the [mkdocs-asciinema](https://github.com/t6g/mkdocs-asciinema) plugin in the documentation site.
