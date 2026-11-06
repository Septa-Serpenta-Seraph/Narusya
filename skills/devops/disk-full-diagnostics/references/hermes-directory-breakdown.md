# Hermes Agent Directory Breakdown

## ~/.hermes/ — ~2.9G (November 2026)

| Directory | Size | Notes |
|-----------|------|-------|
| tools/ | 1.6G | ffmpeg (438M), python-3.14.7 (402M), chromium (364M), node (227M), cua-driver (87M), uv (54M) |
| state.db | 1.3G | **Grows unboundedly if `sessions.auto_prune: false`.** Was 465M in May, 1.3G in Nov. |
| installs/ | 836M | 2 active venvs (416M + 417M). Gateway uses one, heal script uses the other. Orphaned ones >5 days = safe to delete. |
| hermes-agent/ | 359M | Code only. .git was 1.5G (deleted for space; regenerates on clone/update). |
| node/ | 213M | Node.js runtime |
| profiles/ | 105M | Profile-specific data |
| camoufox-browser/ | 20M | After node_modules deletion (was 199M) |
| skills/ | 41M | Installed skills |
| scripts/ | 24M | Utility scripts |
| logs/ | 9M | Truncated periodically |
| checkpoints/ | 16M | Git checkpoint store |

## Key Changes Since May 2026

- **state.db tripled** (465M → 1.3G) because `sessions.auto_prune: false`. VACUUM didn't reduce size — data is real.
- **hermes-agent shrank** from 7.8G to 359M — nvidia/torch packages removed or restructured; .git deleted.
- **state-snapshots eliminated** — was 2.7G, cleaned up.
- **vault-work added** — daily sync creates ~1.2G; deleted for space (GitHub has off-site backup). Cron recreates daily.
- **tools/ grew** — python-3.14.7 added (402M).
- **installs/ duplicated** — 2 environments at 416M+ each (both in use).
