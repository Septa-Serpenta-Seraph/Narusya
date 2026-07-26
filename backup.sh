#!/usr/bin/env bash
set -euo pipefail

# Backup script for Narusya Hermes Agent
# Pushes changes to GitHub remote 'origin'
# FIX 2026-07-26: live ~/.hermes/skills (and other live dirs) are MIRRORED into
# the repo before commit, so skill edits actually back up. Secrets stay excluded
# via .gitignore (.env, *.enc, etc).

REPO="$(cd "$(dirname "$0")" && pwd)"
HERMES_HOME="${HERMES_HOME:-$HOME/.hermes}"

cd "$REPO"

# --- Mirror live sources into the repo (respects .gitignore) ---
# Skills: live edits (e.g. voice-forge patches) -> repo/skills
if [ -d "$HERMES_HOME/skills" ]; then
  rsync -a --delete \
    --exclude='.git' \
    "$HERMES_HOME/skills/" "$REPO/skills/"
fi

# Lorebooks: live lorebook dir -> repo/lorebooks (gitignore still hides private ones)
if [ -d "$HERMES_HOME/lorebooks" ]; then
  rsync -a --delete \
    --exclude='.git' \
    "$HERMES_HOME/lorebooks/" "$REPO/lorebooks/"
fi

# Scripts: live scripts -> repo/scripts
if [ -d "$HERMES_HOME/scripts" ]; then
  rsync -a --delete \
    --exclude='.git' \
    "$HERMES_HOME/scripts/" "$REPO/scripts/"
fi

# Config: copy config.yaml (NOT .env — secrets stay local)
if [ -f "$HERMES_HOME/config.yaml" ]; then
  cp "$HERMES_HOME/config.yaml" "$REPO/config.yaml"
fi

# --- Commit + push ---
git add -A
git commit -m "Automatic backup $(date '+%Y-%m-%d %H:%M:%S')" || echo "No changes to commit"
git push origin main
echo "Backup completed."
