#!/bin/bash
# AutoShip-CLI Dual-Remote Sync Script
# Pushes current branch to both GitHub (origin) and GitCode (gitcode)
set -e

BRANCH=$(git rev-parse --abbrev-ref HEAD)
echo "🔁 Syncing branch '$BRANCH' to both remotes..."

echo "→ Pushing to GitHub (origin)..."
git push origin "$BRANCH"

echo "→ Pushing to GitCode (gitcode)..."
git push gitcode "$BRANCH"

echo "✅ Sync complete!"
