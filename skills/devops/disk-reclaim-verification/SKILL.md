---
name: disk-reclaim-verification
description: Verify disk occupants are redundant before deleting.
category: devops
triggers:
  - disk full
  - reclaim disk space
  - safe to delete
  - before trashing
  - clean up disk
  - what can I delete
---

# Disk Reclaim Verification

Companion to the cleanup-tables skills (`disk-full-diagnostics`, `hyperv-vm-disk-expansion` — those are user-owned; if a patch to them is wanted, run `hermes curator adopt <name>` first). This skill carries the VERIFICATION discipline: on a full disk, never delete until you've PROVEN the target is redundant or re-derivable.

## The hard rule (Adora, 2026-08-23)
"Be careful with the cleanup and verify what you're trashing before you trash it."
Two failure modes, both seen live:
- **Caution without proof** blocks safe reclaims and costs GBs (refused to delete a derived archive export until she pointed out it was just a qdrant/state.db copy).
- **Proof without caution** deletes what matters (a seemingly redundant vault-work local dir that was NOT fully offsite).

When the human asks "isn't that just a copy of X?", **test the claim with direct evidence** — never accept it on faith, never reject it out of caution.

## Proof recipes (each verified working 2026-08-23)

### 1. Garbage git dir — safe to `rm -rf`
e.g. home `~/.git` was **452M** of pure orphan objects. Proof it's trash:
```bash
git -C ~ branch -a                 # no branches
git -C ~ rev-list --all --count    # → 0
git -C ~ ls-files                  # empty (no index/tracked files)
git -C ~ fsck --full | head        # ONLY dangling blobs
git -C ~ remote get-url origin     # no remote
```
Zero commits + zero refs + zero remote + empty index = accumulation from a botched `git init`; deleting loses nothing.

### 2. Derived session archives — export, not source
`Desktop/Narusya-Archive/` (810M) and vault `archive/` are EXPORTS; **live `state.db` is canonical**. Prove before deleting:
```bash
sqlite3 ~/.hermes/state.db 'select count(*) from sessions'
sqlite3 ~/.hermes/state.db 'select count(*) from messages'
```
If the live db holds all sessions (1035 / 125854 verified 8/23), the export is re-derivable (re-run the export script later). Deleting is safe.

### 3. Vault-work local redundancy map
- `state/state.db.gz` = gzip of LIVE `state.db`
- `qdrant/` = copy of live `qdrant_storage`
- `secrets-bundle.enc` = encrypted copy of live `~/.hermes/secrets` (already pushed to the GitHub remote)
- `archive/` = derivable from state.db
- unpushed commits (remote 8/19 vs local 8/23) hold only gz copies of live data → re-derivable
Deleting vault-work local frees ~5.7G, but the **GitHub vault must remain as the offsite DR** — never carve the DR backup without an explicit nod.

### 4. Measure the EXTRACTED footprint, not the download size
Before installing a big engine on a near-full disk: `camoufox fetch` downloads a ~663MB zip but **extracts to ~1.3G** in `~/.cache/camoufox/`. Fetching on a 99% disk craters it to ~0 free instantly. Check headroom ≥ the extracted size.

### 5. Count before `find -delete`
`find ... | wc -l` (or print matches) BEFORE deleting. On an already-cleaned system the targets are gone (request_dump_*/jsonl found 0 matches on 8/23) and "cleaning" frees nothing — when caches are empty and no safe item remains, STOP chipping and pivot: add a disk (see `hyperv-vm-disk-expansion` second-disk flow) or fund more storage.

## Boundaries remembered
- **`mkfs` is on the agent's unconditional blocklist** — the agent cannot format a filesystem even with approval; hand format commands to the human (`sudo parted ... mklabel gpt` + `mkpart` + `sudo mkfs.ext4`), then the agent owns mount/move/symlink.
- `sudo` needs a password on this box; partition/format steps are human-side.

## References
- User-owned `disk-full-diagnostics` — canonical cleanup tables (caches, state-snapshots, journal).
- User-owned `hyperv-vm-disk-expansion` — LVM grow + second-disk additive flow.
- User-owned `camoufox-browser-setup` — engine install (`camoufox-js fetch`), CDP-vs-cloud selection.