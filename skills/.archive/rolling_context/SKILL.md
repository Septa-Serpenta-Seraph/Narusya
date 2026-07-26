# Rolling Context Persistence

**Skill ID:** `rolling_context`  
**Purpose:** Persist conversation summaries across Hermes sessions using Qdrant vector store. Solves memory loss on session reset by injecting relevant past summaries into the system prompt.

---

## When to Use

This skill is automatically activated if the environment variable `HERMES_CONTEXT_QDRANT` is set to `true` and the Qdrant server is reachable. It is ideal for:

- Long‑running projects (e.g., AEGIS hackathon) where you need continuity across days
- Pentesting sessions that span multiple machine restarts
- Any scenario where Hermes resets would otherwise lose important context

---

## How It Works

1. **Session start:** The skill intercepts the first user message, generates an embedding, and performs a semantic search in the Qdrant collection `hermes_session_memories`. The top‑3 most relevant summaries are injected into the system prompt (as an extra layer before the final "Conversation started" line).

2. **During compression:** When Hermes invokes `flush_memories` (before context compression), the skill captures the generated `[CONTEXT SUMMARY]` and stores it in Qdrant with metadata (`session_id`, `timestamp`, `tags`). This ensures that condensed knowledge survives beyond the current session.

3. **Configuration:**
   - `HERMES_CONTEXT_QDRANT`: `"true"` to enable (default: false)
   - `QDRANT_URL`: Qdrant server URL (default: `http://localhost:6333`)
   - `QDRANT_COLLECTION`: Collection name (default: `hermes_session_memories`)
   - `OPENAI_API_KEY` / `OPENAI_BASE_URL`: For embedding generation
   - `CONTEXT_EMBEDDING_MODEL`: Embedding model (default: `text-embedding-3-large`)
   - `CONTEXT_MAX_RESULTS`: Number of summaries to inject (default: `3`)

---

## Implementation Notes

- The skill uses the **existing** `ContextCompressor` summary output; it does not replace summarization.
- Summaries are stored with their full text and a 1536‑dimensional vector (OpenAI large embedding).
- On session boot, the skill appends a marker like `[PAST CONTEXT]\n- Summary 1\n- Summary 2\n...` to the system prompt. This is placed just before the "Conversation started" timestamp so it doesn't interfere with prefix caching.
- If Qdrant is unavailable or embedding fails, the skill fails gracefully (no injection) and logs a warning.
- The collection is created automatically on first use with payload schema: `text` (str), `session_id` (str), `timestamp` (float), `tags` (list[str]).

---

## Benefits

- **Infinite context without token bloat:** Only relevant summaries are retrieved and injected.
- **Sovereign storage:** Qdrant runs locally; you control the data.
- **Seamless integration:** Works alongside existing MemoryStore and session_search; no changes to Hermes core.

---

## Future Enhancements

- Per‑project tag filtering
- Time‑window decay (older summaries gradually lose priority)
- Automatic summarization of MemoryStore entries for cross‑session recall
- Token budgeting: dynamically adjust number of injected summaries based on available context space

---

**Skill created by:** Hermes (Narusya) for Adora, 2026‑03‑10 🐍