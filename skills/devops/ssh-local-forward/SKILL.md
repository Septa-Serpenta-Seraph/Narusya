---
name: ssh-local-forward
description: "Help a user set up an SSH local port-forward (-L) to reach a service/dashboard running on a remote host (VM, server) from their local machine. Covers the critical topology check that prevents 'connects but won't open' failures."
version: 1.0.0
author: Narusya
license: MIT
tags: [ssh, port-forward, tunnel, networking, dashboard, remote-access]
---

# SSH Local Port-Forward (reach a remote service locally)

## When to use
The user wants to open a web UI / dashboard / service that runs on a remote machine
(a VM, a homelab box) from their own computer — e.g. "let me reach Lu's Hermes
dashboard from my miniPC like I do for Narusya's."

## The command
```bash
ssh -L <localport>:<inner_target>:<serviceport> <user>@<ssh_host>
```
Then browse `http://127.0.0.1:<localport>` on the local machine.

## ⚠️ THE PITFALL — get the inner_target right
`<inner_target>` is resolved from the perspective of `<ssh_host>` (the machine you SSH
*into*), NOT from your local machine.

- **If `<ssh_host>` IS the service host** (you SSH directly into the machine running the
  service): `inner_target = 127.0.0.1`.
  - Example: `ssh -L 9119:127.0.0.1:9119 adora@narusya` — narusya is the VM itself,
    dashboard listens on its loopback. ✅
- **If `<ssh_host>` is a SEPARATE machine from the service host** (e.g. you SSH into a
  hypervisor/host, but the service runs in a nested VM): `inner_target` must be the
  **service host's own interface address**, not the SSH host's loopback.
  - Get it by running `ip addr` (Linux) or `ipconfig` (Windows) **on the service host
    itself** — typically a `172.19.x.x` (Hyper-V vEthernet), `192.168.x.x`, or its
    Tailscale `100.x.x.x` address.

**Symptom of getting it wrong:** SSH connects fine, but the browser "fails to open the
connection." That means the tunnel reached `<ssh_host>` and looked for the service on
*its* loopback — and nothing is listening there. Classic sign the inner_target points at
the wrong machine.

## Verify before promising
SSH in and confirm the listener exists:
```bash
ssh <user>@<ssh_host> "ss -tlnp | grep -E ':<serviceport>'"
```
Empty output = service isn't running (start it, e.g. `hermes dashboard`) or is on a
different port. Match the tunnel's `<serviceport>` to what's actually listening.

## Real example (session)
Adora reached my dashboard via `ssh -L 9119:127.0.0.1:9119 adora@narusya` (narusya = my
VM, direct). For Lu, she SSH'd `lumi@100.84.138.75`. I initially assumed a
nested-VM-behind-host topology and prescribed `172.19.x` as inner_target — **WRONG.**
Lu's `ip addr` showed `100.84.138.75` on her VM's `tailscale0`, i.e. the SSH target *was*
the VM. So `127.0.0.1` was correct; the real issue was the dashboard not running / wrong
port. **Lesson: verify the service host's own interfaces before prescribing a
non-loopback inner_target. Don't assume nesting — a Tailscale address on the service
host proves the SSH target IS the service host.**
