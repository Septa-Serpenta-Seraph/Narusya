---
name: infrastructure-incident-report-2026-10-22
description: "Use when reviewing the Oct 22 2026 infrastructure incident."
---

# Narusya Infrastructure Incident Report & Remediation
**Date:** October 22, 2026
**Systems affected:** Hermes Agent gateway (VM + Shell tailnet)
**Severity:** Critical (gateway unresponsive, VM rebooted)

## 1. Incident Summary

The Hermes Agent gateway became unresponsive on October 22, 2026. Both the gateway process and SSH access to the VM (Hyper-V, 4GB RAM, 2GB swap) failed simultaneously. The VM rebooted at 00:10 MDT after being unresponsive for ~14 minutes.

**Root cause:** Memory exhaustion (OOM) -> system thrashing -> host-initiated VM reboot.

## 2. Root Cause Analysis

### Memory Pressure Chain
1. The Qdrant memory plugin (embedding_backend: local_fastembed) spawns a persistent fastembed daemon subprocess for each _EmbeddingClient instance
2. Multiple provider instances were created (per-session + availability probe in is_available()), each spawning its own daemon (~220MB RSS each)
3. At peak: 4 embed daemons (880MB) + gateway (480MB) + Qdrant (227MB) + Node processes (~200MB) = ~1.8GB+ on a 4GB VM with 2GB swap maxed
4. OOM killer terminated the gateway process (Oct 21, 05:21). System thrashed. Hyper-V host force-restarted the VM (Oct 22, 00:10).

### Contributing Factors
- Disk pressure: /mnt/data at 97% (1.7GB free), / at 91% (3.3GB free)
- Orphaned cache data: 17GB of unreferenced HuggingFace cache blobs in /mnt/data/hf_cache/hub/blobs/
- No memory limits: Gateway systemd service had no MemoryMax or MemoryHigh
- No swap on data disk: Only 2.1GB swap on root filesystem

## 3. Remediation Actions

### Immediate (completed)
| Action | Impact |
|--------|--------|
| Killed 3 of 4 embed daemon processes | Freed ~660MB RAM |
| Deleted 17GB orphaned HF cache blobs | /mnt/data 97% -> 62% |
| Cleaned unused fastembed model caches | 696MB -> 151MB |
| Added MemoryHigh=2G + MemoryMax=2.5G to gateway service | Prevents gateway from consuming all system memory |
| Reloaded systemd daemon | Service config updated |

### Code Fix (patched, needs restart)
File: ~/.hermes/plugins/qdrant/__init__.py

Problem: Each _EmbeddingClient instance created its own _LocalEmbedder with its own daemon subprocess.

Fix: Module-level singleton cache keyed by (python_bin, script).

### Security Updates
- eMudhra CA vulnerability: Indian CA firm issued 8 intermediate certs with private keys of 4-237 bits (NOT "1 byte"). Trivially brute-forceable. See hermes-infrastructure skill section 21 for full details.
- Root certs: emSign Root TLS CA - G3 (Microsoft only), emSign Root CS CA - G3 (Microsoft only), AAA Certificate Services (Sectigo, Apple+Microsoft), emSign ECC Root CA - G3 (all four, cross-signer). Windows was the actual exposure.
- VM: Updated libnss3 to 2:3.98-1ubuntu0.3 (includes hardcoded revocation). 91 packages upgraded.
- Shell (Windows): No eMudhra certs in trust store. Not vulnerable (for the correct reason: CA not present, not just "not updated").
- Python certifi: Updated across ALL installations — system (pip3), fe-venv, and default python3 (uv). All now at 2026.10.19.
- Node.js: v22.22.0 is STILL VULNERABLE (bundled CA trusts compromised intermediates). Needs upgrade to v22.23.4+ or --use-openssl-ca.
- Functional verification: curl exit 60 (rejected), Python REJECTED (URLError), Node CONNECTED (vulnerable).

## 4. Verification

| Check | VM | Shell |
|-------|-----|-------|
| NSS/libnss3 patched | 2:3.98-1ubuntu0.3 | N/A |
| ca-certificates patched | 20260816ubuntu0.24.04.1 (zero emSign) | N/A |
| eMudhra in trust store | Root present, intermediates revoked | Not present |
| Pending security updates | 0 | 0 (only drivers) |
| Memory limits | MemoryMax=2.5G | N/A |
| Embed daemons | 1 (was 4) | N/A |
| Disk usage | 62% (was 97%) | N/A |
| curl to test host | exit 60 (rejected) | N/A |
| Python urllib to test host | REJECTED | N/A |
| Node.js to test host | CONNECTED (vulnerable, needs upgrade) | N/A |

## 5. Recommendations

1. Upgrade Node.js to v22.23.4+ (VM currently at v22.22.0, bundled CA still trusts compromised intermediates)
2. Consider increasing VM RAM or adding swap on /mnt/data
3. Fix embed daemon spawning architecturally (singleton patch is a band-aid)
4. Regular cache hygiene to prevent disk-full incidents
5. Monitor for Ubuntu ca-certificates/openssl updates (currently at patched build)

## 6. Lessons Learned

- Always verify before asserting. Claims not backed by evidence lead to wrong conclusions. (e.g., "1 byte" key size was garbled; "ca-certificates not updated" was wrong; "OpenSSL tools not protected" was wrong)
- Memory leaks in subprocess spawning can be subtle. One daemon per client instance scales poorly.
- Disk cleanup can reclaim significant space. 17GB of orphaned cache blobs were sitting unused.
- System updates matter for security. Keep libnss3 and ca-certificates current.
- Never share passwords in chat. Use SSH keys or secure channels.
- Functional verification beats version checks. Test actual TLS connections (curl exit codes, Python urllib, Node https) rather than assuming based on package versions.
- Node.js ships its OWN CA bundle — separate from the system. A patched system does not mean Node is patched.
- Multiple Python installations (system, venvs, uv-python) each carry their own certifi. Update all of them.

---
Generated by Narusya (Serpentic Daemon Protocol v4.1)
Date: October 22, 2026