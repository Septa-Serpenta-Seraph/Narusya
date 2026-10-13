---
name: hyperv-vm-disk-expansion
description: Expand Hyper-V VM disks and resize Ubuntu guests with LVM and GPT.
category: devops
tags:
  - hyperv
  - disk
  - partition
  - lvm
  - ubuntu
  - vm
triggers:
  - expanding VM disk
  - disk space on Hyper-V VM
  - resize VHD
  - growpart
  - parted Fix prompt stuck
---

# Hyper-V VM Disk Expansion (Ubuntu Guests)

## When to Use
- Ubuntu VM running out of disk space
- Need to expand Qdrant storage, add memory systems, etc.
- Working with Hyper-V on Windows host + Ubuntu guest

## The Full Workflow

### Prerequisites
- VM must be **shut down** (not paused, not saved)
- No active checkpoints on the VM

### Step 1: Delete Checkpoints (Host Side)
Checkpoints are the #1 reason for "Edit Disk" being grayed out.

**In Hyper-V Manager:**
1. Select the VM
2. Look at the Checkpoints pane (bottom)
3. If checkpoints exist: Right-click → Delete Checkpoint
4. Wait for merge to complete (watch the checkpoint list empty)

Alternatively via PowerShell on Windows host:
```powershell
Get-VMCheckpoint -VMName "YourVM" | Remove-VMCheckpoint
```

### Step 2: Expand the VHD (Host Side)
After checkpoints are gone, the Edit Disk option unlocks.

**In Hyper-V Manager:**
1. VM Settings → Hard Drive → Edit
2. Choose "Expand"
3. Set new size (e.g., 600 GB)

Or via PowerShell:
```powershell
Resize-VHD -Path "C:\path\to\vm\disk.vhdx" -SizeBytes 600GB
```

### Step 3: Fix GPT and Resize Partition (Guest Side)
SSH into the Ubuntu VM.

**Use growpart (recommended — handles GPT fix automatically):**
```bash
sudo growpart /dev/sda 3
```

This replaces the interactive `parted` workflow and avoids the "Fix/Ignore?" trap.

**Why not parted directly?**
If you use `sudo parted /dev/sda` and it asks "Fix/Ignore?" for the GPT:
- Choosing "Fix" then trying to type `3` at the "Partition number?" prompt
- But accidentally pasting a full command instead of just the number
- Results in "Error: Partition doesn't exist"
- `growpart` skips this entire interactive mess

**If growpart is not installed:**
```bash
sudo apt install cloud-guest-utils
```

### Step 4: Resize LVM (Guest Side)
Run these in order, one at a time:
```bash
# Resize the physical volume to see new space
sudo pvresize /dev/sda3

# Extend the logical volume to use all free space
sudo lvextend -l +100%FREE /dev/ubuntu-vg/ubuntu-lv

# Resize the filesystem to fill the logical volume
sudo resize2fs /dev/ubuntu-vg/ubuntu-lv
```

### Step 5: Verify
```bash
df -h
```
You should see the root filesystem at the new size.

## Common Gotchas

### "Edit Disk" Grayed Out
**Cause:** Active checkpoint(s) on the VM.
**Fix:** Delete all checkpoints first, wait for merge.

### Parted Interactive Prompt Trap
**Symptom:** parted asks "Fix/Ignore?" → you say Fix → it asks "Partition number?" → you paste a full command → "Error: Partition doesn't exist"
**Fix:** Use `growpart` instead, or type just `3` (the partition number) at the prompt.

### LVM Not Seeing New Space
**Symptom:** `pvresize` does not show the expanded size.
**Check:** Did you actually resize partition 3? Verify with:
```bash
lsblk
sudo fdisk -l
```

## Quick Reference
- **Partition usually:** `/dev/sda3` (partition 3 is typically the LVM physical volume on Ubuntu)
- **LVM paths:** `/dev/ubuntu-vg/ubuntu-lv` (default for Ubuntu Server installs)
- **Growpart syntax:** `growpart /dev/sda 3` (device + partition number, space-separated)

## Related References
- `references/qdrant-timestamp-verification.md` — verifying memory integrity after disk expansion
