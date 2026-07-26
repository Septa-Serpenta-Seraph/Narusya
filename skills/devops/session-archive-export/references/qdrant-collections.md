# Qdrant Collection Architecture

## Active Collections (as of May 2026)

| Collection | Dimensions | Model | Points | Purpose |
|---|---|---|---|---|
| `session_messages_archive` | 384d | `all-MiniLM-L6-v2` | ~36K | Full message archive from state.db |
| `intelligent_gould_lumi` | 3072d | `dunzhang/stella_en_1.5B_v5` | 19 | Lumi's curated memory (sister collection to narusya) |
| `intelligent_gould_narusya` | 3072d | `dunzhang/stella_en_1.5B_v5` | ~4K | Curated memories, lorebooks, research |
| `hermes_session_memories` | 3072d | `dunzhang/stella_en_1.5B_v5` | 27 | Hermes-native session memory |
| `narusya_research` | 3072d | `dunzhang/stella_en_1.5B_v5` | 3 | Research docs, community intel |
| `naru_memory` | 1536d | (unknown) | 30 | Legacy Narusya memory |
| `naru_memory_backups` | 3072d | `dunzhang/stella_en_1.5B_v5` | 22 | Memory backups |

## Critical Rule: Dimension Matching

**Never query a collection with vectors from a different embedding model.** A 384d query against a 3072d collection (or vice versa) will either error or return meaningless results.

- For **384d collections** (`session_messages_archive`, `naru_memories_v2`, `security`): use `sentence-transformers/all-MiniLM-L6-v2`
- For **3072d collections** (`intelligent_gould_narusya`, `hermes_session_memories`, `narusya_research`): use `dunzhang/stella_en_1.5B_v5` (~6GB, slow to load)
- For **1536d collections** (`naru_memory`, `hackathon_intel`, `aegis_internal_archive`): model unknown, likely `text-embedding-3-small`

## session_search vs Direct Qdrant Query

The Hermes `session_search` tool uses its own indexing pipeline (separate from raw Qdrant). It has an **indexing lag of several days** — recent sessions may not appear.

When `session_search` returns empty results for recent conversations:
1. Query `~/.hermes/state.db` directly (see SKILL.md for schema)
2. Use `client.query_points()` on `session_messages_archive` with a 384d embedding
3. Cross-reference session IDs between the two

## Re-embedding Pipeline

To rebuild `session_messages_archive` from scratch, run the archive script from this skill as a background process (takes 25-30 min).
