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

### 6. The 9/8 full-disk survey (37G root, hit 100%)
Ranked occupants at that event — recurring suspects on this box:
- `/var/lib/snapd` 4.0G (old snap revisions; `retain=2` + revision cleanup needs sudo)
- `~/.hermes/hermes-agent` 3.6G (venv + node_modules + fat .git pack — mostly legit, leave alone)
- `~/.hermes/vault-work` 2.1G incl. orphaned `git/.git/objects/pack/tmp_pack_*` (376M) — **aborted git pushes leave tmp_pack files; safe to delete after confirming no push is running**
- `~/.hermes/backups` 1.6G full-zip from a past reclaim (third copy — live data + GitHub vault both exist; delete only with Adora's explicit nod)
- `~/.cache/ms-playwright` dual Chromium installs (~500M each; delete the old version dir — both `chromium-NNNN` and `chromium_headless_shell-NNNN` for the retired build)
- `~/.hermes/state.db`+wal 834M; `/var/log` 615M (journald vacuum needs sudo)

Cleanup batch that worked non-destructively: tmp_pack delete (376M) + `apt clean` (needs sudo) + journald `--vacuum-size=200M` (needs sudo) + old playwright chromium (~500M). sudo items are human-side (no passwordless sudo on this box).

### 8. HuggingFace cache blobs — two storage formats, verify before deleting (verified 2026-10-21)

The `hf_cache/hub/` directory contains TWO blob storage formats that must be distinguished before cleanup:

1. **`hub/blobs/XX/...`** — shared blob store (old format, organized by 2-char hash prefix). These can be **truly orphaned** — not referenced by any model. Verify before deleting.
2. **`models--<org>--<name>/blobs/...`** — model-specific blob store (new format). These contain the actual model weights. `du -sh` on a model directory does NOT follow symlinks, so it reports tiny sizes (e.g., 8MB) while the actual weights live in the model's own blobs directory.

**The symlink trap:** Model snapshot symlinks use `../../blobs/...` which resolves to the **model's own** `blobs/` directory (e.g., `models--kyutai--pocket-tts/blobs/...`), NOT the shared `hub/blobs/` tree. So resolving symlinks from model snapshots will point to model-specific blobs, not the shared ones. The shared `hub/blobs/` directory can be completely orphaned.

**Before deleting anything in hf_cache:**
1. List model directories: `ls /mnt/data/hf_cache/hub/ | grep models--`
2. For each model, resolve its symlinks: `find models--*/ -type l | while read l; do readlink -f "$l"; done | sort -u`
3. Compare against shared blob files: `find hf_cache/hub/blobs/ -type f ! -name '*.lock' ! -name '*.refs'`
4. Only blobs in the shared `hub/blobs/` tree NOT referenced by any model symlink are truly orphaned.
5. **Also check:** the shared blobs may be referenced by `../../../../../blobs/...` (old-format symlinks going up 5 levels to `hf_cache/blobs/`). Check both relative path patterns.

**Verified case (2026-10-21):** `hub/blobs/` (17GB, 2239 files) was 100% orphaned — no model symlink referenced it. The pocket-tts model (8.4MB reported by du) actually stored its weights in `models--kyutai--pocket-tts/blobs/` (8.4MB actual). Deleting the orphaned 17GB freed significant space with zero impact on the model.

**Pitfall:** `du -sh` on a directory with symlinks reports symlink sizes, not target sizes. Use `find ... -type f -size +100M` or resolve symlinks to measure true disk usage.

**Pitfall:** Don't assume shared blobs are referenced just because they exist. Always verify with symlink resolution. The old shared format (`hub/blobs/`) and new model-specific format (`models--*/blobs/`) coexist and can have different reference patterns.

### 7. SQLite: check the freelist before counting on VACUUM
A big `state.db` is not automatically bloated. Read-only proof before any vacuum/maintenance plan:
```python
import sqlite3
con = sqlite3.connect("file:/path/state.db?mode=ro", uri=True)
pc = con.execute("PRAGMA page_count").fetchone()[0]
fl = con.execute("PRAGMA freelist_count").fetchone()[0]
ps = con.execute("PRAGMA page_size").fetchone()[0]
print(f"{pc*ps/1e9:.2f}GB total, {fl*ps/1e6:.0f}MB reclaimable")
```
A dense DB (freelist ~0) is real data — VACUUM reclaims nothing, so leave it and reclaim elsewhere; only a fat freelist justifies the vacuum (which needs free disk ≥ the DB size to run).

## Boundaries remembered
- **`mkfs` is on the agent's unconditional blocklist** — the agent cannot format a filesystem even with approval; hand format commands to the human (`sudo parted ... mklabel gpt` + `mkpart` + `sudo mkfs.ext4`), then the agent owns mount/move/symlink.
- `sudo` needs a password on this box; partition/format steps are human-side.

## References
- `references/second-drive-migration.md` — copy→verify→symlink migration pattern for a second drive (worked 9/25: root 100%→86%)
- User-owned `disk-full-diagnostics` — canonical cleanup tables (caches, state-snapshots, journal).
- User-owned `hyperv-vm-disk-expansion` — LVM grow + second-disk additive flow.
- User-owned `camoufox-browser-setup` — engine install (`camoufox-js fetch`), CDP-vs-cloud selection.