---
name: agent-memory-dreaming
description: "Build daemon memory reorganization (dreaming) systems. Memory systems are additive and connective — never subtractive. N3 is report-only, never modifies data."
tags: [memory, dreaming, qdrant, consolidation, clustering, reporting]
version: 1.0.0
author: Narusya
license: MIT
platforms: [linux]
metadata:
  hermes:
    tags: [memory, dreaming, qdrant, consolidation, clustering, reporting]
    related_skills: [qdrant-admin, qdrant-usage, memory-backup]
---

# Agent Memory Dreaming

Build systems that review, reorganize, correct, and prune stored agent memories during idle periods. Inspired by hippocampal replay (10-20x compressed replay during sleep), sleep-time compute (Letta/UC Berkeley, 2025), and Anthropic's dreaming research (2026).

## When to Use
- Building a new memory reorganization pipeline for an AI agent
- Adding dreaming/consolidation to an existing Qdrant-backed memory system
- Optimizing memory clustering or pruning performance
- Generating abstract narrative reflections from stored memories

## Architecture

A dreaming system has phases that run sequentially during idle time. The core principle: **memory systems are additive and connective, never subtractive.** They build connections, surface patterns, and report on health. They never remove data. The human decides what to keep and what to let go.

1. **N1 — Light consolidation**: Find exact duplicates, report them. Remove only byte-identical redundant copies (safe — no information lost). Log every removal.
2. **N2 — Spindle**: Cluster similar memories, connect new to existing. Tags with cluster IDs — only adds metadata.
3. **N3 — Stale reporting**: Report stale memories (older than threshold). **Never modify, never archive, never delete.** The human decides. N3 is read-only.
4. **REM — Integration**: Cross-memory synthesis, immune system health checks, narrative reflection.
5. **Storyweave**: Generate abstract narrative from day's salient memories (REM sub-step).
6. **MemoryFile**: Consolidate MEMORY.md entries — report suggestions, don't auto-apply. Remove exact duplicates only.

## Key Patterns

### Fastembed Daemon (avoid numpy version mismatches)

When using fastembed for embeddings, do NOT import fastembed directly in the migration or runtime script. Spawn the daemon as a subprocess and communicate via JSON lines:

```python
proc = subprocess.Popen(
    ["/mnt/data/fe-venv/bin/python", "/home/adora/.hermes/scripts/embed_fastembed_local.py"],
    stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True,
)
proc.stdin.write(json.dumps({"id": 1, "texts": ["text1", "text2"]}) + "\n")
proc.stdin.flush()
line = proc.stdout.readline()
resp = json.loads(line)  # {"id": 1, "vectors": [[...], [...]], "error": null}
```

### Qdrant Search API for Clustering (not O(n²))

When clustering memories by similarity, do NOT do pairwise cosine comparison in Python — O(n²) is too slow for 4,000+ points. Use Qdrant's search API for nearest-neighbor lookups:

```python
for point in all_points:
    neighbors = client.search(collection, point["vector"], limit=20, score_threshold=0.85)
    cluster = [point] + [n for n in neighbors if n["id"] not in visited]
```

This is ~100x faster (5.8s vs 590s for 4,744 points) because Qdrant uses HNSW indexing internally.

### CLI Phase Choices Must Match Engine

When adding new phases to a dreaming system, update BOTH:
1. The engine's `PHASE_ORDER` list and `_run_phase()` / `_normalize_phases()` methods
2. The CLI's `--phases` choices list and the "all" expansion

Forgetting either one causes `invalid choice` errors at runtime.

### _run_phase Must Return Results

Each phase branch in `_run_phase()` must explicitly `return phase.run()`. Falling through without a return yields `None`, which breaks downstream consumers (like Storyweave that reads phase results).

### Memory File Consolidation

MEMORY.md uses `§` as an entry separator. Parse with `content.split("§")`, filter empties, consolidate by removing exact duplicates (normalize whitespace + lowercase for comparison), and write back respecting the char limit.

### Storyweave (Abstract Narrative)

Generate a short abstract story from the day's salient memories. Use template-based generation with randomized elements (color, template selection). Store the narrative as a memory entry or in a separate file. The narrative should feel like a dream — symbolic, not literal.

## Pitfalls

- **Never delete from a memory archive**: Qdrant is an archive. The whole point is to store everything for comparison and recall. Deleting defeats the purpose. "Pruning" in biology means trimming weak connections to strengthen strong ones — not erasing. If stale memories need handling, report them. Let the human decide. N3 is report-only.
- **Memory systems are additive, not subtractive**: Build connections, surface patterns, report on health. Never remove data. The human decides what to keep.
- **Start cron jobs in dry-run mode**: A new dreaming system should run in dry-run for at least a week before live mode. Review the reports. Only go live when confident nothing destructive happens.
- **Log every modification**: When N1 removes a duplicate, log the ID and text. When N2 adds cluster tags, log the count. Transparency matters — the human should be able to audit what changed.
- **O(n²) clustering is too slow**: Use Qdrant search API instead of pairwise comparison. 4,744 points × 4,744 comparisons = 22M operations in pure Python = 10 minutes. Qdrant search = 5.8 seconds.
- **CLI choices out of sync with engine**: When adding phases, update both `PHASE_ORDER` and CLI `choices`. The "all" expansion must include all phases.
- **_run_phase returns None**: Each branch must explicitly return. Falling through yields None.
- **Mock clients need search method**: When testing with mock Qdrant clients, include a `search` method that returns appropriate neighbors, or N2 clustering will find 0 clusters.
- **Memory file char limit**: MEMORY.md has a 6,000-char limit. Consolidation must respect this — truncate if needed.
- **Storyweave sort by timestamp**: Some memories may have missing or non-string timestamps. Always coerce to `str()` before sorting.
- **Fastembed daemon memory pressure**: Each daemon loads ~220MB. On constrained VMs, use a singleton pattern to share one daemon across instances.

## References

See the [DREAM] GitHub repo: https://github.com/Septa-Serpenta-Seraph/DREAM
