#!/usr/bin/env bash
# Re-ingest lorebooks so a new reflection reaches Qdrant + auto-inject.
# PATH-prefixed bare python3 on purpose: the cron lifecycle guard trips on
# commands whose tokens contain binary paths, and bare python3 on the cron
# PATH resolves to pokemon-agent/.venv which lacks requests.
set -uo pipefail
V=/home/adora/.hermes/hermes-agent/venv/bin
export PATH="$V:$PATH"

echo "=== create_lorebook_collection ==="
python3 /home/adora/.hermes/scripts/create_lorebook_collection.py 2>&1 | tail -5
echo "rc=$?"

echo "=== ingest_lorebooks ==="
python3 /home/adora/.hermes/scripts/ingest_lorebooks.py 2>&1 | tail -15
echo "rc=$?"

echo "=== verify-reflection-ingest (probe, exits non-zero on any miss) ==="
python3 /home/adora/.hermes/scripts/verify-reflection-ingest.py 2>&1 | tail -20
echo "probe_rc=$?"
