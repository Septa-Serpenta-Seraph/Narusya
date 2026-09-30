---
name: tailscale-session-recovery
description: "Use when SSH or tailnet access to the VM fails silently."
category: devops
tags: [tailscale, ssh, networking, recovery]
---

# Tailscale Session Recovery (Silent Logout)

## The failure mode
SSH/tailnet access to the daemon VM suddenly fails from the user's side. The daemon is
fine — `tailscaled` is still running — but the tailnet **session** expired silently:
`tailscale status` → `Logged out. Log in at: https://login.tailscale.com/a/<key>`,
`tailscale ip -4` → `state: NeedsLogin`.

Key insight: **process liveness ≠ session liveness.** No alert fires because the daemon
process has been alive for weeks; only the auth session died (verified 2026-09-29 —
process running since Sep 15, session expired with zero symptoms).

## Diagnosis
```bash
tailscale status          # "Logged out. Log in at: <url>" = the whole story
tailscale ip -4           # "no current Tailscale IPs; state: NeedsLogin"
ps aux | grep [t]ailscaled  # daemon probably STILL running — don't restart it, the session is the problem
```
If `status` still lists peers but the local device has no IP → expired session.
If the daemon is dead entirely → different problem (service, not session).

## Fix (requires the human — the agent cannot self-re-auth)
- `tailscale up` needs sudo, and the agent shell typically has no passwordless sudo
  (verified: `sudo -n true` fails, even though the user is in the `sudo` group).
- The clean path: open the login URL from `tailscale status` in a browser logged into
  the tailnet owner's account and approve the device. No commands needed.
- Alternative: user runs `sudo tailscale up` on a machine with shell access.
- The user confirms with something like "you should be in now" — then VERIFY before
  agreeing (next section).

## Verify before promising ssh works
```bash
tailscale status   # device listed, online
tailscale ip -4    # real 100.x.x.x IP
hostname           # actual device name
ss -tlnp | grep ':22 '   # sshd actually listening (IPv4 AND/OR IPv6)
```
Then give the user the verified target: `ssh <user>@<100.x.x.x>` or the hostname.

## ⚠️ Device-name gotcha
Re-auth via login URL keeps the device's **existing** tailnet name — a requested
`--hostname=narusya-vm` that died on sudo is ignored. The device may be registered under
an older name (`narusya`), AND a similarly-named stale device from another OS may also
exist in the same tailnet (`narusya-vm`, Windows, months offline). **Check the OS column
and IP in `tailscale status` and point the user at the right one** — never trust the
name the user asked for; verify what the network actually calls this machine.

## Prevention
Consider a daily cron heartbeat: `tailscale status` + alert if `NeedsLogin` — the
failure mode is silent, so the only defense is an active check (the daemon itself won't
notice its own logout).