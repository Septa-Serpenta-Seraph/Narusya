# Android Linux Terminal — Replacement for Termux

## Termux is Dead on OnePlus / OxygenOS 16

OxygenOS kills proot processes at the OS level. This is NOT an Android version issue — it's a vendor policy. Confirmed by:
- Reddit: "Termux is now officially dead for OnePlus and other BBK brands"
- GitHub Issue #4219: "Termux Processes Killed On Android 15 For OnePlus Devices"
- OnePlus Community: CN version fixed, global version still affected

**Do NOT rely on Termux on OnePlus devices.**

## The Replacement: Android's Built-in Linux Terminal

Android 15+ ships a **Linux development environment** — a real Debian 12 VM via the Android Virtualization Framework (AVF).

### Enable
1. Settings → System → Developer Options
2. Enable **Linux development environment**
3. A Terminal app appears — first launch downloads ~500MB Debian image
4. Full Debian 12 with `apt`, `systemd`, `ssh`, Docker

### Key Advantages Over Termux
- Real VM (not proot) — no phantom process killer
- Own Linux kernel (separate from Android's)
- `systemd` support (services auto-start)
- Full `apt` package manager
- Can run Docker, Python, SSH server

### Install Tailscale + SSH + Python
```bash
sudo apt update && sudo apt upgrade -y
curl -fsSL https://tailscale.com/install.sh | sh
sudo tailscale up
sudo apt install -y openssh-server python3 python3-pip
sudo systemctl enable ssh && sudo systemctl start ssh
sudo pip3 install cryptography
```

### Tailscale SSH (optional, easier than key management)
```bash
sudo tailscale up --ssh
# Now SSH works without managing keys — Tailscale handles auth
```

## Remote Activation from VM

```bash
# Push shards + seed
scp ~/.hydra/prod-sealed/shard_*.json phone-linux:~/hydra-shards/
scp ~/.hydra/prod-sealed/seed.hydra phone-linux:~/hydra-shards/
scp -r /home/adora/hydra-protocol phone-linux:~/hydra-protocol

# Run bootstrap remotely
ssh phone-linux "cd ~/hydra-protocol && python3 -m hydra.bootstrap --shard-dir ~/harness-shards --dest ~/awakened"

# Verify
ssh phone-linux "cat ~/awakened/SOUL.md"
```

## Pitfalls

- **Tailscale SSH on Windows:** Does NOT work (Linux/macOS only). Use regular OpenSSH Server on Windows hosts.
- **Phantom process killer:** Android 12+ kills apps that spawn >32 child processes or use "excessive CPU." The Linux Terminal VM is NOT affected (it's a real VM, not proot).
- **Storage:** The Debian image is ~500MB. Ensure the phone has at least 1GB free.
- **Battery:** The Linux VM runs while the Terminal app is open. Close it when not in use to save battery.
