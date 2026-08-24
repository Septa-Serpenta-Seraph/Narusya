# Adding a Second Data Disk (Hyper-V + Ubuntu guest)

Verified 2026-08-23 — built "Nar's second Disk" 50GB VHDX alongside the 40GB boot disk, with Adora driving the host UI.

## When to use
- Root disk is full but the host has a spare drive / space for another VHDX.
- You want a data-only volume so the boot disk stays lean (better than growing root when the heavy stuff is non-latency-critical).
- Fully additive: the boot disk is untouched — no resize, no repartition.

## Host side (Hyper-V Manager — USER does this; the agent can't reach the host)
1. VM Settings → Hard Drive → **New...** (additive). Boot disk stays at Location 0; the new disk gets its own location slot.
   - Multiple disks on one SCSI controller is the **recommended** pattern (Microsoft Learn: up to 64 devices per SCSI controller). Spiceworks: "I would use 2 vHDD for VMs that need 2 drives".
   - **Checkpoints block the Edit button, NOT the New button.** If Edit is grayed ("Edit is not available because checkpoints exist"), delete checkpoints first (merge takes a few minutes). Reuse an existing VHDX via Browse, or let the wizard mint a fresh one.
2. Size it (e.g. 50GB), attach to the **SCSI** controller (not IDE — preferred for non-OS disks).
3. No shutdown strictly required (Spiceworks: "you can safely add new disks to a running VM"); a reboot is simplest.
4. Hand off: tell the agent to `lsblk` — the new disk appears as `sdb`.

## Guest side — the agent's hard blocker: mkfs
`mkfs.*` is on the unconditional blocklist — the agent CANNOT format a filesystem even with user approval. `sudo` also needs a password the agent doesn't have. So partitioning/formatting/mounting are USER commands; everything after is agent-able.

User runs (terminal with sudo):
```bash
sudo parted /dev/sdb --script -- mklabel gpt
sudo parted /dev/sdb --script -- mkpart primary ext4 0% 100%
sudo mkfs.ext4 /dev/sdb1
sudo mkdir -p /mnt/data && sudo mount /dev/sdb1 /mnt/data && sudo chown adora:adora /mnt/data
```

## Agent side — verify, then claim
```bash
lsblk -o NAME,SIZE,FSTYPE,TYPE,MOUNTPOINT /dev/sdb   # expect sdb1 ext4
touch /mnt/data/.write-check && rm /mnt/data/.write-check  # writable?
```
Persistent mount: **read the UUID without sudo** via `ls -la /dev/disk/by-uuid/ | grep sdb1`, then user runs one line:
```bash
echo 'UUID=<uuid> /mnt/data ext4 defaults,noatime 0 2' | sudo tee -a /etc/fstab
```
Verify after: `grep mnt/data /etc/fstab`, and `echo 0 > /proc/sys/kernel/...` is NOT needed — fstab takes over on next boot.

## Moving heavy dirs — copy-verify-swap (never delete-then-copy)
For each heavy dir (camoufox engine ~1.3G, vault-work/work payloads ~2.2G):
```bash
cp -a ~/src /mnt/data/src_dest                        # 1. copy
find ~/src -type f | wc -l  ;  find /mnt/data/src_dest -type f | wc -l   # 2. equal?
du -sh ~/src /mnt/data/src_dest                        #    + sizes equal
rm -rf ~/src && ln -s /mnt/data/src_dest ~/src         # 3. swap to symlink
ls -la ~/src/version.json ; curl <service health>      # 4. verify THROUGH the link
```

## Pitfalls (learned the hard way)
- **Do NOT `rm` a live qdrant dir.** Qdrant is a running service; files are open/mmap'd — every file returns Permission denied. That is the OS protecting live data, NOT a failure. Stop the service first if you really must move it (needs sudo); otherwise leave memory where it is.
- **Memory (qdrant) STAYS on the SSD.** Fast recall matters; the data disk is for heavy, non-latency-critical stuff (browser engine, snapshot payloads). Adora's explicit architectural call (8/23).
- Use `du -sh` + file-count verification after every copy — never trust a bare `cp -a` exit code.