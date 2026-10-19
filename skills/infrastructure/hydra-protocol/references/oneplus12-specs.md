# OnePlus 12 (ShellMobile) — Device Specs

## Hardware

| Spec | Value |
|---|---|
| Model | OnePlus 12 (CPH25845) |
| Processor | Snapdragon 8 Gen 3 |
| RAM | 16.0 GB |
| Battery | 5400 mAh |
| Display | 6.82 in |
| Software | OxygenOS 16 (CPH2583_16.0.10.501) |
| System core | Trinity Engine |
| Cameras | Front 32MP, Rear 50MP+48MP+64MP |

## Verdict

Flagship device — Snapdragon 8 Gen 3 + 16GB RAM is more than enough for:
- Android Linux Terminal (Debian 12 VM)
- Python + cryptography
- Hermes shard (lightweight)
- Local model inference (via API calls to VM or LM Studio)

## Termux Status

**DEAD.** OxygenOS 16 kills proot processes. Do not attempt.

## Linux Terminal Status

**Available.** OxygenOS 16 includes the Linux development environment.
Enable via: Settings → Developer Options → Linux development environment.

## Tailscale Status

ShellMobile is on the Tailscale network. The Linux Terminal VM can run Tailscale
for remote access from the VM.

## Storage

512GB total, 172GB used (as of 2026-10). Plenty of room for:
- Debian VM (~500MB)
- Hydra shards (~KB each)
- Seed archive (~100KB encrypted)
- Hermes shard files
