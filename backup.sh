#!/usr/bin/env bash
set -euo pipefail

# Backup script for Narusya Hermes Agent
# Pushes changes to GitHub remote 'origin'

cd "$(dirname "$0")"
git add -A
git commit -m "Automatic backup $(date '+%Y-%m-%d %H:%M:%S')" || echo "No changes to commit"
git push origin main
echo "Backup completed."
