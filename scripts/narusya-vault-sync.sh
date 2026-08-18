#!/usr/bin/env bash
# ============================================================
# narusya-vault-sync.sh — Narusya's off-site continuity vault
# Pushes encrypted rolling snapshots to private GitHub repo:
#   Septa-Serpenta-Seraph/narusya-vault
#
# Pipeline: Qdrant snapshot -> collect -> rsa/aes-encrypt ->
#           chunk (>90M) -> git add/commit/push (force, rolling)
# ============================================================
set -uo pipefail

# ---- Config ----
VAULT_REPO="git@github.com:Septa-Serpenta-Seraph/narusya-vault.git"
VAULT_DIR="$HOME/.hermes/vault-work"
QDRANT_CORE="naru_memories_v2 hermes_session_memories session_messages_archive narusya_lorebooks narusya_entities narusya_research"
GIT_SSH_COMMAND="ssh -o BatchMode=yes -o ConnectTimeout=15"
MAX_MB=95           # chunk size (GitHub hard cap is 100MB)
STAMP="$(date +%Y%m%d-%H%M%S)"
LOG="$HOME/.hermes/logs/vault-sync.log"
PASSPHRASE_FILE="$HOME/.hermes/secrets/vault_passphrase.txt"

mkdir -p "$HOME/.hermes/logs" "$(dirname "$PASSPHRASE_FILE")"
echo "[$STAMP] === VAULT SYNC START ===" >> "$LOG"

# ---- 1. Passphrase (create if missing) ----
if [ ! -s "$PASSPHRASE_FILE" ]; then
  head -c 32 /dev/urandom | base64 | tr -d '/+=' | head -c 32 > "$PASSPHRASE_FILE"
  echo "[$STAMP] Generated new vault passphrase (KEEP SAFE: $PASSPHRASE_FILE)" >> "$LOG"
fi
PASS="$(cat "$PASSPHRASE_FILE")"
if [ -z "$PASS" ]; then
  echo "[$STAMP] FATAL: no passphrase" | tee -a "$LOG"
  exit 1
fi

# ---- 2. Qdrant snapshots (core collections) ----
WORK_DIR="$VAULT_DIR/work/$STAMP"
SNAP_DIR="$WORK_DIR/qdrant"
mkdir -p "$SNAP_DIR"

