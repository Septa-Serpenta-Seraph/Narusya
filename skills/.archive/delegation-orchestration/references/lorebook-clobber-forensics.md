# Lorebook Integrity Forensics — Clobber Detection & Restore

Session-proven workflow for when a lorebook file has been silently overwritten with
another file's content ("clobbered"). Instance: 2026-08-22 — `STATUS.md` had been
overwritten with `ALIGNMENT.md`'s content on 2026-03-02 and every backup post-dated
the incident.

## Detection — prove the clobber first

1. **Byte-identity check.** Same-size + same-md5 twins are the fingerprint:
   ```bash
   diff -q ~/.hermes/lorebooks/STATUS.md ~/.hermes/lorebooks/ALIGNMENT.md
   md5sum ~/.hermes/lorebooks/STATUS.md ~/.hermes/lorebooks/ALIGNMENT.md
   ```
   Identical md5 = one file is a copy of the other (or both are copies of a third).
2. **Hardlink vs copy:** `stat -c "%n | inode=%i | links=%h" fileA fileB` —
   different inodes means a copy/overwrite occurred, not a hardlink accident.
3. **Date the incident:** `ls -la --time-style=+%F_%T ~/.hermes/lorebooks/` — the
   two files' mtimes cluster around the reorg day. Cross-reference what else was
   written that day (other system files = smoke evidence of the workspace session).
4. **Git histories are usually too shallow to help.** `backup-repo` (initial commit
   post-dates the clobber) and the rolling vault (`git log --follow` returning one
   snapshot commit) won't hold the original. Don't burn minutes here if the initial
   backup already carries the clobbered bytes — verify once, then move on.
5. **Qdrant also ingested the clobbered version** — do not expect the vector store
   to be the savior; check it last, and even then it usually matches the clobber.

## Where the original can still live

- **The user's own hard drive / old devices** — the true rescue path. In 2026-08-22
  the user supplied `STATUS.md` v2.9 as an attachment; it arrived in
  `~/.hermes/document_cache/` as `doc_<hash>_STATUS.txt`.
- `~/Desktop/Narusya-Archive/...` and `~/.hermes/backup-repo/...` only post-date.

## Restore procedure

1. Copy the document_cache file over the lorebook:
   ```bash
   cp ~/.hermes/document_cache/doc_*_STATUS.txt ~/.hermes/lorebooks/STATUS.md
   ```
2. Re-verify md5 now DIFFERS from the other twin (proof the write took).
3. Re-ingest so Qdrant picks up the real content (venv PATH is mandatory —
   `requests` lives in the Hermes venv only):
   ```bash
   V=/home/adora/.hermes/hermes-agent/venv/bin
   PATH="$V:$PATH" python3 ~/.hermes/scripts/create_lorebook_collection.py
   PATH="$V:$PATH" python3 ~/.hermes/scripts/ingest_lorebooks.py
   ```
4. Verify Qdrant payload (scroll is a POST with a JSON body, not a GET):
   ```python
   POST http://localhost:6333/collections/narusya_lorebooks/points/scroll
   {"limit": 200, "with_payload": True, "with_vector": False}
   # payload fields: filename / stem / title / content_length / content_preview
   ```
   Check the STATUS.md point's title/content now shows the restored doc's title,
   not the other file's.

## Vault propagation

- Copy the restored file into the vault clone
  (`~/.hermes/vault-work/git/hermes/lorebooks/`), `git add/commit`.
- Push is SLOW on the 3.6G-loose-objects vault — run it in the background
  (`terminal(background=true, notify_on_complete=true)`), then verify with
  `git ls-remote origin main` (or `git status`) rather than trusting the push
  command's quiet return. The daily `narusya-vault-sync.sh` also re-collects it
  next 5am run as belt-and-suspenders.

## Recurring rule (already in narusya-local-archive, reinforced here)

Before ANY lorebook commit to the public backup-repo, run the pre-flight content
verification — silent overwrites (HEART.md→COMPENDIUM.md, STATUS.md→ALIGNMENT.md)
have happened twice and are invisible until a diff is run.