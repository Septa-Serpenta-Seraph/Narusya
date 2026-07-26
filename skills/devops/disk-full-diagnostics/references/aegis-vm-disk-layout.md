# AEGIS VM Disk Layout (as of June 2026)

## Filesystem
- Single LVM logical volume: `/dev/mapper/ubuntu--vg-ubuntu--lv`
- Size: 37G total
- Mount: `/` (everything on one filesystem)

## Top Space Consumers (June 28, 2026 snapshot)

| Path | Size | Cleanable? | Notes |
|------|------|-----------|-------|
| `~/.hermes/hermes-agent/venv/` | 5.2 GB | No | Active Python venv for Hermes; contains torch, nvidia, triton |
| `~/.hermes/` (total) | 8.3 GB | Partial | venv (5.2G) + state.db + sessions + skills + state-snapshots (524M) |
| `~/.local/lib/python3.12/site-packages/` | 1.6 GB | Maybe | User-site packages; may duplicate venv packages |
| `/var/log/journal/` | 845 MB | Needs sudo | systemd journal; grows without limits |
| `~/backups/` | 420 MB | Yes (approval-gated) | Old April 2026 backup tarballs |
| `~/.cache/camoufox/` | 321 MB | Yes | Camoufox/Firefox browser binary; regenerates |
| `~/.hermes/state-snapshots/` | 524 MB | Partial | Pre-update state.db backups; keep latest 1-2 |
| `~/.hermes/camoufox-browser/` | 138 MB | No | Camoufox server installation |
| `~/.cache/huggingface/` | 88 MB | Yes | HF model cache; regenerates |
| `/var/log/` (total) | 861 MB | Needs sudo | Mostly journal |

## What's NOT cleanable without elevated access
- `/var/log/journal/` — needs `sudo journalctl --vacuum-size=100M`
- `/var/log/syslog.*` — needs sudo or logrotate

## What's safe to clean (no approval needed)
- `pip cache purge` — usually already clean
- `uv cache prune --ci` — usually already clean
- `npm cache clean --force` — usually already clean
- Docker builder/image prune — if docker present

## What requires approval (avoid in cron)
- `find ... -delete` — triggers approval gate
- `rm -rf <directory>` — triggers approval gate
- `rm -f` on individual files — usually OK

## Long-term concern
At 37G total with 5.2G for the Hermes venv alone, this disk will continue to fill. Recommend:
1. LV expansion if host has space (`lvextend -L +20G /dev/mapper/ubuntu--vg-ubuntu--lv`)
2. Regular journal vacuuming via sudo
3. Periodic state-snapshot rotation
