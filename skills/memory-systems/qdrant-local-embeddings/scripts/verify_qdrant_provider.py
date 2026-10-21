#!/usr/bin/env python3
"""Probe the live qdrant memory provider the way the gateway does.

Run with the Hermes runtime interpreter (the one the gateway uses), not a
project venv:

    <live-env>/venv/bin/python verify_qdrant_provider.py

Prints the configured collection/backend, the provider's availability, the
embedder's output width, and the dimension + point count of every collection in
play. A provider that passes here but still reports unavailable in the gateway is
a gateway-side problem, not a plugin-side one — instrument the probe before
concluding the fix failed.
"""
import importlib.util
import json
import sys
import urllib.request
from pathlib import Path

AGENT_ROOT = Path.home() / ".hermes" / "hermes-agent"
PLUGIN = Path.home() / ".hermes" / "plugins" / "qdrant" / "__init__.py"
QDRANT = "http://localhost:6333"

sys.path.insert(0, str(AGENT_ROOT))

spec = importlib.util.spec_from_file_location("qdrant_plugin", PLUGIN)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

provider = module.QdrantMemoryProvider()
print(f"collection : {provider._collection}")
print(f"lorebook   : {provider._config.get('lorebook_collection')}")
print(f"backend    : {provider._config.get('embedding_backend')}")
print(f"available  : {provider.is_available()}")

vector = provider._embedder.embed("probe") if provider._embedder else None
print(f"embed dims : {len(vector) if vector else None}")

names = {provider._collection, provider._config.get("lorebook_collection")}
for name in sorted(n for n in names if n):
    try:
        info = json.loads(urllib.request.urlopen(f"{QDRANT}/collections/{name}", timeout=10).read())
        result = info["result"]
        size = result["config"]["params"]["vectors"]["size"]
        print(f"{name:40s} {size:5d}-dim  {result['points_count']} points")
    except Exception as exc:  # noqa: BLE001 - report, keep probing the rest
        print(f"{name:40s} ERROR {exc}")
