# Hermes Agent Directory Breakdown (May 2026 snapshot)

Measured on a 37G Ubuntu LV with hermes-agent installed. Sizes will grow over time.

## ~/.hermes/ — 12G total

| Directory | Size | Notes |
|-----------|------|-------|
| hermes-agent/ | 7.8G | Main installation; venv is 5.1G, node_modules 1.6G |
| state-snapshots/ | 2.7G | Pre-update state.db backups; ~440-465M each; prune to latest 2 |
| state.db | 465M | Active session store; VACUUM if freelist significant |
| node/ | 205M | Node.js runtime |
| sessions/ | 163M | Session JSON files; old ones can be archived |
| camoufox-browser/ | 138M | Camoufox browser binary |
| skills/ | 27M | Installed skills |
| hermes-docs/ | 25M | Documentation mirror |
| lsp/ | 24M | Language server protocol tools |
| backup-repo/ | 11M | Git backup of hermes config |
| logs/ | 7.3M | agent.log, errors.log, gateway.log |

## ~/.hermes/hermes-agent/ — 7.8G

| Directory | Size | Notes |
|-----------|------|-------|
| venv/ | 5.1G | Python 3.11 venv; nvidia packages are 1.7G of this |
| node_modules/ | 1.6G | Electron is 261M alone |
| web/ | 294M | Gateway web assets |
| ui-tui/ | 229M | TUI frontend |
| apps/ | 74M | Desktop apps |
| scripts/ | 67M | Utility scripts |

## ~/.cache/ — 2.3G

| Directory | Size | Notes |
|-----------|------|-------|
| camoufox/ | 1.4G | Fonts are 1G+; safe to delete; regenerates |
| huggingface/ | 664M | Model cache; safe to delete; re-downloads on use |
| electron/ | 110M | Cleared in this session |
| uv/ | 103M | Python package cache |
| node-gyp/ | 67M | Native node build cache |

## ~/.local/ — 2.1G total

| Directory | Size | Notes |
|-----------|------|-------|
| lib/python3.12/ | 1.5G | nvidia (432M) + triton (641M) + others; check if redundant with venv |
| share/piper-voices/ | 191M | TTS voice models |
| share/uv/ | 100M | UV tool cache |

## Other notable

| Path | Size | Notes |
|------|------|-------|
| ~/backups/ | 709M | Manual tarballs; keep latest of each type only |
| /snap/ | 6.8G | Snap packages; firefox, gnome, etc. |
| /var/lib/snapd/ | 2.5G | Snap data |
