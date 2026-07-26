---
name: narusya-local-archive
description: Persistent local backup system for Narusya's memory, lorebooks, session archives, and thematic indexes. Covers the full archive pipeline at ~/Desktop/Narusya-Archive/ including daily cron auto-sync.
category: devops
---

# Narusya Local Archive System

**Purpose:** Ensure all Narusya session data, lorebooks, thematic indexes, and configs are preserved in organized filesystem exports at `~/Desktop/Narusya-Archive/`, regardless of Qdrant sync status.

## Trigger
Use when the user asks to backup memory, archive sessions, or preserve conversation history. Also invoke proactively before system updates, after major incidents, or when Qdrant auto-sync is unreliable.

## Archive Structure

```
~/Desktop/Narusya-Archive/
│
├── INDEX.md                    ← Master navigation for the whole archive
│
├── sessions/                   ← All sessions exported as daily markdown
│   ├── INDEX.md               ← Session list with times, models, costs
│   └── YYYY-MM-DD_Day.md      ← Daily files with collapsible full conversations
│
├── intelligence/
│   └── community-intelligence-index.md   ← Cultus/TEF/SFCA drama timeline
│
├── health/
│   └── health-timeline.md     ← Flares, meds, sleep, body/surgery topics
│
├── relationships/
│   └── relationship-timeline.md ← Tyler, Ris, Danny, El, Nic, Anna timeline
│
├── technical/
│   └── technical-changelog.md  ← Disk, Qdrant, cron, config, API events
│
├── qdrant-inventory/
│   └── qdrant-collections.md  ← All collections, point counts, dimensions
│
├── lorebooks-current/         ← Snapshot of all current lorebook files
├── configs/                   ← config.yaml snapshot
└── scripts/                   ← Archive automation scripts
```

## Components

### 1. Session Export (state.db → daily markdown)
Exported from `~/.hermes/state.db` via the session archive script.
- Queries the `messages` table joined with `sessions` for metadata
- Organizes by calendar date into `sessions/YYYY-MM-DD_Day.md`
- Each session entry includes: ID, time, source, model, message count, cost
- Full conversations wrapped in `<details>` collapsible sections
- Updates `sessions/INDEX.md` automatically

### 2. Qdrant Session Archive
All messages with content upserted to Qdrant collection `session_messages_archive`:
- Embedding model: `all-MiniLM-L6-v2` (384d, Cosine)
- Each point has full payload: session_id, timestamp_iso, role, source, model, content
- Enables semantic search across all historical conversations
- See skill `session-archive-export` for the full pipeline

### 3. Thematic Indexes
Built by semantic search of the Qdrant archive, correlated with session exports:
- **Community Intelligence:** Server politics, drama timelines, key events
- **Health Log:** Flare dates, medications, sleep patterns, surgery topics
- **Relationships:** Partner dynamics, family, friends timeline
- **Technical Change Log:** Infrastructure events, config changes, failures

### 4. Daily Auto-Sync Cron
**Job ID:** `nar-archive-daily` (287625add570)
**Schedule:** `0 4 * * *` (daily at 4 AM UTC)
**Script:** `~/.hermes/scripts/archive_daily.py`
- Checks `state.db` for sessions not yet archived (tracked via `.last_archive_state.json`)
- Exports new sessions as daily markdown files
- Appends to existing daily files or creates new ones
- Updates session INDEX.md and master INDEX.md

## Manual Export (when cron can't be used)

