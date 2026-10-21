#!/usr/bin/env python3
"""Persistent local fastembed daemon: JSON lines in, JSON lines out.

Copy to ~/.hermes/scripts/embed_fastembed_local.py and chmod +x. The Hermes
runtime interpreter cannot import fastembed, so the qdrant memory provider shells
out to this helper; keeping the process alive means the model loads once and every
batch costs milliseconds instead of a cold start.

Reads   {"id": <n>, "texts": ["...", ...]}   per stdin line
Writes  {"id": <n>, "vectors": [[...], ...], "error": null}   per stdout line

Run under a fastembed-capable interpreter, e.g. /mnt/data/fe-venv/bin/python.
"""
import json
import os
import sys

# Keep the model weights on the data disk, never the root filesystem.
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
        except Exception as exc:  # noqa: BLE001 - report, never kill the daemon
            out = {"id": req.get("id"), "vectors": [], "error": str(exc)}
        sys.stdout.write(json.dumps(out) + "\n")
        sys.stdout.flush()


if __name__ == "__main__":
    main()
