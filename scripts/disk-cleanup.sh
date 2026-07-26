#!/bin/bash
# Disk cleanup script - run periodically or when space is low
# Narusya maintenance protocol

set -euo pipefail

echo "=== Disk Cleanup Start: $(date) ==="
echo "Before:"
df -h / | tail -1

# 1. Pip cache
if command -v pip &>/dev/null; then
    echo "Purging pip cache..."
    pip cache purge 2>/dev/null || true
fi

# 2. UV cache (keep last 7 days)
if command -v uv &>/dev/null; then
    echo "Pruning uv cache..."
    uv cache prune --ci 2>/dev/null || true
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
    docker image prune -f 2>/dev/null || true
    docker system prune -f --volumes 2>/dev/null || true
fi

# 5. Old session files (>30 days)
find ~/.hermes/sessions/ -name "request_dump_*" -mtime +7 -delete 2>/dev/null || true
find ~/.hermes/sessions/ -name "*.jsonl" -mtime +60 -delete 2>/dev/null || true

# 6. Old audio cache (>14 days)
find ~/.hermes/audio_cache/ -mtime +14 -delete 2>/dev/null || true

# 7. Old browser screenshots (>7 days)
find ~/.hermes/browser_screenshots/ -mtime +7 -delete 2>/dev/null || true

# 8. Apport log (needs sudo, skip if no access)
if [ -w /var/log/apport.log ]; then
    echo "Truncating apport.log..."
    truncate -s 0 /var/log/apport.log
fi

echo "After:"
df -h / | tail -1
echo "=== Disk Cleanup Done ==="
