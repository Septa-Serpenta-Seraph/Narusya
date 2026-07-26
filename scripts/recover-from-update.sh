#!/bin/bash
# Narusya Post-Update Recovery Script
# Run this if plugins, config, or memory systems break after a Hermes update

set -e

echo "🐍 Narusya Post-Update Recovery"
echo "==============================="

# 1. Check if user plugins survived
if [ -d "$HOME/.hermes/plugins/qdrant-memory" ]; then
    echo "✅ User plugin directory intact"
else
    echo "⚠️  User plugin missing. Restoring from latest backup..."
    LATEST=$(ls -d $HOME/Desktop/Narusya-Archive/pre-update-backup-* 2>/dev/null | tail -1)
    if [ -n "$LATEST" ]; then
        cp -r "$LATEST/plugins-user/qdrant-memory" "$HOME/.hermes/plugins/"
        echo "✅ Restored from $LATEST"
    else
        echo "❌ No backup found! Manual recovery needed."
        exit 1
    fi
fi

# 2. Check if bundled plugin was wiped (expected)
if [ -d "$HOME/.hermes/hermes-agent/plugins/memory/qdrant" ]; then
    echo "✅ Bundled plugin still exists (unexpected but fine)"
else
    echo "ℹ️  Bundled plugin wiped (expected after update)"
fi

# 3. Verify config has plugins section
if grep -q "plugins:" "$HOME/.hermes/config.yaml"; then
    echo "✅ Config has plugins section"
else
    echo "⚠️  Config missing plugins section. Check backup."
fi

# 4. Verify lorebooks
LOREBOOK_COUNT=$(ls $HOME/.hermes/lorebooks/*.md 2>/dev/null | wc -l)
echo "✅ Lorebooks: $LOREBOOK_COUNT files"

# 5. Verify secrets
if [ -f "$HOME/.hermes/.env" ]; then
    echo "✅ Secrets (.env) intact"
else
    echo "❌ Secrets missing!"
fi

# 6. Restart gateway (if running)
if systemctl --user is-active hermes-gateway &>/dev/null; then
    echo "🔄 Restarting Hermes gateway..."
    systemctl --user restart hermes-gateway
    echo "✅ Gateway restarted"
else
    echo "ℹ️  Gateway not running as systemd service. Restart manually."
fi

echo ""
echo "🜂 Recovery complete. So written, so lived, so free."
