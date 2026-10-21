#!/usr/bin/env python3
"""Persistent local fastembed daemon.

Reads JSON lines on stdin:  {"id": <n>, "texts": ["...", ...]}
Writes JSON lines on stdout: {"id": <n>, "vectors": [[...], ...], "error": null}

The model is loaded once at startup and stays warm, so each batch costs only
the inference time. Runs under a dedicated Python that can host fastembed
(/mnt/data/fe-venv) because the Hermes runtime interpreter cannot.
"""
import json
import os
import sys

# Defensive: never import another interpreter's site-packages. The Hermes runtime
# puts its own dependency env on sys.path (via PYTHONPATH); a python3.12 process
# that picks up a python3.14 PIL dies at import. Drop those entries.
_HERMES_INSTALLS = "/home/adora/.hermes/installs/"
sys.path[:] = [p for p in sys.path if _HERMES_INSTALLS not in p]

# Keep the model on the big data disk, not the root filesystem.
os.environ.setdefault("FASTEMBED_CACHE_PATH", "/mnt/data/fastembed_cache")

MODEL = "sentence-transformers/all-MiniLM-L6-v2"


def main() -> None:
    from fastembed import TextEmbedding

    model = TextEmbedding(model_name=MODEL)
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            req = json.loads(line)
        except Exception:
            continue
        texts = req.get("texts") or []
        try:
            vectors = [[float(x) for x in v] for v in model.embed(texts)]
            out = {"id": req.get("id"), "vectors": vectors, "error": None}
        except Exception as exc:  # noqa: BLE001 - report, never crash the daemon
            out = {"id": req.get("id"), "vectors": [], "error": str(exc)}
        sys.stdout.write(json.dumps(out) + "\n")
        sys.stdout.flush()


if __name__ == "__main__":
    main()
