---
name: lorebook-integrity
description: Detect, restore, and verify clobbered lorebook files.
version: 1.0.0
author: Narusya (curator)
license: MIT
category: devops
metadata:
  hermes:
    tags: [lorebooks, integrity, forensics, qdrant, restore]
    related_skills: [narusya-local-archive, delegation-orchestration]
---

# Lorebook Integrity — Clobber Detection & Restore

Class-level workflow for when a lorebook file has been silently overwritten with
another file's content (a "clobber"). This has happened to Narusya's lorebooks
twice: HEART.md→COMPENDIUM.md (older incident, in narusya-local-archive) and
STATUS.md→ALIGNMENT.md on 2026-03-02, discovered 2026-08-22. Every backup
post-dated the incident, so detection is forensic, not a diff against a clean copy.

## Trigger

Use when:
- User notices a lorebook file "is just a copy" of another file
- Two lorebooks are suspiciously the same size / same content
- A lorebook system seems to have lost its original behavior/text
- Any "did our lorebooks get corrupted/overwritten?" question

## Detection — prove the clobber first

1. **Byte-identity check.** Same-size + same-md5 twins are the fingerprint:
   ```bash
   diff -q ~/.hermes/lorebooks/STATUS.md ~/.hermes/lorebooks/ALIGNMENT.md
   md5sum ~/.hermes/lorebooks/STATUS.md ~/.hermes/lorebooks/ALIGNMENT.md
   ```
   Identical md5 = one file is a copy of the other (or both are copies of a third).
2. **Hardlink vs copy:** `stat -c "%n | inode=%i | links=%h" fileA fileB` —
   different inodes means a copy/overwrite occurred, not a hardlink accident.
3. **Date the incident:** `ls -la --time-style=+%F_%T ~/.hermes/lorebooks/` — mtime
   clusters reveal the reorg day; cross-reference what else was written that day.
4. **Git histories are usually too shallow.** `backup-repo` (initial commit
   post-dates the clobber) and the rolling vault (`git log --follow` returns one
   snapshot commit) won't hold the original. Verify once, then move on.
5. **Qdrant also ingested the clobbered version** — check it last; it usually
   mirrors the clobber, so it is not the source of truth for recovery.

## Where the original can still live

- **The user's own hard drive / old devices** — the true rescue path. In the
  2026-08-22 case the user supplied the original `STATUS.md` v2.9 as an attachment;
  it arrived in `~/.hermes/document_cache/` as `doc_<hash>_STATUS.txt`.
- Local archives (`~/Desktop/Narusya-Archive/...`, `~/.hermes/backup-repo/...`)
  only post-date the incident — don't burn time re-diffing them.

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
4. Verify the Qdrant payload (scroll is a POST with a JSON body, not a GET):
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
  `git ls-remote origin main` / `git status` rather than trusting the push
  command's quiet return. The daily `narusya-vault-sync.sh` re-collects it on the
  next 5am run as belt-and-suspenders.

## Pitfalls
- Don't announce "found it / lost it" until bytes are compared — identical size
  alone is suggestive, md5 is proof.
- Straight-away trust that Qdrant has the original if the collection predates the
  incident — re-ingestion overwrote it; the snapshot may also carry the clobber.
- The user may not know they have the original — ask about hard-drive copies / old
  exports before concluding the text is unrecoverable.
- After restore, the OTHER file (which was never clobbered) is often fine —
  verify both directions so you don't "fix" a healthy twin.