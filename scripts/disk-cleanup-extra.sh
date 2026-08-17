#!/bin/bash
# Extra safe cleanup for cron disk alert - Narusya maintenance protocol
# Only touches regenerable caches. NO user data, NO live system dirs.
set -uo pipefail

echo "=== Extra Cleanup Start: $(date) ==="

# 1. HuggingFace hub cache - regenerates on next use (safe per disk-full-diagnostics skill)
if [ -d "$HOME/.cache/huggingface/hub" ]; then
    echo "Removing HuggingFace hub cache..."
    rm -rf "$HOME/.cache/huggingface/hub"
fi

echo "Done. Disk now:"
df -h / | tail -1
echo "=== Extra Cleanup Done ==="
