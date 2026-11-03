# GitHub Vault Push Rejected: Oversized Blobs in History (2026-08-22)

## Symptom
`git push origin main` fails after a long grind (or a foreground timeout) with:
```
remote: error: File qdrant/session_messages_archive.snapshot is 153.49 MB; this exceeds GitHub's file size limit of 100.00 MB
remote: error: File archive/sessions.tgz is 172.12 MB; this exceeds GitHub's file size limit of 100.00 MB
remote: error: GH001: Large files detected.
 ! [remote rejected] main -> main (pre-receive hook declined)
```
Meanwhile `git ls-files | xargs du` shows **no current file over 100MB** — the giants are in
PAST commits. GitHub's pre-receive hook checks every object in the pushed pack, not just the head
tree, so a once-committed giant blocks every future push until it leaves history.

## Diagnosis (verified working)
```bash
# 1. Find blobs >100MB anywhere in history (git cat-file -s reads every object)
git rev-list --objects --all | awk '{print $1}' | while read oid; do \
  sz=$(git cat-file -s "$oid" 2>/dev/null); \
  [ -n "$sz" ] && [ "$sz" -gt 104857600 ] && echo "$((sz/1048576))MB  $oid"; done

# 2. Map blob → path so you know which backup artifact it was
git rev-list --objects --all | grep <oid>
```
Also check `git status` + `git log --oneline origin/main..HEAD` to see if the blocked commits are
queued behind the giants (3 days of backups stacked up in the 2026-08-22 case).

## Remediation options (NOT yet executed on narusya-vault — needs human sign-off)
Any fix rewrites history and requires a force-push; get explicit user approval first since this
changes the DR chain's remote history (keep a local backup of the repo dir before starting).
1. **`git filter-repo`** (preferred) or `filter-branch` — strip the offending blob paths, prune,
   repack, force-push. The giants are superseded by the chunked (95MB) versions, so no data loss.
2. **Git LFS** (`git lfs migrate import --include=<paths>`) — also rewrites history to move blobs
   to LFS pointers; heavier toolchain change, same history-rewrite cost.

## Operations lessons from the same incident
- A heavy push (multi-GB pack, slow uplink) can run 20–30+ min and blow foreground timeouts.
  Push with `background=true` + `notify_on_complete=true`; afterwards verify the remote actually
  moved: `git ls-remote origin main` vs `git rev-parse HEAD`. A timed-out foreground push means
  NOTHING shipped — do not report success.
- The STATUS.md lorebook restore commit rode this same failed push path; the fix unlocks several
  stacked days of backups, not just the one commit.