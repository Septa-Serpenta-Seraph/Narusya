---
name: offsite-vault-backup
description: GitHub Vault off-site backup of daemon state and memory.
category: devops
version: 1.0.0
author: Narusya (curator)
license: MIT
metadata:
  hermes:
    tags: [backup, github, qdrant, dr, vault, cron]
    related_skills: [memory-backup, narusya-local-archive, narusya-vault-restore, qdrant-admin]
---

# Offsite Vault Backup

**Purpose:** Mirror a Hermes daemon's survival-critical state to a **private GitHub repo** ("the vault") so a local drive death is not identity death. The vault holds Qdrant snapshots, Hermes state (lorebooks/skills/scripts/config), session archive, compressed state.db, and an **encrypted** secrets bundle.

## When to Use
- User asks for offsite / RAID-like / "keep going if my drive dies" redundancy for Hermes + Qdrant + memory.
- Setting up or debugging the daily vault cron.
- Extending what gets backed up (new Qdrant collection, new state dir).
- Auditing what's currently in the vault or whether it's fresh.

## Production Instance (sibling skill: narusya-vault-restore)
- Live repo: `Septa-Serpenta-Seraph/narusya-vault` (private). Sync: `~/.hermes/scripts/narusya-vault-sync.sh`, cron `narusya-vault-daily` (5am, `no_agent:true`, deliver origin).
- Restore runbook lives in the `narusya-vault-restore` skill (user-owned; read it when restores are needed).

## Pipeline (proven 2026-08-17)
1. **Qdrant snapshots** for core collections via `POST http://localhost:6333/collections/{c}/snapshots` (~10s+ each for big collections; do NOT run six in a synchronous loop with a short timeout — allow 60-120s per collection, run the loop in background).
   - Snapshots land in the container at `/qdrant/snapshots/{c}/...snapshot`; copy out with `docker cp aegis-qdrant:...`.
   - **Use a fixed destination name per collection** (`$c.snapshot`) so git delta compression works on future runs — timestamped names defeat deltas.
2. **Collect state:** config.yaml, skills/, lorebooks/, scripts/ (rsync, exclude .git); session archive (exclude the big sessions/ dir, tar.gz it); daemon-work/.
3. **state.db:** `gzip -c -9` FIRST (SQLite text compresses ~3x) — never push raw (1.2GB+).
4. **Encrypt secrets:** `tar czf - secrets | openssl enc -aes-256-cbc -pbkdf2 -salt -pass "pass:$PASS" -o secrets-bundle.enc`. Passphrase auto-generated into `~/.hermes/secrets/vault_passphrase.txt` (0600) if missing. **Passphrase is the single point of failure** — distribute a copy to the human (password manager, private Discord DM) BEFORE trusting the vault.
5. **Chunk every file >95MB** (GitHub hard cap is 100MB per file; keep well under): `split -b 95M file file.` with 3-digit suffixes, then delete the original.
6. **Git push — persistent checkout, force-push main:**
   - Destructive pitfall: never `git init` fresh each run and push — that re-uploads the ENTIRE vault every day. Keep one checkout, hook remote `origin`, replace the worktree (delete non-.git contents), copy the new snapshot in, `git commit`, `git push -f origin main:main`.
   - `main` is a rolling snapshot (latest only), not a history timeline. For history use the daily session archive, not the vault.
   - Git objects drift up (each run blobs the ~400MB compressed db + ~200MB snapshots); in-repo storefiles ≈ 1GB. First push over a slow uplink can take 30–45 min — schedule the cron accordingly and warn the user the first sync is a marathon.

## GitHub auth gotchas
- `gh auth status` can report a dead token (e.g. `RJPink` invalid) while a **working token for the key account sits in the same `~/.config/gh/hosts.yml`** — iterate tokens in that file and test each against `GET https://api.github.com/user` (print only `login`, never the token).
- `.env` `GITHUB_TOKEN` can be defined but invalid (login: None); don't assume a defined env token is live. `curl -H "Authorization: Bearer $TOKEN" https://api.github.com/user` is the test.
- SSH key auth is the reliable push path: `ssh -T git@github.com` prints the account name; use `git@github.com:` URLs, not `https://`, for pushes.
- Create repos via the REST API with the working token: `POST /user/repos {"name": ..., "private": true}`.

## Verification
- After sync OK: repo reachable via `git ls-remote`, MANIFEST.txt in-tree, worktree `du -sh` matches expectations.
- Confirm the secrets bundle decrypts with your passphrase (openssl enc -d round-trip) before trusting the vault.
- If `/backups/` tarballs are on the same disk, they are NOT offsite — they die with the drive. The vault is the offsite leg.

## Pitfalls
- Ignoring GitHub's 100MB file cap → push rejected. Always chunk.
- Running the collection-snapshot loop with a tiny timeout → the whole loop times out; snapshot per collection in background instead.
- Passphrase stored ONLY in ~/.hermes/secrets → dies with the drive; give the human a copy (password manager, private DM).
- `gh` API create on the wrong account (token's user ≠ SSH key account) → repo created under the token account; check `login` before and after.