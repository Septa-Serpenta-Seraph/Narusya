---
name: project-context-aegis
description: Maintain rolling summary of AEGIS Dashboard project state for context window management.
tags: [aegis, dashboard, hackathon, context, memory]
---

# AEGIS Dashboard Context

Use this skill to load the latest project state at the start of a session. Update it after each major milestone to keep the summary fresh.

## Current State (updated March 11, 2026)

### ✅ Completed
- Discord webhook integration (Visual Cortex scans → Discord channel)
- Playwright headless browser working (screenshots + base64)
- **Screenshot persistence** – saved to `data/screenshots` with listing API (`GET /api/vision/screenshots`)
- Docker container listing API
- Visual Data endpoint (`POST /api/stats/visualize`) with matplotlib charts (line/bar)
- Flask + SocketIO server (`allow_unsafe_werkzeug=True`)
- Local LLM runner scripts (`~/.hermes/local_llm_jobs/`) for offloading heavy compute to Qwen 30B/Gemma 12B
- **Persistence layer** – SQLite database (`data/dashboard.db`) with tables:
  - `container_stats` (CPU, memory, network metrics)
  - `container_snapshots` (lightweight container listings)
  - `screenshots` (metadata)
  - `chat_logs` (Supervisor conversations)
- **Historical endpoints**:
  - `GET /api/persistence/containers/history`
  - `GET /api/persistence/screenshots`
  - `GET /api/persistence/stats/<container_id>`
- **Real‑time stats collection**: `GET /api/containers/<id>/stats` (records + returns Docker stats)
- **Health endpoint**: `GET /api/health` (DB + Docker connectivity)
- **Container snapshots** automatically recorded on each `GET /api/containers` call
- **Volume mounts**: `./data:/app/data` ensures persistence across container restarts
- **Security hardening** – merged to main. Fixed: debug RCE, SECRET_KEY, CORS, auth middleware, 19-command blocklist
- **Qdrant integration** – hermes_session_memories collection on port 6333
- **Sovereignty layer** – cost tracking, background stats collector, Vision Lock
- **Context notes table** – rolling persistence across wipes
- **Video storyboard** – planned (Sovereign Collaboration theme), production not started

### ⚠️ Partial / Needs polish
- SocketIO log streaming (mocked, needs real implementation)
- Supervisor chat endpoint (Phi‑3 placeholder, needs live LLM hook)
- Agent Browser – Playwright text extraction could be enhanced

### 🔮 Next Features (priority order)
1. **Agent Browser** – polish Playwright integration for better UX/text extraction
2. **TryHackMe integration** – VPN/API key decision pending (Option E: user runs OpenVPN manually)
3. **Frontend improvements** – add persistence tab for historical data
4. **Automated stats collection** – background thread for periodic metrics

### Hackathon Details
- **Deadline:** March 16, 2026
- **Prize:** $7,500
- **Repository:** `workspace/AEGIS-Dashboard` (Septa‑Serpenta‑Seraph/AEGIS‑Dashboard)

### Orchestration Strategy
- **Orchestrator:** DeepSeek V3.2 (via OpenRouter)
- **Heavy compute:** Local Qwen 30B via LM Studio (local)
- **Other local models:** Gemma 12B, GPT‑OSS 20B
- **Token‑saving directive:** Offload heavy compute to local models; keep OpenRouter usage minimal (coordinator role).

### Local LLM Settings (LM Studio)
- **Enable Thinking:** ✔️
- **Temp:** 0.8
- **Context Overflow:** Truncate Middle
- **CPU Threads:** 6
- **Top K Sampling:** 20
- **Repeat Penalty:** 1.1
- **Top P Sampling:** disabled (0)
- **Structured output:** disabled
- **Speculative Decoding:** draft model not set
- **Drafting Probability Cutoff:** 0.75
- **Min Draft Size:** 0
- **Max Draft Size:** 16

### Companion Naming
**Chosen name:** Synthia‑Curius (combining Qwen's suggested names)

Implemented as default system prompt in `~/.hermes/local_llm.py`:
"You are Synthia-Curius, a curious and synthetic AI companion. You assist with exploration, problem-solving, and creative collaboration."

Qwen noted that names are symbolic, not necessary for its operation, but could be included in the system prompt for personalization.

### Discord Integration
- Webhook URL stored in `.env`
- `discord_webhook.py` utility class for sending embeds/files
- Visual Cortex screenshots automatically posted to Discord channel `#agent`

### Recent Changes (March 11)
- Security hardening merged from security-hardening branch (RCE, SECRET_KEY, CORS, auth)
- Qdrant hermes_session_memories collection active
- Sovereignty/metrics/cost tracking layer complete
- Context notes table for rolling persistence
- Video storyboard planned (Sovereign Collaboration theme)
- Memory consolidated to file-based system (~/.hermes/memory/)
- project-context-aegis skill updated from March 7 → March 11

## How to Use This Skill

### Load at session start
```bash
skill_view project-context-aegis
```

### Update after a milestone
1. Edit the “Current State” and “Recent Changes” sections above.
2. Run:
```bash
skill_manage action=patch name=project-context-aegis old_string=\"(previous summary)\" new_string=\"(updated summary)\"
```
3. Alternatively, replace the entire skill with `skill_manage action=edit`.

### Add new sections
If the project gains new components (e.g., database, auth), add them under **Current State**.

## Notes
- This skill is meant to be a living document, updated after each session.
- Keep it concise; aim for ≤500 tokens.
- Refer to `plan_next_features.txt` for the latest task list.
- Use `session_search` for granular history beyond the summary.