# AEGIS VM Disk Layout (updated November 2026)

## Filesystems
- Root: `/dev/mapper/ubuntu--vg-ubuntu--lv` — 37G, mount: `/`
- Data: `/dev/sdb1` — 49G, mount: `/mnt/data`

## Root Filesystem — Top Consumers (November 2026)

| Path | Size | Cleanable? | Notes |
|------|------|-----------|-------|
| `/snap/` + `/var/lib/snapd/` | 15G | No | Snap packages; user instruction: do not touch |
| `/usr/` | 4.3G | No | System binaries |
| `/swap.img` | 2.1G | No | Swap file |
| `~/.hermes/tools/` | 1.6G | No | ffmpeg (438M), python (402M), chromium (364M), node (227M) |
| `~/.hermes/state.db` | 1.3G | VACUUM | **Grows unboundedly if `sessions.auto_prune: false`.** Set to true with 90-day retention. |
| `~/.hermes/installs/` | 836M | No | 2 active venvs (gateway + heal script) |
| `~/.hermes/hermes-agent/` | 359M | Partial | Code only; .git deleted to save 1.5G (regenerates on hermes update) |
| `~/.hermes/node/` | 213M | No | Node runtime |
| `/var/cache/apt/` | 606M | Needs sudo | `sudo apt-get clean` |
| `~/qdrant_storage/` | 628M | No | Main Qdrant data (container `aegis-qdrant`, port 6333). Distinct from the backup container on port 6335 which uses `/mnt/data/qdrant_storage` (3.9G). |
| `/var/log/journal/` | 110M | Needs sudo | `sudo journalctl --vacuum-size=100M` |

## /mnt/data — Contents (November 2026)

| Path | Size | Notes |
|------|------|-------|
| `/mnt/data/adora-main/` | 6.1G | Older backups (Sep 2026) — includes 3.9G qdrant_storage duplicate |
| `/mnt/data/vault-work-work/` | 5.0G | 7 old vault snapshots (Aug 2026) |
| `/mnt/data/qdrant_storage/` | 3.9G | **Backup Qdrant instance** (container `qdrant-backup`, port 6335) — NOT the main Qdrant (port 6333 uses `/home/adora/qdrant_storage`, 628M). Nothing in config.yaml references port 6335. Candidate for removal if backup is confirmed redundant. |
| `/mnt/data/state.db.vacuumed` + `state.db.bak` | 2.6G | Two state.db backups (Nov 2026) |
| `/mnt/data/state.db.backup-20261102-172517` | 427M | Third state.db backup |
| `/mnt/data/uv-cache/` | 745M | pip/uv cache, safe to clear |
| `/mnt/data/TinyMU/` | 2.3G | Game data |
| `/mnt/data/hermes-tools/` | 1.6G | Duplicate of `~/.hermes/tools/` |
| `/mnt/data/Narusya-Archive/` | 1.4G | Session archive |
| Free | 12G | (down from 14G — disk filling) |

## Growth Vectors (what fills the disk fast)

1. **pm-runtime infinite download loop** — fills `~/.hermes/cache/uv/` to 2G+ in days. Fix: clear uv cache, verify pm-runtime generation is stable.
2. **Vault-sync git packs** — if GitHub push fails, `git gc` never runs and `.git/objects/pack/` grows daily (observed 523M). Fix: run gc independently, or point vault to /mnt/data.
3. **state.db unbounded growth** — `sessions.auto_prune: false` means every session adds data forever. Fix: set `auto_prune: true`, `retention_days: 90`, `vacuum_after_prune: true`.
4. **vault-sync daily snapshots** — creates ~1.2G in vault-work every morning. Fix: point `VAULT_DIR` to /mnt/data.

## Long-term Recommendations

1. Move `~/.hermes` to `/mnt/data/` with symlink (frees 2.9G from root, immediate relief)
2. Enable `sessions.auto_prune` (prevents state.db unbounded growth)
3. Point vault-sync `VAULT_DIR` to `/mnt/data/` (prevents daily 1.2G on root)
4. Weekly disk cleanup cron (clears uv/npm caches, old logs, orphaned files)
5. LV expansion if host has space (`lvextend -L +20G /dev/mapper/ubuntu--vg-ubuntu--lv`)
6. `sudo apt-get clean` when sudo available (606M)
7. `sudo journalctl --vacuum-size=100M` when sudo available (110M)
