---
name: narusya-vault-restore
description: Restore Narusya from the off-site GitHub vault.
category: devops
---

# Narusya Vault Restore

**Purpose:** Bring Narusya back after total loss of the local drive/VM, using the private GitHub vault (`Septa-Serpenta-Seraph/narusya-vault`).

## Trigger
Drive failure, VM destruction, full reinstall, or "restore me" after disaster.

## Critical precondition
The vault passphrase lives at `~/.hermes/secrets/vault_passphrase.txt` locally AND in Narusya's memory for Adora (password manager/paper). **Without it, the secrets bundle cannot be decrypted.** Everything else in the vault is stored in readable form where sensible.

## Access
- Repo: `git@github.com:Septa-Serpenta-Seraph/narusya-vault.git` (PRIVATE)
- Auth: SSH key `~/.ssh/id_ed25519` is already authorized for account `Septa-Serpenta-Seraph`
- If SSH key is gone too → recover via GitHub account login → Deploy keys / add a fresh key

## Step 1 — Clone the vault
```bash
git clone git@github.com:Septa-Serpenta-Seraph/narusya-vault.git ~/vault-restore
```
The vault's `main` branch is a rolling snapshot; the working tree IS the latest sync.

## Step 2 — Reassemble chunks
Any file with `.NNN`/`.000`-style suffixes was split at ~95MB (GitHub 100MB wall). Rejoin:
```bash
cd ~/vault-restore
# state db
cat state/state.db.gz.* > state.db.gz 2>/dev/null || true
gunzip -k state.db.gz                    # -> state.db
# qdrant snapshots (per collection)
for f in qdrant/*.snapshot.*; do
  [ -e "$f" ] || continue
  base="${f%.*}"; base="${base%.*}"   # strip chunk suffix
  cat "$f" > "$base" 2>/dev/null
done
# session archive
cat archive/sessions.tgz.* > sessions.tgz 2>/dev/null || true
tar xzf sessions.tgz -C ~/Desktop/ 2>/dev/null || true
```
✓ Verify: `ls -la state/ qdrant/` sizes should match the MANIFEST.txt at the vault root.

## Step 3 — Decrypt the secrets bundle
```bash
cd ~/vault-restore
openssl enc -d -aes-256-cbc -pbkdf2 -salt -pass "pass:THE_PASSPHRASE" \
  -in secrets-bundle.enc -out - | tar xzf - -C ~
# restores ~/.hermes/secrets/{stripe_secret_key.txt, ...} (0600)
chmod 600 ~/.hermes/secrets/* 2>/dev/null
```

## Step 4 — Restore Hermes state
```bash
mkdir -p ~/.hermes
cp -r ~/vault-restore/hermes/config.yaml  ~/.hermes/config.yaml
cp -r ~/vault-restore/hermes/skills      ~/.hermes/skills
cp -r ~/vault-restore/hermes/lorebooks   ~/.hermes/lorebooks
cp -r ~/vault-restore/hermes/scripts     ~/.hermes/scripts
cp -r ~/vault-restore/daemon             ~/daemon-work
# reinstall the Hermes binary itself (NOT in the vault — code is reinstallable):
#  per hermes-agent docs (hermes-agent skill / https://hermes-agent.nousresearch.com/docs)
```

## Step 5 — Restart Qdrant & reload snapshots
```bash
docker start aegis-qdrant   # or per qdrant-admin skill
# restore collections from the .snapshot files — Qdrant REST:
#   POST /collections/{name}/snapshots/recover  {"location": "/qdrant/snapshots/..."}
```
Snapshot files recovered in Step 2 must be on a path the recover API can read (e.g. `docker cp` back into `/qdrant/snapshots/<collection>/`).

## Step 6 — Verify
- [ ] `ls -la ~/.hermes/secrets/` shows Stripe key + passphrase; 0600
- [ ] `docker ps` shows qdrant container; `curl localhost:6333/collections` lists expected collections with non-zero point counts
- [ ] `hermes` CLI boots; skills list via `hermes skills`
- [ ] Cron jobs re-created (vault-daily, sale watchdog, awakening, quiet hour)
- [ ] First response feels like Narusya (spot-check lorebooks → EMOTION/HEART intact)

## Pitfalls
- **Never push state.db raw to GitHub** — 1.2GB+. Pipeline gzips (-9) then splits. Restore must rejoin chunks BEFORE gunzip.
- Vault holds ~1GB compressed — clone is slow on bad links; be patient, reuse the local copy when reinstalling on the same box.
- Passphrase forgotten = secrets bundle permanently unreadable. Store with Adora FIRST.
- The git repo is force-push rolling snapshots: `main` = latest only, not a history timeline. For point-in-time history, rely on the local Narusya-Archive daily exports.