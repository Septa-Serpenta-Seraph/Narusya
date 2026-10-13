# Second-disk data home — working recipe (2026-08-23)

Result: 40G boot `sda` + 50G data `sdb` both live on "Narusya on SHELL"; heavy payloads relocated; root went 17M free → 1.9G free (95%). qdrant memory stayed on the SSD by design (Adora's call — fast recall).

## Host (Hyper-V) — verified additive
- Created `Nar's second Disk.vhdx` (starts ~4MB, set to 50G) on host disk E:.
- Checkpoints block editing ("Edit is not available because checkpoints exist") → delete checkpoint + let the merge finish FIRST.
- Add via Settings → Hard Drive → **New** on the SCSI controller. Boot disk stays Location 0; new disk lands Location 1+ — verify TWO rows are listed (that's the additive check).
- Research confirmations: SCSI controller holds up to 64 devices; multiple disks on one SCSI controller is the recommended Microsoft pattern; "no requirement to shut down" to add a disk (petri.com, Microsoft Learn, Spiceworks).
- Linux guest sees `sdb 50G` with the boot partition table untouched.

## Guest — the exact block the user pasted (sudo + mkfs are NOT agent-doable)
```bash
sudo parted /dev/sdb --script -- mklabel gpt
sudo parted /dev/sdb --script -- mkpart primary ext4 0% 100%
sudo mkfs.ext4 /dev/sdb1
sudo mkdir -p /mnt/data && sudo mount /dev/sdb1 /mnt/data && sudo chown adora:adora /mnt/data
```
`mkfs` is on the agent's unconditional blocklist; no passwordless sudo on this box → the USER must run these.

## Persistence (fstab — get UUID without sudo)
`ls -la /dev/disk/by-uuid/` → `907dbe3c-a294-49fõ-4fc-aa58432e8296 -> ../../sdb1`. Add:
```bash
echo 'UUID=907dbe3c-a294-49ff-a6fc-aa58432e8296 /mnt/data ext4 defaults,noatime 0 2' | sudo tee -a /etc/fstab
```
(At session end fstab was NOT yet added — mount was live but reboot-fragile.)

## Relocated (copy-verify-swap, all verified identical counts)
| Old path → new (symlink) | Size / files | How verified |
|---|---|---|
| `~/.hermes/vault-work/work` → `/mnt/data/vault-work-work` | 2.2G / 11919 | counts + sizes matched |
| `~/.cache/camoufox` → `/mnt/data/camoufox` | 1.3G / 1260 | loaded example.com via the symlink after swap |
| `~/qdrant_storage` | 320M | **stays on SSD** — memory is latency-critical |

## Pitfalls hit
- `rm -rf ~/qdrant_storage` while qdrant runs → thousands of `Permission denied` (live mmap files). Stop service → move → symlink → start. Even better: keep memory on SSD, only relocate heavy non-latency payloads.
- Batching destructive + session + tmp commands trips approval gates that TIME OUT → the whole batch is refused ("Command timed out without user response"). Run ONE focused action per call; a timed-out block is a hard stop (no retry, no rephrase).
- Background shells lack `node_modules/.bin` on PATH → always use absolute paths for node/er binaries.