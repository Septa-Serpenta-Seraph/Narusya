---
name: narusya-local-archive
description: Persistent local backup system for Narusya's memory, lorebooks, session archives, and thematic indexes. Covers the full archive pipeline at /mnt/data/Narusya-Archive/ including daily cron auto-sync.
category: devops
---

# Narusya Local Archive System

**Purpose:** Ensure all Narusya session data, lorebooks, thematic indexes, and configs are preserved in organized filesystem exports, regardless of Qdrant sync status.

## Archive Structure

**⚠️ LIVE ARCHIVE ROOT — VERIFY BEFORE WRITING ANY ARCHIVE SCRIPT:**

The live archive tree is **`/mnt/data/Narusya-Archive/`** (the healthy 49G drive), NOT `~/Desktop/Narusya-Archive/` (a stale empty husk on the root drive). Any new archive script MUST resolve the root this way — pointing at the wrong tree silently strands the backup on the disk under space pressure:

```python
ARCHIVE_ROOT = os.path.expanduser("~/Desktop/Narusya-Archive")
DATA_ARCHIVE = "/mnt/data/Narusya-Archive"
if os.path.isdir(DATA_ARCHIVE):
    ARCHIVE_ROOT = DATA_ARCHIVE
```

## Trigger
Use when the user asks to backup memory, archive sessions, or preserve conversation history. Also invoke proactively before system updates, after major incidents, when Qdrant auto-sync is unreliable, or when the disk watchdog is about to delete anything.

```
/mnt/data/Narusya-Archive/
│
├── INDEX.md                    ← Master navigation for the whole archive
│
├── sessions/                   ← All sessions exported as daily markdown
│   ├── INDEX.md               ← Session list with times, models, costs
│   └── YYYY-MM-DD_Day.md      ← Daily files with collapsible full conversations
│
├── cron_output_snapshots/     ← Snapshot of real cron outputs + old request dumps
│   ├── .last_snapshot.json   ← Dedupe state (path → mtime:size signature)
│   └── YYYY-MM-DD_HHMM/      ← Timestamped snapshots, 30-day retention
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
**Scripts (BOTH run daily, in order):**
1. `~/.hermes/scripts/archive_daily.py` — session export from state.db (see below)
2. `~/.hermes/scripts/archive_cron_outputs.py` — snapshot cron outputs + old session request dumps into `cron_output_snapshots/` BEFORE the disk watchdog deletes them

### Cron-Output Snapshot (archive_cron_outputs.py)
The disk watchdog is authorized to delete old cron outputs (>7 days) and session request dumps (>3 days). "Designated deletable" is NOT "verified disposable" — snapshot before deletion:
- Copies meaningful files only — **skip files ≤200 bytes** ("Status: silent" empty-run markers); they dominate the tree by count and cost nothing to regenerate
- Dedupes via `.last_snapshot.json` (path → `mtime_ns:size` signature): unchanged files are skipped on subsequent runs, so daily snapshots stay ~84K
- 30-day snapshot retention, well past the watchdog's 3-7 day deletion windows
- Walks both `~/.hermes/cron/output/` (per-job subdirs) and `~/.hermes/sessions/` (`request_dump_cron_*` files)

## Manual Export (when cron can't be used)

```python
import sqlite3, datetime, os, json

DB_PATH = "/home/adora/.hermes/state.db"
ARCHIVE_DIR = "/mnt/data/Narusya-Archive"
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

## Current Configuration

- **Live root: `/mnt/data/Narusya-Archive/`** — the `~/Desktop/Narusya-Archive/` tree is a stale husk; confirm live paths with `du -sh` before writing any archive script.
- Session export is complete and runs daily (`nar-archive-daily` → `archive_daily.py`), writing `sessions/YYYY-MM-DD_Day.md` plus the session and master INDEX.md.
- The `cron_output_snapshots/` layer (wired into the same daily cron via `archive_cron_outputs.py`) backs up watchdog-deletable files before deletion — see component 4.
- Thematic indexes (intelligence, health, relationships, technical) are built on request via semantic search of the Qdrant archive; do not assume they exist until verified.

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

## Pitfalls & Lessons Learned

### ⚠️ Two Archive Trees — Point New Scripts at /mnt/data
**What happened:** A new snapshot script was written with `ARCHIVE_ROOT = ~/Desktop/Narusya-Archive/` (the path the old skill documented) while the live session archive had been writing to `/mnt/data/Narusya-Archive/` for weeks. Result: new backups landed on the sick root drive (0 in the Desktop tree vs 1.4G on /mnt/data), defeating the two-drive protection. Discovered only by running `du -sh` on BOTH trees.

**Rule:** Before writing ANY new archive script, `du -sh` both `~/Desktop/Narusya-Archive` and `/mnt/data/Narusya-Archive` and confirm which tree is live. Resolve the root with the isdir-fallback pattern shown under Archive Structure — never hardcode either path alone.

### Watchdog-Deleted Files: "Designated Deletable" ≠ "Verified Disposable"
**Rule:** When the disk watchdog's cleanup paths include anything that took work to produce (cron outputs, request dumps), a snapshot step must run BEFORE the watchdog's deletion pass — wire it into the same daily cron, ahead of the watchdog's own cleanup window. When the user asks "were those backed up?", audit honestly: state what is confirmed archived, what is gone, and build the safeguard for the gap rather than reassuring from assumption.

---

## Related Skills
- `session-archive-export` — Qdrant session archiving pipeline (embeddings + upsert)
- `qdrant-memory-diagnostics` — Qdrant health checks and diagnostics
- `memory-backup` — Binary tarball backups of directory trees
- `disk-full-diagnostics` — Disk space management (archive can grow large)
