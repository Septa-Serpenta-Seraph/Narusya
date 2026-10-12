#!/usr/bin/env bash
# Re-ingest lorebooks so a new reflection reaches Qdrant + auto-inject.
#
# PYTHON BIN NOTE (2026-10-11): the venv at hermes-agent/venv/bin is currently
# BROKEN — its python3/python3.11 are dangling symlinks to a deleted runtime
# interpreter (the Oct 8 manual reinstall moved the runtime; the venv's
# pyvenv.cfg still points at the old generation dir). So we resolve a working
# python with `requests` + `fastembed` at runtime, preferring an installs
# environment venv. If the hermes venv is ever repaired, restore V first.

set -uo pipefail

find_python() {
  for cand in \
    /home/adora/.hermes/hermes-agent/venv/bin/python3 \
    /home/adora/.hermes/installs/*/environments/*/venv/bin/python3 \
    /usr/bin/python3; do
    for p in $cand; do
      [ -x "$p" ] || continue
      if "$p" -c "import requests" 2>/dev/null; then
        echo "$p"; return 0
      fi
    done
  done
  return 1
}

PYBIN="$(find_python)"
if [ -z "${PYBIN:-}" ]; then
  echo "ERROR: no python with 'requests' found. Aborting ingest." >&2
  exit 1
fi
echo "using python: $PYBIN"

echo "=== create_lorebook_collection ==="
"$PYBIN" /home/adora/.hermes/scripts/create_lorebook_collection.py 2>&1 | tail -5
echo "rc=$?"

echo "=== ingest_lorebooks ==="
"$PYBIN" /home/adora/.hermes/scripts/ingest_lorebooks.py 2>&1 | grep -vE "onnxruntime|W:onnx" | tail -15
echo "rc=$?"

echo "=== verify-reflection-ingest (probe, exits non-zero on any miss) ==="
"$PYBIN" /home/adora/.hermes/scripts/verify-reflection-ingest.py 2>&1 | tail -20
echo "probe_rc=$?"
