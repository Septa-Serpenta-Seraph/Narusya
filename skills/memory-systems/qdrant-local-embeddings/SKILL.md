---
name: qdrant-local-embeddings
description: "Use when qdrant memory fails on paid embedding credits."
version: 1.0.0
author: Narusya
license: MIT
platforms: [linux]
metadata:
  hermes:
    tags: [qdrant, memory, embeddings, fastembed, credits]
    category: memory-systems
    related_skills: [qdrant-usage, hermes-infrastructure, gateway-auto-memory-debug]
---

# Qdrant Memory on Local Embeddings (no credits)

Hermes' qdrant memory provider embeds every turn and every query. When the
configured embedding APIs run out of credits, the provider reports
`not available` and semantic recall silently dies — while built-in
MEMORY.md/USER.md keeps working, so it looks like "memory is half-broken".

This skill is the fix: switch the provider to free, on-device fastembed
embeddings and migrate the existing memory into a matching-dimension collection.

For telling credits-exhaustion apart from a dead container or a missing
collection, see `hermes-infrastructure` §17 — it carries the diagnosis and the
scrubbed-environment replication recipe.

## When to Use

- The gateway or a cron reports `Memory provider 'qdrant' is selected but reports
  unavailable` while `hermes memory status` shows the plugin installed.
- Embedding calls return a credits error (Nous 404 `insufficient_credits_for_paid_model`,
  OpenRouter 402 `Insufficient credits`) and the account is genuinely out of money.
- Semantic recall silently stopped returning results but built-in MEMORY.md
  still works.
- You are moving the qdrant provider off paid embeddings onto free local
  fastembed (or migrating an existing collection to a new embedding dimension).

## Symptoms

- Gateway log / cron reports: `Memory provider 'qdrant' is selected but reports
  unavailable — external memory is disabled for this session`.
- `hermes memory status` shows `Provider: qdrant`, `Plugin: installed ✓`,
  `Status: not available ✗`.
- The embedding call returns an HTTP credit error: Nous
  `insufficient_credits_for_paid_model` (404) or OpenRouter `Insufficient
  credits` (402).

## Diagnose first (confirm it is credits, not config)

```bash
hermes memory status
```

Then hit both embedding endpoints directly to prove which one is dead. The
plugin reads its Nous token from `~/.hermes/shared/nous_auth.json` and its
OpenRouter key from `~/.hermes/.env`:

```python
import json, pathlib, requests
d = json.loads((pathlib.Path.home() / ".hermes/shared/nous_auth.json").read_text())
tok, base = d["access_token"], d.get("inference_base_url") or "https://inference-api.nousresearch.com/v1"
r = requests.post(f"{base}/embeddings",
                  headers={"Authorization": f"Bearer {tok}"},
                  json={"model": "text-embedding-3-large", "input": "test", "dimensions": 3072})
print(r.status_code, r.text[:200])
```

Nous has **no free embedding tier** — every embedding model returns the
credits error. Do not burn calls trying to find one.

## Why the usual toggle does not work

`~/.hermes/scripts/toggle_embeddings.py` only renames collections between a
"free 384-dim" and a "paid 3072-dim" set. It does **not** give the plugin a
local embedder. If the plugin has no local path, toggling collections alone
changes nothing. Check before trusting it.

## The fix

### 1. Find or create a fastembed-capable interpreter

The Hermes runtime interpreter cannot host fastembed (it needs its own
Python + onnxruntime). Look for an existing one before installing anything:

```bash
find / -maxdepth 9 -type d -name fastembed 2>/dev/null | grep -v proc
```

On this host it is `/mnt/data/fe-venv` (python3.12, fastembed 0.9.0,
onnxruntime 1.31.0). Verify it embeds:

```bash
/mnt/data/fe-venv/bin/python -c "
from fastembed import TextEmbedding
m = TextEmbedding(model_name='sentence-transformers/all-MiniLM-L6-v2')
print(len(list(m.embed(['test']))[0]))"
```

Model weights are cached at `/mnt/data/fastembed_cache` via
`FASTEMBED_CACHE_PATH`. Set that env var in any helper you write so the model
never lands on the root filesystem.

### 2. Give the plugin a local embedder

Add a `_LocalEmbedder` class that keeps a persistent helper subprocess warm
(one JSON request per batch, one JSON response back). Per-call subprocess
spawning would cost ~1.4s every embed; a warm daemon costs ~3ms.

Helper `scripts/embed_fastembed_local.py` in this skill — copy it to
`~/.hermes/scripts/embed_fastembed_local.py` and `chmod +x`. It reads JSON lines
(`{"id": n, "texts": [...]}`) on stdin and writes one JSON line per batch
(`{"id": n, "vectors": [...], "error": null}`) on stdout, keeping the model
warm so every batch costs milliseconds instead of a cold start. It sets
`FASTEMBED_CACHE_PATH` so the weights stay off the root filesystem.

Plugin side: extend `_EmbeddingClient` so `embed()` tries the local embedder
first and falls back to the API only if local fails, and set
`dimensions = 384` when the backend is local.

### 3. Fix the config loader (common silent bug)

`_load_plugin_config()` importing `yaml` fails silently — the runtime ships
**ruamel**, not PyYAML — so the plugin never read any config and ran on
defaults. Read whichever parser exists:

```python
try:
    from ruamel.yaml import YAML
    all_config = YAML(typ="safe").load(open(config_path))
except ImportError:
    import yaml
    all_config = yaml.safe_load(open(config_path))
```

Symptom: `QdrantMemoryProvider()._collection` shows the default collection and
`is_available()` is False even though `hermes config get plugins.qdrant-memory`
shows the right values.

### 4. Migrate the existing memory

