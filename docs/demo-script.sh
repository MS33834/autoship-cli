#!/usr/bin/env bash
# Demo script for asciinema recording.
# Usage: asciinema rec website/demo.cast --command "bash docs/demo-script.sh"
set -euo pipefail

pause() {
  sleep 1.5
}

# 1. Welcome and install
clear
echo "\$ pipx install autoship"
sleep 0.5
echo "installed autoship"
pause

# 2. Version and help
clear
echo "\$ autoship --version"
autoship --version
pause
echo ""
echo "\$ autoship --help"
autoship --help
pause

# 3. Initialize project
clear
echo "\$ autoship init --yes"
autoship init --yes
pause

# 4. Doctor
clear
echo "\$ autoship doctor"
autoship doctor
pause

# 5. Clean
clear
echo "\$ autoship clean --yes"
autoship clean --yes
pause

# 6. Verify
clear
echo "\$ autoship verify python --version"
autoship verify python --version
pause

# 7. Plugin list
clear
echo "\$ autoship plugin list"
autoship plugin list
pause

# 8. Commit dry-run
clear
echo "\$ autoship commit --dry-run"
autoship commit --dry-run || echo "(demo: no staged changes)"
pause

# 9. Upload dry-run
clear
echo "\$ autoship upload --target pypi --dry-run"
autoship upload --target pypi --dry-run
pause

# 10. End
clear
echo "Thanks for trying AutoShip!"
echo ""
echo "  pipx install autoship"
echo "  https://autoship.dev"
