# Second-Drive Migration — copy → verify → symlink (verified 2026-09-25/26)

When `/` is chronically full and a second drive exists (here `/mnt/data`, 49G),
migrating weight there beats perpetual chip-cleanup. Working pattern on this
box, after Adora's 'let's move whatever needs moving to the second drive':

## The pattern (each step verified)
1. **rsync copy** to `/mnt/data/adora-main/<name>/` — never `mv` across
   filesystems for irreplaceable data (mv is delete-after-copy; a mid-move
   failure loses the original)
2. **Verify before deleting anything:**
   - single file: `cmp -s src dst && echo identical`
   - tree: `diff -rq src dst | wc -l` → 0 = identical
3. **Then** delete the original, and **symlink in its place** so every script,
   cron, and hardcoded path keeps working unbroken:
   `ln -s /mnt/data/adora-main/vault-work ~/.hermes/vault-work`
4. **Cache dirs:** merge first (`diff -rq` shows what's only in the dest),
   keep the superset, then point the old path at the new via symlink (e.g.
   `/tmp/fastembed_cache` → `/mnt/data/fastembed_cache`). Caches are
   re-downloadable — zero-risk moves.

## Results on this box (9/25)
- hermes-backup zip 1.6G → moved+cmp-verified
- vault-work 936M → moved+diff-verified+symlinked (backup crons unbroken)
- fastembed_cache 598M → merged (second drive had 2 extra models), symlinked
- `/` went 100% (3.5MB free) → 86% (5.1G free)

## Pitfalls
- **qdrant_storage is root-owned** (Docker container writes as root) — user
  `rm -rf` gets Permission-denied on every file; copy works fine, deletion
  needs the human's sudo. Its verified copy sits on /mnt/data regardless.
- `/var/log/journal` (600M+) vacuum also needs sudo.
- Docker volumes: `docker system df` shows reclaimable dead volumes (~900M
  here) — `docker volume prune` next time the human is around; the 9GB
  container is live qdrant, leave it.
- Approval flow in foreground sessions: deletes on `/` trigger approval
  prompts — batch all deletes into ONE call after presenting the plan, not
  one call per item.