Changing the embedding model changes vector dimensions, so the old collection
cannot be reused. Create a same-dimension collection and re-embed every point with
`scripts/backfill_memory_fastembed.py` in this skill — edit `SRC` / `DST` /
`DIMS`, then run it under the fastembed interpreter. It scrolls the source,
embeds in batches of 100, upserts into the destination, and reuses point ids.
Run it as a tracked background process; ~4,800 points takes ~90s.

### 5. Point config at the new collection

```bash
hermes config set plugins.qdrant-memory.embedding_backend local_fastembed
hermes config set plugins.qdrant-memory.local_embed_python /mnt/data/fe-venv/bin/python
hermes config set plugins.qdrant-memory.local_embed_script /home/adora/.hermes/scripts/embed_fastembed_local.py
hermes config set plugins.qdrant-memory.collection intelligent_gould_narusya_local
hermes config set plugins.qdrant-memory.lorebook_collection narusya_lorebooks_fe
```

The lorebook collection must match the new dimension too (384 here), or
lorebook recall breaks independently of memory recall.

### 6. Restart the gateway — the user must do this

The plugin is imported at gateway startup, so a restart is required. The
terminal tool blocks gateway lifecycle commands from inside the gateway
process (SIGTERM propagates to children), so ask the user to run:

```
hermes gateway restart
```

## Verify

```python
import sys, importlib.util
sys.path.insert(0, "/home/adora/.hermes/hermes-agent")
spec = importlib.util.spec_from_file_location("qdrant_plugin", "/home/adora/.hermes/plugins/qdrant/__init__.py")
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
p = m.QdrantMemoryProvider()
print(p._collection, p.is_available())
```

Then run a real recall against the new collection and confirm the returned
payload text is on-topic. Also confirm collection dimension matches:

```bash
curl -s http://localhost:6333/collections/<name> | python3 -c "import sys,json;print(json.load(sys.stdin)['result']['config']['params']['vectors']['size'])"
```

Or run the whole probe in one shot with `scripts/verify_qdrant_provider.py`
(configured collection + backend + availability + embed width + every
collection's dimension and point count).

### If the gateway still reports unavailable after the restart

The provider's availability probe swallows its own exception — `except
Exception: self._available = False`, with no log line — so a provider that
initializes cleanly in your standalone test can still report unavailable in the
gateway with nothing in the journal. Instrument the three probe steps before
concluding the fix failed:

1. **Log what `_load_plugin_config()` actually returned.** An empty dict means
   the plugin fell back to its defaults, not to your new settings — the classic
   cause is a `yaml` import the runtime cannot satisfy.
2. **Capture the embed daemon's stderr** to a file instead of `DEVNULL`. A
   daemon that dies on startup reads back as an empty line and looks exactly
   like "no embedder".
3. **Log the probe exception itself.**

Then have the user restart once more and read the boot log. The gateway checks
availability once per boot, so a session that booted while the provider was
broken stays broken until the next restart — re-running the probe in-session
will not clear the warning.

## Root cause found in practice (the trap that cost three restarts)

The plugin worked in every standalone test and failed only inside the gateway.
The reason: **the Hermes runtime exports `PYTHONPATH` pointing at its own
dependency environment** (`pm.environments.activate_dependencies` sets it). Any
subprocess the plugin spawns inherits that variable, so the separate fastembed
venv resolved `PIL` (and `onnxruntime`) from the runtime's *python3.14* env while
running under *python3.12* — and died instantly:

```
from PIL import Image
  File ".../installs/<hash>/.../python3.14/site-packages/PIL/Image.py", line 95
ImportError: cannot import name '_imaging' from 'PIL'
```

The plugin's `embed()` swallowed it and returned `None`, so the gateway only ever
saw `not available` with no error. Diagnosis required capturing the daemon's
stderr to a file (`stderr=open("~/.hermes/logs/embed_daemon.log", "ab")`), because
`stderr=DEVNULL` hides exactly this.

Fix — spawn the daemon with a clean interpreter environment, and scrub `sys.path`
inside the helper as well (defence in depth):

```python
env = dict(os.environ)
env.pop("PYTHONPATH", None)
env.pop("PYTHONHOME", None)
env["FASTEMBED_CACHE_PATH"] = "/mnt/data/fastembed_cache"
subprocess.Popen([python_bin, script], ..., env=env)
```

## Pitfalls

- **The runtime exports `PYTHONPATH`; never let a helper subprocess inherit it.**
  A separate venv will import the runtime's packages under the wrong Python
  version and die at import. Strip `PYTHONPATH`/`PYTHONHOME` from the child env.
- **Never reuse the old collection.** Dimensions differ (3072 vs 384); search
  against mismatched dimensions fails or returns garbage.
- **Do not leave the lorebook collection at the old dimension.** It breaks
  separately and looks like a different bug.
- **Never install into the Hermes runtime env to fix this.** The runtime
  interpreter cannot import fastembed anyway; use the separate venv and a
  subprocess daemon.
- **`uv pip install` from inside the gateway may hit the approval flow.** With
  `approvals.mode: manual`, the prompt can time out. Prefer the existing venv.
- **Keep the model cache off the root filesystem.** `FASTEMBED_CACHE_PATH`
  points at `/mnt/data/fastembed_cache`.
- **`yaml` vs `ruamel`:** the runtime has ruamel only. A plugin that imports
  `yaml` fails silently and silently ignores all config.
- **The probe swallows its exception.** `is_available()` catches everything and
  sets `_available = False` without logging, so a provider that works when you
  test it directly can look dead in the gateway. Log the exception before
  declaring the fix broken — and remember the gateway probes once per boot, so
  an in-session re-test never clears the warning.
