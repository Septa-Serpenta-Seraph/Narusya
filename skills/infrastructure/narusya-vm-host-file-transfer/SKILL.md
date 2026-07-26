---
name: narusya-vm-host-file-transfer
description: Transfer files between the Windows host ("SHELL") and the Narusya Linux VM running on Hyper-V. Covers the VM topology, file sharing mechanisms, and fallback methods.
triggers:
  - "file transfer to VM"
  - "get file into Narusya"
  - "send file to VM"
  - "copy file to Linux VM"
  - "large file upload"
  - "file too big for discord"
  - "hyper-v shared folder"
  - "host file to VM"
---

# Narusya VM-Host File Transfer

## Architecture: Narusya Runs as a Hyper-V VM on Adora's Windows Machine

**Critical context:**

- Narusya runs as a **Linux VM** (Ubuntu, 37GB disk, 4GB RAM) on Hyper-V
- The Windows host machine is named **"SHELL"** — Adora's personal PC (i7-10700KF, 16GB RAM, RTX 2080, Windows 11 Pro 24H2)
- The Hyper-V VM is named **"Narusya"**
- File paths like `C:\Users\Adora\...` are **Windows host paths** — NOT accessible from inside the VM via normal paths
- The Discord gateway cannot transfer large files (169MB+) to the VM — it has size limits
- When the Windows host shuts down, Narusya shuts down

## Method 1: SCP from Windows Host (Preferred — Works for Headless VMs)

**For headless Linux VMs (no desktop/GUI), this is the primary method.** Enhanced Session drag-and-drop does NOT work because the VM only has a CLI — there's no "Show Options" button in the connection window.

**Confirmed working (Apr 2026):**
```powershell
# From Windows PowerShell on the host:
scp "C:\Users\Adora\Desktop\filename.pdf" adora@172.27.54.161:~/destination/file.pdf
```
- First connection triggers host key verification — type `yes`
- Then enter the VM user's password
- Transfer is fast (170MB at ~182MB/s observed)

**VM IP Addresses (as of Apr 2026 — verify with `hostname -I`):**
- Internal Hyper-V network: `172.27.54.161` (primary, use this first)
- Tailscale: `100.77.142.40` (fallback)
- Public: changes (check with `curl api.ipify.org`)

**If SCP connection refused:**
```bash
# Inside the VM:
sudo systemctl start ssh
sudo systemctl enable ssh
```

## Method 1b: Hyper-V Enhanced Session (Does NOT Work for Headless VMs)

⚠️ **This method does NOT work for the current setup.** The Narusya VM is headless Linux (CLI only). When you "Connect..." in Hyper-V Manager, you get a terminal — NOT a desktop with drag-and-drop. There is no "Show Options" button. Ignore this method unless a desktop environment is installed.

If a desktop IS installed in the future:
1. In Hyper-V Manager → Right-click "Narusya" → **Connect...**
2. Click **"Show Options"** → **"Local Resources"** → **"More..."**
3. Check drives to share
4. Shared drives appear under `/mnt/`

## Method 2: SCP/SFTP from Host to VM

If you can determine the VM's IP address:

```bash
# Find the VM's IP from inside the VM:
ip addr show | grep 'inet '
```

Then from Windows (PowerShell or WSL):
```powershell
# Using SCP (requires OpenSSH on Windows, which Win 11 has)
scp C:\path\to\file.pdf adora@<VM-IP>:~/destination/

# Using SFTP
sftp adora@<VM-IP>
put C:\path\to\file.pdf ~/destination/
```

**Finding the VM IP from the host:**
```powershell
# In PowerShell on the host:
Get-VM -Name "Narusya" | Get-VMNetworkAdapter | Select-Object -ExpandProperty IPAddresses
```

## Method 3: Cloud Upload Fallback (Works but Slower)

When Hyper-V sharing isn't available:

1. Upload the file to Google Drive, Dropbox, or similar from the Windows host
2. Share the direct download link with Narusya
3. Narusya downloads via `wget`:

