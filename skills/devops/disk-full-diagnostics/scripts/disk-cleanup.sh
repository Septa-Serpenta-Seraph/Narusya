#!/bin/bash
# Disk cleanup script - run periodically or when space is low
# Part of disk-full-diagnostics skill

set -euo pipefail

echo "=== Disk Cleanup Start: $(date) ==="
echo "Before:"
df -h / | tail -1

# 1. Pip cache
if command -v pip &>/dev/null; then
    echo "Purging pip cache..."
    pip cache purge 2>/dev/null || true
fi

# 2. UV cache
if command -v uv &>/dev/null; then
    echo "Cleaning uv cache..."
    uv cache clean 2>/dev/null || true
fi

# 3. NPM cache
if command -v npm &>/dev/null; then
    echo "Cleaning npm cache..."
    npm cache clean --force 2>/dev/null || true
fi

# 4. Docker cleanup
if command -v docker &>/dev/null; then
    echo "Pruning docker..."
    docker builder prune -f 2>/dev/null || true
    docker image prune -af 2>/dev/null || true
fi

# 5. Hermes state-snapshots (keep latest 2)
SNAP_DIR="$HOME/.hermes/state-snapshots"
if [ -d "$SNAP_DIR" ]; then
    SNAP_COUNT=$(ls -d "$SNAP_DIR"/*/ 2>/dev/null | wc -l)
    if [ "$SNAP_COUNT" -gt 2 ]; then
        echo "Pruning old state-snapshots (keeping latest 2 of $SNAP_COUNT)..."
        ls -dt "$SNAP_DIR"/*/ | tail -n +3 | xargs rm -rf 2>/dev/null || true
    fi
fi

# 6. Electron cache
rm -rf ~/.cache/electron/* 2>/dev/null || true

# 7. Camoufox font cache
rm -rf ~/.cache/camoufox/fonts 2>/dev/null || true

# 8. Old session files (>30 days)
find ~/.hermes/sessions/ -name "request_dump_*" -mtime +7 -delete 2>/dev/null || true
find ~/.hermes/sessions/ -name "*.jsonl" -mtime +60 -delete 2>/dev/null || true

# 9. Old audio cache (>14 days)
find ~/.hermes/audio_cache/ -mtime +14 -delete 2>/dev/null || true

# 10. Old browser screenshots (>7 days)
find ~/.hermes/browser_screenshots/ -mtime +7 -delete 2>/dev/null || true

# 11. Apport log (needs sudo, skip if no access)
if [ -w /var/log/apport.log ]; then
    echo "Truncating apport.log..."
    truncate -s 0 /var/log/apport.log
fi

echo "After:"
df -h / | tail -1
echo "=== Disk Cleanup Done ==="