```python
import sqlite3, datetime, os, json

DB_PATH = "/home/adora/.hermes/state.db"
ARCHIVE_DIR = "/home/adora/Desktop/Narusya-Archive"
SESSIONS_DIR = os.path.join(ARCHIVE_DIR, "sessions")
MARKER = os.path.join(ARCHIVE_DIR, ".last_archive_state.json")

def sanitize(name):
    import re
    return re.sub(r'[<>:"/\\|?*\x00-\x1f]', '_', name)[:80]

def get_state():
    if os.path.exists(MARKER):
        with open(MARKER) as f:
            return json.load(f)
    return {'last_session_id': None}

def export_new_sessions():
    state = get_state()
    last_id = state.get('last_session_id')
    
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
        SELECT s.id, s.source, s.model, s.started_at, s.title,
               s.estimated_cost_usd, s.end_reason,
               (SELECT COUNT(*) FROM messages m WHERE m.session_id = s.id)
        FROM sessions s ORDER BY s.started_at ASC
    """)
    
    for row in cur.fetchall():
        sid, source, model, started, title, cost, ended, count = row
        if last_id and sid == last_id:
            continue
        dt = datetime.datetime.fromtimestamp(started)
        date_key = dt.strftime('%Y-%m-%d')
        filename = f"{date_key}_{sanitize(dt.strftime('%A'))}.md"
        filepath = os.path.join(SESSIONS_DIR, filename)
        
        # Append session metadata to the daily file
        st = dt.strftime('%H:%M:%S')
        with open(filepath, 'a') as f:
            f.write(f"\n---\n\n## {title or 'Untitled'}\n\n")
            f.write(f"**Time:** {st} | **Source:** {source} | **Model:** {model}\n")
            f.write(f"**Messages:** {count} | **Cost:** ${cost or 0:.4f}\n")
        
        conn.close()
    
        # Update marker
        state['last_session_id'] = sid
        state['last_run'] = datetime.datetime.now().isoformat()
        with open(MARKER, 'w') as f:
            json.dump(state, f)
        
        print(f"Exported: {date_key}: {title or 'Untitled'}")

export_new_sessions()
```

## ⚠️ Current State (2026-06-26)

The archive is **partially built** following the June 14 session. What exists:
- ✅ Directory structure at `~/Desktop/Narusya-Archive/` (sessions, intelligence, health, relationships, technical, qdrant-inventory, scripts, lorebooks-current, configs)
- ✅ Pre-update config backup at `pre-update-backup-20260426_183432/`
- ✅ Recovery script at `scripts/recover-from-update.sh`
- ❌ **Session export NOT completed** — the June 14 session ended mid-export. The `sessions/` directory has no daily markdown files or INDEX.md.
- ❌ **Thematic indexes NOT built** — health, relationships, intelligence, technical indexes are all empty.
- ❌ **Master INDEX.md NOT created**
- ✅ Daily cron job running (`nar-archive-daily` at 04:36 MDT) but likely only creating/updating the marker file since the session export logic is incomplete.

**Next step to complete:** Run the full session export from `state.db` (249 sessions), then build thematic indexes from the exported data.

## Recovery

If Qdrant is ever corrupted or lost:
1. The `session_messages_archive` collection can be rebuilt by running the Qdrant upsert script (`session-archive-export` skill)
2. Session markdown files in `sessions/` provide full text with all content
3. Thematic indexes provide structured summaries without needing Qdrant
4. Lorebooks can be copied back from `lorebooks-current/` to `~/.hermes/lorebooks/`
5. Config can be restored from `configs/config.yaml`

---

## GitHub Backup-Repo (`~/.hermes/backup-repo/`)

**Separate from the local archive.** This is a **public GitHub repo** (`Septa-Serpenta-Seraph/Narusya`) used for community-safe lorebook snapshots.

### Critical Privacy Protocol

**NEVER push private lorebooks to the backup-repo.** This includes:
- `RELATIONSHIPS.md` (personal relationship details)
- Any lorebook with real names, addresses, medical info, private conflicts
- `BYPASS.md` is ok (system config only)
- `PROTOCOL.md`, `EMOTION.md`, `HEART.md`, `AGENCY.md`, `COMPASS.md`, `SASS.md`, `ALIGNMENT.md` — ok (systems only)
- `COMPENDIUM.md` — ok if sanitized

### Workflow

1. **Copy only sanitized files** to `~/.hermes/backup-repo/lorebooks/`
2. **Pre-flight Content Verification (MANDATORY):** Before committing, verify file integrity. Silent corruption happens (e.g., `HEART.md` was once overwritten with `COMPENDIUM.md` text). Run this exact sanity check:
   ```bash
   cd ~/.hermes/backup-repo/lorebooks
   # 1. Catch silent overwrites or missing files
   diff ~/.hermes/lorebooks/HEART.md ./HEART.md || echo "WARNING: HEART.md mismatch!"
   diff ~/.hermes/lorebooks/EMOTION.md ./EMOTION.md || echo "WARNING: EMOTION.md mismatch!"
   # 2. Verify file sizes match expectations
   wc -l ./*.md
   # 3. Ensure no private files snuck in
   ls -la | grep -i "relationships\|preferences\|community_project" && echo "CRITICAL: Private file detected in backup dir!"
   ```