```bash
# For Google Drive links, use the direct download format:
wget --no-check-certificate "https://drive.google.com/uc?export=download&id=FILE_ID" -o output.pdf

# For Dropbox links, change ?dl=0 to ?dl=1:
wget "https://www.dropbox.com/s/FILE_ID/file.pdf?dl=1" -o output.pdf
```

Use the `gdrive-download` skill for Google Drive-specific quirks.

## Method 4: Python HTTP Server (Quick & Dirty)

From the Windows host, in the directory with the file:

```powershell
# In PowerShell, navigate to the directory:
cd C:\Users\Adora\Desktop

# Start a simple HTTP server (requires Python):
python -m http.server 8080
```

Then from inside the VM:
```bash
# Adora needs to know the Windows host IP from the VM's perspective
# Try the Hyper-V default gateway:
GATEWAY_IP=$(ip route | grep default | awk '{print $3}')
wget "http://${GATEWAY_IP}:8080/EMR%20Report.PDF" -O ~/health-record.pdf
```

**Note:** This requires the VM's network to have a route to the host on port 8080. May be blocked by Windows Firewall.

## Method 5: Base64 Encoding (Tiny Files Only)

For small text files (NOT large binaries):

```bash
# On Windows PowerShell:
[Convert]::ToBase64String([IO.File]::ReadAllBytes("C:\path\to\file.txt"))

# On Linux VM:
echo "BASE64STRING" | base64 -d > output.txt
```

## Decision Matrix

| Method | Speed | Ease | Size Limit | Works for Headless VM? |
|--------|-------|------|------------|------------------------|
| **SCP from Host** | ⚡ Fast | ✅ Easy | **None** | ✅ **YES — primary method** |
| Enhanced Session + Drag/Drop | ⚡ Fast | ✅ Easiest | None | ❌ No — needs desktop GUI |
| Cloud Upload | 🐢 Slow | ⚠️ Medium | Cloud limit | ✅ Yes |
| Python HTTP Server | ⚡ Fast | ⚠️ Tricky | None | ✅ Yes (firewall issues) |
| Base64 | 🐢 Slow | ❌ Tedious | ~10MB | ✅ Yes |

## VM Lifecycle Notes

- **Host shutdown = VM shutdown** — Narusya dies when SHELL goes down
- **Host sleep = VM freezes** — cron jobs, pending operations, and active sessions may be affected
- **VM checkpoints** exist dated 3/2 through 3/16/2026 — can revert to known-good states
- **Disk space**: 37GB total, check with `df -h` — large files can fill it up

## Troubleshooting

**"No C: drive mount found"** — Hyper-V shared folders aren't set up. Use SCP or cloud upload.

**"SCP connection refused"** — SSH might not be running on the VM:
```bash
sudo systemctl start ssh
sudo systemctl enable ssh
```

**"wget returns HTML"** — Cloud link isn't a direct download. See `gdrive-download` skill.

**`<my-ip>` literal in command** — Make sure the user replaces `<my-ip>` with the actual IP address. Common mistake when copy-pasting.

## Processing Large PDFs After Transfer

For large PDFs (800+ pages from EMR systems like Epic):

```bash
# Install pymupdf
pip install pymupdf --quiet

# Quick info
python3 -c "
import fitz
doc = fitz.open('/home/adora/health-record.pdf')
print(f'Pages: {len(doc)}')
print(f'Metadata: {doc.metadata}')
"

# Extract all text for easier searching
python3 -c "
import fitz
doc = fitz.open('/home/adora/health-record.pdf')
with open('/home/adora/health-record-full.txt', 'w') as f:
    for i, page in enumerate(doc):
        text = page.get_text()
        if text.strip():
            f.write(f'=== PAGE {i+1} ===\n')
            f.write(text + '\n')
print('Done. Search with: grep -n keyword ~/health-record-full.txt')
" 2>&1
```

This converts a multi-thousand-page PDF into a searchable plaintext file. 8,069 pages → ~13MB, 700K+ lines. Use `grep -n -i "keyword"` to search efficiently.