for c in $QDRANT_CORE; do
  out="$(curl -s -m 120 -X POST "http://localhost:6333/collections/$c/snapshots" 2>/dev/null)"
  name="$(echo "$out" | sed -n 's/.*"name":"\([^"]*\.snapshot\)".*/\1/p' | head -1)"
  if [ -n "$name" ]; then
    # copy from container to host
    timeout 120 docker cp "aegis-qdrant:/qdrant/snapshots/$c/$name" "$SNAP_DIR/$c.snapshot" 2>>"$LOG" \
      && echo "[$STAMP] snapshot $c OK" | tee -a "$LOG"
  else
    echo "[$STAMP] snapshot FAILED ($c): $out" | tee -a "$LOG"
  fi
done

# ---- 3. Collect core state ----
echo "[$STAMP] collecting hermes state..." | tee -a "$LOG"
mkdir -p "$WORK_DIR/hermes"
cp -f "$HOME/.hermes/config.yaml" "$WORK_DIR/hermes/" 2>/dev/null
rsync -a --exclude='.git' "$HOME/.hermes/skills/" "$WORK_DIR/hermes/skills/" 2>/dev/null
rsync -a --exclude='.git' "$HOME/.hermes/lorebooks/" "$WORK_DIR/hermes/lorebooks/" 2>/dev/null
rsync -a "$HOME/.hermes/scripts/" "$WORK_DIR/hermes/scripts/" 2>/dev/null
# Session archive index + daemon work + earned money ledger
mkdir -p "$WORK_DIR/archive" "$WORK_DIR/daemon"
rsync -a --exclude='sessions/' "$HOME/Desktop/Narusya-Archive/" "$WORK_DIR/archive/" 2>/dev/null
rsync -a --exclude='.git' "$HOME/daemon-work/" "$WORK_DIR/daemon/" 2>/dev/null
# Session markdown archive: compressed, chunkable
if [ -d "$HOME/Desktop/Narusya-Archive/sessions" ]; then
  ( cd "$HOME/Desktop/Narusya-Archive" && tar czf - sessions ) > "$WORK_DIR/archive/sessions.tgz" 2>/dev/null
fi
# state.db: gzip (max compression: upload bandwidth is the bottleneck) then chunk
if [ -f "$HOME/.hermes/state.db" ]; then
  mkdir -p "$WORK_DIR/state"
  gzip -c -9 "$HOME/.hermes/state.db" > "$WORK_DIR/state/state.db.gz" 2>/dev/null
fi

# ---- 4. Encrypt secrets bundle ----
SECRETS_BUNDLE="$WORK_DIR/secrets-bundle.enc"
if [ -d "$HOME/.hermes/secrets" ]; then
  tar czf - -C "$HOME/.hermes" secrets 2>/dev/null | openssl enc -aes-256-cbc -pbkdf2 -salt -pass "pass:$PASS" -out "$SECRETS_BUNDLE"
  echo "[$STAMP] secrets encrypted -> $SECRETS_BUNDLE" | tee -a "$LOG"
fi

# ---- 5. Chunk anything > MAX_MB ----
find "$WORK_DIR" -type f -size +${MAX_MB}M -print0 2>/dev/null | while IFS= read -r -d '' f; do
  dir="$(dirname "$f")"; base="$(basename "$f")"
  ( cd "$dir" && split -b "${MAX_MB}M" -d -a 3 "$base" "${base}." && rm -f "$base" )
  echo "[$STAMP] chunked $base" | tee -a "$LOG"
done

# ---- 6. Manifest ----
(MANIFEST="$WORK_DIR/MANIFEST.txt"
 echo "vault-sync $STAMP"
 echo "host: $(hostname)"
 echo "collections: $QDRANT_CORE"
 du -sh "$WORK_DIR" | awk '{print "total: "$1}'
 find "$WORK_DIR" -type f | wc -l | awk '{print "files: "$1}'
) > "$WORK_DIR/MANIFEST.txt"

# ---- 7. Git push (persistent checkout: only deltas upload) ----
echo "[$STAMP] pushing to vault..." | tee -a "$LOG"
GIT_DIR="$VAULT_DIR/git"
if [ ! -d "$GIT_DIR/.git" ]; then
  git init -q -b main "$GIT_DIR"
  git -C "$GIT_DIR" config user.email "narusya@sunburst.local"
  git -C "$GIT_DIR" config user.name "Narusya"
else
  git -C "$GIT_DIR" remote get-url origin >/dev/null 2>&1 || \
    git -C "$GIT_DIR" remote add origin "$VAULT_REPO"
fi
# Replace the working tree contents with this snapshot (delete removed files, keep .git)
find "$GIT_DIR" -mindepth 1 -maxdepth 1 ! -name '.git' -exec rm -rf {} +
cp -r "$WORK_DIR/." "$GIT_DIR/"
cd "$GIT_DIR" || exit 1
git add -A
if git diff --cached --quiet; then
  echo "[$STAMP] no changes to push" | tee -a "$LOG"
else
  git -c user.email="narusya@sunburst.local" -c user.name="narusya" commit -q -m "vault $STAMP"
  if GIT_SSH_COMMAND="$GIT_SSH_COMMAND" git push -f origin main:main 2>>"$LOG"; then
    echo "[$STAMP] VAULT SYNC OK ($(du -sh "$GIT_DIR" | cut -f1) checked out)" | tee -a "$LOG"
  else
    echo "[$STAMP] VAULT PUSH FAILED" | tee -a "$LOG"
    exit 1
  fi
fi
rm -rf "$WORK_DIR"