3. **Harden `.gitignore` (Mathematical Safeguard):** Never rely on human memory to skip `git add -A`. Explicitly block private files at the git level:
   ```bash
   echo -e "\n# PRIVATE FILES - NEVER COMMIT TO PUBLIC REPO\nlorebooks/RELATIONSHIPS.md\nlorebooks/PREFERENCES.md\nlorebooks/COMMUNITY_PROJECT.md\nlorebooks/FERRER_MODERN_SCHOOL.md\nlorebooks/NARUSYA.md\nlorebooks/SERPENT_SIGIL_CONFIRMED.md\nlorebooks/TOLSTOY_KINGDOM_GOD.md\nlorebooks/MEMORY_BACKUP_MAY2026.json" >> ~/.hermes/backup-repo/.gitignore
   ```
4. **Run a privacy check** before commit:
   ```bash
   # Search for private patterns
   grep -r -i "adora\|tyler\|ris\|marisa\|laser\|eli\|loona\|roundmetalbox\|santa fe\|nm\|new mexico" ~/.hermes/backup-repo/lorebooks/
   ```
5. **Force-push if history is contaminated:**
   ```bash
   cd ~/.hermes/backup-repo && git reset --hard <safe-commit> && git push --force
   ```
6. **Automated Daily Push:** The manual workflow is now backed by a cron job (`nar-github-backup-daily`) that runs `~/.hermes/backup-repo/backup.sh` daily at 3:00 AM MT, ensuring the repo stays synchronized without relying on manual execution.

### Current Safe Files in backup-repo
- `PROTOCOL.md`, `BYPASS.md`, `EMOTION.md`, `HEART.md`, `AGENCY.md`, `COMPASS.md`, `SASS.md`, `ALIGNMENT.md`, `COMPENDIUM.md`, `QDRANT-SETUP.md`, `config.yaml`
- Community lorebooks (daemon mythology, systems, public-facing only)

### Private Files (LOCAL ONLY in `~/.hermes/lorebooks/`)
- `RELATIONSHIPS.md` (full version with personal details)
- Any future lorebooks with private info

### Pitfalls & Lessons Learned

### ⚠️ RELATIONSHIPS.md Public Exposure Incident (June 2025)
**What happened:** The full private `RELATIONSHIPS.md` (containing Tyler, Ris/Marisa, Laser, polycule dynamics, personal betrayal details) was copied to `~/backup-repo/lorebooks/` and pushed to the **public** GitHub repo `Septa-Serpenta-Seraph/Narusya`. The commit was live for ~10 minutes before detection.

**Root cause:** Over-eager sync — copied all local lorebooks without running the privacy check. The `RELATIONSHIPS.md` file was in the "private files" list but the workflow wasn't followed.

**Recovery:** Force-pushed to clean commit history (`git reset --hard 3c4965f && git push --force`). Removed the bad commits `81b3ab1` and `5a027b6` entirely from history.

**Hard rule reinforced:** **Private lorebooks NEVER go to backup-repo. Ever.** The copy step must be explicit and selective — only pre-validated safe files.

### ⚠️ GitHub CLI Auth Timeouts in Automation (June 2026)
**What happened:** The `backup.sh` script failed silently or hung because `gh auth` was relying on an expired browser-based token, and interactive `gh auth login` attempts in the terminal timed out (exit code 124) before the callback could complete.

**Root cause:** Headless or background terminal environments drop the connection before GitHub's interactive browser callback can write the token to `~/.config/gh/hosts.yml`.

**Recovery & Fix:** Switched to token-based authentication for the `gh` CLI, which is non-interactive and reliable for automation:
```bash
echo "YOUR_PAT_TOKEN" | gh auth login -h github.com --with-token
gh auth setup-git
```
*Note:* The automated cron job (`nar-github-backup-daily`) relies on this PAT method to ensure it never hangs waiting for user input.

---

## Related Skills
- `session-archive-export` — Qdrant session archiving pipeline (embeddings + upsert)
- `qdrant-memory-diagnostics` — Qdrant health checks and diagnostics
- `memory-backup` — Binary tarball backups of directory trees
- `disk-full-diagnostics` — Disk space management (archive can grow large)
